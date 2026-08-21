# Project memory

Last updated: 2026-08-21

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

Bahamut login happens interactively in a dedicated browser profile. Passwords
are never captured. Raw cookies, qBittorrent credentials, and AI keys are never
committed. Portable exports exclude authenticated state.

### D-006: GitHub and releases

Every meaningful change is committed with contemporaneous status and change
notes. A private GitHub repository named `baha-qbit` is the default because the
project will contain machine-specific integration documentation. Publishing is
pending local GitHub CLI authentication.

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

## Known environment facts

- Development workspace: `C:\Users\30871\Desktop\baha-qbit`.
- Obsidian vault: `C:\PersonalBlog\Obsidian Vault`.
- Existing integration folder: `bangumi1`; existing QuickAdd, Dataview, and
  Templater plugins are installed.
- qBittorrent 4.5.5 is installed and was observed running; WebUI availability
  has not yet been established.
- System Python is absent. Development verification uses the bundled Codex
  Python runtime; the eventual package must include its own runtime.
