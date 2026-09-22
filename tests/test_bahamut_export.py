from __future__ import annotations

import json
import unittest

from anime_bridge.adapters.bahamut_export import parse_bahamut_export_json


def export_payload() -> dict:
    return {
        "format": "anime-bridge-bahamut-favorites",
        "schema_version": 1,
        "exported_at": "2026-08-21T18:00:00.000Z",
        "source_url": "https://ani.gamer.com.tw/mygather.php",
        "pages_scanned": 2,
        "complete": True,
        "warnings": [],
        "favorites": [
            {
                "title": "測試動畫 第二季",
                "href": "https://ani.gamer.com.tw/animeRef.php?sn=42",
                "sn": 42,
                "page": 1,
            },
            {
                "title": "測試動畫 第二季",
                "href": "https://ani.gamer.com.tw/animeRef.php?sn=42",
                "sn": 42,
                "page": 2,
            },
        ],
    }


class BahamutExportTests(unittest.TestCase):
    def test_parses_and_deduplicates_browser_export(self) -> None:
        parsed = parse_bahamut_export_json(json.dumps(export_payload()))
        self.assertEqual(len(parsed.favorites), 1)
        self.assertEqual(parsed.favorites[0].sn, 42)
        self.assertEqual(parsed.pages_scanned, 2)

    def test_rejects_non_bahamut_links(self) -> None:
        payload = export_payload()
        payload["favorites"][0]["href"] = "https://example.com/animeRef.php?sn=42"
        with self.assertRaisesRegex(ValueError, "ani.gamer.com.tw"):
            parse_bahamut_export_json(json.dumps(payload))

    def test_rejects_unknown_schema(self) -> None:
        payload = export_payload()
        payload["schema_version"] = 99
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            parse_bahamut_export_json(json.dumps(payload))

    def test_loader_refuses_incomplete_export(self) -> None:
        from pathlib import Path
        import tempfile

        payload = export_payload()
        payload["complete"] = False
        payload["warnings"] = ["page 2 failed"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "favorites.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            from anime_bridge.adapters.bahamut_export import load_bahamut_export

            with self.assertRaisesRegex(ValueError, "incomplete"):
                load_bahamut_export(path)


if __name__ == "__main__":
    unittest.main()
