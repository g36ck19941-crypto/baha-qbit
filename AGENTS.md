# Project operating rules

## Purpose

Build a maintainable and portable local application that discovers the current
Japanese anime quarter, subtracts titles already favorited in Bahamut Anime
Crazy, stages candidates in Obsidian, and later manages approved RSS feeds and
qBittorrent rules through explicit previews.

## Non-negotiable rules

- Never store account passwords, browser cookies, qBittorrent credentials, or
  AI API keys in the repository.
- Mutating Obsidian or qBittorrent operations must provide a preview and require
  explicit confirmation.
- Low-confidence cross-site title matches must remain visible for manual review;
  they must not be silently removed.
- Preserve user-written Obsidian content such as watched progress, watch URLs,
  and personal summaries.
- Keep the domain and workflow layers independent from GUI, Obsidian, browser,
  and qBittorrent implementations.
- Each meaningful change updates `docs/CHANGELOG.md`, `docs/STATUS.md`, and when
  relevant `docs/TASKS.md` or `docs/PROJECT_MEMORY.md` in the same commit.
- Run one proportionate representative verification before committing. Do not
  claim live integration from fixture-only tests.
- Release ZIP snapshots are local artifacts. Keep only the newest three;
  Git history is never pruned to satisfy the snapshot limit.

## Current product decisions

- Four quarters: Jan-Mar, Apr-Jun, Jul-Sep, Oct-Dec.
- Current scope scans only the quarter containing the run date.
- Include TV, WEB, movies, and sequels. Exclude OVA and other categories.
- Sequel detection is not a separate exclusion rule: an independently listed
  subject is included when its category and first air date match the quarter.
- The existing Obsidian `.base` file is a view, not a row store. Formal import
  creates compatible Markdown notes tagged `bangumi`.

