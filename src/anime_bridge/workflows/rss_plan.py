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


@dataclass(frozen=True, slots=True)
class RSSBundlePlan:
    """Several feed URLs covered by one qBittorrent download rule."""

    feeds: tuple[RSSFeedDraft, ...]
    rule: RSSRuleDraft
    feed_conflicts: tuple[bool, ...]
    rule_conflict: bool

    @property
    def has_conflict(self) -> bool:
        return any(self.feed_conflicts) or self.rule_conflict


@dataclass(frozen=True, slots=True)
class RSSBatchPlan:
    plans: tuple[RSSPlan | RSSBundlePlan, ...]
    duplicate_targets: tuple[str, ...] = ()

    @property
    def has_conflict(self) -> bool:
        return bool(self.duplicate_targets) or any(plan.has_conflict for plan in self.plans)


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


def plan_rss_bundle(
    client: RSSClient, feeds: tuple[RSSFeedDraft, ...], rule: RSSRuleDraft
) -> RSSBundlePlan:
    if not feeds:
        raise ValueError("RSS bundle requires at least one feed")
    paths = _rss_paths(client.rss_items())
    return RSSBundlePlan(
        feeds=feeds,
        rule=rule,
        feed_conflicts=tuple(feed.path in paths for feed in feeds),
        rule_conflict=rule.name in client.rss_rules(),
    )


def apply_rss_bundle(client: RSSClient, plan: RSSBundlePlan) -> None:
    fresh = plan_rss_bundle(client, plan.feeds, plan.rule)
    if plan.has_conflict or fresh.has_conflict:
        raise RSSPlanConflict("RSS apply refused because the preview contains conflicts")
    for feed in fresh.feeds:
        client.add_feed(feed.url, feed.path)
    client.set_rule(fresh.rule.name, fresh.rule.to_qbittorrent_definition())


def plan_rss_batch(
    client: RSSClient,
    drafts: tuple[tuple[RSSFeedDraft | tuple[RSSFeedDraft, ...], RSSRuleDraft], ...],
) -> RSSBatchPlan:
    paths = [feed.path for feed_group, _ in drafts for feed in (feed_group if isinstance(feed_group, tuple) else (feed_group,))]
    rules = [rule.name for _, rule in drafts]
    duplicates = tuple(
        sorted(
            {f"feed:{value}" for value in paths if paths.count(value) > 1}
            | {f"rule:{value}" for value in rules if rules.count(value) > 1}
        )
    )
    existing_paths = _rss_paths(client.rss_items())
    existing_rules = client.rss_rules()
    plans = tuple(
        (
            RSSBundlePlan(
                feeds=feed_group,
                rule=rule,
                feed_conflicts=tuple(feed.path in existing_paths for feed in feed_group),
                rule_conflict=rule.name in existing_rules,
            )
            if isinstance(feed_group, tuple)
            else RSSPlan(
                feed=feed_group,
                rule=rule,
                feed_conflict=feed_group.path in existing_paths,
                rule_conflict=rule.name in existing_rules,
            )
        )
        for feed_group, rule in drafts
    )
    return RSSBatchPlan(plans=plans, duplicate_targets=duplicates)


def apply_rss_batch(client: RSSClient, batch: RSSBatchPlan) -> None:
    drafts = tuple(
        ((plan.feeds if isinstance(plan, RSSBundlePlan) else plan.feed), plan.rule)
        for plan in batch.plans
    )
    fresh = plan_rss_batch(client, drafts)
    if batch.has_conflict or fresh.has_conflict:
        raise RSSPlanConflict("RSS batch apply refused because the preview contains conflicts")
    for plan in fresh.plans:
        if isinstance(plan, RSSBundlePlan):
            for feed in plan.feeds:
                client.add_feed(feed.url, feed.path)
        else:
            client.add_feed(plan.feed.url, plan.feed.path)
        client.set_rule(plan.rule.name, plan.rule.to_qbittorrent_definition())
