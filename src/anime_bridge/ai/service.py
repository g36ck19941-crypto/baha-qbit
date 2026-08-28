"""Safety-gated operations shared by MCP and future local AI interfaces."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from anime_bridge.adapters.bangumi import BangumiClient
from anime_bridge.adapters.candidate_markdown import parse_candidate_markdown
from anime_bridge.adapters.qbittorrent import QBittorrentClient
from anime_bridge.domain import AnimeCategory, RSSFeedDraft, RSSRuleDraft
from anime_bridge.workflows import (
    apply_import_plan,
    apply_formal_note_delete,
    apply_rss_batch,
    apply_rss_bundle,
    apply_rss_plan,
    build_candidate_rss_drafts,
    list_formal_anime_notes,
    plan_checked_import,
    plan_formal_note_delete,
    plan_rss,
    plan_rss_batch,
    plan_rss_bundle,
)


WRITE_CONFIRMATION = "CONFIRM_LOCAL_WRITE"


class WritePermissionError(RuntimeError):
    """The server or individual call did not explicitly authorize a write."""


class AnimeBridgeAIService:
    def __init__(
        self,
        vault_path: Path,
        *,
        formal_root: str = "C/bangumi",
        qbit_base_url: str = "http://127.0.0.1:8080",
        allow_writes: bool = False,
        bangumi: Any | None = None,
        qbit: Any | None = None,
    ) -> None:
        self.vault_path = vault_path.resolve()
        self.formal_root = formal_root
        self.allow_writes = allow_writes
        self.bangumi = bangumi or BangumiClient()
        self.qbit = qbit or QBittorrentClient(qbit_base_url)

    def _vault_markdown(self, candidate_path: str) -> Path:
        path = Path(candidate_path)
        if not path.is_absolute():
            path = self.vault_path / path
        resolved = path.resolve()
        try:
            resolved.relative_to(self.vault_path)
        except ValueError as exc:
            raise ValueError("Candidate note must stay inside the configured Vault") from exc
        if resolved.suffix.lower() != ".md":
            raise ValueError("Candidate note must be a Markdown file")
        return resolved

    def bangumi_subject(self, subject_id: int, category: str) -> dict[str, Any]:
        subject = self.bangumi.get_subject(
            int(subject_id), AnimeCategory.from_config_name(category)
        )
        return {
            "bangumi_id": subject.bangumi_id,
            "title": subject.display_name,
            "name": subject.name,
            "name_cn": subject.name_cn,
            "aliases": list(subject.aliases),
            "category": subject.category.config_name,
            "air_date": subject.air_date.isoformat(),
            "episodes": subject.episodes,
            "score": subject.score,
            "summary": subject.summary,
            "cover_url": subject.cover_url,
            "url": subject.bangumi_url,
        }

    def plan_obsidian_import(self, candidate_path: str) -> dict[str, Any]:
        candidate = self._vault_markdown(candidate_path)
        document = parse_candidate_markdown(candidate.read_text(encoding="utf-8"))
        plans = plan_checked_import(
            document, self.bangumi, self.vault_path, self.formal_root
        )
        return {
            "candidate": str(candidate),
            "checked_count": len(plans),
            "conflict_count": sum(plan.conflict for plan in plans),
            "items": [
                {
                    "bangumi_id": plan.subject.bangumi_id,
                    "title": plan.subject.display_name,
                    "target": plan.target_relative.as_posix(),
                    "conflict": plan.conflict,
                }
                for plan in plans
            ],
        }

    def apply_obsidian_import(
        self, candidate_path: str, confirmation: str
    ) -> dict[str, Any]:
        self._require_write(confirmation)
        candidate = self._vault_markdown(candidate_path)
        document = parse_candidate_markdown(candidate.read_text(encoding="utf-8"))
        plans = plan_checked_import(
            document, self.bangumi, self.vault_path, self.formal_root
        )
        written = apply_import_plan(plans, self.vault_path)
        return {"written_count": len(written), "paths": [str(path) for path in written]}

    def list_obsidian_library(self) -> dict[str, Any]:
        items = list_formal_anime_notes(self.vault_path, self.formal_root)
        return {"count": len(items), "items": [item.as_dict() for item in items]}

    def plan_obsidian_delete(self, relative_path: str) -> dict[str, Any]:
        return plan_formal_note_delete(
            self.vault_path, self.formal_root, relative_path
        ).as_dict()

    def apply_obsidian_delete(
        self, relative_path: str, expected_sha256: str, confirmation: str
    ) -> dict[str, Any]:
        self._require_write(confirmation)
        plan = plan_formal_note_delete(
            self.vault_path, self.formal_root, relative_path
        )
        moved_to = apply_formal_note_delete(plan, self.vault_path, expected_sha256)
        return {
            "deleted": plan.relative_path,
            "moved_to": str(moved_to),
            "recoverable": True,
        }

    def qbit_status(self) -> dict[str, Any]:
        version, api_version = self.qbit.versions()
        return {
            "version": version,
            "web_api_version": api_version,
            "feeds": self.qbit.rss_items(),
            "rules": self.qbit.rss_rules(),
        }

    def plan_qbit_rss(
        self,
        feed_url: str,
        feed_path: str,
        rule_name: str,
        must_contain: str = "",
        must_not_contain: str = "",
        use_regex: bool = False,
        episode_filter: str = "",
        smart_filter: bool = False,
        category: str = "",
        save_path: str = "",
        feed_urls: tuple[str, ...] = (),
    ) -> dict[str, Any]:
        feeds, rule = self._rss_drafts(
            feed_url,
            feed_path,
            rule_name,
            must_contain,
            must_not_contain,
            use_regex,
            episode_filter,
            smart_filter,
            category,
            save_path, feed_urls,
        )
        if len(feeds) == 1:
            feed = feeds[0]
            plan = plan_rss(self.qbit, feed, rule)
            feed_conflicts = [plan.feed_conflict]
        else:
            plan = plan_rss_bundle(self.qbit, feeds, rule)
            feed_conflicts = list(plan.feed_conflicts)
        return {
            "feeds": [{"url": feed.url, "path": feed.path} for feed in feeds],
            "rule": {"name": rule.name, **rule.to_qbittorrent_definition()},
            "feed_conflicts": feed_conflicts,
            "rule_conflict": plan.rule_conflict,
        }

    def apply_qbit_rss(
        self,
        feed_url: str,
        feed_path: str,
        rule_name: str,
        confirmation: str,
        must_contain: str = "",
        must_not_contain: str = "",
        use_regex: bool = False,
        episode_filter: str = "",
        smart_filter: bool = False,
        category: str = "",
        save_path: str = "",
        feed_urls: tuple[str, ...] = (),
    ) -> dict[str, Any]:
        self._require_write(confirmation)
        feeds, rule = self._rss_drafts(
            feed_url,
            feed_path,
            rule_name,
            must_contain,
            must_not_contain,
            use_regex,
            episode_filter,
            smart_filter,
            category,
            save_path, feed_urls,
        )
        if len(feeds) == 1:
            plan = plan_rss(self.qbit, feeds[0], rule)
            apply_rss_plan(self.qbit, plan)
        else:
            plan = plan_rss_bundle(self.qbit, feeds, rule)
            apply_rss_bundle(self.qbit, plan)
        return {
            "created": True,
            "feed_paths": [feed.path for feed in feeds],
            "rule_name": rule.name,
            "enabled": False,
            "add_paused": True,
        }

    def analyze_candidate_note(self, candidate_path: str) -> dict[str, Any]:
        """Return deterministic note state and fuzzy evidence without editing it."""
        candidate = self._vault_markdown(candidate_path)
        document = parse_candidate_markdown(candidate.read_text(encoding="utf-8"))
        return {
            "candidate": str(candidate),
            "bahamut_subtracted": document.bahamut_subtracted,
            "selection_count": len(document.selections),
            "checked_count": len(document.checked),
            "unchecked_count": len(document.selections) - len(document.checked),
            "selections": [
                {
                    "bangumi_id": item.bangumi_id,
                    "title": item.title,
                    "category": item.category.config_name,
                    "air_date": item.air_date.isoformat(),
                    "checked": item.checked,
                }
                for item in document.selections
            ],
            "fuzzy_reviews": [
                {
                    "bangumi_id": review.bangumi_id,
                    "subject_title": review.subject_title,
                    "favorite_title": review.favorite_title,
                    "favorite_href": review.favorite_href,
                    "score": review.score,
                    "policy": "human_review_required_never_auto_exclude",
                }
                for review in document.reviews
            ],
        }

    def plan_candidate_rss(
        self,
        candidate_path: str,
        provider: str | tuple[str, ...],
        extra_terms: tuple[str, ...] = (),
        custom_template: str = "",
        must_contain: str = "",
        must_not_contain: str = "",
        episode_filter: str = "",
        category: str = "anime",
        save_root: str = "",
    ) -> dict[str, Any]:
        candidate = self._vault_markdown(candidate_path)
        document = parse_candidate_markdown(candidate.read_text(encoding="utf-8"))
        drafts = build_candidate_rss_drafts(
            document,
            provider,
            extra_terms=extra_terms,
            custom_template=custom_template,
            must_contain=must_contain,
            must_not_contain=must_not_contain,
            episode_filter=episode_filter,
            category=category,
            save_root=save_root,
        )
        batch = plan_rss_batch(
            self.qbit, tuple((draft.feeds, draft.rule) for draft in drafts)
        )
        return self._candidate_rss_payload(candidate, drafts, batch)

    def apply_candidate_rss(
        self,
        candidate_path: str,
        provider: str | tuple[str, ...],
        confirmation: str,
        extra_terms: tuple[str, ...] = (),
        custom_template: str = "",
        must_contain: str = "",
        must_not_contain: str = "",
        episode_filter: str = "",
        category: str = "anime",
        save_root: str = "",
    ) -> dict[str, Any]:
        self._require_write(confirmation)
        candidate = self._vault_markdown(candidate_path)
        document = parse_candidate_markdown(candidate.read_text(encoding="utf-8"))
        drafts = build_candidate_rss_drafts(
            document,
            provider,
            extra_terms=extra_terms,
            custom_template=custom_template,
            must_contain=must_contain,
            must_not_contain=must_not_contain,
            episode_filter=episode_filter,
            category=category,
            save_root=save_root,
        )
        batch = plan_rss_batch(
            self.qbit, tuple((draft.feeds, draft.rule) for draft in drafts)
        )
        apply_rss_batch(self.qbit, batch)
        return {
            "created_count": len(drafts),
            "feed_paths": [feed.path for draft in drafts for feed in draft.feeds],
            "rule_names": [draft.rule.name for draft in drafts],
            "enabled": False,
            "add_paused": True,
            "atomic": False,
        }

    @staticmethod
    def _candidate_rss_payload(candidate: Path, drafts: Any, batch: Any) -> dict[str, Any]:
        return {
            "candidate": str(candidate),
            "draft_count": len(drafts),
            "conflict_count": sum(plan.has_conflict for plan in batch.plans)
            + len(batch.duplicate_targets),
            "duplicate_targets": list(batch.duplicate_targets),
            "items": [
                {
                    "bangumi_id": draft.bangumi_id,
                    "title": draft.title,
                    "providers": list(draft.providers),
                    "search_terms": list(draft.search_terms),
                    "feeds": [
                        {"url": feed.url, "path": feed.path} for feed in draft.feeds
                    ],
                    "rule": {
                        "name": draft.rule.name,
                        **draft.rule.to_qbittorrent_definition(),
                    },
                    "feed_conflicts": list(
                        plan.feed_conflicts if hasattr(plan, "feed_conflicts")
                        else (plan.feed_conflict,)
                    ),
                    "rule_conflict": plan.rule_conflict,
                }
                for draft, plan in zip(drafts, batch.plans, strict=True)
            ],
            "safe_defaults": {"enabled": False, "add_paused": True},
        }

    def _require_write(self, confirmation: str) -> None:
        if not self.allow_writes:
            raise WritePermissionError(
                "This MCP server was started without explicit write permission"
            )
        if confirmation != WRITE_CONFIRMATION:
            raise WritePermissionError(
                f"Write call requires confirmation={WRITE_CONFIRMATION!r}"
            )

    @staticmethod
    def _rss_drafts(
        feed_url: str,
        feed_path: str,
        rule_name: str,
        must_contain: str,
        must_not_contain: str,
        use_regex: bool,
        episode_filter: str,
        smart_filter: bool,
        category: str,
        save_path: str,
        feed_urls: tuple[str, ...] = (),
    ) -> tuple[tuple[RSSFeedDraft, ...], RSSRuleDraft]:
        urls = tuple(dict.fromkeys(url.strip() for url in (feed_url, *feed_urls) if url.strip()))
        if not urls:
            raise ValueError("At least one RSS URL is required")
        feeds = tuple(
            RSSFeedDraft(
                url,
                feed_path if len(urls) == 1 else f"{feed_path}/source-{index}",
            )
            for index, url in enumerate(urls, start=1)
        )
        rule = RSSRuleDraft(
            name=rule_name,
            affected_feeds=tuple(feed.url for feed in feeds),
            must_contain=must_contain,
            must_not_contain=must_not_contain,
            use_regex=use_regex,
            episode_filter=episode_filter,
            smart_filter=smart_filter,
            assigned_category=category,
            save_path=save_path,
            enabled=False,
            add_paused=True,
        )
        return feeds, rule
    build_candidate_rss_drafts,
