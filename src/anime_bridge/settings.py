"""Portable, non-secret local settings with atomic persistence."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

from anime_bridge.storage import write_text_atomic


@dataclass(slots=True)
class UserSettings:
    vault_path: str = "C:/PersonalBlog/Obsidian Vault"
    integration_folder: str = "bangumi1"
    formal_root: str = "C/bangumi"
    qbit_base_url: str = "http://127.0.0.1:8080"
    qbit_executable_path: str = ""

    @classmethod
    def load(cls, path: Path) -> "UserSettings":
        if not path.exists():
            return cls()
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Anime Bridge settings must be a JSON object")
        allowed = {key: payload[key] for key in asdict(cls()) if key in payload}
        return cls(**allowed)

    def save(self, path: Path) -> None:
        payload = json.dumps(asdict(self), ensure_ascii=False, indent=2) + "\n"
        write_text_atomic(path, payload)


def default_settings_path() -> Path:
    base = os.environ.get("LOCALAPPDATA")
    if base:
        return Path(base) / "AnimeBridge" / "config.json"
    return Path.home() / ".anime-bridge" / "config.json"
