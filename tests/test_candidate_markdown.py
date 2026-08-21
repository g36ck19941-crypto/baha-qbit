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

    def test_refuses_task_without_marker(self) -> None:
        with self.assertRaises(CandidateParseError):
            parse_candidate_markdown("- [x] **损坏的候选项**\n")


if __name__ == "__main__":
    unittest.main()

