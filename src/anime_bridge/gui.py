"""Loopback-only web interface over Anime Bridge's stable workflows."""

from __future__ import annotations

import argparse
import json
import secrets
import sys
import threading
import webbrowser
from dataclasses import replace
from datetime import date
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Sequence
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

from anime_bridge import __version__
from anime_bridge.adapters.bangumi import BangumiClient
from anime_bridge.adapters.bahamut_catalog import (
    BahamutCatalogExport,
    load_bahamut_catalog,
    parse_bahamut_catalog_json,
)
from anime_bridge.ai.service import AnimeBridgeAIService, WRITE_CONFIRMATION
from anime_bridge.migration import apply_migration, plan_migration
from anime_bridge.matching import normalized_title_forms
from anime_bridge.renderers import render_candidate_markdown
from anime_bridge.settings import UserSettings, default_settings_path
from anime_bridge.storage import write_text_atomic, write_text_new_atomic
from anime_bridge.workflows import CurrentQuarterScanner, subtract_bahamut_catalog


WEB_ROOT = Path(__file__).with_name("web")
MAX_REQUEST_BYTES = 1024 * 1024
DEFAULT_GUI_PORT = 18765


class WebGUIController:
    def __init__(self, settings_path: Path | None = None) -> None:
        self.settings_path = settings_path or default_settings_path()
        self.browser_bridge_token_path = self.settings_path.with_name(
            "browser-bridge-token.txt"
        )
        self.latest_bahamut_catalog_path = self.settings_path.with_name(
            "bahamut-current-quarter-latest.json"
        )
        self.browser_bridge_token = self._load_or_create_browser_bridge_token()
        self._ingest_lock = threading.Lock()
        try:
            self.settings = UserSettings.load(self.settings_path)
        except (OSError, ValueError, json.JSONDecodeError):
            self.settings = UserSettings()

    def _load_or_create_browser_bridge_token(self) -> str:
        try:
            token = self.browser_bridge_token_path.read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            token = secrets.token_urlsafe(32)
            try:
                write_text_new_atomic(self.browser_bridge_token_path, token + "\n")
            except FileExistsError:
                token = self.browser_bridge_token_path.read_text(encoding="utf-8").strip()
        if len(token) < 32:
            raise ValueError("Browser bridge pairing token is invalid")
        return token

    def public_status(self) -> dict[str, Any]:
        return {
            "version": __version__,
            "settings": self.settings_dict(),
            "runner_path": str(Path(sys.executable).resolve()) if getattr(sys, "frozen", False) else "",
            "bahamut_auto_sync": {
                "configured": True,
                "has_export": self.latest_bahamut_catalog_path.is_file(),
            },
            "milestones": [
                {"name": "Bangumi 当季扫描", "state": "ready"},
                {"name": "动画疯公开当季目录同步", "state": "bridge_ready"},
                {"name": "Obsidian 入库核心", "state": "ready"},
                {"name": "qBittorrent RSS 核心", "state": "ready"},
                {"name": "GitHub 私有远端", "state": "ready"},
                {"name": "Windows 可迁移包", "state": "ready"},
            ],
        }

    def settings_dict(self) -> dict[str, str]:
        return {
            "vault_path": self.settings.vault_path,
            "integration_folder": self.settings.integration_folder,
            "formal_root": self.settings.formal_root,
            "qbit_base_url": self.settings.qbit_base_url,
        }

    def update_settings(self, payload: dict[str, Any]) -> dict[str, Any]:
        values: dict[str, str] = {}
        for key in self.settings_dict():
            value = payload.get(key)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Setting {key} must be a non-empty string")
            values[key] = value.strip()
        candidate = UserSettings(**values)
        AnimeBridgeAIService(
            Path(candidate.vault_path), qbit_base_url=candidate.qbit_base_url
        )
        candidate.save(self.settings_path)
        self.settings = candidate
        return {"saved": True, "path": str(self.settings_path)}

    def scan_current(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload or {}
        catalog_path_text = str(payload.get("bahamut_catalog_path") or "").strip()
        catalog = None
        if catalog_path_text:
            catalog = load_bahamut_catalog(Path(catalog_path_text))
        elif self.latest_bahamut_catalog_path.is_file():
            catalog = load_bahamut_catalog(self.latest_bahamut_catalog_path)
        return self._scan_with_catalog(catalog)

    def ingest_bahamut_catalog(self, payload: dict[str, Any]) -> dict[str, Any]:
        serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        catalog = parse_bahamut_catalog_json(serialized)
        if not catalog.complete or catalog.warnings:
            details = "; ".join(catalog.warnings) or "catalog marked incomplete"
            raise ValueError(
                "Bahamut catalog is incomplete and cannot prove safe subtraction: "
                + details
            )
        today = date.today()
        expected_start_month = ((today.month - 1) // 3) * 3 + 1
        if (catalog.quarter_year, catalog.quarter_start_month) != (
            today.year,
            expected_start_month,
        ):
            raise ValueError("Bahamut catalog does not describe the current quarter")
        with self._ingest_lock:
            write_text_atomic(
                self.latest_bahamut_catalog_path,
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            )
            result = self._scan_with_catalog(catalog)
        result["automatic_sync"] = True
        result["pages_scanned"] = catalog.pages_scanned
        return result

    def _scan_with_catalog(
        self, catalog: BahamutCatalogExport | None
    ) -> dict[str, Any]:
        result = CurrentQuarterScanner(BangumiClient()).scan(date.today())
        difference = None
        if catalog is not None:
            difference = subtract_bahamut_catalog(result.subjects, catalog.items)
            result = replace(result, subjects=difference.candidates)
        directory = Path(self.settings.vault_path) / self.settings.integration_folder
        output = directory / f"{result.year}-{result.quarter.start_month:02d}-动画候选.md"
        write_text_atomic(
            output,
            render_candidate_markdown(
                result,
                bahamut_difference=difference,
                bahamut_catalog_count=(
                    len(catalog.items) if catalog is not None else 0
                ),
                bahamut_exported_at=(
                    catalog.exported_at if catalog is not None else ""
                ),
            ),
        )
        return {
            "count": len(result.subjects),
            "excluded_without_japan_tag": len(result.excluded_without_japan_tag),
            "output": str(output),
            "bahamut_subtraction": "completed" if difference is not None else "not_run",
            "bahamut_catalog_titles": (
                len(catalog.items) if catalog is not None else 0
            ),
            "bahamut_exact_removed": (
                len(difference.exact_matches) if difference is not None else 0
            ),
            "bahamut_review_matches": (
                len(difference.review_matches) if difference is not None else 0
            ),
            "bahamut_export_warnings": (
                list(catalog.warnings) if catalog is not None else []
            ),
        }

    def _service(self, *, allow_writes: bool = False) -> AnimeBridgeAIService:
        return AnimeBridgeAIService(
            Path(self.settings.vault_path),
            formal_root=self.settings.formal_root,
            qbit_base_url=self.settings.qbit_base_url,
            allow_writes=allow_writes,
        )

    def obsidian_plan(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._service().plan_obsidian_import(_required_text(payload, "candidate_path"))

    def obsidian_apply(self, payload: dict[str, Any]) -> dict[str, Any]:
        _require_browser_confirmation(payload)
        return self._service(allow_writes=True).apply_obsidian_import(
            _required_text(payload, "candidate_path"), WRITE_CONFIRMATION
        )

    def qbit_status(self) -> dict[str, Any]:
        return self._service().qbit_status()

    def qbit_plan(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._service().plan_qbit_rss(**_rss_arguments(payload))

    def qbit_apply(self, payload: dict[str, Any]) -> dict[str, Any]:
        _require_browser_confirmation(payload)
        return self._service(allow_writes=True).apply_qbit_rss(
            **_rss_arguments(payload), confirmation=WRITE_CONFIRMATION
        )

    def qbit_batch_plan(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._service().plan_candidate_rss(**_batch_rss_arguments(payload))

    def qbit_batch_apply(self, payload: dict[str, Any]) -> dict[str, Any]:
        _require_browser_confirmation(payload)
        return self._service(allow_writes=True).apply_candidate_rss(
            **_batch_rss_arguments(payload), confirmation=WRITE_CONFIRMATION
        )

    def migration_plan(self, payload: dict[str, Any]) -> dict[str, Any]:
        runner = Path(_required_text(payload, "runner_path"))
        return plan_migration(
            self.settings, self.settings_path, runner
        ).as_dict()

    def migration_apply(self, payload: dict[str, Any]) -> dict[str, Any]:
        _require_browser_confirmation(payload)
        runner = Path(_required_text(payload, "runner_path"))
        plan = plan_migration(self.settings, self.settings_path, runner)
        written = apply_migration(plan, self.settings, self.settings_path)
        return {"written": [str(path) for path in written]}


def _required_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} is required")
    return value.strip()


def _require_browser_confirmation(payload: dict[str, Any]) -> None:
    if payload.get("confirmed") is not True:
        raise ValueError("Write operation requires the visible browser confirmation")


def _rss_arguments(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "feed_url": _required_text(payload, "feed_url"),
        "feed_path": _required_text(payload, "feed_path"),
        "rule_name": _required_text(payload, "rule_name"),
        "must_contain": str(payload.get("must_contain") or ""),
        "must_not_contain": str(payload.get("must_not_contain") or ""),
        "use_regex": bool(payload.get("use_regex", False)),
        "episode_filter": str(payload.get("episode_filter") or ""),
        "smart_filter": bool(payload.get("smart_filter", False)),
        "category": str(payload.get("category") or ""),
        "save_path": str(payload.get("save_path") or ""),
    }


def _batch_rss_arguments(payload: dict[str, Any]) -> dict[str, Any]:
    raw_terms = str(payload.get("extra_terms") or "")
    terms = tuple(
        term.strip()
        for line in raw_terms.splitlines()
        for term in line.split(",")
        if term.strip()
    )
    return {
        "candidate_path": _required_text(payload, "candidate_path"),
        "provider": _required_text(payload, "provider"),
        "extra_terms": terms,
        "custom_template": str(payload.get("custom_template") or ""),
        "must_contain": str(payload.get("must_contain") or ""),
        "must_not_contain": str(payload.get("must_not_contain") or ""),
        "episode_filter": str(payload.get("episode_filter") or ""),
        "category": str(payload.get("category") or "anime"),
        "save_root": str(payload.get("save_root") or ""),
    }


class AnimeBridgeWebServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, controller: WebGUIController, token: str, port: int = 0) -> None:
        self.controller = controller
        self.token = token
        super().__init__(("127.0.0.1", port), AnimeBridgeRequestHandler)

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.server_port}/?token={self.token}"


class AnimeBridgeRequestHandler(BaseHTTPRequestHandler):
    server: AnimeBridgeWebServer

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/":
            supplied = parse_qs(parsed.query).get("token", [""])[0]
            if supplied != self.server.token:
                self._error(HTTPStatus.FORBIDDEN, "Invalid local session token")
                return
            html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")
            html = html.replace("__ANIME_BRIDGE_TOKEN__", self.server.token)
            self._bytes(HTTPStatus.OK, html.encode("utf-8"), "text/html; charset=utf-8")
            return
        if parsed.path in {"/bahamut-catalog.user.js", "/bahamut-export.user.js"}:
            supplied = parse_qs(parsed.query).get("token", [""])[0]
            if supplied != self.server.token:
                self._error(HTTPStatus.FORBIDDEN, "Invalid local session token")
                return
            helper = (WEB_ROOT / "bahamut-catalog.user.js").read_text(encoding="utf-8")
            helper = helper.replace(
                "__ANIME_BRIDGE_ENDPOINT__",
                f"http://127.0.0.1:{self.server.server_port}/api/bahamut/ingest",
            ).replace(
                "__ANIME_BRIDGE_BRIDGE_TOKEN__",
                self.server.controller.browser_bridge_token,
            )
            self._bytes(
                HTTPStatus.OK, helper.encode("utf-8"), "text/javascript; charset=utf-8"
            )
            return
        if parsed.path in {"/app.css", "/app.js"}:
            filename = parsed.path.lstrip("/")
            content_type = (
                "text/css; charset=utf-8"
                if filename.endswith(".css")
                else "text/javascript; charset=utf-8"
            )
            self._bytes(HTTPStatus.OK, (WEB_ROOT / filename).read_bytes(), content_type)
            return
        if parsed.path == "/favicon.ico":
            self._bytes(HTTPStatus.NO_CONTENT, b"", "image/x-icon")
            return
        self._error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/bahamut/ingest":
            expected = self.server.controller.browser_bridge_token
            supplied = self.headers.get("X-Anime-Bridge-Bridge-Token")
            if not supplied or not secrets.compare_digest(supplied, expected):
                self._error(HTTPStatus.FORBIDDEN, "Invalid browser bridge pairing token")
                return
        elif self.headers.get("X-Anime-Bridge-Token") != self.server.token:
            self._error(HTTPStatus.FORBIDDEN, "Invalid local session token")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._error(HTTPStatus.BAD_REQUEST, "Invalid content length")
            return
        if length > MAX_REQUEST_BYTES:
            self._error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "Request is too large")
            return
        try:
            body = self.rfile.read(length)
            payload = json.loads(body.decode("utf-8")) if body else {}
            if not isinstance(payload, dict):
                raise ValueError("JSON body must be an object")
            result = self._dispatch(path, payload)
        except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
            self._json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)})
            return
        self._json(HTTPStatus.OK, {"ok": True, "result": result})

    def _dispatch(self, path: str, payload: dict[str, Any]) -> Any:
        controller = self.server.controller
        routes = {
            "/api/status": lambda: controller.public_status(),
            "/api/settings": lambda: controller.update_settings(payload),
            "/api/scan": lambda: controller.scan_current(payload),
            "/api/bahamut/ingest": lambda: controller.ingest_bahamut_catalog(payload),
            "/api/obsidian/plan": lambda: controller.obsidian_plan(payload),
            "/api/obsidian/apply": lambda: controller.obsidian_apply(payload),
            "/api/qbit/status": lambda: controller.qbit_status(),
            "/api/qbit/plan": lambda: controller.qbit_plan(payload),
            "/api/qbit/apply": lambda: controller.qbit_apply(payload),
            "/api/qbit/batch-plan": lambda: controller.qbit_batch_plan(payload),
            "/api/qbit/batch-apply": lambda: controller.qbit_batch_apply(payload),
            "/api/migration/plan": lambda: controller.migration_plan(payload),
            "/api/migration/apply": lambda: controller.migration_apply(payload),
        }
        if path == "/api/shutdown":
            threading.Thread(target=self.server.shutdown, daemon=True).start()
            return {"shutting_down": True}
        operation = routes.get(path)
        if operation is None:
            raise ValueError("Unknown API operation")
        return operation()

    def _json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
        self._bytes(status, data, "application/json; charset=utf-8")

    def _error(self, status: HTTPStatus, message: str) -> None:
        self._json(status, {"ok": False, "error": message})

    def _bytes(self, status: HTTPStatus, data: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self' https: data:; connect-src 'self'; frame-ancestors 'none'",
        )
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format: str, *args: Any) -> None:
        return


def _smoke_test(server: AnimeBridgeWebServer) -> None:
    if "网络胜利组" not in normalized_title_forms("網路勝利組"):
        raise RuntimeError("Regional title dictionaries were not packaged")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    with urlopen(server.url, timeout=5) as response:
        page = response.read().decode("utf-8")
    if "Anime Bridge" not in page:
        raise RuntimeError("Web GUI page did not render")
    with urlopen(
        f"http://127.0.0.1:{server.server_port}/bahamut-catalog.user.js?token={server.token}",
        timeout=5,
    ) as response:
        helper = response.read().decode("utf-8")
    if "anime-bridge-bahamut-current-quarter" not in helper:
        raise RuntimeError("Bahamut browser helper was not packaged")
    request = Request(
        f"http://127.0.0.1:{server.server_port}/api/status",
        data=b"{}",
        headers={
            "Content-Type": "application/json",
            "X-Anime-Bridge-Token": server.token,
        },
        method="POST",
    )
    with urlopen(request, timeout=5) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not payload.get("ok") or payload["result"].get("version") != __version__:
        raise RuntimeError("Web GUI status API smoke test failed")
    server.shutdown()
    thread.join(timeout=5)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Anime Bridge local web interface")
    parser.add_argument("--smoke-test", action="store_true")
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--settings", type=Path, default=None)
    parser.add_argument("--port", type=int, default=DEFAULT_GUI_PORT)
    args = parser.parse_args(argv)
    server = AnimeBridgeWebServer(
        WebGUIController(args.settings), secrets.token_urlsafe(24), args.port
    )
    if args.smoke_test:
        _smoke_test(server)
        print("Web GUI smoke test passed.")
        return 0
    print(f"Anime Bridge interface: {server.url}", flush=True)
    if not args.no_browser:
        webbrowser.open(server.url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0
