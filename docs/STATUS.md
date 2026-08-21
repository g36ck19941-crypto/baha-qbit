# Project status

Last updated: 2026-08-21

## v0.9.0.dev0 batch RSS milestone

- Added replaceable per-anime URL builders for Comicat through RSSHub, DMHY,
  and credential-free custom HTTPS templates.
- Added checked-candidate batch preview/apply surfaces in CLI, GUI, and MCP.
- A real qBittorrent state read produced one conflict-free plan and performed
  no write. Full regression: 41 tests passed.
- Live browser checks found Cloudflare human verification on both Comicat and
  public rsshub.app; those routes are not claimed as directly usable by the
  downloader until the user supplies an accessible/self-hosted endpoint.
- Bahamut `mygather.php` is likewise waiting for the user to complete the
  visible Cloudflare challenge and login personally.
- Added a project-scoped Codex MCP configuration with write-tool prompts. The
  TOML contract is locally verified; Codex must be restarted before live tool
  discovery can be claimed.

## v0.8.0.dev0 packaging milestone

- Built a 20.9 MB self-contained Windows x64 executable with GUI, CLI, MCP,
  web assets, and the Obsidian plugin payload.
- Added preview-first migration in both CLI and GUI. Existing different plugin
  files refuse the entire installation; no real Vault installation was run.
- Verified the frozen executable's version, GUI HTTP smoke test, MCP argument
  loading, and a real-path migration preview against the user's Vault.
- Full source regression: 35 tests passed; JavaScript and Python compilation
  checks passed. The final GUI screenshot reported zero console errors.

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
| qBittorrent RSS | Batch source/rule preview complete | Accessible source endpoint and approved apply pending |
| AI/MCP | Codex project config added | Restart-time discovery and AI review pending |
| GUI | Packaged and visually verified | Frozen HTTP smoke and screenshot passed |
| GitHub remote | Draft PR open | `feature/v0.9-rss-batch` is pushed; merge awaits approval |

## Verification levels

- Static/source inspection: completed for the existing Obsidian schema and
  official Bangumi/qBittorrent documentation.
- Local execution: 42 representative tests passed; compile and CLI version checks passed.
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
  environment. Its in-memory client discovered exactly five tools in default
  read-only mode, eight in explicitly write-enabled mode, and successfully
  called the structured Bangumi tool. No real write tool was invoked.
- Codex MCP host configuration: `.codex/config.toml` parses as TOML and uses
  `default_tools_approval_mode = "writes"`. It has not yet been loaded by a
  restarted Codex Desktop process, so host discovery is not established.
- GUI: Tkinter was rejected after its real smoke test found the bundled runtime
  lacked Tcl/Tk. The replacement loopback web UI passed page/API/security smoke
  tests, Edge console inspection, 1440×900 and 720px screenshots, and a no-
  horizontal-overflow check. No scan or write action was triggered visually.

## Current demonstration

- Regenerable command and evidence: `docs/DEMO.md`.
- Local preview artifact: `out/2026-07-live-candidates.md` (ignored by Git).
- The preview explicitly warns that Bahamut subtraction is not implemented.
