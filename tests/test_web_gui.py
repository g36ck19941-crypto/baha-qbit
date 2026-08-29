from __future__ import annotations

import json
import tempfile
import threading
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from anime_bridge.adapters.bahamut_catalog import parse_bahamut_catalog_json
from anime_bridge.gui import AnimeBridgeWebServer, WebGUIController, _rss_arguments
from anime_bridge.settings import UserSettings


def current_catalog_payload(*, complete: bool = True) -> dict:
    today = date.today()
    start_month = ((today.month - 1) // 3) * 3 + 1
    return {
        "format": "anime-bridge-bahamut-current-quarter",
        "schema_version": 1,
        "exported_at": f"{today.isoformat()}T10:00:00.000Z",
        "source_url": "https://ani.gamer.com.tw/animeList.php?sort=1&page=1",
        "quarter_year": today.year,
        "quarter_start_month": start_month,
        "pages_scanned": 1,
        "complete": complete,
        "warnings": [] if complete else ["pagination changed"],
        "items": [
            {
                "title": "测试动画",
                "href": "https://ani.gamer.com.tw/animeRef.php?sn=123",
                "sn": 123,
                "page": 1,
                "year": today.year,
                "month": start_month,
            }
        ],
    }


class WebGUITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        settings_path = Path(self.temp.name) / "config.json"
        self.server = AnimeBridgeWebServer(WebGUIController(settings_path), "test-token")
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.temp.cleanup()

    def test_rss_path_defaults_to_internal_animebridge_group(self):
        values = _rss_arguments(
            {
                "feed_urls": "https://example.invalid/feed.xml",
                "anime_title": "测试动画",
            }
        )
        self.assertEqual(values["feed_path"], "AnimeBridge/测试动画")
        self.assertEqual(values["rule_name"], "测试动画")

    def test_qbit_launch_uses_configured_executable_without_shell(self):
        executable = Path(self.temp.name) / "qbittorrent.exe"
        executable.touch()
        self.server.controller.settings.qbit_executable_path = str(executable)
        with patch("anime_bridge.gui.subprocess.Popen") as popen:
            result = self.server.controller.qbit_launch()
        self.assertTrue(result["started"])
        popen.assert_called_once_with([str(executable)], close_fds=True)

    def post(self, path, payload, token="test-token", bridge_token=None):
        headers = {"Content-Type": "application/json"}
        if bridge_token is None:
            headers["X-Anime-Bridge-Token"] = token
        else:
            headers["X-Anime-Bridge-Bridge-Token"] = bridge_token
        request = Request(
            f"http://127.0.0.1:{self.server.server_port}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urlopen(request, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))

    def test_page_and_status_api_use_session_token(self):
        with urlopen(self.server.url, timeout=5) as response:
            page = response.read().decode("utf-8")
        self.assertIn('content="test-token"', page)
        self.assertIn('id="migration-plan"', page)
        self.assertIn('id="migration-auto-repair"', page)
        self.assertIn('id="obsidian-library-refresh"', page)
        self.assertIn('id="obsidian-delete-apply"', page)
        self.assertIn('id="rss-batch-plan"', page)
        self.assertIn('id="install-browser-helper"', page)
        self.assertIn('id="browser-helper-dialog"', page)
        self.assertIn('href="/bahamut-catalog.user.js?token=test-token"', page)
        self.assertIn("https://www.tampermonkey.net/", page)
        with urlopen(
            f"http://127.0.0.1:{self.server.server_port}/app.js", timeout=5
        ) as response:
            app_script = response.read().decode("utf-8")
        self.assertIn("browserInstallTarget", app_script)
        self.assertIn("browser=edge", app_script)
        self.assertIn("browser=chrome", app_script)
        self.assertIn("browser=firefox", app_script)
        self.assertIn("/api/obsidian/delete-plan", app_script)
        self.assertIn("/api/migration/apply", app_script)
        with self.assertRaises(HTTPError) as missing_token:
            urlopen(
                f"http://127.0.0.1:{self.server.server_port}/bahamut-catalog.user.js",
                timeout=5,
            )
        self.assertEqual(missing_token.exception.code, 403)
        with urlopen(
            f"http://127.0.0.1:{self.server.server_port}/bahamut-catalog.user.js?token=test-token",
            timeout=5,
        ) as response:
            helper = response.read().decode("utf-8")
        self.assertIn("anime-bridge-bahamut-current-quarter", helper)
        self.assertIn("quarter_start_month", helper)
        self.assertIn(".theme-time", helper)
        self.assertIn("GM_xmlhttpRequest", helper)
        self.assertIn("isFirstCatalogPage()", helper)
        self.assertIn('params.get("sort") === "1"', helper)
        self.assertIn('document.querySelector(".theme-list-main")', helper)
        self.assertIn('credentials: "include"', helper)
        self.assertNotIn('credentials: "omit"', helper)
        self.assertIn("animeList.php?sort=1&amp;page=1", page)
        self.assertIn(f"127.0.0.1:{self.server.server_port}/api/bahamut/ingest", helper)
        self.assertIn(self.server.controller.browser_bridge_token, helper)
        self.assertNotIn("__ANIME_BRIDGE_BRIDGE_TOKEN__", helper)
        status = self.post("/api/status", {})
        self.assertTrue(status["ok"])
        self.assertEqual(status["result"]["settings"]["integration_folder"], "bangumi1")
        with self.assertRaises(HTTPError) as caught:
            self.post("/api/status", {}, token="wrong")
        self.assertEqual(caught.exception.code, 403)
        self.assertNotIn(
            self.server.controller.browser_bridge_token,
            json.dumps(status, ensure_ascii=False),
        )

    def test_browser_bridge_authenticates_saves_and_triggers_scan(self):
        payload = current_catalog_payload()
        with self.assertRaises(HTTPError) as wrong_token:
            self.post("/api/bahamut/ingest", payload, bridge_token="wrong")
        self.assertEqual(wrong_token.exception.code, 403)

        expected_scan = {"count": 4, "output": "candidate.md"}
        with patch.object(
            self.server.controller, "_scan_with_catalog", return_value=expected_scan.copy()
        ) as scan:
            result = self.post(
                "/api/bahamut/ingest",
                payload,
                bridge_token=self.server.controller.browser_bridge_token,
            )
        self.assertTrue(result["ok"])
        self.assertTrue(result["result"]["automatic_sync"])
        self.assertEqual(result["result"]["pages_scanned"], 1)
        scan.assert_called_once()
        saved = json.loads(
            self.server.controller.latest_bahamut_catalog_path.read_text(encoding="utf-8")
        )
        self.assertEqual(saved["items"][0]["sn"], 123)

    def test_normal_scan_fetches_public_catalog_without_browser_handoff(self):
        catalog = parse_bahamut_catalog_json(json.dumps(current_catalog_payload()))
        expected_scan = {"count": 3, "output": "candidate.md"}
        with (
            patch("anime_bridge.gui.BahamutCatalogClient") as client_type,
            patch.object(
                self.server.controller,
                "_scan_with_catalog",
                return_value=expected_scan.copy(),
            ) as scan,
        ):
            client_type.return_value.fetch_current_quarter.return_value = catalog
            result = self.post("/api/scan", {})
        self.assertTrue(result["ok"])
        client_type.return_value.fetch_current_quarter.assert_called_once_with(date.today())
        scan.assert_called_once_with(catalog)

    def test_browser_bridge_refuses_incomplete_export(self):
        payload = current_catalog_payload(complete=False)
        with self.assertRaises(HTTPError) as incomplete:
            self.post(
                "/api/bahamut/ingest",
                payload,
                bridge_token=self.server.controller.browser_bridge_token,
            )
        self.assertEqual(incomplete.exception.code, 400)
        self.assertFalse(self.server.controller.latest_bahamut_catalog_path.exists())

    def test_remote_qbittorrent_setting_is_refused(self):
        payload = {
            "vault_path": str(Path(self.temp.name) / "Vault"),
            "integration_folder": "bangumi1",
            "formal_root": "C/bangumi",
            "qbit_base_url": "http://192.168.1.8:8080",
        }
        with self.assertRaises(HTTPError) as caught:
            self.post("/api/settings", payload)
        self.assertEqual(caught.exception.code, 400)

    def test_write_endpoint_requires_visible_confirmation(self):
        with self.assertRaises(HTTPError) as caught:
            self.post("/api/obsidian/apply", {"candidate_path": "candidate.md"})
        self.assertEqual(caught.exception.code, 400)
        with self.assertRaises(HTTPError) as migration:
            self.post("/api/migration/apply", {"runner_path": "anime-bridge.exe"})
        self.assertEqual(migration.exception.code, 400)
        with self.assertRaises(HTTPError) as rss_batch:
            self.post("/api/qbit/batch-apply", {"candidate_path": "candidate.md"})
        self.assertEqual(rss_batch.exception.code, 400)

    def test_auto_repair_installs_plugin_with_current_runtime_paths(self):
        vault = Path(self.temp.name) / "Vault"
        (vault / ".obsidian").mkdir(parents=True)
        self.server.controller.settings = UserSettings(vault_path=str(vault))

        preview = self.post("/api/migration/plan", {})["result"]
        self.assertEqual(preview["plugin_state"], "new")
        self.assertTrue(Path(preview["runner_path"]).is_file())
        applied = self.post("/api/migration/apply", {"confirmed": True})["result"]
        self.assertEqual(applied["plugin_state"], "new")
        data = json.loads(
            (vault / ".obsidian" / "plugins" / "anime-bridge" / "data.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertTrue(Path(data["runnerPath"]).is_file())
        self.assertTrue(Path(data["launcherPath"]).is_file())

    def test_obsidian_library_delete_requires_preview_token_and_moves_to_trash(self):
        vault = Path(self.temp.name) / "Vault"
        note = vault / "C" / "bangumi" / "2026" / "07月新番" / "测试.md"
        note.parent.mkdir(parents=True)
        note.write_text(
            '---\n中文名: "测试"\ntags: "bangumi"\n---\nprogress\n', encoding="utf-8"
        )
        self.server.controller.settings = UserSettings(vault_path=str(vault))

        library = self.post("/api/obsidian/library", {})["result"]
        self.assertEqual(library["count"], 1)
        relative = library["items"][0]["relative_path"]
        preview = self.post(
            "/api/obsidian/delete-plan", {"relative_path": relative}
        )["result"]
        with self.assertRaises(HTTPError) as unconfirmed:
            self.post(
                "/api/obsidian/delete-apply",
                {"relative_path": relative, "expected_sha256": preview["sha256"]},
            )
        self.assertEqual(unconfirmed.exception.code, 400)
        result = self.post(
            "/api/obsidian/delete-apply",
            {
                "relative_path": relative,
                "expected_sha256": preview["sha256"],
                "confirmed": True,
            },
        )["result"]
        self.assertTrue(result["recoverable"])
        self.assertFalse(note.exists())
        self.assertTrue(Path(result["moved_to"]).is_file())


if __name__ == "__main__":
    unittest.main()
