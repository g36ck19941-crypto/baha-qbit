# User guide — v0.1.0

## Runtime note

This source milestone requires Python 3.11 or newer. The current computer has no
system Python installation, so development checks use the Codex bundled runtime.
A later packaging milestone will ship a self-contained executable.

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

The QuickAdd/custom Obsidian plugin shell is not yet included, so this command
is currently a developer-facing interface rather than the final one-click UX.

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
