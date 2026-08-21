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
