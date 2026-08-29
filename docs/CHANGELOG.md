# Changelog

All notable changes are recorded here. The project follows semantic versioning.

## [Unreleased]

### qBittorrent launch and RSS discovery access

- Added a visible **自动发现 RSS** shortcut at the top of the RSS page, which
  scrolls directly to the checked-candidate automatic-discovery form.
- Added a user-triggered **启动 qBittorrent** button. It uses the configured
  executable path or common Windows installation paths and never starts a
  shell. Starting the app does not bypass or configure its WebUI.

### Verified automatic RSS discovery

- Batch RSS generation now probes each generated public source URL with bounded,
  credential-free reads and only includes verified RSS/Atom responses in a
  qBittorrent preview. Source failures such as HTTP 403 remain visible.
- The automatic discovery path never bypasses Comicat's human verification;
  unavailable providers are skipped rather than guessed or silently applied.

### Simplified RSS subscription setup

- Moved the qBittorrent RSS-panel grouping path into a collapsed advanced
  section. Normal setup now generates `AnimeBridge/<动画名>` automatically;
  users only supply the RSS URL(s) and animation name.

### Multi-source RSS rules

- RSS manual entry accepts several feed URLs (one per line) and creates one
  disabled, add-paused qBittorrent rule covering all of them.
- Candidate batch generation can select Comicat, DMHY, and one or more custom
  HTTPS templates together. It now creates source-specific subscription paths
  but one rule named after the anime; only an actual duplicate title receives a
  visible Bangumi ID suffix.
- Clarified in the UI and guide that an RSS URL is the remote XML endpoint,
  whereas a subscription path is only qBittorrent's internal folder hierarchy;
  neither is the download directory.

### Obsidian plugin load compatibility

- Inlined the checked-first candidate sorter into the plugin entry file so
  Obsidian does not need to resolve a relative CommonJS module while loading.
  The standalone sorter remains as a testable development artifact.

### Obsidian self-repair and library management

- Added one-button detection of the current packaged/source runtime and a
  preview-confirm repair path for missing, stale, or old Anime Bridge plugin
  files and plugin runner settings. Unknown plugin directories remain blocked.
- Added formal-library listing and recoverable delete management. Delete plans
  are Vault/formal-root constrained, require confirmation, recheck SHA-256, and
  move notes to `.trash/anime-bridge` instead of permanently erasing them.
- Added stable checked-first candidate ordering when a candidate note is next
  opened in Obsidian. New notes delimit the generated item region so user text
  outside it is preserved.

### Additional Bahamut regional and franchise aliases

- Added curated official-title equivalences for `我是不才惡女`,
  `超超超超超喜歡你的 100 個女朋友`, and `靠死亡遊戲混飯吃。` so season
  suffixes and episode subtitles do not prevent exact subtraction when the
  Bahamut franchise card uses a shorter title.

### Sequel matching and separate fuzzy-review note

- Canonicalized common sequel suffixes such as `Ⅱ`, `第二季`, `2nd Season`,
  and `2` so `幼女戦記Ⅱ` matches Bahamut's `幼女战记 2` exactly.
- Moved fuzzy title matches out of the safe candidate Markdown into a separate
  `*-复核.md` note with cover, summary, links, score, and human-review markers.
  Fuzzy rows are no longer eligible for Obsidian import or batch RSS by accident.

### Direct Bahamut catalog retrieval and 403-safe fallback

- Made the GUI and CLI fetch the public current-quarter Anime Crazy catalog
  directly by default, so the normal scan does not require opening Bahamut or
  installing Tampermonkey.
- Added bounded official-host HTTP retrieval, page parsing, descending-date and
  quarter-boundary proof, and refusal of incomplete or changed page structures.
- Reduced catalog requests to the year-sort and page parameters and added
  ordinary browser-language and referrer headers; no Cookie or account state is
  read or stored.
- Fixed the optional Tampermonkey fallback after a user-observed HTTP 403: it
  parses the already rendered first catalog page and uses the same-origin
  browser session for later pages without exporting Cookie values.
- Added a one-month boundary carry-in because Bahamut's catalog display month
  can precede Bangumi's first-air month; this keeps entries such as `2026/06`
  for a Bangumi `2026-07-02` title available for exact matching.
- Kept 403, Cloudflare, network, and decoding failures visible. Anime Bridge
  does not bypass CAPTCHA or silently treat a partial catalog as complete.

### Public Bahamut current-quarter catalog

- Replaced personal-favorites subtraction with every Anime Crazy catalog title
  whose displayed `YYYY/MM` falls inside the current four-season quarter.
- Added an account-free Tampermonkey helper that scans year-sorted public
  catalog pages until it proves the older-quarter boundary and hands validated
  JSON directly to the loopback service.
- Added strict catalog schema, host/path, quarter, item-date, completeness, and
  page-limit validation. Personal-favorites JSON is not accepted by the new
  normal workflow.
- Preserved exact-only automatic removal, Taiwan/Hong Kong title forms, and
  visible human review for fuzzy matches.

### Taiwan and Hong Kong title matching

- Added OpenCC-backed `t2s`, `tw2sp`, and `hk2s` canonical title forms for both
  Bangumi subjects and Bahamut favorites.
- Added explicit Bangumi infobox alias keys for Taiwan, Hong Kong, Traditional
  Chinese, and general Chinese translated names.
- Kept automatic subtraction exact-only and retained unrelated/fuzzy titles for
  human review.
- Added OpenCC data collection to the Windows build and regression cases for
  Taiwan phrases, Hong Kong forms, explicit regional aliases, and false matches.
- Expanded the complete source suite to 60 tests.

### Guided browser-helper installation

- Added an in-app three-step installation guide for Tampermonkey, the paired
  Anime Bridge userscript, and the Bahamut collection page.
- Added Edge, Chrome/Chromium, and Firefox detection with official Tampermonkey
  browser-specific destinations and a generic fallback.
- Kept browser-store and userscript confirmation visible and user-controlled;
  the guide never changes browser or enterprise policies.

### Automatic Bahamut handoff

- Replaced the normal manual JSON download/path step with authenticated-page
  detection, direct loopback transfer, validation, atomic retention, and an
  immediate current-quarter difference scan.
- Added a persistent browser-pairing secret separate from the GUI session token;
  the userscript installer is session-gated and the ingest endpoint is
  loopback-only.
- Retained manual JSON input as an advanced fallback and refused incomplete
  automatic exports before they can replace the last valid snapshot.
- Moved the normal GUI port to stable `127.0.0.1:18765` so an installed helper
  remains portable across restarts.
- Expanded the source suite to 56 tests.

### AI candidate-note analysis

- Added machine-readable fuzzy-review evidence to filtered candidate notes.
- Added the read-only MCP `obsidian_analyze_candidate_note` tool for checkbox,
  subtraction-gate, and fuzzy-match inspection.
- Fixed the policy to human review; similarity can never become automatic
  exclusion or a silent note edit.
- Expanded the source suite to 54 tests.

### Logged-in Bahamut browser bridge

- Added an installable same-origin userscript that exports paginated favorites
  from the user's authenticated browser without exporting passwords, cookies,
  tokens, or raw page HTML.
- Added strict, size-limited schema validation for the favorite JSON export.
- Incomplete exports and any pagination/parser warning now block subtraction.
- Wired exact-only Bahamut subtraction into CLI and GUI seasonal scans; fuzzy
  title matches remain visible for manual review.
- Added a hard gate: formal Obsidian import and candidate-driven RSS refuse a
  note unless `bahamut_subtraction: true` is present.
- Expanded the source suite to 52 tests. A real authenticated export remains a
  separate user-assisted verification gate.

### Batch anime RSS sources

- Added Comicat-via-RSSHub, DMHY, and custom HTTPS source templates.
- Added checked-candidate batch planning to CLI, GUI, and MCP.
- Added all-conflict preflight before batch writes; rules stay disabled and
  matches stay paused.
- Documented that the public RSSHub instance currently presents Cloudflare
  verification and may need an accessible or self-hosted replacement.
- Expanded the verified suite from 35 to 41 tests.

### Codex host connection

- Added a project-scoped Codex MCP configuration for the packaged stdio server.
- Kept host-side approval prompts for write tools in addition to Anime Bridge's
  per-call confirmation token.
- Added a configuration contract test and Codex Desktop/CLI/IDE setup guidance.
- Removed the machine-specific Vault path from project MCP configuration. MCP
  now reads the GUI-saved profile by default, and the portable ZIP embeds a
  package-relative `.codex/config.toml`.

### Portable Windows package

- Added one-file Windows GUI/CLI/MCP launcher and reproducible build script.
- Added conflict-safe Obsidian migration planning and installation.
- Added GUI migration controls with explicit confirmation.
- Added portable ZIP creation with embedded and sidecar SHA-256 manifests.
- Expanded the verified suite to 35 tests.

### Repository operations

- Published the full linear commit history to `origin/main` without force.
- Corrected the newly created GitHub repository from public to private, then
  verified that remote main and local HEAD matched at `21ed56f`.

### Local operational interface

- Loopback-only browser interface with random-port startup, per-process session
  token, restrictive response headers, and no external frontend dependencies.
- Current-quarter scan, Obsidian plan/confirmed apply, qBittorrent status, RSS
  plan/confirmed apply, settings, progress panel, and activity ledger.
- Three restrained themes and three persisted type-density choices, with
  responsive desktop/narrow layouts.
- Replaced the initial Tkinter approach after real smoke evidence showed Tcl/Tk
  was absent from the available runtime.
- 32 tests, HTTP smoke test, Edge desktop/narrow rendering, console check, and
  horizontal-overflow check pass. No real scan/write was performed in visual QA.

### AI/MCP core

- Official MCP Python SDK v2 optional dependency and local stdio launcher.
- Five default read-only tools for Bangumi details, Obsidian batch planning,
  qBittorrent status, and single/batch RSS-rule planning.
- Three write tools registered only with an explicit process startup gate, plus a
  required per-call confirmation and the existing Vault/loopback/conflict gates.
- AI-facing service layer remains independent of the MCP SDK and model provider.
- Official in-memory MCP client verified tool discovery and a structured call;
  27 total tests pass. A real AI-host connection remains pending.

### Obsidian command shell

- Installable, dependency-free desktop plugin package with commands to preview
  or formally import checked candidates through the shared Python CLI.
- Candidate-document validation, non-shell process spawning, settings for
  packaged/source runners, and a second confirmation dialog before apply.
- JavaScript syntax and manifest JSON checks pass. Real Obsidian runtime and
  real-Vault write verification remain pending.

### Added

- Pure standard-library parser for user-exported Bahamut `mygather.php` HTML,
  including theme-list scoping, title extraction, SN parsing, deduplication, and
  empty-collection detection.
- Bangumi infobox alias extraction and normalized title variants.
- Conservative cross-site matcher and difference workflow: normalized exact
  matches may be excluded; fuzzy matches remain candidates for manual review.
- Offline `parse-bahamut-html` diagnostic command and representative fixtures.

### Verification

- 11 local tests pass. Authenticated Bahamut access remains unverified and is
  not represented as complete.

### qBittorrent RSS core

- Loopback-only standard-library WebUI client with optional interactive login,
  installed-version/API negotiation, and existing RSS state reads.
- Validated feed/rule drafts, live conflict preview, explicit apply gate, and a
  second state check immediately before writes.
- Safe defaults keep new rules disabled and matched downloads paused; separate
  flags are required to relax either behavior.
- Live read connected to qBittorrent 4.5.5 / WebUI API 2.8.19 and produced a
  preview without changing RSS or download state.
- 21 local tests pass after this addition. Real RSS apply remains unverified.

### Obsidian import core

- Candidate Markdown parser that rejects checked tasks without valid machine
  metadata instead of silently skipping them.
- Formal-note renderer compatible with the existing animation frontmatter,
  `C/bangumi/{year}/{MM}月新番/` layout, cover callout, information table, summary,
  and personal-summary section.
- Windows-safe note filenames, full-batch conflict preflight, exclusive atomic
  publication that cannot overwrite a racing target, rollback of files newly
  created by a failed batch, and explicit `--apply` gating.
- Live preview for Bangumi subject `579787` planned one conflict-free target in
  the real Vault layout. The preview did not write to the Vault.
- 17 local tests pass after this addition.

## [0.1.0] - 2026-08-21

### Added

- Project charter, durable memory, status panel, agile task board, and repository
  operating rules.
- Frozen definitions for quarter boundaries, included categories, Obsidian
  compatibility, secret handling, and GitHub publishing.
- Dependency-free Python domain model for four quarters and the approved TV,
  Movie, WEB, sequel, and Japanese-origin policy.
- Paginated read-only Bangumi `/v0/subjects` adapter with contextual failures.
- Current-quarter scanner with exact date filtering and subject-ID deduplication.
- Atomic Obsidian candidate renderer with checkboxes, covers, summaries, source
  links, and machine-readable item markers.
- Representative domain, pagination, filtering, and rendering tests.
- Source-checkout launcher, example configuration, architecture/user guides,
  live demonstration record, and newest-three Git archive snapshot utility.

### Safety

- Candidate notes are tagged `anime-bridge-candidates`, not `bangumi`.
- v0.1.0 output warns that Bahamut subtraction has not yet occurred.
- Items without Bangumi's `日本` meta tag are counted and excluded rather than
  being silently mixed into the Japanese seasonal list.

## [0.0.0] - 2026-08-21

- Project initialized after feasibility and risk review.
