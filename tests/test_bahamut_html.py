from __future__ import annotations

import unittest
from pathlib import Path

from anime_bridge.adapters.bahamut_html import parse_mygather_html


FIXTURES = Path(__file__).parent / "fixtures"


class BahamutHTMLTests(unittest.TestCase):
    def test_parses_only_theme_list_favorites_and_extracts_sn(self) -> None:
        html = (FIXTURES / "bahamut_mygather_page.html").read_text(encoding="utf-8")
        result = parse_mygather_html(html, page=2)
        self.assertFalse(result.empty_collection_marker)
        self.assertEqual(
            [(item.title, item.sn, item.page) for item in result.items],
            [("葬送的芙莉蓮", 12345, 2), ("藥師少女的獨語 第二季", 67890, 2)],
        )
        self.assertNotIn("导航项目", [item.title for item in result.items])

    def test_detects_empty_collection_marker(self) -> None:
        result = parse_mygather_html("<main>目前沒有訂閱內容</main>")
        self.assertTrue(result.empty_collection_marker)
        self.assertEqual(result.items, ())


if __name__ == "__main__":
    unittest.main()

