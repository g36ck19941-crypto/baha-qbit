"""Validated current-quarter catalog exported from Bahamut's public pages."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from anime_bridge.domain import BahamutCatalogItem


FORMAT_NAME = "anime-bridge-bahamut-current-quarter"
SCHEMA_VERSION = 1
MAX_EXPORT_BYTES = 5 * 1024 * 1024
_ALLOWED_HOST = "ani.gamer.com.tw"
_QUARTER_START_MONTHS = {1, 4, 7, 10}


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
