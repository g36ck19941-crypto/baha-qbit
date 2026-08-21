from __future__ import annotations

import unittest

from anime_bridge.adapters.candidate_markdown import (
    CandidateParseError,
    parse_candidate_markdown,
)
from anime_bridge.domain import AnimeCategory


class CandidateMarkdownTests(unittest.TestCase):
    def test_reads_checked_and_unchecked_machine_markers(self) -> None:
        document = parse_candidate_markdown(
            """
- [x] **已选择作品**
  <!-- anime-bridge:item {"air_date":"2026-07-05","bangumi_id":10,"category":"tv"} -->
- [ ] **未选择作品**
  <!-- anime-bridge:item {"air_date":"2026-08-09","bangumi_id":20,"category":"movie"} -->
"""
        )
        self.assertEqual(len(document.selections), 2)
        self.assertEqual([item.bangumi_id for item in document.checked], [10])
        self.assertIs(document.selections[1].category, AnimeCategory.MOVIE)
        self.assertFalse(document.bahamut_subtracted)

    def test_reads_completed_bahamut_subtraction_gate(self) -> None:
        document = parse_candidate_markdown(
            "---\nbahamut_subtraction: true\n---\n"
            '- [x] **已筛选**\n  <!-- anime-bridge:item {"air_date":"2026-07-05","bangumi_id":10,"category":"tv"} -->\n'
        )
        self.assertTrue(document.bahamut_subtracted)

    def test_reads_machine_fuzzy_review_evidence(self) -> None:
        document = parse_candidate_markdown(
            "---\nbahamut_subtraction: true\n---\n"
            '- [ ] **测试**\n  <!-- anime-bridge:item {"air_date":"2026-07-05","bangumi_id":10,"category":"tv"} -->\n'
            '  <!-- anime-bridge:bahamut-review {"bangumi_id":10,"favorite_href":"https://ani.gamer.com.tw/animeRef.php?sn=9","favorite_title":"测试 第二季","score":0.78,"subject_title":"测试"} -->\n'
        )
        self.assertEqual(len(document.reviews), 1)
        self.assertEqual(document.reviews[0].bangumi_id, 10)
        self.assertAlmostEqual(document.reviews[0].score, 0.78)

    def test_refuses_task_without_marker(self) -> None:
        with self.assertRaises(CandidateParseError):
            parse_candidate_markdown("- [x] **损坏的候选项**\n")


if __name__ == "__main__":
    unittest.main()

