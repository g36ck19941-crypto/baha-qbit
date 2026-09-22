from __future__ import annotations

import unittest
from datetime import date

from anime_bridge.adapters.rss_probe import RSSProbeResult
from anime_bridge.domain import AnimeCategory, CandidateDocument, CandidateSelection
from anime_bridge.workflows import build_candidate_rss_drafts, discover_candidate_rss


class Probe:
    def probe(self, url):
        return RSSProbeResult(url, "dmhy" in url, "RSS/Atom 已验证" if "dmhy" in url else "HTTP 403")


class RSSDiscoveryTests(unittest.TestCase):
    def test_only_verified_sources_are_kept_in_rule_preview(self):
        document = CandidateDocument((
            CandidateSelection(True, "测试动画", 10, AnimeCategory.TV, date(2026, 7, 1)),
        ), bahamut_subtracted=True)
        drafts = build_candidate_rss_drafts(document, ("comicat-rsshub", "dmhy"))
        item = discover_candidate_rss(drafts, Probe())[0]
        self.assertIsNotNone(item.draft)
        self.assertEqual(len(item.results), 2)
        self.assertEqual(len(item.draft.feeds), 1)
        self.assertIn("dmhy", item.draft.feeds[0].url)
        self.assertEqual(item.draft.rule.affected_feeds, (item.draft.feeds[0].url,))

    def test_no_verified_source_keeps_animation_out_of_apply_plan(self):
        class DownProbe:
            def probe(self, url): return RSSProbeResult(url, False, "HTTP 403")
        document = CandidateDocument((
            CandidateSelection(True, "测试动画", 10, AnimeCategory.TV, date(2026, 7, 1)),
        ), bahamut_subtracted=True)
        drafts = build_candidate_rss_drafts(document, "dmhy")
        item = discover_candidate_rss(drafts, DownProbe())[0]
        self.assertIsNone(item.draft)
