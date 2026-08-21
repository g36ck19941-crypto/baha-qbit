"""Current-quarter discovery use case."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable, Protocol

from anime_bridge.domain import AnimeCategory, AnimeSubject, Quarter, ScanPolicy


class MonthlySubjectSource(Protocol):
    def iter_month(
        self,
        year: int,
        month: int,
        category: AnimeCategory,
    ) -> Iterable[AnimeSubject]: ...


@dataclass(frozen=True, slots=True)
class CurrentQuarterResult:
    reference_date: date
    year: int
    quarter: Quarter
    subjects: tuple[AnimeSubject, ...]
    excluded_without_japan_tag: tuple[AnimeSubject, ...] = ()

    @property
    def identifier(self) -> str:
        return f"{self.year}-{self.quarter.slug}"


class CurrentQuarterScanner:
    def __init__(self, source: MonthlySubjectSource, policy: ScanPolicy | None = None) -> None:
        self.source = source
        self.policy = policy or ScanPolicy()

    def scan(self, reference_date: date | None = None) -> CurrentQuarterResult:
        effective_date = reference_date or date.today()
        quarter = Quarter.containing(effective_date)
        start, end = quarter.bounds(effective_date.year)
        deduplicated: dict[int, AnimeSubject] = {}
        excluded_without_japan_tag: dict[int, AnimeSubject] = {}

        for category in self.policy.included_categories:
            for month in quarter.months:
                for subject in self.source.iter_month(effective_date.year, month, category):
                    if not self.policy.includes(subject.category):
                        continue
                    if not (start <= subject.air_date < end):
                        continue
                    if not self.policy.includes_subject(subject):
                        excluded_without_japan_tag.setdefault(subject.bangumi_id, subject)
                        continue
                    deduplicated.setdefault(subject.bangumi_id, subject)

        ordered = tuple(
            sorted(
                deduplicated.values(),
                key=lambda item: (item.air_date, item.display_name.casefold(), item.bangumi_id),
            )
        )
        return CurrentQuarterResult(
            reference_date=effective_date,
            year=effective_date.year,
            quarter=quarter,
            subjects=ordered,
            excluded_without_japan_tag=tuple(
                sorted(
                    excluded_without_japan_tag.values(),
                    key=lambda item: (
                        item.air_date,
                        item.display_name.casefold(),
                        item.bangumi_id,
                    ),
                )
            ),
        )
