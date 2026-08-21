from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from anime_bridge.settings import UserSettings


class SettingsTests(unittest.TestCase):
    def test_round_trip_non_secret_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested" / "config.json"
            expected = UserSettings(
                vault_path="D:/Vault",
                integration_folder="candidates",
                formal_root="Anime",
                qbit_base_url="http://localhost:9090",
            )
            expected.save(path)
            self.assertEqual(UserSettings.load(path), expected)
            content = path.read_text(encoding="utf-8")
            self.assertNotIn("password", content.lower())
            self.assertNotIn("cookie", content.lower())

    def test_unknown_future_keys_are_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text('{"vault_path":"D:/Vault","future":true}', encoding="utf-8")
            self.assertEqual(UserSettings.load(path).vault_path, "D:/Vault")


if __name__ == "__main__":
    unittest.main()
