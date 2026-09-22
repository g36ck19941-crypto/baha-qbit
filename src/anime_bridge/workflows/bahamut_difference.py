"""Subtract proven Bahamut current-quarter catalog titles from candidates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from anime_bridge.domain import AnimeSubject, BahamutCatalogItem
from anime_bridge.matching import MatchKind, TitleMatch, best_title_match


@dataclass(frozen=True, slots=True)
class BahamutDifferenceResult:
    candidates: tuple[AnimeSubject, ...]
    exact_matches: tuple[TitleMatch, ...]
    review_matches: tuple[TitleMatch, ...]


def subtract_bahamut_catalog(
    subjects: Iterable[AnimeSubject],
    catalog_items: Iterable[BahamutCatalogItem],
) -> BahamutDifferenceResult:
    catalog = tuple(catalog_items)
    candidates: list[AnimeSubject] = []
    exact_matches: list[TitleMatch] = []
    review_matches: list[TitleMatch] = []

    for subject in subjects:
        match = best_title_match(subject, catalog)
        if match.kind is MatchKind.EXACT:
            exact_matches.append(match)
            continue
        if match.kind is MatchKind.REVIEW:
            review_matches.append(match)
            continue
        candidates.append(subject)

    return BahamutDifferenceResult(
        candidates=tuple(candidates),
        exact_matches=tuple(exact_matches),
        review_matches=tuple(review_matches),
    )


# Compatibility for extensions using the pre-v0.15 workflow name.
subtract_bahamut_favorites = subtract_bahamut_catalog

