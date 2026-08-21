"""Stable domain model for seasonal discovery.

Nothing in this module knows about HTTP, Obsidian, or qBittorrent. Keeping the
calendar and inclusion policy here lets later releases scan selected or historic
quarters without replacing service adapters.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any, Mapping


class AnimeCategory(Enum):
    """Bangumi anime categories supported by the discovery adapter."""

    TV = ("tv", 1, "TV")
    OVA = ("ova", 2, "OVA")
    MOVIE = ("movie", 3, "Movie")
    WEB = ("web", 5, "WEB")
    OTHER = ("other", 0, "Other")

    def __init__(self, config_name: str, bangumi_id: int, label: str) -> None:
        self.config_name = config_name
        self.bangumi_id = bangumi_id
        self.label = label

    @classmethod
    def from_config_name(cls, name: str) -> "AnimeCategory":
        normalized = name.strip().lower()
        for category in cls:
            if category.config_name == normalized:
                return category
        raise ValueError(f"Unsupported anime category: {name}")


class Quarter(Enum):
    WINTER = ("winter", "冬季", 1, (1, 2, 3))
    SPRING = ("spring", "春季", 4, (4, 5, 6))
    SUMMER = ("summer", "夏季", 7, (7, 8, 9))
    AUTUMN = ("autumn", "秋季", 10, (10, 11, 12))

    def __init__(
        self,
        slug: str,
        cn_name: str,
        start_month: int,
        months: tuple[int, int, int],
    ) -> None:
        self.slug = slug
        self.cn_name = cn_name
        self.start_month = start_month
        self.months = months

    @classmethod
    def containing(cls, value: date) -> "Quarter":
        for quarter in cls:
            if value.month in quarter.months:
                return quarter
        raise AssertionError("Every calendar month belongs to a quarter")

    def bounds(self, year: int) -> tuple[date, date]:
        start = date(year, self.start_month, 1)
        if self is Quarter.AUTUMN:
            return start, date(year + 1, 1, 1)
        return start, date(year, self.start_month + 3, 1)

    def folder_name(self) -> str:
        return f"{self.start_month:02d}月新番"


@dataclass(frozen=True, slots=True)
class ScanPolicy:
    """User-approved discovery policy for the current milestone."""

    included_categories: tuple[AnimeCategory, ...] = (
        AnimeCategory.TV,
        AnimeCategory.MOVIE,
        AnimeCategory.WEB,
    )
    include_sequels: bool = True
    required_meta_tag: str = "日本"

    def includes(self, category: AnimeCategory) -> bool:
        return category in self.included_categories

    def includes_subject(self, subject: "AnimeSubject") -> bool:
        return self.includes(subject.category) and self.required_meta_tag in subject.meta_tags


@dataclass(frozen=True, slots=True)
class AnimeSubject:
    bangumi_id: int
    name: str
    name_cn: str
    summary: str
    air_date: date
    category: AnimeCategory
    platform: str = ""
    cover_url: str = ""
    episodes: int | None = None
    score: float | None = None
    meta_tags: tuple[str, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @property
    def display_name(self) -> str:
        return self.name_cn.strip() or self.name.strip() or f"Bangumi {self.bangumi_id}"

    @property
    def bangumi_url(self) -> str:
        return f"https://bgm.tv/subject/{self.bangumi_id}"

    @classmethod
    def from_bangumi_payload(
        cls,
        payload: Mapping[str, Any],
        category: AnimeCategory,
    ) -> "AnimeSubject":
        raw_date = str(payload.get("date") or payload.get("air_date") or "").strip()
        try:
            parsed_date = date.fromisoformat(raw_date)
        except ValueError as exc:
            raise ValueError(
                f"Bangumi subject {payload.get('id', '?')} has invalid air date {raw_date!r}"
            ) from exc

        images = payload.get("images") or {}
        cover_url = ""
        if isinstance(images, Mapping):
            cover_url = str(
                images.get("large") or images.get("common") or images.get("medium") or ""
            )

        rating = payload.get("rating") or {}
        score: float | None = None
        if isinstance(rating, Mapping) and rating.get("score") not in (None, ""):
            score = float(rating["score"])

        episodes_raw = payload.get("eps")
        episodes = int(episodes_raw) if episodes_raw not in (None, "") else None

        meta_tags_raw = payload.get("meta_tags") or []
        meta_tags = (
            tuple(str(item) for item in meta_tags_raw if str(item).strip())
            if isinstance(meta_tags_raw, list)
            else ()
        )

        return cls(
            bangumi_id=int(payload["id"]),
            name=str(payload.get("name") or ""),
            name_cn=str(payload.get("name_cn") or ""),
            summary=str(payload.get("summary") or "").strip(),
            air_date=parsed_date,
            category=category,
            platform=str(payload.get("platform") or ""),
            cover_url=cover_url,
            episodes=episodes,
            score=score,
            meta_tags=meta_tags,
            raw=payload,
        )
