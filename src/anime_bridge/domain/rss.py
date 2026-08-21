"""Validated qBittorrent RSS drafts, independent of HTTP and UI code."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RSSFeedDraft:
    url: str
    path: str

    def __post_init__(self) -> None:
        if not self.url.startswith(("http://", "https://")):
            raise ValueError("RSS feed URL must use HTTP or HTTPS")
        if not self.path.strip() or self.path.startswith("/") or ".." in self.path.split("/"):
            raise ValueError("RSS feed path must be a relative qBittorrent path")


@dataclass(frozen=True, slots=True)
class RSSRuleDraft:
    name: str
    affected_feeds: tuple[str, ...]
    must_contain: str = ""
    must_not_contain: str = ""
    use_regex: bool = False
    episode_filter: str = ""
    smart_filter: bool = False
    add_paused: bool = True
    assigned_category: str = ""
    save_path: str = ""
    enabled: bool = False

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("RSS rule name cannot be empty")
        if not self.affected_feeds:
            raise ValueError("RSS rule must reference at least one feed")
        if any(not url.startswith(("http://", "https://")) for url in self.affected_feeds):
            raise ValueError("Affected qBittorrent feeds must be feed URLs")

    def to_qbittorrent_definition(self) -> dict[str, object]:
        return {
            "enabled": self.enabled,
            "mustContain": self.must_contain,
            "mustNotContain": self.must_not_contain,
            "useRegex": self.use_regex,
            "episodeFilter": self.episode_filter,
            "smartFilter": self.smart_filter,
            "previouslyMatchedEpisodes": [],
            "affectedFeeds": list(self.affected_feeds),
            "ignoreDays": 0,
            "lastMatch": "",
            "addPaused": self.add_paused,
            "assignedCategory": self.assigned_category,
            "savePath": self.save_path,
        }
