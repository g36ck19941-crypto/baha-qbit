from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from anime_bridge.workflows import (
    ObsidianLibraryConflict,
    apply_formal_note_delete,
    list_formal_anime_notes,
    plan_formal_note_delete,
)


NOTE = '''---
中文名: "测试动画"
tags: "bangumi"
---
用户观看进度
'''


class ObsidianLibraryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.vault = Path(self.temporary.name)
        self.note = self.vault / "C" / "bangumi" / "2026" / "07月新番" / "测试动画.md"
        self.note.parent.mkdir(parents=True)
        self.note.write_text(NOTE, encoding="utf-8")

    def tearDown(self):
        self.temporary.cleanup()

    def test_list_and_preview_are_read_only(self):
        items = list_formal_anime_notes(self.vault, "C/bangumi")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].title, "测试动画")
        plan = plan_formal_note_delete(
            self.vault, "C/bangumi", items[0].relative_path
        )
        self.assertFalse(plan.conflict)
        self.assertTrue(self.note.is_file())

    def test_confirmed_delete_moves_note_to_recoverable_trash(self):
        plan = plan_formal_note_delete(
            self.vault, "C/bangumi", self.note.relative_to(self.vault).as_posix()
        )
        trash = apply_formal_note_delete(plan, self.vault, plan.sha256)
        self.assertFalse(self.note.exists())
        self.assertEqual(trash.read_text(encoding="utf-8"), NOTE)
        self.assertIn(".trash/anime-bridge", trash.as_posix())

    def test_changed_note_is_refused_after_preview(self):
        plan = plan_formal_note_delete(
            self.vault, "C/bangumi", self.note.relative_to(self.vault).as_posix()
        )
        self.note.write_text(NOTE + "changed", encoding="utf-8")
        with self.assertRaisesRegex(ObsidianLibraryConflict, "changed after preview"):
            apply_formal_note_delete(plan, self.vault, plan.sha256)
        self.assertTrue(self.note.exists())

    def test_non_bangumi_note_and_parent_escape_are_refused(self):
        other = self.note.with_name("私人笔记.md")
        other.write_text("---\ntags: private\n---\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "not tagged bangumi"):
            plan_formal_note_delete(
                self.vault, "C/bangumi", other.relative_to(self.vault).as_posix()
            )
        with self.assertRaisesRegex(ValueError, "Vault-relative"):
            plan_formal_note_delete(self.vault, "C/bangumi", "../outside.md")


if __name__ == "__main__":
    unittest.main()
