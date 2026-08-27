# User guide — v0.16.1 development

## Portable Windows build

The verified build is `dist/anime-bridge.exe` (Windows x64, no separate Python
installation required). Double-click it to open the local interface. The same
file also provides CLI and MCP modes:

```powershell
.\anime-bridge.exe --version
.\anime-bridge.exe mcp --vault "C:/Path/To/Vault"
```

On another computer, open **本机设置**, update the Vault and loopback
qBittorrent paths, save them, preview the migration installation, and only then
confirm installation. Existing different Obsidian plugin files cause full
refusal; the assistant never silently overwrites them. Obsidian still requires
manual plugin enablement after installation.

The ZIP also contains `.codex/config.toml`. When the extracted directory is
opened as a trusted Codex project, this starts the EXE in MCP mode and reads the
same GUI-saved paths. Restart Codex after saving the new machine profile; no
absolute Vault path is embedded in the portable MCP file.

## Runtime note

Source development requires Python 3.11 or newer. End users can use the
self-contained Windows executable instead.

## Start the local interface

In the project development environment:

```powershell
.\.venv\Scripts\python.exe gui_launcher.py
```

Anime Bridge binds to `127.0.0.1:18765` and opens the session-token
URL in the default browser. The interface provides current-quarter scanning,
Obsidian plan/confirmed apply, qBittorrent status, RSS plan/confirmed apply, and
non-secret settings. Use **结束本机界面服务** before closing the page.

Three restrained visual themes and compact/standard/large type sizes are
available in the header; the browser remembers the choice locally.

## Scan the current quarter

```powershell
python launcher.py scan
```

By default the preview is written below `out/`. A reproducible date and path can
be supplied explicitly:

```powershell
python launcher.py scan --date 2026-08-21 --output out/2026-07-candidates.md
```

Use `--dry-run` to fetch and report the count without writing a file.

## Synchronize Bahamut's public current-quarter catalog

Anime Bridge no longer reads your personal favorites and does not require a
Bahamut login. In the normal workflow, select **扫描当季差集**: Anime Bridge
directly reads the public year-sorted catalog, proves the current-quarter page
boundary, and subtracts those titles. You do not need to open Bahamut or install
Tampermonkey.

Anime Crazy may return HTTP 403 or a Cloudflare verification page to a local
non-browser client. Anime Bridge reports that failure instead of accepting an
incomplete catalog. Only then use **安装备用浏览器助手**. The guide detects Edge,
Chrome/Chromium, or Firefox and opens the matching official Tampermonkey page:

1. Confirm Tampermonkey installation in the browser's own store UI.
2. Return to the guide and select **继续安装自动同步脚本**, then confirm the
   userscript in Tampermonkey.
3. Open `https://ani.gamer.com.tw/animeList.php`; no account login is required.
4. Helper v0.4 reads the already rendered first page, then uses the browser's
   same-origin session for later public catalog pages until it reaches the
   current quarter boundary, then sends only current-quarter rows to Anime Bridge.
5. Anime Bridge validates and retains the latest JSON internally, performs the
   current-quarter difference, and writes the candidate note automatically.
6. If automatic sync is skipped within its six-hour cooldown, select **同步
   Anime Bridge 当季目录** in the lower-right corner to force a retry.

If an older catalog/favorites helper is installed, reinstall the helper from
the v0.16 guide and disable or remove the old script. This update is required
for the first-page HTTP 403 fix.

Browser security requires both confirmations. Anime Bridge never changes
enterprise policy, registry extension lists, or the browser's extension UI.

No file selection or browser is required in the normal workflow. The advanced
manual JSON path and CLI remain recovery/diagnostic options:

```powershell
python launcher.py scan `
  --bahamut-catalog "C:/Users/you/Downloads/bahamut-current-quarter.json"
```

The helper transmits title, link, SN, page, and displayed `YYYY/MM` metadata.
The JSON declares its quarter, and the backend rejects entries outside that
quarter (apart from a one-month Bahamut display-date carry-in used to handle
cross-site premiere-date drift), personal-favorites JSON, warnings, or incomplete pagination. It never
exports account state, Cookie values, passwords, or raw HTML. A persistent
random pairing secret is kept in the local application profile and installed
userscript and is never committed to Git. Exact normalized title matches are
removed; fuzzy matches remain in the candidate note with a warning.

Title comparison includes literal text plus OpenCC standard-Traditional,
Taiwan-with-regional-phrases, and Hong-Kong-to-Simplified forms. Bangumi
infobox fields for Taiwan/Hong Kong, Traditional-Chinese, and general Chinese
translated names are also exact aliases. A completely different regional title
missing from Bangumi's aliases remains visible for manual review; Anime Bridge
does not lower the fuzzy threshold or guess a silent exclusion.

Keep Anime Bridge running on port `18765` while opening the catalog page.
If another process occupies that port, close the older Anime Bridge instance
before starting the new one; the installed helper deliberately uses a stable
loopback address.

If no catalog is supplied, Anime Bridge may still create a Bangumi-only preview,
but `bahamut_subtraction: false` makes both formal import and batch RSS refuse it.

## Offline Bahamut parser diagnostic

For parser diagnostics, a UTF-8 HTML file saved from `mygather.php` can still be
parsed without transmitting credentials:

```powershell
python launcher.py parse-bahamut-html mygather.html `
  --json-output out/bahamut-favorites.json
```

This older command proves the HTML parser only; use the browser-helper JSON for
the actual seasonal difference workflow.

## Preview checked Obsidian imports

### AI candidate-note analysis

The MCP tool `obsidian_analyze_candidate_note` reads an Anime Bridge candidate
file inside the configured Vault and returns checkbox counts, item metadata,
the Bahamut-subtraction gate, and machine-readable fuzzy-match evidence. It is
read-only. Every fuzzy row carries the policy
`human_review_required_never_auto_exclude`; the AI may explain or compare the
titles, but cannot silently remove the candidate or approve it as collected.

The AI can then call `bangumi_get_subject` for refreshed detail and use the
existing preview/apply tools only after the user has made checkbox decisions.

After checking candidate tasks, build a JSON plan without writing to the Vault:

```powershell
python launcher.py obsidian-import candidates.md `
  --vault "C:/PersonalBlog/Obsidian Vault" `
  --plan-output out/obsidian-import-plan.json
```

The command re-fetches checked Bangumi subjects and reports every formal target
and conflict. It remains preview-only unless `--apply` is explicitly supplied.
Even with `--apply`, any existing or duplicate target refuses the full batch.

### Obsidian plugin package

The installable desktop plugin is in `integrations/obsidian-plugin`. Copy that
directory to `<Vault>/.obsidian/plugins/anime-bridge`, restart or reload
Obsidian, and enable **Anime Bridge** under Community plugins.

In its settings, packaged mode needs only the future `anime-bridge.exe` path.
For the current source mode, set **运行程序** to a Python 3.11+ executable and
**源码启动文件** to this repository's `launcher.py`. Then open a generated
candidate note and run one of these commands from the command palette:

- `Anime Bridge: 预览已勾选动画的正式归入计划`
- `Anime Bridge: 正式归入已勾选动画`

The second command displays a confirmation dialog. The Python importer still
refuses the full batch when any target conflicts. This package has passed static
checks but has not yet been enabled or run in the real Vault.

## Preview a qBittorrent RSS feed and rule

In qBittorrent, enable Web User Interface under `Tools > Options > Web UI` and
bind it to `127.0.0.1`. Confirm the local connection without changing state:

```powershell
python launcher.py qbittorrent-check
```

Build a feed/rule preview with an RSS URL you are authorized to use:

```powershell
python launcher.py qbittorrent-rss `
  --feed-url "https://example.com/authorized-feed.xml" `
  --feed-path "AnimeBridge/Title" `
  --rule-name "Title 1080p" `
  --must-contain "1080" `
  --plan-output out/rss-plan.json
```

This only reads qBittorrent. `--apply` is required to create anything. A new
rule remains disabled and adds matches paused unless `--enable-rule` and
`--start-downloads` are also explicitly supplied. If WebUI authentication is
enabled, add `--username NAME`; the password is prompted and never saved.

The feed and rule are two WebUI API writes rather than one atomic transaction.
If the connection fails after feed creation, inspect qBittorrent before retrying.

## Batch RSS drafts from checked candidates

The GUI's **RSS 下载器 → 从已勾选动画批量生成** section creates one feed
URL and disabled/add-paused rule draft per checked candidate. Supported source
templates are:

- `comicat-rsshub`: `/comicat/search/:keyword` through RSSHub;
- `dmhy`: the DMHY keyword RSS route;
- `custom`: a credential-free HTTPS template containing `{query}`.

The public Comicat and `rsshub.app` pages currently present Cloudflare human
verification on this computer. A generated URL is therefore a draft, not proof
that qBittorrent can refresh it. For Comicat, provide an accessible or
self-hosted RSSHub template such as
`https://your-rsshub.example/comicat/search/{query}`.

CLI preview example:

```powershell
.\anime-bridge.exe qbittorrent-rss-batch `
  "C:/Path/To/Vault/bangumi1/2026-07-动画候选.md" `
  --vault "C:/Path/To/Vault" `
  --provider dmhy `
  --extra-term 1080P `
  --extra-term CHS `
  --must-not-contain 720P `
  --plan-output rss-batch-plan.json
```

Without `--apply`, qBittorrent is read only. Batch apply rechecks every target
before the first write, but the WebUI API has no multi-item transaction; a
network failure can leave a partial batch that must be inspected before retry.

## Troubleshooting

- A network or HTTP failure exits with code `2` and does not replace an existing
  candidate file.
- Bangumi requires a meaningful User-Agent. Use `--user-agent` to supply a
  project/contact identifier if the default is rejected.
- Never put tokens, account cookies, or passwords in `config.toml`.

## Developer verification

From a source checkout, run:

```powershell
python scripts/run_tests.py
```

MCP installation, host configuration, exposed tools, and write-mode safeguards
are documented separately in `docs/MCP_GUIDE.md`.
