"""Validated interchange format from the logged-in Bahamut browser helper."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from anime_bridge.domain import BahamutFavorite


FORMAT_NAME = "anime-bridge-bahamut-favorites"
SCHEMA_VERSION = 1
MAX_EXPORT_BYTES = 5 * 1024 * 1024
_ALLOWED_HOST = "ani.gamer.com.tw"


@dataclass(frozen=True, slots=True)
class BahamutFavoritesExport:
    favorites: tuple[BahamutFavorite, ...]
    exported_at: str
    source_url: str
    pages_scanned: int
    complete: bool
    warnings: tuple[str, ...] = ()


def _required_text(value: object, field: str, *, max_length: int = 500) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Bahamut export field {field!r} must be non-empty text")
    cleaned = value.strip()
    if len(cleaned) > max_length:
        raise ValueError(f"Bahamut export field {field!r} is too long")
    return cleaned


def _bahamut_url(value: object, field: str) -> str:
    url = _required_text(value, field, max_length=2048)
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != _ALLOWED_HOST:
        raise ValueError(f"Bahamut export field {field!r} must use https://{_ALLOWED_HOST}")
    return url


def _optional_int(value: object, field: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"Bahamut export field {field!r} must be a non-negative integer")
    return value


def parse_bahamut_export_json(text: str) -> BahamutFavoritesExport:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("Bahamut export is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("Bahamut export root must be an object")
    if payload.get("format") != FORMAT_NAME or payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Unsupported Bahamut export format or schema version")

    source_url = _bahamut_url(payload.get("source_url"), "source_url")
    if urlparse(source_url).path.rstrip("/") != "/mygather.php":
        raise ValueError("Bahamut export source_url must point to mygather.php")
    exported_at = _required_text(payload.get("exported_at"), "exported_at", max_length=64)
    pages_scanned = _optional_int(payload.get("pages_scanned"), "pages_scanned")
    if pages_scanned is None or pages_scanned < 1 or pages_scanned > 100:
        raise ValueError("Bahamut export pages_scanned must be between 1 and 100")
    complete = payload.get("complete")
    if not isinstance(complete, bool):
        raise ValueError("Bahamut export complete must be a boolean")

    raw_favorites = payload.get("favorites")
    if not isinstance(raw_favorites, list):
        raise ValueError("Bahamut export favorites must be an array")
    deduplicated: dict[tuple[str, str], BahamutFavorite] = {}
    for index, row in enumerate(raw_favorites):
        if not isinstance(row, dict):
            raise ValueError(f"Bahamut export favorite #{index + 1} must be an object")
        title = _required_text(row.get("title"), f"favorites[{index}].title")
        href = _bahamut_url(row.get("href"), f"favorites[{index}].href")
        parsed_href = urlparse(href)
        if parsed_href.path.rstrip("/") != "/animeRef.php":
            raise ValueError(f"Bahamut export favorite #{index + 1} has an invalid href")
        sn = _optional_int(row.get("sn"), f"favorites[{index}].sn")
        if sn is None:
            values = parse_qs(parsed_href.query).get("sn") or []
            if values and values[-1].isdigit():
                sn = int(values[-1])
        page = _optional_int(row.get("page"), f"favorites[{index}].page")
        favorite = BahamutFavorite(title=title, href=href, sn=sn, page=page)
        deduplicated.setdefault((title, href), favorite)

    raw_warnings = payload.get("warnings", [])
    if not isinstance(raw_warnings, list) or not all(
        isinstance(item, str) and len(item) <= 500 for item in raw_warnings
    ):
        raise ValueError("Bahamut export warnings must be a short text array")
    return BahamutFavoritesExport(
        favorites=tuple(deduplicated.values()),
        exported_at=exported_at,
        source_url=source_url,
        pages_scanned=pages_scanned,
        complete=complete,
        warnings=tuple(item.strip() for item in raw_warnings if item.strip()),
    )


def load_bahamut_export(
    path: Path, *, require_complete: bool = True
) -> BahamutFavoritesExport:
    resolved = path.expanduser().resolve()
    size = resolved.stat().st_size
    if size > MAX_EXPORT_BYTES:
        raise ValueError("Bahamut export exceeds the 5 MiB safety limit")
    result = parse_bahamut_export_json(resolved.read_text(encoding="utf-8"))
    if require_complete and (not result.complete or result.warnings):
        details = "; ".join(result.warnings) or "export marked incomplete"
        raise ValueError(
            "Bahamut export is incomplete and cannot prove safe subtraction: " + details
        )
    return result
