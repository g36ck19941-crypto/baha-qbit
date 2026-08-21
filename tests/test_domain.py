from __future__ import annotations

import unittest
from datetime import date

from anime_bridge.domain import AnimeCategory, AnimeSubject, Quarter, ScanPolicy


class QuarterTests(unittest.TestCase):
    def test_four_quarter_boundaries(self) -> None:
        cases = {
            date(2026, 1, 1): (Quarter.WINTER, date(2026, 1, 1), date(2026, 4, 1)),
            date(2026, 4, 30): (Quarter.SPRING, date(2026, 4, 1), date(2026, 7, 1)),
            date(2026, 8, 21): (Quarter.SUMMER, date(2026, 7, 1), date(2026, 10, 1)),
            date(2026, 12, 31): (Quarter.AUTUMN, date(2026, 10, 1), date(2027, 1, 1)),
        }
        for value, (expected, start, end) in cases.items():
            with self.subTest(value=value):
                actual = Quarter.containing(value)
                self.assertIs(actual, expected)
                self.assertEqual(actual.bounds(value.year), (start, end))

    def test_default_policy_includes_user_approved_categories_only(self) -> None:
        policy = ScanPolicy()
        self.assertTrue(policy.includes(AnimeCategory.TV))
        self.assertTrue(policy.includes(AnimeCategory.MOVIE))
        self.assertTrue(policy.includes(AnimeCategory.WEB))
        self.assertFalse(policy.includes(AnimeCategory.OVA))
        self.assertFalse(policy.includes(AnimeCategory.OTHER))
        self.assertTrue(policy.include_sequels)
        japanese = AnimeSubject(
            bangumi_id=1,
            name="Sample",
            name_cn="示例",
            summary="",
            air_date=date(2026, 7, 1),
            category=AnimeCategory.TV,
            meta_tags=("日本",),
        )
        foreign = AnimeSubject(
            bangumi_id=2,
            name="Foreign",
            name_cn="非日本示例",
            summary="",
            air_date=date(2026, 7, 1),
            category=AnimeCategory.TV,
            meta_tags=("欧美",),
        )
        self.assertTrue(policy.includes_subject(japanese))
        self.assertFalse(policy.includes_subject(foreign))


if __name__ == "__main__":
    unittest.main()
