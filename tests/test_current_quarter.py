from __future__ import annotations

import unittest
from dataclasses import replace
from datetime import date, datetime, timezone

from anime_bridge.domain import AnimeCategory, AnimeSubject, BahamutFavorite
from anime_bridge.renderers import render_candidate_markdown
from anime_bridge.workflows import CurrentQuarterScanner, subtract_bahamut_favorites


def anime(subject_id: int, air_date: date, category: AnimeCategory, title: str) -> AnimeSubject:
    return AnimeSubject(
        bangumi_id=subject_id,
        name=f"JP {title}",
        name_cn=title,
        summary="第一行。\n第二行。",
        air_date=air_date,
        category=category,
        cover_url=f"https://example.invalid/{subject_id}.jpg",
        episodes=12,
        score=7.8,
        meta_tags=("日本",),
    )


class FakeSource:
    def iter_month(self, year, month, category):
        rows = {
            (7, AnimeCategory.TV): [
                anime(10, date(2026, 7, 5), AnimeCategory.TV, "当前季度 TV"),
                anime(99, date(2026, 6, 30), AnimeCategory.TV, "越界条目"),
            ],
            (8, AnimeCategory.MOVIE): [
                anime(20, date(2026, 8, 9), AnimeCategory.MOVIE, "当前季度剧场版"),
            ],
            (9, AnimeCategory.WEB): [
                anime(30, date(2026, 9, 1), AnimeCategory.WEB, "当前季度续作 WEB"),
                anime(10, date(2026, 7, 5), AnimeCategory.WEB, "重复条目"),
            ],
        }
        if (month, category) == (7, AnimeCategory.MOVIE):
            foreign = anime(40, date(2026, 7, 15), AnimeCategory.MOVIE, "非日本动画")
            return [
                AnimeSubject(
                    bangumi_id=foreign.bangumi_id,
                    name=foreign.name,
                    name_cn=foreign.name_cn,
                    summary=foreign.summary,
                    air_date=foreign.air_date,
                    category=foreign.category,
                    meta_tags=("欧美",),
                )
            ]
        return rows.get((month, category), [])


class CurrentQuarterTests(unittest.TestCase):
    def test_scan_filters_dates_and_deduplicates_by_bangumi_id(self) -> None:
        result = CurrentQuarterScanner(FakeSource()).scan(date(2026, 8, 21))
        self.assertEqual(result.identifier, "2026-summer")
        self.assertEqual([item.bangumi_id for item in result.subjects], [10, 20, 30])
        self.assertEqual([item.bangumi_id for item in result.excluded_without_japan_tag], [40])

    def test_candidate_markdown_has_tasks_cover_summary_and_machine_metadata(self) -> None:
        result = CurrentQuarterScanner(FakeSource()).scan(date(2026, 8, 21))
        rendered = render_candidate_markdown(
            result,
            generated_at=datetime(2026, 8, 21, 12, 0, tzinfo=timezone.utc),
        )
        self.assertIn("- [ ] **当前季度 TV**", rendered)
        self.assertIn("![当前季度 TV|180]", rendered)
        self.assertIn("> 第一行。", rendered)
        self.assertIn('<!-- anime-bridge:item {"air_date":"2026-07-05"', rendered)
        self.assertIn("tags:\n  - anime-bridge-candidates", rendered)
        self.assertNotIn("\n  - bangumi\n", rendered)
        self.assertIn("因缺少 `日本` 元标签而未纳入", rendered)

    def test_filtered_candidate_records_gate_and_review_match(self) -> None:
        original = CurrentQuarterScanner(FakeSource()).scan(date(2026, 8, 21))
        favorites = (
            BahamutFavorite(
                "当前季度 TV", "https://ani.gamer.com.tw/animeRef.php?sn=10", 10
            ),
            BahamutFavorite(
                "当前季度续作 WEB版",
                "https://ani.gamer.com.tw/animeRef.php?sn=30",
                30,
            ),
        )
        difference = subtract_bahamut_favorites(original.subjects, favorites)
        filtered = replace(original, subjects=difference.candidates)
        rendered = render_candidate_markdown(
            filtered,
            bahamut_difference=difference,
            bahamut_favorite_count=2,
            bahamut_exported_at="2026-08-21T18:00:00Z",
        )
        self.assertIn("bahamut_subtraction: true", rendered)
        self.assertNotIn("**当前季度 TV**", rendered)
        self.assertIn("巴哈标题待人工确认", rendered)
        self.assertIn("模糊匹配仍保留", rendered)


if __name__ == "__main__":
    unittest.main()
