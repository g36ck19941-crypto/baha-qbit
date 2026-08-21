# MCP connection guide

Anime Bridge uses the [official MCP Python SDK v2](https://py.sdk.modelcontextprotocol.io/)
and local stdio transport. The
AI host starts the process; no HTTP port, cloud service, or AI API key is needed.

## Codex Desktop / CLI / IDE

This repository includes a project-scoped `.codex/config.toml`. For a trusted
checkout, Codex starts `./dist/anime-bridge.exe` as a local stdio server. The
configuration is shared by Codex Desktop, CLI, and the IDE extension. Restart
the client after building or downloading the executable, then use `/mcp` (or
the MCP servers settings page) to confirm that `anime_bridge` is connected.

The MCP launcher reads the same non-secret local profile saved by the GUI, so
the checked-in config does not contain a machine-specific Vault path. Open the
GUI and save **本机设置** before restarting Codex. `--vault`, `--formal-root`,
`--qbit-base-url`, and `--settings` remain available as explicit overrides.

The checked-in configuration exposes the write-capable tools but sets Codex's
approval mode to `writes`. Anime Bridge independently requires the exact
`CONFIRM_LOCAL_WRITE` confirmation value for every apply call. To make the
connection read-only, remove `--allow-writes` from `.codex/config.toml`.

The portable ZIP includes its own `.codex/config.toml` pointing to the EXE at
the package root. Extract the complete ZIP, open that directory as a trusted
Codex project, save local paths in Anime Bridge, and restart Codex. No TOML path
editing is needed for the normal portable flow.

## Source-mode installation

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[mcp]"
```

Configure an MCP host with this command and argument array:

```json
{
  "command": "C:/Users/30871/Desktop/baha-qbit/.venv/Scripts/python.exe",
  "args": [
    "C:/Users/30871/Desktop/baha-qbit/mcp_launcher.py",
    "--settings",
    "C:/Path/To/AnimeBridge/config.json"
  ]
}
```

The default server exposes five read-only tools:

- `bangumi_get_subject`
- `obsidian_plan_checked_import`
- `qbittorrent_get_rss_status`
- `qbittorrent_plan_rss`
- `qbittorrent_plan_candidate_rss`

## Optional write tools

Add `--allow-writes` to the argument array only when the AI host should expose:

- `obsidian_apply_checked_import`
- `qbittorrent_apply_rss`
- `qbittorrent_apply_candidate_rss`

Each write call must also include `confirmation: "CONFIRM_LOCAL_WRITE"`. This is
an application guard, not a replacement for the host's visible tool-confirmation
dialog. Do not configure unattended auto-approval for these three tools.

Obsidian paths are restricted to the configured Vault. qBittorrent remains
restricted to a loopback WebUI. The RSS apply tool always creates a disabled
rule whose matches are added paused; it cannot delete feeds, rules, or torrents.

## Packaged mode

The portable executable bundles the runtime and MCP SDK. Configure the host as:

```json
{
  "command": "C:/Path/To/anime-bridge.exe",
  "args": ["mcp"]
}
```

Without explicit path arguments, packaged mode reads the GUI's saved local
profile. Add `--vault` only for a deliberate one-host override.

Add `--allow-writes` only when the host should register the three write tools.
The tool contract and confirmation gates are identical to source mode.
