"""Conservative cross-site title matching.

Only normalized exact equality is eligible for automatic subtraction. Fuzzy
similarity is surfaced for review and never silently removes a candidate.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from enum import Enum
from typing import Iterable

from anime_bridge.domain import AnimeSubject, BahamutFavorite


_NON_WORD = re.compile(r"[^\w\u3040-\u30ff\u3400-\u9fff]+", re.UNICODE)


def normalize_title(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return _NON_WORD.sub("", normalized).replace("_", "")


class MatchKind(Enum):
    EXACT = "exact"
    REVIEW = "review"
    NONE = "none"


@dataclass(frozen=True, slots=True)
class TitleMatch:
    kind: MatchKind
    score: float
    subject: AnimeSubject
    favorite: BahamutFavorite | None = None
    subject_title: str = ""

    @property
    def auto_exclude(self) -> bool:
        return self.kind is MatchKind.EXACT and self.favorite is not None


def _pairs(
    subject_titles: Iterable[str], favorites: Iterable[BahamutFavorite]
) -> Iterable[tuple[str, str, BahamutFavorite]]:
    for subject_title in subject_titles:
        normalized_subject = normalize_title(subject_title)
        if not normalized_subject:
            continue
        for favorite in favorites:
            normalized_favorite = normalize_title(favorite.title)
            if normalized_favorite:
                yield normalized_subject, normalized_favorite, favorite


def best_title_match(
    subject: AnimeSubject,
    favorites: Iterable[BahamutFavorite],
    review_threshold: float = 0.72,
) -> TitleMatch:
    best_score = 0.0
    best_favorite: BahamutFavorite | None = None
    best_subject_title = ""

    for subject_title in subject.title_variants:
        for normalized_subject, normalized_favorite, favorite in _pairs(
            (subject_title,), favorites
        ):
            if normalized_subject == normalized_favorite:
                return TitleMatch(
                    kind=MatchKind.EXACT,
                    score=1.0,
                    subject=subject,
                    favorite=favorite,
                    subject_title=subject_title,
                )
            score = SequenceMatcher(None, normalized_subject, normalized_favorite).ratio()
            if score > best_score:
                best_score = score
                best_favorite = favorite
                best_subject_title = subject_title

    if best_favorite is not None and best_score >= review_threshold:
        return TitleMatch(
            kind=MatchKind.REVIEW,
            score=best_score,
            subject=subject,
            favorite=best_favorite,
            subject_title=best_subject_title,
        )
    return TitleMatch(kind=MatchKind.NONE, score=best_score, subject=subject)

