from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path

from anime_bridge.ai.service import AnimeBridgeAIService, WritePermissionError
from anime_bridge.domain import AnimeCategory, AnimeSubject


class FakeBangumi:
    def get_subject(self, subject_id, category):
        return AnimeSubject(
            bangumi_id=subject_id,
            name="テスト",
            name_cn="测试动画",
            summary="简介",
            air_date=date(2026, 7, 1),
            category=category,
            meta_tags=("日本",),
        )


class FakeQbit:
    def __init__(self): self.calls = []
    def versions(self): return "v4.5.5", "2.8.19"
    def rss_items(self): return {}
    def rss_rules(self): return {}
    def add_feed(self, url, path): self.calls.append(("feed", url, path))
    def set_rule(self, name, definition): self.calls.append(("rule", name, definition))


class AIServiceTests(unittest.TestCase):
    @staticmethod
    def write_candidate(vault: Path) -> Path:
        candidate = vault / "candidate.md"
        candidate.write_text(
            "---\nbahamut_subtraction: true\n---\n"
            "- [x] **测试动画**\n"
            "  <!-- anime-bridge:item {\"bangumi_id\":10,\"category\":\"tv\",\"air_date\":\"2026-07-01\"} -->\n",
            encoding="utf-8",
        )
        return candidate

    def test_candidate_analysis_is_read_only_and_surfaces_review_policy(self):
        with tempfile.TemporaryDirectory() as directory:
            vault = Path(directory)
            candidate = vault / "candidate.md"
            candidate.write_text(
                "---\nbahamut_subtraction: true\n---\n"
                "- [ ] **测试动画**\n"
                "  <!-- anime-bridge:item {\"bangumi_id\":10,\"category\":\"tv\",\"air_date\":\"2026-07-01\"} -->\n"
                "  <!-- anime-bridge:bahamut-review {\"bangumi_id\":10,\"favorite_href\":\"https://ani.gamer.com.tw/animeRef.php?sn=10\",\"favorite_title\":\"测试动画 第二季\",\"score\":0.8,\"subject_title\":\"测试动画\"} -->\n",
                encoding="utf-8",
            )
            before = candidate.read_bytes()
            service = AnimeBridgeAIService(vault, bangumi=FakeBangumi(), qbit=FakeQbit())
            result = service.analyze_candidate_note("candidate.md")
            self.assertTrue(result["bahamut_subtracted"])
            self.assertEqual(result["selection_count"], 1)
            self.assertEqual(
                result["fuzzy_reviews"][0]["policy"],
                "human_review_required_never_auto_exclude",
            )
            self.assertEqual(candidate.read_bytes(), before)

    def test_subject_details_are_structured(self):
        with tempfile.TemporaryDirectory() as directory:
            service = AnimeBridgeAIService(
                Path(directory), bangumi=FakeBangumi(), qbit=FakeQbit()
            )
            result = service.bangumi_subject(10, "tv")
            self.assertEqual(result["title"], "测试动画")
            self.assertEqual(result["url"], "https://bgm.tv/subject/10")

    def test_candidate_cannot_escape_vault(self):
        with tempfile.TemporaryDirectory() as directory:
            service = AnimeBridgeAIService(
                Path(directory), bangumi=FakeBangumi(), qbit=FakeQbit()
            )
            with self.assertRaises(ValueError):
                service.plan_obsidian_import(str(Path(directory).parent / "outside.md"))

    def test_write_requires_server_gate_and_exact_confirmation(self):
        with tempfile.TemporaryDirectory() as directory:
            qbit = FakeQbit()
            service = AnimeBridgeAIService(
                Path(directory), bangumi=FakeBangumi(), qbit=qbit
            )
            with self.assertRaises(WritePermissionError):
                service.apply_qbit_rss(
                    "https://example.invalid/feed.xml", "Anime/Test", "Test", "CONFIRM_LOCAL_WRITE"
                )
            enabled = AnimeBridgeAIService(
                Path(directory), allow_writes=True, bangumi=FakeBangumi(), qbit=qbit
            )
            with self.assertRaises(WritePermissionError):
                enabled.apply_qbit_rss(
                    "https://example.invalid/feed.xml", "Anime/Test", "Test", "yes"
                )
            self.assertEqual(qbit.calls, [])

    def test_write_enabled_creates_only_safe_rule(self):
        with tempfile.TemporaryDirectory() as directory:
            qbit = FakeQbit()
            service = AnimeBridgeAIService(
                Path(directory), allow_writes=True, bangumi=FakeBangumi(), qbit=qbit
            )
            result = service.apply_qbit_rss(
                "https://example.invalid/feed.xml",
                "Anime/Test",
                "Test",
                "CONFIRM_LOCAL_WRITE",
            )
            self.assertTrue(result["created"])
            definition = qbit.calls[1][2]
            self.assertFalse(definition["enabled"])
            self.assertTrue(definition["addPaused"])

    def test_candidate_rss_batch_is_preview_first_and_safely_applied(self):
        with tempfile.TemporaryDirectory() as directory:
            vault = Path(directory)
            candidate = self.write_candidate(vault)
            qbit = FakeQbit()
            preview_service = AnimeBridgeAIService(vault, qbit=qbit)
            preview = preview_service.plan_candidate_rss(
                str(candidate), "comicat-rsshub", ("1080P", "CHS")
            )
            self.assertEqual(preview["draft_count"], 1)
            self.assertEqual(qbit.calls, [])
            enabled = AnimeBridgeAIService(vault, allow_writes=True, qbit=qbit)
            result = enabled.apply_candidate_rss(
                str(candidate),
                "comicat-rsshub",
                "CONFIRM_LOCAL_WRITE",
                ("1080P", "CHS"),
            )
            self.assertEqual(result["created_count"], 1)
            self.assertEqual([call[0] for call in qbit.calls], ["feed", "rule"])
            self.assertFalse(qbit.calls[1][2]["enabled"])
            self.assertTrue(qbit.calls[1][2]["addPaused"])


if __name__ == "__main__":
    unittest.main()
