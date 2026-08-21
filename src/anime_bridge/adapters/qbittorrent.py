"""Small standard-library client for qBittorrent's local WebUI API."""

from __future__ import annotations

import ipaddress
import json
from http.cookiejar import CookieJar
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import HTTPCookieProcessor, OpenerDirector, Request, build_opener


class QBittorrentAPIError(RuntimeError):
    """A contextual qBittorrent connection or API failure."""


def _validate_local_base_url(base_url: str) -> str:
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("qBittorrent base URL must be an HTTP(S) URL")
    hostname = parsed.hostname
    if hostname != "localhost":
        try:
            if not ipaddress.ip_address(hostname).is_loopback:
                raise ValueError("qBittorrent base URL must point to this computer")
        except ValueError as exc:
            if str(exc) == "qBittorrent base URL must point to this computer":
                raise
            raise ValueError("qBittorrent base URL must point to this computer") from exc
    return base_url.rstrip("/")


class QBittorrentClient:
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8080",
        *,
        timeout: float = 10,
        opener: OpenerDirector | None = None,
    ) -> None:
        self.base_url = _validate_local_base_url(base_url)
        self.timeout = timeout
        self._opener = opener or build_opener(HTTPCookieProcessor(CookieJar()))

    def _request(
        self, endpoint: str, *, data: dict[str, str] | None = None
    ) -> str:
        encoded = urlencode(data).encode("utf-8") if data is not None else None
        request = Request(
            f"{self.base_url}/api/v2/{endpoint}",
            data=encoded,
            headers={"Referer": f"{self.base_url}/"},
        )
        try:
            with self._opener.open(request, timeout=self.timeout) as response:
                return response.read().decode("utf-8")
        except HTTPError as exc:
            raise QBittorrentAPIError(
                f"qBittorrent API {endpoint} returned HTTP {exc.code}"
            ) from exc
        except (URLError, OSError) as exc:
            raise QBittorrentAPIError(
                f"Cannot reach qBittorrent at {self.base_url}: {exc}"
            ) from exc

    def login(self, username: str, password: str) -> None:
        response = self._request(
            "auth/login", data={"username": username, "password": password}
        ).strip()
        if response != "Ok.":
            raise QBittorrentAPIError("qBittorrent login was refused")

    def versions(self) -> tuple[str, str]:
        return self._request("app/version").strip(), self._request(
            "app/webapiVersion"
        ).strip()

    def rss_items(self) -> dict[str, Any]:
        payload = self._request("rss/items?withData=false")
        return _json_object(payload, "RSS items")

    def rss_rules(self) -> dict[str, Any]:
        return _json_object(self._request("rss/rules"), "RSS rules")

    def add_feed(self, url: str, path: str) -> None:
        self._request("rss/addFeed", data={"url": url, "path": path})

    def set_rule(self, name: str, definition: dict[str, object]) -> None:
        self._request(
            "rss/setRule",
            data={
                "ruleName": name,
                "ruleDef": json.dumps(definition, ensure_ascii=False),
            },
        )


def _json_object(payload: str, label: str) -> dict[str, Any]:
    try:
        value = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise QBittorrentAPIError(f"qBittorrent returned invalid {label} JSON") from exc
    if not isinstance(value, dict):
        raise QBittorrentAPIError(f"qBittorrent returned non-object {label} JSON")
    return value
