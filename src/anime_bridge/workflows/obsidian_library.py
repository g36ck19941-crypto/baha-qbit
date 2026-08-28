"""Preview-first management of formal Obsidian anime notes."""

from __future__ import annotations

import hashlib
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath


_SCALAR_BANGUMI_TAG = re.compile(
    r"^tags:\s*(?:[\"']?bangumi[\"']?|\[[^\]]*\bbangumi\b[^\]]*\])\s*$",
    re.IGNORECASE | re.MULTILINE,
)
_LIST_BANGUMI_TAG = re.compile(
    r"^tags:\s*$[\s\S]*?^\s*-\s*bangumi\s*$",
    re.IGNORECASE | re.MULTILINE,
)
_TITLE = re.compile(r'^中文名:\s*["\']?(.*?)["\']?\s*$', re.MULTILINE)


class ObsidianLibraryConflict(RuntimeError):
    """Raised when a formal-note management operation is no longer safe."""


@dataclass(frozen=True, slots=True)
class ObsidianLibraryItem:
    title: str
    relative_path: str
    sha256: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ObsidianDeletePlan:
    title: str
    relative_path: str
    sha256: str
    trash_relative_path: str
    conflict: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def list_formal_anime_notes(
    vault_path: Path, formal_root: str
) -> tuple[ObsidianLibraryItem, ...]:
    vault, root = _formal_root(vault_path, formal_root)
    if not root.is_dir():
        return ()
    items: list[ObsidianLibraryItem] = []
    for path in root.rglob("*.md"):
        if not path.is_file():
            continue
        content = path.read_text(encoding="utf-8")
        if not _is_managed_anime_note(content):
            continue
        relative = path.relative_to(vault).as_posix()
        items.append(
            ObsidianLibraryItem(
                title=_title(content, path.stem),
                relative_path=relative,
                sha256=_digest(path),
            )
        )
    return tuple(sorted(items, key=lambda item: (item.title.casefold(), item.relative_path)))


def plan_formal_note_delete(
    vault_path: Path, formal_root: str, relative_path: str
) -> ObsidianDeletePlan:
    vault, root = _formal_root(vault_path, formal_root)
    target = _vault_relative_markdown(vault, relative_path)
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError("The selected note is outside the configured formal anime root") from exc
    if not target.is_file():
        raise ValueError(f"Formal anime note does not exist: {target}")
    content = target.read_text(encoding="utf-8")
    if not _is_managed_anime_note(content):
        raise ValueError("Refused because the selected note is not tagged bangumi")
    relative = target.relative_to(vault)
    trash = vault / ".trash" / "anime-bridge" / relative
    return ObsidianDeletePlan(
        title=_title(content, target.stem),
        relative_path=relative.as_posix(),
        sha256=_digest(target),
        trash_relative_path=trash.relative_to(vault).as_posix(),
        conflict=trash.exists(),
    )


def apply_formal_note_delete(
    plan: ObsidianDeletePlan, vault_path: Path, expected_sha256: str
) -> Path:
    if plan.conflict:
        raise ObsidianLibraryConflict(
            f"Delete refused because the trash target already exists: {plan.trash_relative_path}"
        )
    if expected_sha256 != plan.sha256:
        raise ObsidianLibraryConflict("Delete refused because the preview token is stale")
    vault = vault_path.resolve()
    target = vault.joinpath(*PurePosixPath(plan.relative_path).parts)
    if not target.is_file() or _digest(target) != expected_sha256:
        raise ObsidianLibraryConflict("Delete refused because the note changed after preview")
    trash = vault.joinpath(*PurePosixPath(plan.trash_relative_path).parts)
    if trash.exists():
        raise ObsidianLibraryConflict("Delete refused because the trash target appeared after preview")
    trash.parent.mkdir(parents=True, exist_ok=True)
    os.replace(target, trash)
    return trash


def _formal_root(vault_path: Path, formal_root: str) -> tuple[Path, Path]:
    vault = vault_path.resolve()
    root = vault.joinpath(*PurePosixPath(formal_root).parts).resolve()
    try:
        root.relative_to(vault)
    except ValueError as exc:
        raise ValueError("Formal anime root must stay inside the configured Vault") from exc
    return vault, root


def _vault_relative_markdown(vault: Path, relative_path: str) -> Path:
    relative = PurePosixPath(relative_path.replace("\\", "/"))
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Formal note path must be Vault-relative")
    target = vault.joinpath(*relative.parts).resolve()
    try:
        target.relative_to(vault)
    except ValueError as exc:
        raise ValueError("Formal note path must stay inside the configured Vault") from exc
    if target.suffix.lower() != ".md":
        raise ValueError("Formal note must be a Markdown file")
    return target


def _frontmatter(content: str) -> str:
    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    if not normalized.startswith("---\n"):
        return ""
    parts = normalized.split("---\n", 2)
    return parts[1] if len(parts) == 3 else ""


def _is_managed_anime_note(content: str) -> bool:
    frontmatter = _frontmatter(content)
    return bool(
        frontmatter
        and (
            _SCALAR_BANGUMI_TAG.search(frontmatter)
            or _LIST_BANGUMI_TAG.search(frontmatter)
        )
    )


def _title(content: str, fallback: str) -> str:
    match = _TITLE.search(_frontmatter(content))
    return (match.group(1).strip() if match else fallback) or fallback


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
