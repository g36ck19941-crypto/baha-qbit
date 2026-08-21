# User guide — v0.7.0 development

## Runtime note

This source milestone requires Python 3.11 or newer. The current computer has no
system Python installation, so development checks use the Codex bundled runtime.
A later packaging milestone will ship a self-contained executable.

## Start the local interface

In the project development environment:

```powershell
.\.venv\Scripts\python.exe gui_launcher.py
```

Anime Bridge binds to `127.0.0.1` on a random port and opens the session-token
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

## Important limitation

v0.1.0 is the Bangumi discovery slice only. Its candidate file has not yet had
the user's Bahamut favorites removed. The note says this explicitly and is not
tagged for the formal animation Base.

## Offline Bahamut parser diagnostic

Until interactive login is implemented, a UTF-8 HTML file exported from the
logged-in `mygather.php` page can be parsed without transmitting credentials:

```powershell
python launcher.py parse-bahamut-html mygather.html `
  --json-output out/bahamut-favorites.json
```

This command proves the parser interface only. It does not claim that the
application has connected to the user's account.

## Preview checked Obsidian imports

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
