from __future__ import annotations

import json
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SORTER = ROOT / "integrations" / "obsidian-plugin" / "candidate-sort.js"
PLUGIN_MAIN = ROOT / "integrations" / "obsidian-plugin" / "main.js"


class CandidateSortTests(unittest.TestCase):
    def test_plugin_entry_does_not_require_relative_runtime_modules(self):
        entry = PLUGIN_MAIN.read_text(encoding="utf-8")
        self.assertNotIn('require("./candidate-sort")', entry)
        self.assertIn("function reorderCheckedCandidates", entry)

    @unittest.skipUnless(shutil.which("node"), "Node.js is required for plugin behavior tests")
    def test_checked_items_move_first_stably_and_non_candidates_are_unchanged(self):
        candidate = """---
anime_bridge_document: candidates
---
<!-- anime-bridge:items-start -->
- [ ] **一**
  <!-- anime-bridge:item {\"bangumi_id\":1} -->

> first

- [x] **二**
  <!-- anime-bridge:item {\"bangumi_id\":2} -->

> second

- [x] **三**
  <!-- anime-bridge:item {\"bangumi_id\":3} -->

> third
<!-- anime-bridge:items-end -->

用户尾注
"""
        script = (
            "const {reorderCheckedCandidates}=require(process.argv[1]);"
            "const input=JSON.parse(process.argv[2]);"
            "process.stdout.write(JSON.stringify({sorted:reorderCheckedCandidates(input),"
            "plain:reorderCheckedCandidates('- [x] **私人任务**\\n')}));"
        )
        result = subprocess.run(
            ["node", "-e", script, str(SORTER), json.dumps(candidate)],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        payload = json.loads(result.stdout)
        sorted_note = payload["sorted"]
        self.assertLess(sorted_note.index("**二**"), sorted_note.index("**三**"))
        self.assertLess(sorted_note.index("**三**"), sorted_note.index("**一**"))
        self.assertTrue(sorted_note.endswith("<!-- anime-bridge:items-end -->\n\n用户尾注\n"))
        self.assertEqual(payload["plain"], "- [x] **私人任务**\n")


if __name__ == "__main__":
    unittest.main()
