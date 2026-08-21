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

## Integration boundaries

- `bahamut_html`: implemented pure parser for `mygather.php`; interactive browser
  session acquisition and paginated live reads remain pending.
- `TitleMatcher`: implemented deterministic aliases and confidence scores.
  Exact normalized equality is the only automatic exclusion; AI may later
  suggest low-confidence matches but cannot silently approve them.
- `BahamutDifference`: implemented safe core that retains fuzzy review matches
  in the candidate list; live favorites are not wired yet.
- `ObsidianImporter`: implemented checked-marker parser, detail refresh, formal
  renderer, preview plan, and conflict-safe apply core. A dependency-free
  desktop Obsidian command shell delegates to the same CLI and adds a second
  confirmation before apply. Vault installation/runtime verification and an
  approved real-Vault apply remain pending.
- `QbittorrentRSS`: implemented loopback-only Web API client, version probe,
  existing-state reader, feed/rule preview, conflict refusal, and explicit
  apply. Rules default disabled and add matches paused. RSS-source discovery
  and higher-level per-anime rule generation remain pending.
- MCP uses the official SDK v2 over local stdio and exposes the same workflows.
  The default server registers four read-only tools. Two write tools are absent
  unless the process starts with `--allow-writes`; individual write calls still
  require confirmation and retain all underlying conflict/safe-default gates.
