from __future__ import annotations

import unittest
from typing import Any, Mapping

from anime_bridge.adapters.bangumi import BangumiClient
from anime_bridge.domain import AnimeCategory


def subject(subject_id: int, air_date: str) -> dict[str, Any]:
    return {
        "id": subject_id,
        "name": f"Sample {subject_id}",
        "name_cn": f"示例动画 {subject_id}",
        "summary": "仅用于固定测试。",
        "date": air_date,
        "platform": "TV",
        "images": {"large": f"https://example.invalid/{subject_id}.jpg"},
        "eps": 12,
        "rating": {"score": 7.5},
        "meta_tags": ["TV", "日本"],
    }


class FakeTransport:
    def __init__(self) -> None:
        self.calls: list[Mapping[str, str | int]] = []

    def get_json(self, url, params, headers, timeout_seconds):
        self.calls.append(dict(params))
        if params["offset"] == 0:
            return {"data": [subject(1, "2026-07-02"), subject(2, "2026-07-03")], "total": 3}
        return {"data": [subject(3, "2026-07-04")], "total": 3}


class BangumiClientTests(unittest.TestCase):
    def test_month_browsing_is_paginated_and_preserves_category(self) -> None:
        transport = FakeTransport()
        client = BangumiClient(page_size=2, transport=transport)
        results = list(client.iter_month(2026, 7, AnimeCategory.TV))
        self.assertEqual([item.bangumi_id for item in results], [1, 2, 3])
        self.assertTrue(all(item.category is AnimeCategory.TV for item in results))
        self.assertTrue(all("日本" in item.meta_tags for item in results))
        self.assertEqual([call["offset"] for call in transport.calls], [0, 2])
        self.assertTrue(all(call["cat"] == 1 for call in transport.calls))


if __name__ == "__main__":
    unittest.main()
