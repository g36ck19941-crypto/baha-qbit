# Architecture

## Dependency direction

```text
CLI / GUI / MCP / frozen launcher
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

Bangumi-only output carries an explicit warning and `bahamut_subtraction: false`.
Formal import and batch RSS reject that state. A validated public-catalog export
changes the gate to true after exact-only subtraction; candidate notes remain
tagged `anime-bridge-candidates`, not `bangumi`.

## Integration boundaries

- `bahamut_catalog`: a userscript reads the public `animeList.php` pages in
  year order until it crosses the current quarter boundary. It posts only rows
  whose displayed `YYYY/MM` falls inside that quarter. The backend independently
  validates the declared quarter, item dates, host, paths, completeness, and
  page limit before atomically retaining the JSON and running the difference.
- `browser_helper_guide`: a static, browser-aware dialog routes Edge,
  Chrome/Chromium, and Firefox to Tampermonkey's official browser-specific page,
  then exposes the session-gated paired userscript URL. It cannot and does not
  bypass either browser confirmation or write browser management policy.
- `bahamut_html`: retained as a pure offline diagnostic parser.
- `TitleMatcher`: implemented deterministic aliases and confidence scores.
  Each title expands into literal, OpenCC `t2s`, `tw2sp`, and `hk2s` forms;
  flexible Bangumi infobox aliases include explicit Taiwan/Hong Kong translated
  name fields. Exact equality across these proven forms is the only automatic
  exclusion; AI may later
  suggest low-confidence matches but cannot silently approve them.
- `BahamutDifference`: wired into CLI and GUI scans. Exact matches are removed;
  fuzzy review matches remain visibly annotated in the candidate list.
- `ObsidianImporter`: implemented checked-marker parser, detail refresh, formal
  renderer, preview plan, and conflict-safe apply core. A dependency-free
  desktop Obsidian command shell delegates to the same CLI and adds a second
  confirmation before apply. Vault installation/runtime verification and an
  approved real-Vault apply remain pending.
- `QbittorrentRSS`: implemented loopback-only Web API client, version probe,
  existing-state reader, feed/rule preview, conflict refusal, and explicit
  apply. Rules default disabled and add matches paused. RSS-source discovery
  and checked-candidate batch rule generation. RSS source URL construction is
  isolated in `rss_sources`, with built-in Comicat/RSSHub and DMHY templates
  plus a credential-free custom HTTPS template. Endpoint availability remains
  an external precondition and is reported separately from URL construction.
- MCP uses the official SDK v2 over local stdio and exposes the same workflows.
  The default server registers six read-only tools. Three write tools are absent
  unless the process starts with `--allow-writes`; individual write calls still
  require confirmation and retain all underlying conflict/safe-default gates.
  With no explicit CLI overrides, MCP reads the same local non-secret profile
  as the GUI. The release ZIP carries a project-scoped config whose EXE path is
  relative to the extracted package root.
- Candidate notes carry machine-readable fuzzy-review markers. The read-only AI
  analyzer exposes checkbox state and evidence with a fixed human-review policy;
  it cannot edit the note or turn similarity into automatic exclusion.
- The desktop UX is a dependency-free local web server bound to
  `127.0.0.1:18765`. A high-entropy per-process token gates the page and normal
  API calls. The userscript installer is session-gated and embeds a separate
  persistent random pairing token; only that token authorizes catalog ingest.
  CSP/no-store headers reduce browser attack surface. The browser UI delegates
  to the same service layer and adds a visible dialog before write requests.
- `app_launcher.py` is the single frozen entry point: no arguments select the
  GUI, `mcp` selects stdio MCP, and all other arguments delegate to the CLI.
  PyInstaller embeds web assets and the Obsidian plugin payload. Migration
  stages a new plugin directory and refuses any differing existing file.
