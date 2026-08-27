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
from functools import lru_cache
from typing import Iterable

from opencc import OpenCC

from anime_bridge.domain import AnimeSubject, BahamutCatalogItem


_NON_WORD = re.compile(r"[^\w\u3040-\u30ff\u3400-\u9fff]+", re.UNICODE)
_SEQUEL_SUFFIXES = (
    (re.compile(r"(?:第二季|第2季|2ndseason|season2|ii)$"), "2"),
    (re.compile(r"(?:第三季|第3季|3rdseason|season3|iii)$"), "3"),
    (re.compile(r"(?:第四季|第4季|4thseason|season4|iv)$"), "4"),
)


def normalize_title(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return _NON_WORD.sub("", normalized).replace("_", "")


def _sequel_forms(normalized: str) -> tuple[str, ...]:
    forms = [normalized]
    for suffix, replacement in _SEQUEL_SUFFIXES:
        if suffix.search(normalized):
            forms.append(suffix.sub(replacement, normalized))
    return tuple(dict.fromkeys(forms))


@lru_cache(maxsize=3)
def _converter(configuration: str) -> OpenCC:
    return OpenCC(configuration)


@lru_cache(maxsize=8192)
def normalized_title_forms(value: str) -> tuple[str, ...]:
    """Return literal plus generic, Taiwan-phrase, and Hong Kong canonical forms."""

    text = unicodedata.normalize("NFKC", value).casefold()
    candidates = (
        text,
        _converter("t2s").convert(text),
        _converter("tw2sp").convert(text),
        _converter("hk2s").convert(text),
    )
    normalized = tuple(dict.fromkeys(filter(None, (normalize_title(item) for item in candidates))))
    return tuple(dict.fromkeys(form for item in normalized for form in _sequel_forms(item)))


class MatchKind(Enum):
    EXACT = "exact"
    REVIEW = "review"
    NONE = "none"


@dataclass(frozen=True, slots=True)
class TitleMatch:
    kind: MatchKind
    score: float
    subject: AnimeSubject
    favorite: BahamutCatalogItem | None = None
    subject_title: str = ""

    @property
    def auto_exclude(self) -> bool:
        return self.kind is MatchKind.EXACT and self.favorite is not None


def best_title_match(
    subject: AnimeSubject,
    favorites: Iterable[BahamutCatalogItem],
    review_threshold: float = 0.72,
) -> TitleMatch:
    best_score = 0.0
    best_favorite: BahamutCatalogItem | None = None
    best_subject_title = ""

    favorite_forms = tuple(
        (favorite, normalized_title_forms(favorite.title)) for favorite in favorites
    )
    for subject_title in subject.title_variants:
        subject_forms = normalized_title_forms(subject_title)
        subject_form_set = set(subject_forms)
        for favorite, normalized_favorites in favorite_forms:
            if subject_form_set.intersection(normalized_favorites):
                return TitleMatch(
                    kind=MatchKind.EXACT,
                    score=1.0,
                    subject=subject,
                    favorite=favorite,
                    subject_title=subject_title,
                )
            for normalized_subject in subject_forms:
                for normalized_favorite in normalized_favorites:
                    score = SequenceMatcher(
                        None, normalized_subject, normalized_favorite
                    ).ratio()
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

