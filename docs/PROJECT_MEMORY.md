# Project memory

Last updated: 2026-08-27

## D-020 — Direct catalog retrieval is default; browser helper is fallback

- GUI and CLI scans fetch `animeList.php` directly from the official HTTPS host
  by default. Users do not open Bahamut or install Tampermonkey for the normal
  path, and no account state is needed.
- The client uses only year-sort and page parameters, enforces host redirects,
  size/page bounds, complete card metadata, descending dates, and proof of the
  older-quarter boundary. Any uncertainty refuses subtraction.
- Anime Crazy can reject non-browser traffic with HTTP 403 or Cloudflare. The
  app reports this honestly; it does not automate CAPTCHA or import browser
  cookies. The optional helper is the recovery path.
- After a user-observed first-page 403, helper v0.4 reads the rendered first
  `animeList.php` document and requests later pages with the same-origin browser
  session. Only parsed public metadata is posted to the loopback service.
- Bahamut display months can be one month earlier than Bangumi first-air dates.
  The catalog keeps one boundary-month carry-in for exact matching; the
  Bangumi-side current-quarter filter remains unchanged, and fuzzy matches never
  auto-exclude.

## D-021 — Sequel normalization and fuzzy-review isolation

- Title forms canonicalize common sequel suffixes (`Ⅱ`, `第二季`, `2nd Season`,
  and numeric `2`) so regional/script variants can become exact matches when the
  underlying work is the same.
- Fuzzy matches are not included in the safe candidate note. CLI/GUI scans write
  a separate `*-复核.md` note containing evidence and links; no formal import or
  batch RSS path consumes that note automatically.

## D-022 — Curated official Bahamut title aliases

- A small, reviewable alias table covers official regional/franchise naming
  where a Bahamut card intentionally omits a season suffix or episode subtitle.
  It currently includes the three user-reported works and is tested as exact
  matching; it does not turn general fuzzy similarity into automatic exclusion.

## D-019 — Bahamut scope is the public current-quarter catalog

- The subtraction set is every title publicly listed by Anime Crazy with a
  displayed start month inside the current four-season quarter, not the user's
  favorites.
- The paired userscript reads year-sorted `animeList.php` pages without login
  until it proves the older-quarter boundary. Any missing card metadata,
  request failure, or page-limit exhaustion makes the export incomplete.
- The backend rejects the old favorites schema for this workflow, cross-quarter
  items, incorrect source paths, warnings, and incomplete exports. Fuzzy title
  matches remain visible for human review and never auto-exclude.
- The prior `mygather.php` parser/export modules remain only as historical
  diagnostics; normal GUI and CLI scans no longer consume personal favorites.

## D-018 — Taiwan and Hong Kong title equivalence

- Cross-site matching canonicalizes every Bangumi and Bahamut title through
  OpenCC standard Traditional, Taiwan-with-phrases, and Hong Kong conversions.
- Bangumi infobox aliases explicitly accept Taiwan, Hong Kong, Traditional
  Chinese, and general Chinese translated-name keys in both scripts.
- Only exact equality after deterministic conversion or an explicit alias may
  auto-exclude. A completely different regional translation missing from the
  source aliases remains a review candidate; fuzzy thresholds are unchanged.
- A read-only audit of the user's 2026 summer note and 515-title local export
  found 13 additional exact title matches from normalization alone. This did
  not rewrite the Vault or claim a fresh full scan.

## D-017 — Browser-helper installation guide

- Anime Bridge provides a browser-aware three-step guide: open the appropriate
  official Tampermonkey page, install the session-gated paired userscript, then
  open the Bahamut collection page.
- Edge, Chrome/Chromium, and Firefox are recognized from the current browser;
  unknown browsers use Tampermonkey's generic official page.
- Extension and userscript confirmation remain user-controlled. The app does
  not use registry external-install entries, enterprise force-install policy,
  page overlays, or simulated confirmation clicks.

## D-016 — Automatic Bahamut JSON handoff

- The installed userscript detects a rendered authenticated collection and
  sends its validated JSON directly to `127.0.0.1:18765`; users do not download
  or select the interchange file in the normal workflow.
- The ingest endpoint uses a persistent random browser-pairing token distinct
  from the GUI session token. The installer itself is session-gated. Neither
  token is committed, placed in portable archives, or treated as an account
  credential.
- Complete data is atomically retained as the latest local export and directly
  triggers current-quarter subtraction and candidate-note generation. Warnings
  or incomplete pagination refuse the workflow before replacement or scanning.
- Login and Cloudflare verification remain visible user actions; Anime Bridge
  does not automate CAPTCHA or receive the Bahamut Cookie/password.

## D-015 — AI candidate-note review boundary

- Fuzzy Bahamut matches are stored as machine-readable comments alongside the
  visible warning, including Bangumi ID, both titles, score, and Bahamut link.
- `obsidian_analyze_candidate_note` is read-only and returns checkbox state,
  subtraction proof, and fuzzy evidence to the AI.
- Its policy is always `human_review_required_never_auto_exclude`. AI may explain
  evidence and fetch Bangumi details, but only the user decides checkboxes and
  fuzzy-match disposition.

## D-014 — Portable Codex MCP profile

- MCP defaults to the GUI's locally saved non-secret profile; explicit
  `--vault`, `--formal-root`, `--qbit-base-url`, and `--settings` remain valid.
- The source checkout config points to `./dist/anime-bridge.exe`; the release
  ZIP contains `.codex/config.toml` pointing to `./anime-bridge.exe`.
- A moved installation therefore needs one GUI settings save plus a Codex
  restart, not manual editing of an absolute TOML path.

## D-013 — Bahamut authenticated browser bridge

- Authentication stays in the user's browser. A same-origin userscript reads
  `mygather.php` after the user completes login/CAPTCHA and follows only visible
  pagination links, with a 50-page ceiling.
- Its JSON contains title, canonical Anime Crazy link, SN, page number, export
  time, and warnings. It excludes passwords, cookies, tokens, and raw HTML.
- Imports accept only schema v1 HTTPS URLs on `ani.gamer.com.tw` and are capped
  at 5 MiB. Any pagination/parser warning marks the export incomplete and blocks
  subtraction. Exact normalized matches are removed; fuzzy matches remain visible.
- Obsidian formal import and candidate-driven RSS refuse notes whose frontmatter
  does not prove `bahamut_subtraction: true`.

## D-008 — RSS source adapters and availability evidence

- Source discovery is a replaceable URL-template layer, separate from the
  qBittorrent adapter and batch conflict planner.
- Built-in providers are Comicat via RSSHub and DMHY; custom templates must be
  credential-free HTTPS and contain `{query}`.
- Public Comicat/RSSHub endpoints currently show Cloudflare verification, so
  their generated URLs are drafts rather than proven downloader-readable feeds.
- Batch writes preflight all conflicts but cannot be atomic because the
  qBittorrent WebUI API exposes separate feed and rule writes.

## D-007 — Portable distribution policy

- The Windows artifact is one console-enabled `anime-bridge.exe`: double-click
  starts the GUI, ordinary arguments run the CLI, and `mcp` starts stdio MCP.
- Migration is preview-first and refuses existing differing plugin files. It
  never stores passwords, cookies, tokens, or AI keys.
- PyInstaller builds must run on Windows because it is not a cross-compiler.

## Project introduction

Anime Bridge is a portable local application for seasonal anime discovery,
Bahamut favorite subtraction, Obsidian review/import, RSS discovery, and
qBittorrent automation. It should expose deterministic tools to an AI/MCP layer
without allowing the AI to bypass previews or confirmations.

## Developer preferences

- The developer has programming experience but prefers clear guidance and a
  simple operating interface.
- Report objective evidence and distinguish fixture tests, live reads, and
  external writes.
- Use an agile workflow with visible status, demonstrations, and a record for
  every major update.
- Favor maintainability, readable code, portability, and safe extension points.
- Avoid repeated verification once a representative check has established that
  a change is unlikely to damage prior behavior.
- Keep only the newest three packaged snapshots, while retaining Git history.

## Decisions

### D-023 — Current-date gate for quarter scans (2026-08-27)

Quarter discovery keeps only subjects whose first air date is within the
current quarter and is not later than the scan reference date. This prevents
future, not-yet-aired titles from entering candidate notes while preserving
titles airing today. Per-episode upload times remain a future harness concern.

### D-001: Quarter boundaries

The application uses four calendar quarters: winter Jan-Mar, spring Apr-Jun,
summer Jul-Sep, and autumn Oct-Dec.

### D-002: Current discovery scope

The initial scanner only discovers subjects whose first air/release date is in
the quarter containing the run date. The domain API must accept an explicit
date so later releases can scan historical or selected quarters without
rewriting adapters.

### D-003: Included animation categories

Include Bangumi anime categories TV (`1`), Movie (`3`), and WEB (`5`). Exclude
OVA (`2`) and Other (`0`). Sequels are included when Bangumi lists them as an
independent subject satisfying the same category and date rules.

### D-003a: Japanese-origin filter

The initial scanner requires Bangumi's `日本` meta tag. Items without that tag
are excluded from the candidate list and their count is reported. This avoids
mixing other countries' animation into a Japanese seasonal list. A later review
workflow may expose unclassified entries without weakening the default filter.

### D-004: Obsidian compatibility

The existing vault stores formal notes below `C/bangumi/{year}/{MM}月新番/` and
the `动画库.base` view selects notes tagged `bangumi`. Candidate notes must not
be tagged `bangumi` until checked items are formally imported.

Formal notes must remain compatible with these frontmatter keys:

`中文名`, `日文名`, `cover`, `改编类型`, `总集数`, `观看状态`, `制作公司`,
`监督`, `音乐`, `开播年份`, `开播季度`, `记录日期`, `BGM链接`, `BGM评分`,
`下载路径`, optional `Netaba链接`, and `tags`.

### D-005: Authentication and secrets

Bahamut login happens interactively in the user's browser. Passwords and cookies
are never captured; the browser helper exports only validated favorite metadata.
Raw cookies, qBittorrent credentials, and AI keys are never committed.

### D-006: GitHub and releases

Every meaningful change is committed with contemporaneous status and change
notes. A private GitHub repository named `baha-qbit` is the default because the
project contains machine-specific integration documentation. The repository is
`https://github.com/g36ck19941-crypto/baha-qbit`; it was corrected from public to
private on 2026-08-21 and `origin/main` was verified against local HEAD. Windows
Git Credential Manager can push even though the standalone `gh` CLI is not logged in.

### D-007: Cross-site matching safety

Only exact equality after Unicode width/case/punctuation normalization is
eligible for automatic Bahamut subtraction. Bangumi Chinese, Japanese, and
infobox aliases are all considered. Similar but non-exact titles remain in the
candidate list and are reported for manual review. AI may later assist that
review but cannot lower the deterministic auto-exclusion boundary.

### D-008: Obsidian formal import safety

Candidate tasks carry a machine marker independent of the visible title. Formal
import re-fetches Bangumi details, previews vault-relative paths, and refuses the
entire apply operation if any target already exists or collides within the
batch. The importer never edits `.base`; a new Markdown note enters the existing
view through the compatible `tags: bangumi` frontmatter.

### D-009: qBittorrent control safety

The built-in WebUI client accepts loopback URLs only. Credentials, when needed,
are prompted without echo and never stored. Feed/rule operations read and show a
plan first, refuse known name/path conflicts, and require explicit `--apply`.
New rules default disabled and add matches paused; enabling or starting downloads
requires separate explicit flags. The API has no atomic feed-plus-rule operation,
so a connection failure after feed creation can leave a feed without its rule.

### D-010: Obsidian plugin boundary

The Obsidian plugin is a thin desktop command shell. It does not duplicate
matching, rendering, or conflict behavior; it starts the packaged executable or
source launcher with an argument array and `shell: false`. Preview is a separate
command. Apply requires an Obsidian confirmation, then remains subject to the
CLI's own conflict gate.

### D-011: AI and MCP boundary

The project uses the official MCP Python SDK v2 over local stdio. The deterministic
service layer does not depend on MCP or an AI provider. Default startup registers
read/plan tools only. Write tools require both `--allow-writes` at process startup
and the exact per-call confirmation value; host auto-approval must remain off.
MCP cannot bypass Vault containment, target conflict checks, loopback-only
qBittorrent access, or disabled/add-paused RSS defaults.

### D-012: Local interface and portability

The operational GUI uses a local web interface instead of Tkinter because the
available bundled Python failed a real Tcl/Tk startup smoke test. It binds only
to `127.0.0.1:18765` and requires a high-entropy per-process
token for the page and API calls. Browser write actions require a visible dialog
and remain subject to service-layer gates. Static assets have no CDN dependency
and are included as Python package data.

## Known environment facts

- Development workspace: `C:\Users\30871\Desktop\baha-qbit`.
- Obsidian vault: `C:\PersonalBlog\Obsidian Vault`.
- Existing integration folder: `bangumi1`; existing QuickAdd, Dataview, and
  Templater plugins are installed.
- qBittorrent 4.5.5 is installed; loopback WebUI API 2.8.19 was read successfully.
- System Python is absent. Development verification uses the bundled Codex
  Python runtime; the eventual package must include its own runtime.
