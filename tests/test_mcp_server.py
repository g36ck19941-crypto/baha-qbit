from __future__ import annotations

import importlib.util
import tempfile
import unittest
from datetime import date
from pathlib import Path

from anime_bridge.ai import AnimeBridgeAIService
from anime_bridge.domain import AnimeSubject
from anime_bridge.mcp_server import build_mcp_server


MCP_AVAILABLE = importlib.util.find_spec("mcp") is not None


class FakeBangumi:
    def get_subject(self, subject_id, category):
        return AnimeSubject(
            bangumi_id=subject_id,
            name="MCP Test",
            name_cn="MCP 测试",
            summary="MCP summary",
            air_date=date(2026, 7, 1),
            category=category,
        )


class FakeQbit:
    def versions(self): return "v4.5.5", "2.8.19"
    def rss_items(self): return {}
    def rss_rules(self): return {}
    def add_feed(self, url, path): pass
    def set_rule(self, name, definition): pass


@unittest.skipUnless(MCP_AVAILABLE, "official MCP SDK optional dependency not installed")
class MCPServerTests(unittest.IsolatedAsyncioTestCase):
    async def test_read_only_server_lists_and_calls_five_tools(self):
        from mcp import Client

        with tempfile.TemporaryDirectory() as directory:
            service = AnimeBridgeAIService(
                Path(directory), bangumi=FakeBangumi(), qbit=FakeQbit()
            )
            server = build_mcp_server(service)
            async with Client(server, raise_exceptions=True) as client:
                tools = await client.list_tools()
                names = {tool.name for tool in tools.tools}
                self.assertEqual(
                    names,
                    {
                        "bangumi_get_subject",
                        "obsidian_plan_checked_import",
                        "qbittorrent_get_rss_status",
                        "qbittorrent_plan_rss",
                        "qbittorrent_plan_candidate_rss",
                    },
                )
                result = await client.call_tool(
                    "bangumi_get_subject", {"subject_id": 10, "category": "tv"}
                )
                self.assertFalse(result.is_error)
                self.assertEqual(result.structured_content["title"], "MCP 测试")

    async def test_write_tools_are_registered_only_with_startup_gate(self):
        from mcp import Client

        with tempfile.TemporaryDirectory() as directory:
            service = AnimeBridgeAIService(
                Path(directory),
                allow_writes=True,
                bangumi=FakeBangumi(),
                qbit=FakeQbit(),
            )
            server = build_mcp_server(service)
            async with Client(server, raise_exceptions=True) as client:
                tools = await client.list_tools()
                names = {tool.name for tool in tools.tools}
                self.assertIn("obsidian_apply_checked_import", names)
                self.assertIn("qbittorrent_apply_rss", names)
                self.assertIn("qbittorrent_apply_candidate_rss", names)
                self.assertEqual(len(names), 8)


if __name__ == "__main__":
    unittest.main()
