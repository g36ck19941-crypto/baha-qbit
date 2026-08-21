from __future__ import annotations

import unittest
from datetime import date

from anime_bridge.domain import AnimeCategory, AnimeSubject, BahamutFavorite
from anime_bridge.matching import MatchKind, best_title_match, normalize_title
from anime_bridge.workflows import subtract_bahamut_favorites


def subject(subject_id: int, cn: str, jp: str, aliases=()) -> AnimeSubject:
    return AnimeSubject(
        bangumi_id=subject_id,
        name=jp,
        name_cn=cn,
        summary="",
        air_date=date(2026, 7, 1),
        category=AnimeCategory.TV,
        meta_tags=("日本",),
        aliases=tuple(aliases),
    )


class MatchingTests(unittest.TestCase):
    def test_normalization_removes_width_case_spacing_and_punctuation(self) -> None:
        self.assertEqual(normalize_title("ＡＢＣ：Season 2"), "abcseason2")

    def test_exact_alias_is_eligible_for_automatic_exclusion(self) -> None:
        anime = subject(1, "药师少女的独语 第二季", "薬屋のひとりごと 第2期", ("藥師少女的獨語 第二季",))
        favorite = BahamutFavorite("藥師少女的獨語　第二季", "/animeRef.php?sn=9", 9)
        match = best_title_match(anime, [favorite])
        self.assertIs(match.kind, MatchKind.EXACT)
        self.assertTrue(match.auto_exclude)

    def test_fuzzy_match_is_review_only_and_remains_a_candidate(self) -> None:
        anime = subject(2, "测试动画 第二季", "テストアニメ 2")
        favorite = BahamutFavorite("测试动画 第2季", "/animeRef.php?sn=10", 10)
        result = subtract_bahamut_favorites([anime], [favorite])
        self.assertEqual(result.candidates, (anime,))
        self.assertEqual(result.exact_matches, ())
        self.assertEqual(len(result.review_matches), 1)

    def test_exact_match_is_subtracted_and_unmatched_remains(self) -> None:
        collected = subject(3, "已收藏动画", "収集済み")
        remaining = subject(4, "完全不同的作品", "まったく別の作品")
        favorite = BahamutFavorite("已收藏动画", "/animeRef.php?sn=11", 11)
        result = subtract_bahamut_favorites([collected, remaining], [favorite])
        self.assertEqual(result.candidates, (remaining,))
        self.assertEqual([item.subject for item in result.exact_matches], [collected])
        self.assertEqual(result.review_matches, ())


if __name__ == "__main__":
    unittest.main()
