from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from anime_bridge.migration import (
    PLUGIN_FILES,
    MigrationConflict,
    apply_migration,
    plan_migration,
)
from anime_bridge.settings import UserSettings


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.vault = self.root / "Vault"
        (self.vault / ".obsidian").mkdir(parents=True)
        self.source = self.root / "plugin-source"
        self.source.mkdir()
        for name in PLUGIN_FILES:
            (self.source / name).write_text(f"fixture:{name}\n", encoding="utf-8")
        self.settings = UserSettings(vault_path=str(self.vault))
        self.settings_path = self.root / "local" / "config.json"
        self.runner = self.root / "anime-bridge.exe"
        self.runner.write_bytes(b"runner")

    def tearDown(self):
        self.temporary.cleanup()

    def test_new_install_is_preview_first_and_idempotent(self):
        plan = plan_migration(
            self.settings, self.settings_path, self.runner, self.source
        )
        self.assertEqual(plan.plugin_state, "new")
        self.assertFalse(Path(plan.plugin_target).exists())

        written = apply_migration(
            plan, self.settings, self.settings_path, self.source
        )
        self.assertEqual(len(written), len(PLUGIN_FILES) + 2)
        self.assertTrue((Path(plan.plugin_target) / "manifest.json").is_file())
        data = json.loads(
            (Path(plan.plugin_target) / "data.json").read_text(encoding="utf-8")
        )
        self.assertEqual(data["runnerPath"], str(self.runner.resolve()))
        self.assertNotIn("password", self.settings_path.read_text(encoding="utf-8"))

        current = plan_migration(
            self.settings, self.settings_path, self.runner, self.source
        )
        self.assertEqual(current.plugin_state, "current")
        self.assertEqual(current.conflicts, ())

    def test_different_existing_plugin_refuses_the_batch(self):
        target = self.vault / ".obsidian" / "plugins" / "anime-bridge"
        target.mkdir(parents=True)
        (target / "main.js").write_text("user edit", encoding="utf-8")
        plan = plan_migration(
            self.settings, self.settings_path, self.runner, self.source
        )
        self.assertEqual(plan.plugin_state, "conflict")
        with self.assertRaises(MigrationConflict):
            apply_migration(plan, self.settings, self.settings_path, self.source)
        self.assertFalse(self.settings_path.exists())

    def test_known_plugin_with_stale_runner_is_repaired_after_confirmation(self):
        target = self.vault / ".obsidian" / "plugins" / "anime-bridge"
        target.mkdir(parents=True)
        (target / "manifest.json").write_text(
            '{"id":"anime-bridge","version":"old"}', encoding="utf-8"
        )
        (target / "data.json").write_text(
            '{"runnerPath":"C:/missing/anime-bridge.exe"}', encoding="utf-8"
        )
        (target / "personal.txt").write_text("preserve me", encoding="utf-8")

        plan = plan_migration(
            self.settings, self.settings_path, self.runner, self.source
        )
        self.assertEqual(plan.plugin_state, "repair")
        self.assertTrue(plan.repairs)

        apply_migration(plan, self.settings, self.settings_path, self.source)
        data = json.loads((target / "data.json").read_text(encoding="utf-8"))
        self.assertEqual(data["runnerPath"], str(self.runner.resolve()))
        self.assertEqual((target / "personal.txt").read_text(encoding="utf-8"), "preserve me")

    def test_missing_runner_is_reported_before_plugin_changes(self):
        self.runner.unlink()
        with self.assertRaisesRegex(ValueError, "runner does not exist"):
            plan_migration(self.settings, self.settings_path, self.runner, self.source)

    def test_non_vault_is_rejected(self):
        empty = self.root / "not-a-vault"
        empty.mkdir()
        settings = UserSettings(vault_path=str(empty))
        with self.assertRaisesRegex(ValueError, "missing .obsidian"):
            plan_migration(settings, self.settings_path, self.runner, self.source)


if __name__ == "__main__":
    unittest.main()
