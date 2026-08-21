"""Preview-first qBittorrent RSS planning and application."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from anime_bridge.domain.rss import RSSFeedDraft, RSSRuleDraft


class RSSClient(Protocol):
    def rss_items(self) -> dict[str, Any]: ...
    def rss_rules(self) -> dict[str, Any]: ...
    def add_feed(self, url: str, path: str) -> None: ...
    def set_rule(self, name: str, definition: dict[str, object]) -> None: ...


class RSSPlanConflict(RuntimeError):
    """The requested feed path or rule name already exists."""


@dataclass(frozen=True, slots=True)
class RSSPlan:
    feed: RSSFeedDraft
    rule: RSSRuleDraft
    feed_conflict: bool
    rule_conflict: bool

    @property
    def has_conflict(self) -> bool:
        return self.feed_conflict or self.rule_conflict


def _rss_paths(tree: dict[str, Any], prefix: str = "") -> set[str]:
    paths: set[str] = set()
    for name, node in tree.items():
        path = f"{prefix}/{name}" if prefix else name
        paths.add(path)
        if isinstance(node, dict):
            children = node.get("children")
            if isinstance(children, dict):
                paths.update(_rss_paths(children, path))
    return paths


def plan_rss(client: RSSClient, feed: RSSFeedDraft, rule: RSSRuleDraft) -> RSSPlan:
    return RSSPlan(
        feed=feed,
        rule=rule,
        feed_conflict=feed.path in _rss_paths(client.rss_items()),
        rule_conflict=rule.name in client.rss_rules(),
    )


def apply_rss_plan(client: RSSClient, plan: RSSPlan) -> None:
    fresh_plan = plan_rss(client, plan.feed, plan.rule)
    if plan.has_conflict or fresh_plan.has_conflict:
        raise RSSPlanConflict("RSS apply refused because the preview contains conflicts")
    client.add_feed(plan.feed.url, plan.feed.path)
    client.set_rule(plan.rule.name, plan.rule.to_qbittorrent_definition())
