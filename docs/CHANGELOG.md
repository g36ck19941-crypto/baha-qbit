# Changelog

All notable changes are recorded here. The project follows semantic versioning.

## [Unreleased]

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
- Four default read-only tools for Bangumi details, Obsidian batch planning,
  qBittorrent status, and RSS-rule planning.
- Two write tools registered only with an explicit process startup gate, plus a
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

### Planned

- Interactive Bahamut login, favorite export, and confidence-aware difference.

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
