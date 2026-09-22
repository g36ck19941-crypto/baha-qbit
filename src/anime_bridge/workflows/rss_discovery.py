"""Keep only verified public RSS feeds in a preview-first candidate plan."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Protocol

from anime_bridge.adapters.rss_probe import RSSProbeResult
from anime_bridge.domain import RSSRuleDraft
from anime_bridge.workflows.rss_sources import CandidateRSSDraft


class RSSProbe(Protocol):
    def probe(self, url: str) -> RSSProbeResult: ...


@dataclass(frozen=True, slots=True)
class CandidateRSSDiscovery:
    draft: CandidateRSSDraft | None
    title: str
    results: tuple[RSSProbeResult, ...]


def discover_candidate_rss(
    drafts: tuple[CandidateRSSDraft, ...], probe: RSSProbe
) -> tuple[CandidateRSSDiscovery, ...]:
    discoveries: list[CandidateRSSDiscovery] = []
    for draft in drafts:
        results = tuple(probe.probe(feed.url) for feed in draft.feeds)
        feeds = tuple(feed for feed, result in zip(draft.feeds, results, strict=True) if result.available)
        discovered = None
        if feeds:
            rule = replace(draft.rule, affected_feeds=tuple(feed.url for feed in feeds))
            discovered = replace(draft, feeds=feeds, providers=tuple(feed.path.rsplit("/", 1)[-1] for feed in feeds), rule=rule)
        discoveries.append(CandidateRSSDiscovery(discovered, draft.title, results))
    return tuple(discoveries)
