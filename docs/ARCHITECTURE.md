# Architecture

## Dependency direction

```text
CLI / future GUI / future MCP
              |
          workflows
          /       \
      domain     renderers/storage
                   |
                adapters
```

The domain model has no dependency on HTTP, Obsidian, browser automation,
qBittorrent, or AI. Workflows depend on small protocols, so an external parser
can be replaced without changing quarter or safety rules.

## v0.1.0 data flow

1. Determine the quarter containing the supplied reference date.
2. Query Bangumi `/v0/subjects` for each of the three months and each allowed
   category: TV (`1`), Movie (`3`), and WEB (`5`).
3. Paginate, reject malformed/undated rows, enforce exact date bounds, and
   require Bangumi's `日本` meta tag, then deduplicate by Bangumi subject ID.
4. Render an Obsidian candidate document with one unchecked task, cover,
   summary, source link, and machine-readable marker per subject.
5. Write atomically so an interrupted run does not leave a partial candidate.

The v0.1.0 output carries an explicit warning because Bahamut subtraction is a
later milestone. It is deliberately tagged `anime-bridge-candidates`, not
`bangumi`, so it cannot enter the existing formal Base accidentally.

## Planned integration boundaries

- `BahamutFavoritesSource`: interactive browser session and paginated read-only
  access to `mygather.php`.
- `TitleMatcher`: deterministic aliases and confidence scores; AI may suggest
  low-confidence matches but cannot silently approve them.
- `ObsidianImporter`: parses checked markers, previews target paths, and creates
  compatible notes without overwriting user sections.
- `QbittorrentRSS`: negotiates Web API version, previews feeds/rules, and only
  mutates after explicit confirmation.
- MCP exposes the same workflows and safety gates; it does not bypass them.
