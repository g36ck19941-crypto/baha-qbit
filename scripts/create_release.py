"""Create a portable ZIP and SHA-256 manifest."""

from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from anime_bridge import __version__  # noqa: E402


SOURCE_FILES = (
    (ROOT / "dist" / "anime-bridge.exe", "anime-bridge.exe"),
    (ROOT / "README.md", "README.md"),
    (ROOT / "docs" / "USER_GUIDE.md", "docs/USER_GUIDE.md"),
    (ROOT / "docs" / "MCP_GUIDE.md", "docs/MCP_GUIDE.md"),
)


def main() -> int:
    missing = [str(source) for source, _ in SOURCE_FILES if not source.is_file()]
    if missing:
        raise FileNotFoundError("Missing release inputs: " + ", ".join(missing))
    release_dir = ROOT / "release"
    release_dir.mkdir(exist_ok=True)
    archive = release_dir / f"AnimeBridge-{__version__}-windows-x64.zip"
    manifest: dict[str, object] = {"version": __version__, "files": {}}
    with zipfile.ZipFile(
        archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as bundle:
        for source, destination in SOURCE_FILES:
            content = source.read_bytes()
            bundle.writestr(destination, content)
            manifest["files"][destination] = {
                "sha256": hashlib.sha256(content).hexdigest(),
                "size": len(content),
            }
        bundle.writestr(
            "manifest.json",
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        )
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum = archive.with_suffix(archive.suffix + ".sha256")
    checksum.write_text(f"{digest}  {archive.name}\n", encoding="ascii")
    print(f"Release archive: {archive} ({archive.stat().st_size} bytes)")
    print(f"SHA-256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
