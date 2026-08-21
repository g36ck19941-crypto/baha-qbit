# Project status

Last updated: 2026-08-21

## Progress panel

| Area | State | Evidence / next gate |
|---|---|---|
| Scope and quarter rules | Complete | Decisions D-001 through D-003 |
| Obsidian compatibility contract | Complete | Decision D-004 and inspected existing notes/scripts |
| Project skeleton | Complete | Python 3.11+ package, CLI, docs, tests, snapshot tool |
| Bangumi current-quarter scanner | Complete for v0.1.0 | Live official API read on 2026-08-21 |
| Candidate Markdown preview | Complete for v0.1.0 | Atomic checkbox note with cover, summary, source metadata |
| Bahamut favorites | Parser complete; login pending | Fixture-proven `mygather.php` parser; no live account evidence |
| Cross-site difference | Core complete; integration pending | Exact-only auto exclusion; fuzzy titles retained for review |
| Obsidian formal import | Core, live preview, plugin package complete | Plugin runtime and real apply pending |
| qBittorrent RSS | Core and live preview complete | Source discovery and approved apply pending |
| AI/MCP | MCP core verified | Real host connection and AI review pending |
| GUI | Core and visual verification complete | Packaged executable pending |
| GitHub remote | Complete | Private `origin/main` matches local HEAD |

## Verification levels

- Static/source inspection: completed for the existing Obsidian schema and
  official Bangumi/qBittorrent documentation.
- Local execution: 32 representative tests passed; compile and CLI version checks passed.
- Live Bangumi read: established on 2026-08-21. The 2026 summer scan included
  101 Japan-tagged subjects (78 TV, 13 Movie, 10 WEB) and reported 76 excluded
  subjects without the `日本` meta tag. This is not Bahamut or Obsidian evidence.
- Bahamut parser/matcher: 11 local tests pass, including fixture HTML, aliases,
  exact subtraction, and fuzzy-review retention. This is interface evidence only;
  the user's authenticated `mygather.php` has not been read.
- GitHub: the repository was initially created public, corrected to private,
  and pushed through Windows Git Credential Manager without exposing a token.
  Private `origin/main` and local HEAD both resolve to commit `21ed56f` at this
  milestone. The standalone `gh` CLI remains unauthenticated but is not needed.
- Obsidian planner: 17 total tests pass. A live Bangumi detail read planned one
  checked title to `C/bangumi/2026/07月新番/LV999的村民.md` with zero conflicts and
  stopped in preview-only mode. No file was written to the real Vault.
- qBittorrent: a live read connected to installed version 4.5.5 and WebUI API
  2.8.19, then read the existing RSS feed/rule state and produced a conflict-free
  disabled/paused preview. No RSS state was changed.
- Obsidian plugin package: manifest/JSON and JavaScript syntax checks pass. It
  exposes preview and confirmed-apply commands backed by the existing CLI, but
  has not yet been installed, enabled, or executed inside Obsidian.
- MCP: official SDK 2.0.0 was installed in the ignored project virtual
  environment. Its in-memory client discovered exactly four tools in default
  read-only mode, six in explicitly write-enabled mode, and successfully called
  the structured Bangumi tool. No real write tool was invoked.
- GUI: Tkinter was rejected after its real smoke test found the bundled runtime
  lacked Tcl/Tk. The replacement loopback web UI passed page/API/security smoke
  tests, Edge console inspection, 1440×900 and 720px screenshots, and a no-
  horizontal-overflow check. No scan or write action was triggered visually.

## Current demonstration

- Regenerable command and evidence: `docs/DEMO.md`.
- Local preview artifact: `out/2026-07-live-candidates.md` (ignored by Git).
- The preview explicitly warns that Bahamut subtraction is not implemented.
