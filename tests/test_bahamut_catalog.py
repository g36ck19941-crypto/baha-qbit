from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from typing import Mapping

from anime_bridge.adapters.bahamut_catalog import (
    BahamutCatalogClient,
    BahamutCatalogError,
    load_bahamut_catalog,
    parse_bahamut_catalog_page,
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


def catalog_html(*rows: tuple[str, str, int]) -> str:
    cards = "".join(
        f'<a class="theme-list-main" href="animeRef.php?sn={sn}">'
        f'<div class="theme-name"><p>{title}</p></div>'
        f'<div class="theme-time">年份：{year_month}</div></a>'
        for title, year_month, sn in rows
    )
    return f'<div class="animate-theme-list"><div class="theme-list-block">{cards}</div></div>'


class FakeTextTransport:
    def __init__(self, pages: list[str]) -> None:
        self.pages = pages
        self.calls: list[str] = []

    def get_text(
        self, url: str, headers: Mapping[str, str], timeout_seconds: float
    ) -> str:
        self.calls.append(url)
        return self.pages[len(self.calls) - 1]


class BahamutCatalogTests(unittest.TestCase):
    def test_page_parser_reads_public_catalog_cards(self) -> None:
        parsed = parse_bahamut_catalog_page(
            catalog_html(("動畫 A", "2026/08", 41), ("動畫 B", "2026/07", 42)),
            2,
        )
        self.assertEqual(parsed.visible_cards, 2)
        self.assertEqual([item.title for item in parsed.items], ["動畫 A", "動畫 B"])
        self.assertEqual((parsed.items[0].year, parsed.items[0].month), (2026, 8))
        self.assertEqual(parsed.items[0].page, 2)

    def test_client_fetches_until_older_quarter_boundary(self) -> None:
        transport = FakeTextTransport(
            [
                catalog_html(("未来作品", "2026/10", 40), ("動畫 A", "2026/08", 41)),
                catalog_html(("動畫 B", "2026/07", 42), ("旧作品", "2026/06", 43)),
            ]
        )
        result = BahamutCatalogClient(transport=transport).fetch_current_quarter(
            date(2026, 8, 26)
        )
        self.assertEqual([item.title for item in result.items], ["動畫 A", "動畫 B"])
        self.assertEqual(result.pages_scanned, 2)
        self.assertTrue(result.complete)
        self.assertIn("page=2", transport.calls[-1])
        self.assertNotIn("category=", transport.calls[-1])

    def test_client_refuses_incomplete_card_metadata(self) -> None:
        malformed = (
            '<div class="animate-theme-list"><div class="theme-list-block">'
            '<a class="theme-list-main" href="animeRef.php?sn=41">'
            '<div class="theme-name">動畫 A</div></a></div></div>'
        )
        with self.assertRaisesRegex(BahamutCatalogError, "incomplete"):
            BahamutCatalogClient(transport=FakeTextTransport([malformed])).fetch_current_quarter(
                date(2026, 8, 26)
            )

    def test_client_refuses_unproven_page_limit(self) -> None:
        current_page = catalog_html(("動畫 A", "2026/08", 41))
        with self.assertRaisesRegex(BahamutCatalogError, "quarter boundary"):
            BahamutCatalogClient(
                transport=FakeTextTransport([current_page]), max_pages=1
            ).fetch_current_quarter(date(2026, 8, 26))

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
