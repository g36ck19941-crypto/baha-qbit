"""Obsidian candidate and formal-import domain values."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import PurePosixPath

from .models import AnimeCategory, AnimeSubject


@dataclass(frozen=True, slots=True)
class CandidateSelection:
    checked: bool
    title: str
    bangumi_id: int
    category: AnimeCategory
    air_date: date


@dataclass(frozen=True, slots=True)
class CandidateDocument:
    selections: tuple[CandidateSelection, ...]

    @property
    def checked(self) -> tuple[CandidateSelection, ...]:
        return tuple(item for item in self.selections if item.checked)


@dataclass(frozen=True, slots=True)
class FormalNotePlan:
    subject: AnimeSubject
    target_relative: PurePosixPath
    content: str
    conflict: bool

