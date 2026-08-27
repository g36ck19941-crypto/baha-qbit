"""Validated current-quarter catalog exported from Bahamut's public pages."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Mapping, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urljoin, urlparse
from urllib.request import Request, urlopen

from anime_bridge import __version__
from anime_bridge.domain import BahamutCatalogItem


FORMAT_NAME = "anime-bridge-bahamut-current-quarter"
SCHEMA_VERSION = 1
MAX_EXPORT_BYTES = 5 * 1024 * 1024
_ALLOWED_HOST = "ani.gamer.com.tw"
_QUARTER_START_MONTHS = {1, 4, 7, 10}
_PAGE_BYTE_LIMIT = 5 * 1024 * 1024
_DATE_PATTERN = re.compile(r"(20\d{2})\s*[/／-]\s*(\d{1,2})")


class BahamutCatalogError(RuntimeError):
    """A public catalog request or completeness failure."""


class TextTransport(Protocol):
    def get_text(
        self,
        url: str,
        headers: Mapping[str, str],
        timeout_seconds: float,
    ) -> str: ...


class UrlLibTextTransport:
    def get_text(
        self,
        url: str,
        headers: Mapping[str, str],
        timeout_seconds: float,
    ) -> str:
        request = Request(url, headers=dict(headers), method="GET")
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                final_url = response.geturl()
                if urlparse(final_url).hostname != _ALLOWED_HOST:
                    raise BahamutCatalogError("Bahamut catalog redirected outside its host")
                raw = response.read(_PAGE_BYTE_LIMIT + 1)
        except HTTPError as exc:
            raise BahamutCatalogError(
                f"Bahamut catalog returned HTTP {exc.code}; use the browser-helper fallback"
            ) from exc
        except (URLError, TimeoutError) as exc:
            reason = getattr(exc, "reason", str(exc))
            raise BahamutCatalogError(
                f"Unable to reach Bahamut catalog ({reason}); use the browser-helper fallback"
            ) from exc
        if len(raw) > _PAGE_BYTE_LIMIT:
            raise BahamutCatalogError("Bahamut catalog page exceeds the 5 MiB safety limit")
        try:
            return raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise BahamutCatalogError(
                "Bahamut catalog returned invalid UTF-8; use the browser-helper fallback"
            ) from exc


@dataclass(frozen=True, slots=True)
class ParsedCatalogPage:
    items: tuple[BahamutCatalogItem, ...]
    visible_cards: int


class _CatalogHTMLParser(HTMLParser):
    def __init__(self, page: int) -> None:
        super().__init__(convert_charrefs=True)
        self.page = page
        self.stack: list[tuple[str, frozenset[str]]] = []
        self.current: dict[str, object] | None = None
        self.item_depth = 0
        self.visible_cards = 0
        self.items: list[BahamutCatalogItem] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {key: value or "" for key, value in attrs}
        classes = frozenset(attributes.get("class", "").split())
        self.stack.append((tag, classes))
        if self.current is None and tag == "a" and "theme-list-main" in classes:
            self.visible_cards += 1
            self.current = {
                "href": attributes.get("href", ""),
                "name": [],
                "time": [],
            }
            self.item_depth = len(self.stack)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        return

    def handle_data(self, data: str) -> None:
        if self.current is None or not data.strip():
            return
        active_classes = {name for _, classes in self.stack for name in classes}
        if "theme-name" in active_classes:
            self.current["name"].append(data)  # type: ignore[union-attr]
        if "theme-time" in active_classes:
            self.current["time"].append(data)  # type: ignore[union-attr]

    def handle_endtag(self, tag: str) -> None:
        if not self.stack:
            return
        matching = next(
            (index for index in range(len(self.stack) - 1, -1, -1) if self.stack[index][0] == tag),
            None,
        )
        if matching is None:
            return
        closes_item = self.current is not None and matching < self.item_depth
        self.stack = self.stack[:matching]
        if closes_item:
            self._finish_item()

    def _finish_item(self) -> None:
        assert self.current is not None
        title = " ".join("".join(self.current["name"]).split())  # type: ignore[arg-type]
        time_text = " ".join("".join(self.current["time"]).split())  # type: ignore[arg-type]
        match = _DATE_PATTERN.search(time_text)
        href = urljoin("https://ani.gamer.com.tw/", str(self.current["href"]))
        parsed = urlparse(href)
        if title and match and parsed.hostname == _ALLOWED_HOST and parsed.path == "/animeRef.php":
            values = parse_qs(parsed.query).get("sn") or []
            sn = int(values[-1]) if values and values[-1].isdigit() else None
            self.items.append(
                BahamutCatalogItem(
                    title=title,
                    href=href,
                    sn=sn,
                    page=self.page,
                    year=int(match.group(1)),
                    month=int(match.group(2)),
                )
            )
        self.current = None
        self.item_depth = 0


def parse_bahamut_catalog_page(html: str, page: int) -> ParsedCatalogPage:
    parser = _CatalogHTMLParser(page)
    parser.feed(html)
    parser.close()
    if parser.current is not None:
        parser._finish_item()
    return ParsedCatalogPage(tuple(parser.items), parser.visible_cards)


@dataclass(frozen=True, slots=True)
class BahamutCatalogExport:
    items: tuple[BahamutCatalogItem, ...]
    exported_at: str
    source_url: str
    quarter_year: int
    quarter_start_month: int
    pages_scanned: int
    complete: bool
    warnings: tuple[str, ...] = ()


@dataclass(slots=True)
class BahamutCatalogClient:
    """Fetch the public year-sorted catalog without browser or account state."""

    base_url: str = "https://ani.gamer.com.tw/animeList.php"
    user_agent: str = (
        f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        f"AppleWebKit/537.36 Chrome/135 Safari/537.36 AnimeBridge/{__version__}"
    )
    timeout_seconds: float = 20.0
    max_pages: int = 20
    transport: TextTransport | None = None

    def __post_init__(self) -> None:
        parsed = urlparse(self.base_url)
        if parsed.scheme != "https" or parsed.hostname != _ALLOWED_HOST:
            raise ValueError("Bahamut catalog base_url must use the official HTTPS host")
        if not 1 <= self.max_pages <= 50:
            raise ValueError("max_pages must be between 1 and 50")
        if self.transport is None:
            self.transport = UrlLibTextTransport()

    def page_url(self, page: int) -> str:
        return f"{self.base_url}?{urlencode({'sort': 1, 'page': page})}"

    def fetch_current_quarter(self, reference_date: date | None = None) -> BahamutCatalogExport:
        reference = reference_date or date.today()
        start_month = ((reference.month - 1) // 3) * 3 + 1
        start_key = reference.year * 12 + start_month
        end_key = start_key + 3
        collected: dict[tuple[str, str], BahamutCatalogItem] = {}
        previous_key: int | None = None
        pages_scanned = 0
        boundary_reached = False

        for page in range(1, self.max_pages + 1):
            assert self.transport is not None
            html = self.transport.get_text(
                self.page_url(page),
                {
                    "Accept": "text/html,application/xhtml+xml",
                    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.7",
                    "Referer": "https://ani.gamer.com.tw/",
                    "User-Agent": self.user_agent,
                },
                self.timeout_seconds,
            )
            parsed_page = parse_bahamut_catalog_page(html, page)
            pages_scanned += 1
            if parsed_page.visible_cards != len(parsed_page.items):
                raise BahamutCatalogError(
                    f"Bahamut catalog page {page} contains incomplete card metadata; "
                    "use the browser-helper fallback"
                )
            if not parsed_page.items:
                if page == 1:
                    raise BahamutCatalogError(
                        "Bahamut catalog page structure was not recognized; "
                        "use the browser-helper fallback"
                    )
                boundary_reached = True
                break

            for item in parsed_page.items:
                assert item.year is not None and item.month is not None
                key = item.year * 12 + item.month
                if previous_key is not None and key > previous_key:
                    raise BahamutCatalogError(
                        "Bahamut catalog is not in descending year order; "
                        "safe quarter completion cannot be proven"
                    )
                previous_key = key
                if start_key <= key < end_key:
                    collected.setdefault((item.title, item.href), item)
            if any(
                (item.year or 0) * 12 + (item.month or 0) < start_key
                for item in parsed_page.items
            ):
                boundary_reached = True
                break

        if not boundary_reached:
            raise BahamutCatalogError(
                f"Bahamut catalog did not reach the quarter boundary within {self.max_pages} pages"
            )
        return BahamutCatalogExport(
            items=tuple(collected.values()),
            exported_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            source_url=self.page_url(1),
            quarter_year=reference.year,
            quarter_start_month=start_month,
            pages_scanned=pages_scanned,
            complete=True,
        )


def _required_text(value: object, field: str, *, max_length: int = 500) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Bahamut catalog field {field!r} must be non-empty text")
    cleaned = value.strip()
    if len(cleaned) > max_length:
        raise ValueError(f"Bahamut catalog field {field!r} is too long")
    return cleaned


def _bahamut_url(value: object, field: str) -> str:
    url = _required_text(value, field, max_length=2048)
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != _ALLOWED_HOST:
        raise ValueError(f"Bahamut catalog field {field!r} must use https://{_ALLOWED_HOST}")
    return url


def _bounded_int(value: object, field: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"Bahamut catalog field {field!r} must be an integer")
    if value < minimum or value > maximum:
        raise ValueError(
            f"Bahamut catalog field {field!r} must be between {minimum} and {maximum}"
        )
    return value


def _optional_int(value: object, field: str) -> int | None:
    if value is None:
        return None
    return _bounded_int(value, field, 0, 2_147_483_647)


def parse_bahamut_catalog_json(text: str) -> BahamutCatalogExport:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("Bahamut catalog is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("Bahamut catalog root must be an object")
    if payload.get("format") != FORMAT_NAME or payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Unsupported Bahamut catalog format or schema version")

    source_url = _bahamut_url(payload.get("source_url"), "source_url")
    if urlparse(source_url).path.rstrip("/") != "/animeList.php":
        raise ValueError("Bahamut catalog source_url must point to animeList.php")
    exported_at = _required_text(payload.get("exported_at"), "exported_at", max_length=64)
    quarter_year = _bounded_int(payload.get("quarter_year"), "quarter_year", 2000, 2100)
    quarter_start_month = _bounded_int(
        payload.get("quarter_start_month"), "quarter_start_month", 1, 12
    )
    if quarter_start_month not in _QUARTER_START_MONTHS:
        raise ValueError("Bahamut catalog quarter_start_month must be 1, 4, 7, or 10")
    pages_scanned = _bounded_int(payload.get("pages_scanned"), "pages_scanned", 1, 50)
    complete = payload.get("complete")
    if not isinstance(complete, bool):
        raise ValueError("Bahamut catalog complete must be a boolean")

    raw_items = payload.get("items")
    if not isinstance(raw_items, list):
        raise ValueError("Bahamut catalog items must be an array")
    quarter_months = range(quarter_start_month, quarter_start_month + 3)
    deduplicated: dict[tuple[str, str], BahamutCatalogItem] = {}
    for index, row in enumerate(raw_items):
        if not isinstance(row, dict):
            raise ValueError(f"Bahamut catalog item #{index + 1} must be an object")
        title = _required_text(row.get("title"), f"items[{index}].title")
        href = _bahamut_url(row.get("href"), f"items[{index}].href")
        parsed_href = urlparse(href)
        if parsed_href.path.rstrip("/") != "/animeRef.php":
            raise ValueError(f"Bahamut catalog item #{index + 1} has an invalid href")
        year = _bounded_int(row.get("year"), f"items[{index}].year", 2000, 2100)
        month = _bounded_int(row.get("month"), f"items[{index}].month", 1, 12)
        if year != quarter_year or month not in quarter_months:
            raise ValueError(f"Bahamut catalog item #{index + 1} is outside the declared quarter")
        sn = _optional_int(row.get("sn"), f"items[{index}].sn")
        if sn is None:
            values = parse_qs(parsed_href.query).get("sn") or []
            if values and values[-1].isdigit():
                sn = int(values[-1])
        page = _optional_int(row.get("page"), f"items[{index}].page")
        item = BahamutCatalogItem(title, href, sn, page, year, month)
        deduplicated.setdefault((title, href), item)

    raw_warnings = payload.get("warnings", [])
    if not isinstance(raw_warnings, list) or not all(
        isinstance(item, str) and len(item) <= 500 for item in raw_warnings
    ):
        raise ValueError("Bahamut catalog warnings must be a short text array")
    return BahamutCatalogExport(
        items=tuple(deduplicated.values()),
        exported_at=exported_at,
        source_url=source_url,
        quarter_year=quarter_year,
        quarter_start_month=quarter_start_month,
        pages_scanned=pages_scanned,
        complete=complete,
        warnings=tuple(item.strip() for item in raw_warnings if item.strip()),
    )


def load_bahamut_catalog(
    path: Path, *, require_complete: bool = True
) -> BahamutCatalogExport:
    resolved = path.expanduser().resolve()
    if resolved.stat().st_size > MAX_EXPORT_BYTES:
        raise ValueError("Bahamut catalog exceeds the 5 MiB safety limit")
    result = parse_bahamut_catalog_json(resolved.read_text(encoding="utf-8"))
    if require_complete and (not result.complete or result.warnings):
        details = "; ".join(result.warnings) or "catalog marked incomplete"
        raise ValueError(
            "Bahamut catalog is incomplete and cannot prove safe subtraction: " + details
        )
    return result
