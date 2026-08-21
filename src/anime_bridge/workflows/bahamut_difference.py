"""Subtract only proven Bahamut favorites from Bangumi candidates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from anime_bridge.domain import AnimeSubject, BahamutFavorite
from anime_bridge.matching import MatchKind, TitleMatch, best_title_match


@dataclass(frozen=True, slots=True)
class BahamutDifferenceResult:
    candidates: tuple[AnimeSubject, ...]
    exact_matches: tuple[TitleMatch, ...]
    review_matches: tuple[TitleMatch, ...]


def subtract_bahamut_favorites(
    subjects: Iterable[AnimeSubject],
    favorites: Iterable[BahamutFavorite],
) -> BahamutDifferenceResult:
    favorite_list = tuple(favorites)
    candidates: list[AnimeSubject] = []
    exact_matches: list[TitleMatch] = []
    review_matches: list[TitleMatch] = []

    for subject in subjects:
        match = best_title_match(subject, favorite_list)
        if match.kind is MatchKind.EXACT:
            exact_matches.append(match)
            continue
        candidates.append(subject)
        if match.kind is MatchKind.REVIEW:
            review_matches.append(match)

    return BahamutDifferenceResult(
        candidates=tuple(candidates),
        exact_matches=tuple(exact_matches),
        review_matches=tuple(review_matches),
    )

