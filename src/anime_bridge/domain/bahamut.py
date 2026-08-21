"""Bahamut-facing domain values without browser or HTTP dependencies."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BahamutFavorite:
    title: str
    href: str
    sn: int | None = None
    page: int | None = None

