from __future__ import annotations

import unittest
from datetime import date

from anime_bridge.domain import AnimeCategory, CandidateDocument, CandidateSelection
from anime_bridge.workflows.rss_sources import (
    build_candidate_rss_drafts,
    build_feed_url,
    provider_catalog,
)


class RSSSourceTests(unittest.TestCase):
    def document(self):
        return CandidateDocument(
            (
                CandidateSelection(
                    True, "跃动青春 / 第二季", 101, AnimeCategory.TV, date(2026, 7, 2)
                ),
                CandidateSelection(
                    False, "未选择动画", 102, AnimeCategory.TV, date(2026, 7, 3)
                ),
            )
        )

    def test_catalog_is_replaceable_and_uses_https(self):
        providers = {provider.key: provider for provider in provider_catalog()}
        self.assertEqual(set(providers), {"comicat-rsshub", "dmhy"})
        self.assertTrue(all(provider.template.startswith("https://") for provider in providers.values()))
        self.assertIn("self-hosted", providers["comicat-rsshub"].operational_note)

    def test_provider_urls_encode_title_and_extra_terms(self):
        comicat = build_feed_url("comicat-rsshub", ("跃动青春", "1080P", "简日"))
        self.assertEqual(
            comicat,
            "https://rsshub.app/comicat/search/%E8%B7%83%E5%8A%A8%E9%9D%92%E6%98%A5+1080P+%E7%AE%80%E6%97%A5",
        )
        dmhy = build_feed_url("dmhy", ("跃动青春", "1080P"))
        self.assertIn("keyword=%E8%B7%83%E5%8A%A8%E9%9D%92%E6%98%A5+1080P", dmhy)

    def test_custom_template_requires_credential_free_https(self):
        with self.assertRaises(ValueError):
            build_feed_url("custom", ("Title",), custom_template="http://example.com/{query}")
        with self.assertRaises(ValueError):
            build_feed_url("custom", ("Title",), custom_template="https://user:pw@example.com/{query}")
        with self.assertRaises(ValueError):
            build_feed_url("unknown", ("Title",), custom_template="https://example.com/{query}")

    def test_checked_candidates_produce_disabled_paused_safe_drafts(self):
        drafts = build_candidate_rss_drafts(
            self.document(),
            "comicat-rsshub",
            extra_terms=("1080P", "CHS"),
            must_not_contain="720P",
            episode_filter="1-12",
            save_root="D:/Anime",
        )
        self.assertEqual(len(drafts), 1)
        draft = drafts[0]
        self.assertEqual(draft.bangumi_id, 101)
        self.assertNotIn("/", draft.feed.path.rsplit("/", 1)[-1])
        definition = draft.rule.to_qbittorrent_definition()
        self.assertFalse(definition["enabled"])
        self.assertTrue(definition["addPaused"])
        self.assertEqual(definition["episodeFilter"], "1-12")
        self.assertIn("跃动青春", draft.search_terms[0])
        with self.assertRaisesRegex(ValueError, "absolute"):
            build_candidate_rss_drafts(
                self.document(), "dmhy", save_root="relative/path"
            )


if __name__ == "__main__":
    unittest.main()
