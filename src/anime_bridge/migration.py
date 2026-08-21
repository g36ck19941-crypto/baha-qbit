"""Conflict-safe migration planning and Obsidian plugin installation."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

from anime_bridge.resources import obsidian_plugin_source
from anime_bridge.settings import UserSettings


PLUGIN_FILES = ("manifest.json", "main.js", "styles.css", "README.md")


class MigrationConflict(RuntimeError):
    """Raised when migration would overwrite an existing installation."""


@dataclass(frozen=True, slots=True)
class MigrationPlan:
    vault_path: str
    plugin_target: str
    settings_target: str
    runner_path: str
    plugin_state: str
    conflicts: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def plan_migration(
    settings: UserSettings,
    settings_path: Path,
    runner_path: Path,
    plugin_source: Path | None = None,
) -> MigrationPlan:
    vault = Path(settings.vault_path).expanduser().resolve()
    if not vault.is_dir():
        raise ValueError(f"Obsidian Vault does not exist: {vault}")
    if not (vault / ".obsidian").is_dir():
        raise ValueError(f"Not an Obsidian Vault (missing .obsidian): {vault}")

    source = (plugin_source or obsidian_plugin_source()).resolve()
    missing = [name for name in PLUGIN_FILES if not (source / name).is_file()]
    if missing:
        raise ValueError(f"Packaged Obsidian plugin is incomplete: {', '.join(missing)}")

    target = vault / ".obsidian" / "plugins" / "anime-bridge"
    expected = {name: (source / name).read_bytes() for name in PLUGIN_FILES}
    data = _plugin_data(runner_path.resolve(), settings.formal_root)
    expected["data.json"] = data

    conflicts: list[str] = []
    if not target.exists():
        state = "new"
    elif not target.is_dir():
        state = "conflict"
        conflicts.append(str(target))
    else:
        for name, content in expected.items():
            path = target / name
            if not path.is_file() or path.read_bytes() != content:
                conflicts.append(str(path))
        state = "current" if not conflicts else "conflict"

    return MigrationPlan(
        vault_path=str(vault),
        plugin_target=str(target),
        settings_target=str(settings_path.resolve()),
        runner_path=str(runner_path.resolve()),
        plugin_state=state,
        conflicts=tuple(conflicts),
    )


def apply_migration(
    plan: MigrationPlan,
    settings: UserSettings,
    settings_path: Path,
    plugin_source: Path | None = None,
) -> tuple[Path, ...]:
    if plan.conflicts:
        raise MigrationConflict(
            "Migration refused because existing files differ: " + ", ".join(plan.conflicts)
        )

    target = Path(plan.plugin_target)
    written: list[Path] = []
    if plan.plugin_state == "new":
        source = (plugin_source or obsidian_plugin_source()).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=".anime-bridge-", dir=target.parent))
        try:
            for name in PLUGIN_FILES:
                shutil.copyfile(source / name, staging / name)
            (staging / "data.json").write_bytes(
                _plugin_data(Path(plan.runner_path), settings.formal_root)
            )
            os.replace(staging, target)
            written.extend(target / name for name in (*PLUGIN_FILES, "data.json"))
        finally:
            if staging.exists():
                shutil.rmtree(staging)
    settings.save(settings_path)
    written.append(settings_path)
    return tuple(written)


def _plugin_data(runner_path: Path, formal_root: str) -> bytes:
    payload = {
        "runnerPath": str(runner_path),
        "launcherPath": "",
        "formalRoot": formal_root,
    }
    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
