"""Read-only Bangumi API adapter."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterator, Mapping, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from anime_bridge import __version__
from anime_bridge.domain import AnimeCategory, AnimeSubject


class BangumiAPIError(RuntimeError):
    """A contextual, user-facing Bangumi transport or payload failure."""


class JsonTransport(Protocol):
    def get_json(
        self,
        url: str,
        params: Mapping[str, str | int],
        headers: Mapping[str, str],
        timeout_seconds: float,
    ) -> Mapping[str, Any]: ...


class UrlLibJsonTransport:
    def get_json(
        self,
        url: str,
        params: Mapping[str, str | int],
        headers: Mapping[str, str],
        timeout_seconds: float,
    ) -> Mapping[str, Any]:
        request_url = f"{url}?{urlencode(params)}"
        request = Request(request_url, headers=dict(headers), method="GET")
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            raise BangumiAPIError(
                f"Bangumi returned HTTP {exc.code} for {request_url}"
            ) from exc
        except URLError as exc:
            raise BangumiAPIError(f"Unable to reach Bangumi: {exc.reason}") from exc
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise BangumiAPIError("Bangumi returned invalid JSON") from exc
        if not isinstance(payload, Mapping):
            raise BangumiAPIError("Bangumi returned an unexpected top-level payload")
        return payload


@dataclass(slots=True)
class BangumiClient:
    base_url: str = "https://api.bgm.tv"
    user_agent: str = f"AnimeBridge/{__version__} (local application)"
    timeout_seconds: float = 20.0
    page_size: int = 100
    transport: JsonTransport | None = None

    def __post_init__(self) -> None:
        self.base_url = self.base_url.rstrip("/")
        if self.transport is None:
            self.transport = UrlLibJsonTransport()
        if not 1 <= self.page_size <= 100:
            raise ValueError("page_size must be between 1 and 100")

    def iter_month(
        self,
        year: int,
        month: int,
        category: AnimeCategory,
    ) -> Iterator[AnimeSubject]:
        """Yield every subject in one Bangumi category/month, with pagination."""

        offset = 0
        while True:
            assert self.transport is not None
            payload = self.transport.get_json(
                f"{self.base_url}/v0/subjects",
                {
                    "type": 2,
                    "cat": category.bangumi_id,
                    "sort": "date",
                    "year": year,
                    "month": month,
                    "limit": self.page_size,
                    "offset": offset,
                },
                {
                    "Accept": "application/json",
                    "User-Agent": self.user_agent,
                },
                self.timeout_seconds,
            )
            data = payload.get("data")
            if not isinstance(data, list):
                raise BangumiAPIError("Bangumi response does not contain a data list")

            yielded = 0
            for raw_subject in data:
                if not isinstance(raw_subject, Mapping):
                    continue
                try:
                    subject = AnimeSubject.from_bangumi_payload(raw_subject, category)
                except (KeyError, TypeError, ValueError):
                    # A malformed or undated item cannot prove it belongs in the quarter.
                    continue
                yielded += 1
                yield subject

            offset += len(data)
            total_raw = payload.get("total")
            total = int(total_raw) if total_raw not in (None, "") else None
            if not data or len(data) < self.page_size or (total is not None and offset >= total):
                return
            if yielded == 0 and data:
                # Still advance once for malformed rows, but pagination remains bounded by total.
                if total is None:
                    return

