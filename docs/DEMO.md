# Demonstration record

## v0.1.0 — Bangumi current-quarter discovery

Date: 2026-08-21 (Asia/Shanghai)

### Command

The project had no system Python installation. The live run used the bundled
Codex Python 3.11+ runtime with this logical command:

```powershell
python launcher.py scan `
  --date 2026-08-21 `
  --output out/2026-07-live-candidates.md `
  --user-agent "AnimeBridge/0.1.0 (github.com/g36ck19941-crypto/baha-qbit)"
```

### Observed result

| Measure | Observed |
|---|---:|
| Quarter | 2026 summer, 2026-07-01 through 2026-09-30 |
| Included subjects | 101 |
| TV | 78 |
| Movie | 13 |
| WEB | 10 |
| Excluded without Bangumi `日本` meta tag | 76 |
| Candidate task markers | 101 |

The generated file was 157,613 bytes and contained one unchecked Obsidian task
per included subject, plus a cover, summary, release date, score, Bangumi link,
and a machine-readable item marker.

### Verification scope

- **Established:** real read from the official Bangumi API, current-quarter
  filtering, Japanese-origin filtering, candidate rendering, and local write.
- **Not established:** Bahamut login/favorite subtraction, formal Obsidian
  import, qBittorrent RSS, AI/MCP, GUI, packaging, or migration.
- The live output is ignored by Git because seasonal results are generated data.
  Re-run the command to regenerate it.

## v0.2 development — Bahamut parser and safe difference core

### Fixture command

```powershell
python launcher.py parse-bahamut-html `
  tests/fixtures/bahamut_mygather_page.html `
  --json-output out/bahamut-fixture.json
```

Observed: two fixture favorites were parsed with titles, canonical absolute
links, and SN values. Eleven total local tests passed. Exact normalized aliases
were subtracted; a similar but non-exact title remained a candidate and was
reported for review.

This section is fixture evidence, not authenticated Bahamut evidence.

## v0.3 development — Obsidian formal-import preview

One checked item using live Bangumi subject `579787` was planned against the
real Vault path without applying changes.

```json
{
  "bangumi_id": 579787,
  "title": "LV999的村民",
  "target": "C/bangumi/2026/07月新番/LV999的村民.md",
  "conflict": false
}
```

Observed output explicitly stated `Preview only: no Obsidian files written`.
This establishes the read/plan path, not a real Vault write or plugin UX.

## v0.4 development — qBittorrent RSS live preview

```powershell
python launcher.py qbittorrent-check
python launcher.py qbittorrent-rss `
  --feed-url "https://example.invalid/anime.xml" `
  --feed-path "AnimeBridge/Preview" `
  --rule-name "AnimeBridge Preview" `
  --must-contain "1080" `
  --plan-output out/qbittorrent-rss-preview.json
```

The first command connected to qBittorrent 4.5.5 / WebUI API 2.8.19. The second
read the real existing RSS state, reported no conflicts for the proposed names,
and wrote a preview whose rule was disabled with `addPaused: true`. It explicitly
stopped in preview-only mode. No feed, rule, torrent, or download state changed.

## v0.5 development — Obsidian plugin package

The package under `integrations/obsidian-plugin` passed Node.js `--check`, and
its manifest parsed as JSON with plugin ID `anime-bridge`. Source inspection
establishes that it uses `spawn(..., { shell: false })`, validates the active
candidate marker, and requires a confirmation modal for apply. This is static
package evidence only; no real Obsidian installation or command run is claimed.

## v0.6 development — official MCP client verification

The project-local virtual environment installed `mcp==2.0.0`. The official
in-memory `Client(server)` test established:

| Server mode | Tool count | Write tools visible |
|---|---:|---|
| default | 4 | no |
| `--allow-writes` | 6 | yes |

The client called `bangumi_get_subject` and received structured content with the
expected title. Twenty-seven total tests passed. This verifies MCP discovery and
in-process tool execution; connection to the user's chosen AI host remains open.
