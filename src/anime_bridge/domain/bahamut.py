"""Bahamut-facing domain values without browser or HTTP dependencies."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BahamutCatalogItem:
    """One title publicly listed in Bahamut Anime Crazy's catalog."""

    title: str
    href: str
    sn: int | None = None
    page: int | None = None
    year: int | None = None
    month: int | None = None


# Source compatibility for older callers and already-rendered review metadata.
BahamutFavorite = BahamutCatalogItem

