# MCP connection guide

Anime Bridge uses the [official MCP Python SDK v2](https://py.sdk.modelcontextprotocol.io/)
and local stdio transport. The
AI host starts the process; no HTTP port, cloud service, or AI API key is needed.

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
    "--vault",
    "C:/PersonalBlog/Obsidian Vault"
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
  "args": ["mcp", "--vault", "C:/Path/To/Obsidian Vault"]
}
```

Add `--allow-writes` only when the host should register the three write tools.
The tool contract and confirmation gates are identical to source mode.
