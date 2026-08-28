"""Application workflows composed from domain rules and adapters."""

from .current_quarter import CurrentQuarterResult, CurrentQuarterScanner
from .bahamut_difference import (
    BahamutDifferenceResult,
    subtract_bahamut_catalog,
    subtract_bahamut_favorites,
)
from .obsidian_import import (
    ObsidianImportConflict,
    apply_import_plan,
    plan_checked_import,
)
from .obsidian_library import (
    ObsidianDeletePlan,
    ObsidianLibraryConflict,
    ObsidianLibraryItem,
    apply_formal_note_delete,
    list_formal_anime_notes,
    plan_formal_note_delete,
)
from .rss_plan import (
    RSSBatchPlan,
    RSSPlan,
    RSSPlanConflict,
    apply_rss_batch,
    apply_rss_plan,
    plan_rss,
    plan_rss_batch,
)
from .rss_sources import (
    CandidateRSSDraft,
    RSSSourceProvider,
    build_candidate_rss_drafts,
    build_feed_url,
    provider_catalog,
)

__all__ = [
    "BahamutDifferenceResult",
    "CurrentQuarterResult",
    "CurrentQuarterScanner",
    "ObsidianImportConflict",
    "apply_import_plan",
    "plan_checked_import",
    "ObsidianDeletePlan",
    "ObsidianLibraryConflict",
    "ObsidianLibraryItem",
    "apply_formal_note_delete",
    "list_formal_anime_notes",
    "plan_formal_note_delete",
    "RSSPlan",
    "RSSBatchPlan",
    "RSSPlanConflict",
    "apply_rss_plan",
    "apply_rss_batch",
    "plan_rss",
    "plan_rss_batch",
    "CandidateRSSDraft",
    "RSSSourceProvider",
    "build_candidate_rss_drafts",
    "build_feed_url",
    "provider_catalog",
    "subtract_bahamut_catalog",
    "subtract_bahamut_favorites",
]
