# Demonstration record

## v0.15.0.dev0 public current-quarter catalog

- Contract tests accept deduplicated public catalog rows and reject the old
  personal-favorites schema, non-catalog sources, cross-quarter rows, warnings,
  and incomplete pagination.
- HTTP tests prove the session-gated installer serves the new catalog helper,
  a wrong bridge token is refused, and valid current-quarter JSON is retained
  before invoking the scan.
- Matching tests retain Taiwan/Hong Kong exact conversion and fuzzy-review
  safety. Full source regression: 65 tests passed; Python compilation and both
  browser-helper/application JavaScript syntax checks passed.
- No live Anime Crazy page was read by the executable in this run, and no
  Obsidian candidate note was rewritten; public-page live evidence is pending.
- Frozen verification: the EXE reported `0.15.0.dev0` and passed GUI smoke with
  the new helper and OpenCC data. Because the sandbox default temporary folder
  rejected PyInstaller extraction, the smoke process used a workspace-local
  temporary directory; normal double-click behavior was not asserted here.

## v0.14.0.dev0 Taiwan/Hong Kong title matching

- Fixed tests prove simplified `药师少女的独语` matches traditional
  `藥師少女的獨語`, Taiwan `網路勝利組` matches `网络胜利组`, and Hong Kong
  `機動戰士高達` matches `机动战士高达`.
- An explicit Bangumi Taiwan alias proves the distinct localization
  `機動戰士鋼彈` can match without pretending OpenCC inferred `高达/鋼彈`.
- A negative test keeps the unrelated `膽小鬼` separate from `胆大党`.
- Read-only real-data audit: 515 latest Bahamut favorites versus the existing
  90-item 2026 summer candidate note yielded 13 additional exact matches. The
  audit did not write the candidate note or rerun the live network scan.
- Full source regression: 60 tests passed.
- Packaged-app verification: `anime-bridge.exe --version` reported
  `0.14.0.dev0`, and the frozen GUI smoke test passed after checking
  `網路勝利組` canonicalizes to `网络胜利组`.

## v0.13.0.dev0 browser-helper installation guide

- The overview now opens a three-step modal: official Tampermonkey destination,
  session-gated paired userscript, and the Bahamut collection page.
- JavaScript syntax and HTTP page tests verify the dialog IDs, paired helper
  URL, all three browser-specific official destinations, and the generic
  fallback. The frozen GUI passes its HTTP smoke test. This run's browser
  automation environment blocked new loopback navigation, so modal visual
  inspection is not claimed as evidence.

## v0.12.0.dev0 automatic Bahamut handoff

- HTTP tests prove the userscript installer rejects a missing GUI session token
  and embeds a per-profile bridge token without exposing it in public status.
- Ingest tests prove a wrong bridge token returns 403 and an incomplete export
  returns 400 without replacing the saved snapshot.
- A valid one-page contract export is atomically retained and invokes the
  seasonal scan directly; no manual JSON path is involved.
- The frozen v0.12 GUI passed its HTTP smoke test from a sandbox-writable local
  profile. A 1265 px browser inspection showed the correct installer URL,
  version, no horizontal overflow, and no activity-log errors.
- Source regression: 56 tests. JavaScript syntax validation passes. This is
  local contract evidence, not proof of a real authenticated collection sync.

## v0.11.0.dev0 AI candidate-note review

- A rendered fuzzy match contains both a visible warning and an
  `anime-bridge:bahamut-review` machine marker.
- Parser and service tests prove the MCP-facing analysis returns checkbox state,
  subtraction proof, titles, score, and the fixed human-review-only policy while
  leaving the candidate file byte-for-byte unchanged.
- Official in-memory MCP discovery expects six read-only tools and nine tools
  when the explicit startup write gate is enabled. Source regression: 54 tests.

## v0.10.0.dev0 logged-in browser bridge

- The local GUI serves `bahamut-export.user.js`; JavaScript syntax validation
  passes and HTTP tests confirm the installation link and asset are present.
- Schema tests accept a valid two-page export, deduplicate repeated favorites,
  and reject non-Bahamut links, unknown schema versions, and incomplete exports.
- A filtered renderer test proves exact matches disappear, fuzzy matches remain
  annotated, and `bahamut_subtraction: true` is recorded.
- Negative tests prove unfiltered candidates are refused by Obsidian planning
  and batch RSS generation.
- A live Bangumi read plus explicitly synthetic one-favorite export generated
  `out/2026-07-filtered-contract-demo.md`: 101 eligible subjects became 100,
  `LV999的村民` was absent, and the note recorded
  `bahamut_subtraction: true`. This proves wiring, not authenticated ownership.
- Source regression: 52 tests passed. This is not live-account evidence; the
  user must still complete Cloudflare verification/login and run the exporter.
- Frozen `anime-bridge.exe` reported `0.10.0.dev0`; its GUI smoke test loaded
  the embedded userscript. A live 1280×720 DOM inspection showed the exporter
  path and helper link, no horizontal overflow, and zero console errors.
- Portable-config tests prove the release MCP command is relative to the package
  root and a moved GUI profile supplies Vault/formal-root/qBittorrent paths.

## v0.9.0.dev0 checked-candidate RSS batch

- Read the real loopback qBittorrent RSS state without changing it.
- Generated `out/rss-batch-plan.json` for one checked candidate using the
  Comicat RSSHub route with `1080P` and `CHS` search terms.
- Plan evidence: one draft, zero conflicts, `enabled=false`, `addPaused=true`.
- Browser verification showed Cloudflare challenges on Comicat, public RSSHub,
  and Bahamut; no CAPTCHA was solved and no authenticated data was read.
- Added and parsed a project-level Codex MCP configuration; live discovery is
  deferred until Codex Desktop restarts.
- Source regression: 42 tests passed.

## v0.8.0.dev0 portable build

- `dist/anime-bridge.exe --version` returned `anime-bridge 0.8.0.dev0`.
- Frozen GUI smoke returned `Web GUI smoke test passed.`
- Real Vault migration preview reported `plugin_state: new` and no conflicts;
  it remained preview-only and made no Vault changes.
- GUI screenshot: `out/gui-migration-v080.png`; console errors: none.
- The executable also loaded the MCP help surface successfully.

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

## v0.7 development — operational web interface

An initial Tkinter smoke test failed because the bundled runtime had no usable
Tcl/Tk installation. The uncommitted implementation was replaced rather than
carrying an unverified portability dependency.

The replacement interface passed its real HTTP page/status smoke test, session-
token refusal, remote-qBittorrent refusal, unconfirmed-write refusal, JavaScript
syntax, and full 32-test regression. Headless installed Edge rendered desktop
1440×900 and narrow 720px screenshots with no console error or horizontal
overflow. The visual run did not trigger Bangumi scanning or any write action.

Generated demonstration images (ignored by Git):

- `out/gui-workbench.png`
- `out/gui-narrow.png`

## GitHub publication evidence

The linear local history was fast-forwarded to `main` and pushed without force
to `https://github.com/g36ck19941-crypto/baha-qbit`. Repository metadata exposed
that it had initially been created public, so it was changed to private. After
that change, authenticated `git ls-remote origin refs/heads/main` and local
`git rev-parse HEAD` both returned `21ed56fc2804f61830abcd056e886bf8cd4cf943`.
