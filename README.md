# Anime Bridge (`baha-qbit`)

Anime Bridge is a local-first bridge between Bangumi, Bahamut Anime Crazy,
Obsidian, and qBittorrent. The project is being delivered incrementally so each
external integration remains replaceable and testable.

Private upstream: `https://github.com/g36ck19941-crypto/baha-qbit`

Current development version: `0.16.4.dev0`. The Windows x64 build is
generated as `dist/anime-bridge.exe`; double-clicking it opens the local UI.

## Confirmed scope

- Detect titles whose first release date falls in the current anime quarter.
- Include TV, WEB, movie, and sequel subjects; exclude OVA and other subjects.
- Preserve an extension point for historical or manually selected quarters.
- Stage candidates as checkbox-based Obsidian Markdown before formal import.
- Subtract every title publicly listed by Bahamut in the current quarter and manage approved RSS
  subscriptions and qBittorrent rules through preview-first operations.

## Current milestone

`v0.16.4.dev0` includes the Bangumi scanner, conservative Bahamut matching core,
conflict-safe Obsidian import core, and preview-first local qBittorrent RSS
control, an installable Obsidian command shell, a tested local MCP server, and a
loopback-only browser interface, self-contained Windows executable, and a
preview-first migration assistant, batch per-anime RSS source/rule drafts, and
account-free direct retrieval of the validated public current-quarter catalog,
with a session-aware Tampermonkey helper retained only for HTTP 403 fallback,
plus a read-only MCP candidate-note analyzer for AI-assisted
review, and a browser-aware guided installer for Tampermonkey plus the paired
Anime Bridge userscript, and Taiwan/Hong Kong title canonicalization backed by
Bangumi regional aliases. See
[the user guide](docs/USER_GUIDE.md), [live demo record](docs/DEMO.md),
[project status](docs/STATUS.md),
[tasks](docs/TASKS.md), and [change log](docs/CHANGELOG.md).

Source-checkout example:

```powershell
python launcher.py scan --date 2026-08-21
```

Launch the local interface from the development environment:

```powershell
.\.venv\Scripts\python.exe gui_launcher.py
```

Unfiltered candidate output is deliberately refused by formal Obsidian import
and batch RSS. A complete public-catalog export must complete the Bahamut subtraction gate.

No credentials or authenticated account state belong in this repository.
