from __future__ import annotations

import unittest
from datetime import date

from anime_bridge.domain import AnimeCategory, AnimeSubject, BahamutCatalogItem
from anime_bridge.matching import (
    MatchKind,
    best_title_match,
    normalize_title,
    normalized_title_forms,
)
from anime_bridge.workflows import subtract_bahamut_catalog


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
        anime = subject(1, "药师少女的独语 第二季", "薬屋のひとりごと 第2期")
        item = BahamutCatalogItem("藥師少女的獨語　第二季", "/animeRef.php?sn=9", 9)
        match = best_title_match(anime, [item])
        self.assertIs(match.kind, MatchKind.EXACT)
        self.assertTrue(match.auto_exclude)

    def test_taiwan_phrase_title_is_canonicalized_for_exact_exclusion(self) -> None:
        anime = subject(5, "网络胜利组", "ネト充のススメ")
        item = BahamutCatalogItem("網路勝利組", "/animeRef.php?sn=12", 12)
        self.assertIn("网络胜利组", normalized_title_forms(item.title))
        self.assertIs(best_title_match(anime, [item]).kind, MatchKind.EXACT)

    def test_hong_kong_title_is_canonicalized_for_exact_exclusion(self) -> None:
        anime = subject(6, "机动战士高达", "機動戦士ガンダム")
        item = BahamutCatalogItem("機動戰士高達", "/animeRef.php?sn=13", 13)
        self.assertIn("机动战士高达", normalized_title_forms(item.title))
        self.assertIs(best_title_match(anime, [item]).kind, MatchKind.EXACT)

    def test_distinct_taiwan_translation_uses_explicit_bangumi_alias(self) -> None:
        anime = subject(8, "机动战士高达", "機動戦士ガンダム", ("機動戰士鋼彈",))
        item = BahamutCatalogItem("機動戰士鋼彈", "/animeRef.php?sn=15", 15)
        match = best_title_match(anime, [item])
        self.assertIs(match.kind, MatchKind.EXACT)
        self.assertEqual(match.subject_title, "機動戰士鋼彈")

    def test_unrelated_title_is_not_automatically_excluded(self) -> None:
        anime = subject(7, "胆大党", "ダンダダン")
        item = BahamutCatalogItem("膽小鬼", "/animeRef.php?sn=14", 14)
        self.assertIs(best_title_match(anime, [item]).kind, MatchKind.NONE)

    def test_fuzzy_match_is_review_only_and_leaves_safe_candidates_empty(self) -> None:
        anime = subject(2, "测试动画 续篇", "テストアニメ 特別編")
        item = BahamutCatalogItem("测试动画 第2季", "/animeRef.php?sn=10", 10)
        result = subtract_bahamut_catalog([anime], [item])
        self.assertEqual(result.candidates, ())
        self.assertEqual(result.exact_matches, ())
        self.assertEqual(len(result.review_matches), 1)

    def test_sequel_markers_match_roman_and_chinese_forms(self) -> None:
        anime = subject(8, "幼女战记 第二季", "幼女戦記Ⅱ")
        item = BahamutCatalogItem("幼女战记 2", "https://ani.gamer.com.tw/animeRef.php?sn=12", 12)
        result = subtract_bahamut_catalog([anime], [item])
        self.assertEqual([item.subject for item in result.exact_matches], [anime])
        self.assertEqual(result.review_matches, ())

    def test_cross_site_aliases_match_three_reported_bahamut_titles(self) -> None:
        subjects = (
            subject(9, "超超超超超喜欢你的100个女朋友 第三季", "君のことが大大大大大好きな100人の彼女 第3期"),
            subject(10, "靠死亡游戏混饭吃。 44:CLOUDY BEACH", "死亡遊戯で飯を食う。 44:CLOUDY BEACH"),
            subject(11, "恶女不才，请多关照 ～雏宫蝶鼠换身传～", "ふつつかな悪女ではございますが ～雛宮蝶鼠とりかえ伝～"),
        )
        items = (
            BahamutCatalogItem("超超超超超喜歡你的 100 個女朋友", "https://ani.gamer.com.tw/animeRef.php?sn=21", 21),
            BahamutCatalogItem("靠死亡遊戲混飯吃。", "https://ani.gamer.com.tw/animeRef.php?sn=22", 22),
            BahamutCatalogItem("我是不才惡女", "https://ani.gamer.com.tw/animeRef.php?sn=23", 23),
        )
        result = subtract_bahamut_catalog(subjects, items)
        self.assertEqual([match.subject.bangumi_id for match in result.exact_matches], [9, 10, 11])
        self.assertEqual(result.candidates, ())
        self.assertEqual(result.review_matches, ())

    def test_exact_match_is_subtracted_and_unmatched_remains(self) -> None:
        collected = subject(3, "已收藏动画", "収集済み")
        remaining = subject(4, "完全不同的作品", "まったく別の作品")
        item = BahamutCatalogItem("已收藏动画", "/animeRef.php?sn=11", 11)
        result = subtract_bahamut_catalog([collected, remaining], [item])
        self.assertEqual(result.candidates, (remaining,))
        self.assertEqual([item.subject for item in result.exact_matches], [collected])
        self.assertEqual(result.review_matches, ())


if __name__ == "__main__":
    unittest.main()
