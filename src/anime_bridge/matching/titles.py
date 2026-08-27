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
_SEQUEL_BASE_SUFFIX = re.compile(
    r"(?:第二季|第三季|第四季|第[234]期|第[234]季|2ndseason|3rdseason|4thseason|season[234]|ii|iii|iv)$"
)
_COLON_SUBTITLE = re.compile(
    r"^(.+?)(?:\s+\d+)?\s*:[a-z0-9][a-z0-9 _-]*$", re.IGNORECASE
)
_CURATED_ALIAS_GROUPS = (
    (
        "我是不才恶女",
        "恶女不才，请多关照 ～雏宫蝶鼠换身传～",
        "ふつつかな悪女ではございますが ～雛宮蝶鼠とりかえ伝～",
    ),
)


def normalize_title(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return _NON_WORD.sub("", normalized).replace("_", "")


def _sequel_forms(normalized: str) -> tuple[str, ...]:
    forms = [normalized]
    for suffix, replacement in _SEQUEL_SUFFIXES:
        if suffix.search(normalized):
            forms.append(suffix.sub(replacement, normalized))
    base = _SEQUEL_BASE_SUFFIX.sub("", normalized)
    if base != normalized and base:
        forms.append(base)
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
    forms = {form for item in normalized for form in _sequel_forms(item)}
    for item in candidates:
        match = _COLON_SUBTITLE.match(unicodedata.normalize("NFKC", item).casefold().strip())
        if match:
            forms.add(normalize_title(match.group(1)))
    for group in _CURATED_ALIAS_GROUPS:
        group_forms = {normalize_title(item) for item in group}
        if forms.intersection(group_forms):
            forms.update(group_forms)
    return tuple(dict.fromkeys(form for form in forms if form))


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

