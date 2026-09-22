"""Official-SDK MCP adapter for the deterministic Anime Bridge service."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Sequence

from anime_bridge import __version__
from anime_bridge.ai import AnimeBridgeAIService
from anime_bridge.settings import UserSettings, default_settings_path


def resolve_runtime_settings(
    vault_path: Path | None,
    settings_path: Path | None,
    formal_root: str | None,
    qbit_base_url: str | None,
) -> tuple[Path, str, str]:
    """Resolve explicit MCP overrides or fall back to the GUI's local profile."""
    if vault_path is not None:
        defaults = UserSettings()
        return (
            vault_path,
            formal_root or defaults.formal_root,
            qbit_base_url or defaults.qbit_base_url,
        )
    profile_path = settings_path or default_settings_path()
    profile = UserSettings.load(profile_path)
    return (
        Path(profile.vault_path),
        formal_root or profile.formal_root,
        qbit_base_url or profile.qbit_base_url,
    )


def build_mcp_server(service: AnimeBridgeAIService) -> Any:
    try:
        from mcp.server import MCPServer
        from mcp.types import ToolAnnotations
    except ImportError as exc:
        raise RuntimeError(
            "MCP support is not installed; install the project with its 'mcp' extra"
        ) from exc

    server = MCPServer("Anime Bridge", version=__version__)
    read_external = ToolAnnotations(read_only_hint=True, open_world_hint=True)
    read_local = ToolAnnotations(read_only_hint=True, open_world_hint=False)
    safe_write = ToolAnnotations(
        read_only_hint=False,
        destructive_hint=False,
        idempotent_hint=False,
        open_world_hint=False,
    )

    @server.tool(title="读取 Bangumi 动画详情", annotations=read_external)
    def bangumi_get_subject(subject_id: int, category: str) -> dict[str, Any]:
        """Read one Bangumi subject. Category is tv, movie, web, ova, or other."""
        return service.bangumi_subject(subject_id, category)

    @server.tool(title="分析候选动画笔记", annotations=read_local)
    def obsidian_analyze_candidate_note(candidate_path: str) -> dict[str, Any]:
        """Read checkbox state and fuzzy Bahamut evidence without modifying the note."""
        return service.analyze_candidate_note(candidate_path)

    @server.tool(title="预览 Obsidian 动画入库", annotations=read_local)
    def obsidian_plan_checked_import(candidate_path: str) -> dict[str, Any]:
        """Plan all checked candidates without writing; path must be inside the Vault."""
        return service.plan_obsidian_import(candidate_path)

    @server.tool(title="读取 qBittorrent RSS 状态", annotations=read_local)
    def qbittorrent_get_rss_status() -> dict[str, Any]:
        """Read local qBittorrent version, RSS feeds, and downloader rules."""
        return service.qbit_status()

    @server.tool(title="预览 qBittorrent RSS 规则", annotations=read_local)
    def qbittorrent_plan_rss(
        feed_url: str,
        feed_path: str,
        rule_name: str,
        must_contain: str = "",
        must_not_contain: str = "",
        use_regex: bool = False,
        episode_filter: str = "",
        smart_filter: bool = False,
        category: str = "",
        save_path: str = "",
    ) -> dict[str, Any]:
        """Preview a disabled, add-paused RSS rule without changing qBittorrent."""
        return service.plan_qbit_rss(
            feed_url, feed_path, rule_name, must_contain, must_not_contain,
            use_regex, episode_filter, smart_filter, category, save_path,
        )

    @server.tool(title="批量生成动画 RSS 规则草案", annotations=read_local)
    def qbittorrent_plan_candidate_rss(
        candidate_path: str,
        provider: str,
        extra_terms: list[str] | None = None,
        custom_template: str = "",
        must_contain: str = "",
        must_not_contain: str = "",
        episode_filter: str = "",
        category: str = "anime",
        save_root: str = "",
    ) -> dict[str, Any]:
        """Build disabled/add-paused per-anime RSS drafts from checked candidates."""
        return service.plan_candidate_rss(
            candidate_path,
            provider,
            tuple(extra_terms or ()),
            custom_template,
            must_contain,
            must_not_contain,
            episode_filter,
            category,
            save_root,
        )

    if service.allow_writes:

        @server.tool(title="正式批量归入 Obsidian", annotations=safe_write)
        def obsidian_apply_checked_import(
            candidate_path: str, confirmation: str
        ) -> dict[str, Any]:
            """Write checked notes after a human-approved call and conflict recheck."""
            return service.apply_obsidian_import(candidate_path, confirmation)

        @server.tool(title="创建 qBittorrent RSS 规则", annotations=safe_write)
        def qbittorrent_apply_rss(
            feed_url: str,
            feed_path: str,
            rule_name: str,
            confirmation: str,
            must_contain: str = "",
            must_not_contain: str = "",
            use_regex: bool = False,
            episode_filter: str = "",
            smart_filter: bool = False,
            category: str = "",
            save_path: str = "",
        ) -> dict[str, Any]:
            """Create a disabled/add-paused feed rule after a human-approved call."""
            return service.apply_qbit_rss(
                feed_url, feed_path, rule_name, confirmation, must_contain,
                must_not_contain, use_regex, episode_filter, smart_filter,
                category, save_path,
            )

        @server.tool(title="批量创建动画 RSS 规则", annotations=safe_write)
        def qbittorrent_apply_candidate_rss(
            candidate_path: str,
            provider: str,
            confirmation: str,
            extra_terms: list[str] | None = None,
            custom_template: str = "",
            must_contain: str = "",
            must_not_contain: str = "",
            episode_filter: str = "",
            category: str = "anime",
            save_root: str = "",
        ) -> dict[str, Any]:
            """Create a checked-candidate RSS batch after preview and confirmation."""
            return service.apply_candidate_rss(
                candidate_path,
                provider,
                confirmation,
                tuple(extra_terms or ()),
                custom_template,
                must_contain,
                must_not_contain,
                episode_filter,
                category,
                save_root,
            )

    return server


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Anime Bridge as a local MCP server")
    parser.add_argument(
        "--vault",
        type=Path,
        default=None,
        help="explicit Vault override; otherwise read the saved local GUI profile",
    )
    parser.add_argument(
        "--settings",
        type=Path,
        default=None,
        help="optional local profile path used when --vault is omitted",
    )
    parser.add_argument("--formal-root", default=None)
    parser.add_argument("--qbit-base-url", default=None)
    parser.add_argument(
        "--allow-writes",
        action="store_true",
        help="register write tools; individual calls still require confirmation",
    )
    args = parser.parse_args(argv)
    vault_path, formal_root, qbit_base_url = resolve_runtime_settings(
        args.vault, args.settings, args.formal_root, args.qbit_base_url
    )
    service = AnimeBridgeAIService(
        vault_path,
        formal_root=formal_root,
        qbit_base_url=qbit_base_url,
        allow_writes=args.allow_writes,
    )
    build_mcp_server(service).run()
    return 0
