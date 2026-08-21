from __future__ import annotations

import unittest

from anime_bridge.adapters.qbittorrent import QBittorrentClient
from anime_bridge.domain.rss import RSSFeedDraft, RSSRuleDraft
from anime_bridge.workflows.rss_plan import RSSPlanConflict, apply_rss_plan, plan_rss


class FakeRSSClient:
    def __init__(self, items=None, rules=None):
        self.items = items or {}
        self.rules = rules or {}
        self.calls = []

    def rss_items(self): return self.items
    def rss_rules(self): return self.rules
    def add_feed(self, url, path): self.calls.append(("feed", url, path))
    def set_rule(self, name, definition): self.calls.append(("rule", name, definition))


def drafts():
    feed = RSSFeedDraft("https://example.invalid/anime.xml", "动画/LV999")
    rule = RSSRuleDraft(
        "LV999 1080p", ("https://example.invalid/anime.xml",), must_contain="1080"
    )
    return feed, rule


class QBittorrentRSSTests(unittest.TestCase):
    def test_remote_webui_is_refused(self):
        with self.assertRaises(ValueError):
            QBittorrentClient("http://192.168.1.8:8080")

    def test_safe_defaults_are_serialized(self):
        _, rule = drafts()
        definition = rule.to_qbittorrent_definition()
        self.assertFalse(definition["enabled"])
        self.assertTrue(definition["addPaused"])
        self.assertEqual(
            definition["affectedFeeds"], ["https://example.invalid/anime.xml"]
        )

    def test_plan_detects_nested_feed_and_rule_conflicts(self):
        feed, rule = drafts()
        client = FakeRSSClient(
            {"动画": {"children": {"LV999": {"url": feed.url}}}},
            {rule.name: {}},
        )
        plan = plan_rss(client, feed, rule)
        self.assertTrue(plan.feed_conflict)
        self.assertTrue(plan.rule_conflict)
        with self.assertRaises(RSSPlanConflict):
            apply_rss_plan(client, plan)
        self.assertEqual(client.calls, [])

    def test_apply_adds_feed_then_disabled_rule(self):
        feed, rule = drafts()
        client = FakeRSSClient()
        plan = plan_rss(client, feed, rule)
        apply_rss_plan(client, plan)
        self.assertEqual(client.calls[0], ("feed", feed.url, feed.path))
        self.assertEqual(client.calls[1][0:2], ("rule", rule.name))
        self.assertFalse(client.calls[1][2]["enabled"])


if __name__ == "__main__":
    unittest.main()
