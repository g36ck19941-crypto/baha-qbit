from __future__ import annotations

import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CodexConfigTests(unittest.TestCase):
    def test_project_mcp_config_is_safe_and_points_to_packaged_server(self) -> None:
        config = tomllib.loads((ROOT / ".codex" / "config.toml").read_text("utf-8"))
        server = config["mcp_servers"]["anime_bridge"]

        self.assertEqual(server["command"], "./dist/anime-bridge.exe")
        self.assertEqual(server["args"][0], "mcp")
        self.assertIn("--allow-writes", server["args"])
        self.assertEqual(server["default_tools_approval_mode"], "writes")
        self.assertFalse(server["required"])


if __name__ == "__main__":
    unittest.main()
