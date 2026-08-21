"""Build the portable Windows executable with PyInstaller."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    try:
        import PyInstaller.__main__
    except ImportError:
        print("PyInstaller is missing. Install the project build extra first.", file=sys.stderr)
        return 2

    output = ROOT / "dist"
    work = ROOT / "build" / "pyinstaller"
    executable = output / "anime-bridge.exe"
    if executable.exists():
        executable.unlink()
    if work.exists():
        shutil.rmtree(work)

    PyInstaller.__main__.run(
        [
            str(ROOT / "app_launcher.py"),
            "--name=anime-bridge",
            "--onefile",
            "--console",
            "--clean",
            f"--distpath={output}",
            f"--workpath={work}",
            f"--specpath={ROOT / 'build'}",
            f"--paths={ROOT / 'src'}",
            f"--add-data={ROOT / 'src' / 'anime_bridge' / 'web'}:anime_bridge/web",
            f"--add-data={ROOT / 'integrations' / 'obsidian-plugin'}:integrations/obsidian-plugin",
        ]
    )
    if not executable.is_file():
        print("Build finished without the expected executable.", file=sys.stderr)
        return 3
    print(f"Portable executable: {executable} ({executable.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
