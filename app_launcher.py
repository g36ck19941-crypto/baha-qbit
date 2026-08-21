"""Unified source and frozen entry point for Anime Bridge."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if SRC.is_dir() and str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main() -> int:
    arguments = sys.argv[1:]
    if not arguments or arguments[0] == "gui":
        from anime_bridge.gui import main as gui_main

        return gui_main(arguments[1:] if arguments else [])
    if arguments[0] == "mcp":
        from anime_bridge.mcp_server import main as mcp_main

        return mcp_main(arguments[1:])

    from anime_bridge.cli import main as cli_main

    return cli_main(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
