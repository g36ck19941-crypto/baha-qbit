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
    apply_rss_plan,
    plan_checked_import,
    plan_rss,
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
    ) -> dict[str, Any]:
        feed, rule = self._rss_drafts(
            feed_url,
            feed_path,
            rule_name,
            must_contain,
            must_not_contain,
            use_regex,
            episode_filter,
            smart_filter,
            category,
            save_path,
        )
        plan = plan_rss(self.qbit, feed, rule)
        return {
            "feed": {"url": feed.url, "path": feed.path},
            "rule": {"name": rule.name, **rule.to_qbittorrent_definition()},
            "feed_conflict": plan.feed_conflict,
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
    ) -> dict[str, Any]:
        self._require_write(confirmation)
        feed, rule = self._rss_drafts(
            feed_url,
            feed_path,
            rule_name,
            must_contain,
            must_not_contain,
            use_regex,
            episode_filter,
            smart_filter,
            category,
            save_path,
        )
        plan = plan_rss(self.qbit, feed, rule)
        apply_rss_plan(self.qbit, plan)
        return {
            "created": True,
            "feed_path": feed.path,
            "rule_name": rule.name,
            "enabled": False,
            "add_paused": True,
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
    ) -> tuple[RSSFeedDraft, RSSRuleDraft]:
        feed = RSSFeedDraft(feed_url, feed_path)
        rule = RSSRuleDraft(
            name=rule_name,
            affected_feeds=(feed_url,),
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
        return feed, rule
