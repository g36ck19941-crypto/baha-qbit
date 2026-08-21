"""Preview-first formal Obsidian import workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from anime_bridge.domain import (
    AnimeCategory,
    AnimeSubject,
    CandidateDocument,
    FormalNotePlan,
)
from anime_bridge.renderers import formal_note_path, render_formal_note
from anime_bridge.storage import write_text_new_atomic


class SubjectDetailsSource(Protocol):
    def get_subject(self, subject_id: int, category: AnimeCategory) -> AnimeSubject: ...


class ObsidianImportConflict(RuntimeError):
    pass


def plan_checked_import(
    document: CandidateDocument,
    source: SubjectDetailsSource,
    vault_path: Path,
    formal_root: str = "C/bangumi",
) -> tuple[FormalNotePlan, ...]:
    if not document.bahamut_subtracted:
        raise ObsidianImportConflict(
            "Import refused because this candidate note has not completed "
            "Bahamut favorite subtraction"
        )
    plans: list[FormalNotePlan] = []
    seen_targets: set[str] = set()
    for selection in document.checked:
        subject = source.get_subject(selection.bangumi_id, selection.category)
        target_relative = formal_note_path(subject, formal_root)
        normalized_target = target_relative.as_posix().casefold()
        duplicate_in_batch = normalized_target in seen_targets
        seen_targets.add(normalized_target)
        target_absolute = vault_path.joinpath(*target_relative.parts)
        plans.append(
            FormalNotePlan(
                subject=subject,
                target_relative=target_relative,
                content=render_formal_note(subject),
                conflict=duplicate_in_batch or target_absolute.exists(),
            )
        )
    return tuple(plans)


def apply_import_plan(plans: tuple[FormalNotePlan, ...], vault_path: Path) -> tuple[Path, ...]:
    conflicts = [plan.target_relative.as_posix() for plan in plans if plan.conflict]
    if conflicts:
        raise ObsidianImportConflict(
            "Import refused because targets already exist or collide: " + ", ".join(conflicts)
        )

    absolute_targets = [vault_path.joinpath(*plan.target_relative.parts) for plan in plans]
    newly_conflicting = [path for path in absolute_targets if path.exists()]
    if newly_conflicting:
        raise ObsidianImportConflict(
            "Import refused because targets appeared after preview: "
            + ", ".join(str(path) for path in newly_conflicting)
        )

    written: list[Path] = []
    try:
        for plan, target in zip(plans, absolute_targets, strict=True):
            write_text_new_atomic(target, plan.content)
            written.append(target)
    except BaseException:
        for target in reversed(written):
            target.unlink(missing_ok=True)
        raise
    return tuple(written)
