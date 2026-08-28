"""Conflict-safe migration planning and Obsidian plugin installation."""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

from anime_bridge.resources import obsidian_plugin_source
from anime_bridge.settings import UserSettings


PLUGIN_FILES = (
    "manifest.json",
    "main.js",
    "candidate-sort.js",
    "styles.css",
    "README.md",
)


class MigrationConflict(RuntimeError):
    """Raised when migration would overwrite an existing installation."""


@dataclass(frozen=True, slots=True)
class MigrationPlan:
    vault_path: str
    plugin_target: str
    settings_target: str
    runner_path: str
    launcher_path: str
    plugin_state: str
    repairs: tuple[str, ...]
    conflicts: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def plan_migration(
    settings: UserSettings,
    settings_path: Path,
    runner_path: Path,
    plugin_source: Path | None = None,
    launcher_path: Path | None = None,
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

    runner = runner_path.expanduser().resolve()
    if not runner.is_file():
        raise ValueError(f"Anime Bridge runner does not exist: {runner}")
    launcher = launcher_path.expanduser().resolve() if launcher_path else None
    if launcher is not None and not launcher.is_file():
        raise ValueError(f"Anime Bridge launcher does not exist: {launcher}")

    target = vault / ".obsidian" / "plugins" / "anime-bridge"
    expected = {name: (source / name).read_bytes() for name in PLUGIN_FILES}
    data = _plugin_data(runner, settings.formal_root, launcher)
    expected["data.json"] = data

    repairs: list[str] = []
    conflicts: list[str] = []
    if not target.exists():
        state = "new"
    elif not target.is_dir():
        state = "conflict"
        conflicts.append(str(target))
    elif all(
        (target / name).is_file() and (target / name).read_bytes() == content
        for name, content in expected.items()
    ):
        state = "current"
    elif _is_managed_plugin_directory(target):
        repairs.extend(
            str(target / name)
            for name, content in expected.items()
            if not (target / name).is_file() or (target / name).read_bytes() != content
        )
        state = "repair"
    else:
        state = "conflict"
        conflicts.append(str(target))

    return MigrationPlan(
        vault_path=str(vault),
        plugin_target=str(target),
        settings_target=str(settings_path.resolve()),
        runner_path=str(runner),
        launcher_path=str(launcher) if launcher is not None else "",
        plugin_state=state,
        repairs=tuple(repairs),
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
    if plan.plugin_state in {"new", "repair"}:
        source = (plugin_source or obsidian_plugin_source()).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=".anime-bridge-", dir=target.parent))
        backup: Path | None = None
        try:
            if target.is_dir():
                shutil.copytree(target, staging, dirs_exist_ok=True)
            for name in PLUGIN_FILES:
                shutil.copyfile(source / name, staging / name)
            (staging / "data.json").write_bytes(
                _plugin_data(
                    Path(plan.runner_path),
                    settings.formal_root,
                    Path(plan.launcher_path) if plan.launcher_path else None,
                )
            )
            if target.exists():
                backup = Path(tempfile.mkdtemp(prefix=".anime-bridge-backup-", dir=target.parent))
                backup.rmdir()
                os.replace(target, backup)
            os.replace(staging, target)
            if backup is not None:
                shutil.rmtree(backup)
            written.extend(target / name for name in (*PLUGIN_FILES, "data.json"))
        except BaseException:
            if backup is not None and backup.exists() and not target.exists():
                os.replace(backup, target)
            raise
        finally:
            if staging.exists():
                shutil.rmtree(staging)
    settings.save(settings_path)
    written.append(settings_path)
    return tuple(written)


def current_runtime_command() -> tuple[Path, Path | None]:
    """Return the command the Obsidian plugin should use for this running build."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve(), None
    project_root = Path(__file__).resolve().parents[2]
    return Path(sys.executable).resolve(), (project_root / "launcher.py").resolve()


def _is_managed_plugin_directory(target: Path) -> bool:
    entries = {path.name for path in target.iterdir()}
    if not entries:
        return True
    manifest = target / "manifest.json"
    if manifest.is_file():
        try:
            return json.loads(manifest.read_text(encoding="utf-8")).get("id") == "anime-bridge"
        except (OSError, ValueError, json.JSONDecodeError):
            return False
    return False


def _plugin_data(
    runner_path: Path, formal_root: str, launcher_path: Path | None = None
) -> bytes:
    payload = {
        "runnerPath": str(runner_path),
        "launcherPath": str(launcher_path) if launcher_path is not None else "",
        "formalRoot": formal_root,
        "pinCheckedOnOpen": True,
    }
    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
