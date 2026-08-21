"""Create a Git archive snapshot and keep only the newest three ZIP files."""

from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKUPS = ROOT / "backups"


def git(*args: str) -> str:
    completed = subprocess.run(
        ["git", "-c", f"safe.directory={ROOT.as_posix()}", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def main() -> int:
    BACKUPS.mkdir(parents=True, exist_ok=True)
    short_sha = git("rev-parse", "--short", "HEAD")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = BACKUPS / f"baha-qbit-{timestamp}-{short_sha}.zip"
    git("archive", "--format=zip", f"--output={output}", "HEAD")

    snapshots = sorted(
        BACKUPS.glob("baha-qbit-*.zip"), key=lambda item: item.stat().st_mtime, reverse=True
    )
    for stale in snapshots[3:]:
        stale.unlink()
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

