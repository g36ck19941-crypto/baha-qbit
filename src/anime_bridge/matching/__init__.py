"""Deterministic title matching and confidence decisions."""

from .titles import MatchKind, TitleMatch, best_title_match, normalize_title

__all__ = ["MatchKind", "TitleMatch", "best_title_match", "normalize_title"]

