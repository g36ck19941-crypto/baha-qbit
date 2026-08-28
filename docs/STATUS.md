# Project status

Last updated: 2026-08-28

## v0.16.5.dev0 Obsidian management milestone

- The GUI can detect its own runtime and preview/confirm repair the managed
  Obsidian plugin payload and stale runner/launcher paths.
- The Obsidian workspace now supports candidate-based addition plus recoverable
  formal-note deletion with path confinement and preview hash revalidation.
- The plugin stably pins checked generated candidate blocks on the next note
  open. Text outside new item-region markers is not reordered.
- Source verification: 83 tests pass before packaging; real-Vault repair,
  deletion, and plugin runtime behavior remain unverified until user approval.

## v0.16.3.dev0 reported-title alias correction

- Added tests for the three reported works. Their official Bahamut naming is
  respectively a short regional title, a franchise card without the season
  suffix, and a base title without the `44:CLOUDY BEACH` subtitle.
- These now become exact matches when their Bahamut cards are present in the
  supplied catalog; high-confidence fuzzy rows still go to `*-复核.md`.

## v0.16.2.dev0 sequel matching and review separation

- Common sequel suffixes now canonicalize across Chinese, Japanese Roman
  numerals, and English forms. The live Bahamut `幼女战记 2` card matches
  Bangumi `幼女戦記Ⅱ` exactly.
- Fuzzy matches are removed from the safe candidate note and written to a
  separate `*-复核.md` review note. They remain human-review-only and are not
  importable as checked candidates.
- Full source regression after the change: 72 tests passed.

## v0.16.1.dev0 cross-site premiere-date correction

- Bahamut rows on the first older-quarter boundary month are retained for
  exact matching because its catalog display month can precede Bangumi's first
  air date. This fixes `THE WORLD IS DANCING 世界在起舞` (`2026/06` on Bahamut,
  `2026-07-02` on Bangumi) without broadening fuzzy exclusion.
- Full source regression after the correction: 71 tests passed.

## v0.16.0.dev0 direct public-catalog retrieval milestone

- Normal GUI and CLI scans now request the public year-sorted Anime Crazy
  catalog directly; opening Bahamut or installing the helper is no longer part
  of the normal path.
- Retrieval is restricted to the official HTTPS host, bounded to 20 pages and
  5 MiB per page, and must prove a complete older-quarter boundary before any
  subtraction is accepted.
- The optional browser fallback now avoids the reported first-page HTTP 403 by
  parsing the rendered catalog page and reusing the same-origin browser session
  for later pages. It never sends Cookie values to Anime Bridge.
- Full source regression: 70 tests passed. Python compilation and both browser
  helper/application JavaScript syntax checks passed.
- A read-only live backend run on 2026-08-27 retrieved 45 titles for the
  2026-07 quarter and proved the boundary on page 2 without opening a browser.
  This does not guarantee every network: HTTP 403/Cloudflare remains an explicit
  browser-fallback case, with no bypass or false completeness claim.
- The 21.6 MB frozen EXE reports `0.16.0.dev0` and passes its packaged GUI,
  catalog-helper, and OpenCC smoke test using a workspace-local extraction
  directory. Normal double-click extraction was not reasserted in the sandbox.

## v0.15.0.dev0 public current-quarter catalog milestone

- Normal subtraction no longer reads the user's Anime Crazy favorites or
  requires login. The browser helper scans the public year-sorted catalog and
  exports only titles whose displayed month is inside the current quarter.
- The backend independently rejects old favorites JSON, cross-quarter rows,
  incomplete scans, warnings, non-catalog source paths, and unsafe links.
- Exact regional-title matches are removed; fuzzy matches remain annotated for
  human review. Existing Obsidian and qBittorrent preview/write gates remain.
- Full source regression: 65 tests passed. Python compilation and both browser
  helper/application JavaScript syntax checks passed.
- The 21.4 MB frozen EXE reports `0.15.0.dev0` and passes its GUI smoke test,
  including packaged catalog-helper and OpenCC checks. The sandbox default
  temporary directory rejected one-file extraction, so this verification used
  a workspace-local temporary directory; that limitation is recorded rather
  than presented as an ordinary double-click run.

## v0.14.0.dev0 regional-title matching milestone

- Bahamut/Bangumi comparison now canonicalizes standard Traditional, Taiwan
  regional phrases, and Hong Kong forms before exact matching.
- Explicit Taiwan/Hong Kong translated-name fields in Bangumi infobox data join
  the existing alias set. The fuzzy threshold and human-review boundary did not
  change.
- A read-only audit against the user's latest 515-title export found 13
  additional exact matches inside the existing 90-item summer candidate note.
  No Vault note was changed by the audit.
- Full source regression: 60 tests passed.
- The rebuilt Windows executable reports `0.14.0.dev0`; its frozen GUI smoke
  test passed after executing a Taiwan-title conversion, proving the OpenCC
  dictionaries are present in the packaged application.

## v0.13.0.dev0 browser-helper guide milestone

- The local interface now presents a three-step browser-aware installation
  guide instead of a bare userscript link.
- Edge, Chrome/Chromium, and Firefox route to official Tampermonkey pages before
  the paired script and Bahamut collection steps. Unknown browsers use the
  official generic page.
- Both security confirmations remain manual; no browser policy is modified.

## v0.12.0.dev0 automatic Bahamut handoff milestone

- The browser helper now detects a rendered logged-in collection, scans its
  pagination, and posts metadata directly to the loopback service. No manual
  JSON download or path selection remains in the normal workflow.
- The receiver uses a persistent pairing token, validates completeness, stores
  the latest JSON atomically, and immediately generates the filtered current-
  quarter candidate note. Account passwords, cookies, and HTML remain outside
  the transfer.
- Full source regression: 56 tests passed; helper JavaScript syntax passes.
- The frozen EXE reports v0.12 and passes its HTTP smoke test; a 1265 px live
  UI inspection found no horizontal overflow or activity-log errors.
- Real authenticated sync still requires the user to finish Cloudflare/login
  and is not claimed from fixture evidence.

## v0.11.0.dev0 AI review milestone

- Filtered candidate notes now retain machine-readable fuzzy Bahamut evidence.
- A new read-only MCP tool returns checkbox state, subtraction proof, candidate
  metadata, and fuzzy evidence to the AI without editing the note.
- Every fuzzy result is explicitly human-review-only and cannot trigger automatic
  exclusion. Full source regression: 54 tests passed.

## v0.10.0.dev0 Bahamut browser-bridge milestone

- Added a same-origin userscript served by the local GUI. It runs after the
  user signs in, follows visible `mygather.php` pagination, and downloads only
  favorite metadata—never passwords, cookies, tokens, or raw HTML.
- Added strict schema/host/path/size/completeness validation and wired the export
  into CLI and GUI seasonal scans. Partial export warnings block the workflow.
- Exact normalized favorites are removed; fuzzy matches remain annotated for
  review. Unfiltered candidate notes are now refused by formal import and batch
  RSS instead of relying on a warning alone.
- Source regression: 52 tests passed. JavaScript and Python syntax checks pass.
- The 20.9 MB frozen executable reported v0.10, served the embedded exporter,
  and passed GUI smoke plus a 1280×720 zero-console-error inspection.
- Live authenticated account evidence is still pending the user's Cloudflare
  verification and login; fixture/export-contract evidence is not substituted
  for that gate.
- Portable MCP now reads the GUI-saved machine profile and the ZIP embeds a
  package-relative Codex config. Source regression: 52 tests passed.

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
| Bahamut public catalog | Account-free automatic handoff implemented | Contract tests complete; live public-page sync pending |
| Cross-site difference | CLI/GUI integration complete; live evidence pending | Exact-only exclusion; fuzzy titles retained and annotated |
| Obsidian formal import | Core, live preview, plugin package complete | Plugin runtime and real apply pending |
| qBittorrent RSS | Batch source/rule preview complete | Accessible source endpoint and approved apply pending |
| AI/MCP | Codex project config added | Restart-time discovery and AI review pending |
| GUI | Packaged and visually verified | Frozen HTTP smoke and screenshot passed |
| GitHub remote | Draft PR open | `feature/v0.9-rss-batch` is pushed; merge awaits approval |

## Verification levels

- Static/source inspection: completed for the existing Obsidian schema and
  official Bangumi/qBittorrent documentation.
- Local execution: 56 representative tests passed; compile and CLI/JavaScript syntax checks passed.
- Live Bangumi read: established on 2026-08-21. The 2026 summer scan included
  101 Japan-tagged subjects (78 TV, 13 Movie, 10 WEB) and reported 76 excluded
  subjects without the `日本` meta tag. This is not Bahamut or Obsidian evidence.
- Bahamut bridge/parser/matcher: local tests cover export validation, fixture
  HTML, aliases, exact subtraction, fuzzy-review retention, and downstream
  gating. This is interface evidence only; the user's authenticated
  `mygather.php` has not been read.
- GitHub: the repository was initially created public, corrected to private,
  and pushed through Windows Git Credential Manager without exposing a token.
  The current integration branch is tracked by draft PR #1; `main` remains at
  the last approved baseline. The standalone `gh` CLI remains unauthenticated.
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
  environment. Its in-memory client discovered exactly six tools in default
  read-only mode, nine in explicitly write-enabled mode, and successfully
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
- Legacy Bangumi-only preview: `out/2026-07-live-candidates.md` (ignored by Git).
- The next live artifact must come from the authenticated browser export and
  prove `bahamut_subtraction: true`; it has not been generated yet.
