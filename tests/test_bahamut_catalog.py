from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from anime_bridge.adapters.bahamut_catalog import (
    load_bahamut_catalog,
    parse_bahamut_catalog_json,
)


def catalog_payload() -> dict:
    return {
        "format": "anime-bridge-bahamut-current-quarter",
        "schema_version": 1,
        "exported_at": "2026-08-26T12:00:00.000Z",
        "source_url": "https://ani.gamer.com.tw/animeList.php?sort=1&page=1",
        "quarter_year": 2026,
        "quarter_start_month": 7,
        "pages_scanned": 3,
        "complete": True,
        "warnings": [],
        "items": [
            {
                "title": "測試動畫 第二季",
                "href": "https://ani.gamer.com.tw/animeRef.php?sn=42",
                "sn": 42,
                "page": 1,
                "year": 2026,
                "month": 7,
            },
            {
                "title": "測試動畫 第二季",
                "href": "https://ani.gamer.com.tw/animeRef.php?sn=42",
                "sn": 42,
                "page": 2,
                "year": 2026,
                "month": 7,
            },
        ],
    }


class BahamutCatalogTests(unittest.TestCase):
    def test_parses_deduplicates_and_keeps_quarter_metadata(self) -> None:
        parsed = parse_bahamut_catalog_json(json.dumps(catalog_payload()))
        self.assertEqual(len(parsed.items), 1)
        self.assertEqual(parsed.items[0].sn, 42)
        self.assertEqual((parsed.quarter_year, parsed.quarter_start_month), (2026, 7))

    def test_rejects_personal_favorites_schema(self) -> None:
        payload = catalog_payload()
        payload["format"] = "anime-bridge-bahamut-favorites"
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            parse_bahamut_catalog_json(json.dumps(payload))

    def test_rejects_item_outside_declared_quarter(self) -> None:
        payload = catalog_payload()
        payload["items"][0]["month"] = 4
        with self.assertRaisesRegex(ValueError, "outside"):
            parse_bahamut_catalog_json(json.dumps(payload))

    def test_rejects_non_catalog_source_url(self) -> None:
        payload = catalog_payload()
        payload["source_url"] = "https://ani.gamer.com.tw/mygather.php"
        with self.assertRaisesRegex(ValueError, "animeList"):
            parse_bahamut_catalog_json(json.dumps(payload))

    def test_loader_refuses_incomplete_catalog(self) -> None:
        payload = catalog_payload()
        payload["complete"] = False
        payload["warnings"] = ["page boundary not reached"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "incomplete"):
                load_bahamut_catalog(path)


if __name__ == "__main__":
    unittest.main()
