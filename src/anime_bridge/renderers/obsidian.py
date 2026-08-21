"""Obsidian-compatible candidate document renderer."""

from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING

from anime_bridge import __version__
from anime_bridge.domain import AnimeSubject

if TYPE_CHECKING:
    from anime_bridge.workflows.current_quarter import CurrentQuarterResult


def _yaml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _blockquote(text: str) -> str:
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not cleaned:
        return "> 暂无简介"
    return "\n".join(f"> {line}" if line else ">" for line in cleaned.splitlines())


def _render_subject(subject: AnimeSubject) -> str:
    metadata = json.dumps(
        {
            "bangumi_id": subject.bangumi_id,
            "category": subject.category.config_name,
            "air_date": subject.air_date.isoformat(),
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    score = "未知" if subject.score is None else f"{subject.score:g}"
    episodes = "未知" if subject.episodes is None else str(subject.episodes)
    lines = [
        f"- [ ] **{subject.display_name}**",
        f"  <!-- anime-bridge:item {metadata} -->",
        f"  - 日文名：{subject.name or '未知'}",
        f"  - 类型：{subject.category.label}",
        f"  - 开播日期：{subject.air_date.isoformat()}",
        f"  - 总集数：{episodes}",
        f"  - Bangumi 评分：{score}",
        f"  - 条目：[{subject.bangumi_url}]({subject.bangumi_url})",
    ]
    if subject.cover_url:
        lines.append(f"  - 封面：![{subject.display_name}|180]({subject.cover_url})")
    lines.extend(["", _blockquote(subject.summary), ""])
    return "\n".join(lines)


def render_candidate_markdown(
    result: "CurrentQuarterResult",
    generated_at: datetime | None = None,
) -> str:
    timestamp = generated_at or datetime.now().astimezone()
    start, end = result.quarter.bounds(result.year)
    header = [
        "---",
        "anime_bridge_document: candidates",
        f"anime_bridge_version: {_yaml_quote(__version__)}",
        f"quarter: {_yaml_quote(result.identifier)}",
        f"quarter_name: {_yaml_quote(result.quarter.cn_name)}",
        f"range_start: {start.isoformat()}",
        f"range_end_exclusive: {end.isoformat()}",
        f"generated_at: {_yaml_quote(timestamp.isoformat(timespec='seconds'))}",
        "formal_imported: false",
        "tags:",
        "  - anime-bridge-candidates",
        "---",
        "",
        f"# {result.year} {result.quarter.cn_name}动画候选",
        "",
        "> [!warning] 预览阶段",
        "> 本文件尚未执行巴哈收藏差集。请勿把它当作最终待选清单。",
        "> 后续版本只会正式导入已勾选且通过差集确认的条目。",
        "",
        f"共发现 **{len(result.subjects)}** 个符合当前类型和日期规则的 Bangumi 条目。",
        f"另有 **{len(result.excluded_without_japan_tag)}** 个条目因缺少 `日本` 元标签而未纳入。",
        "",
    ]
    if not result.subjects:
        header.append("当前没有发现符合规则的条目。\n")
        return "\n".join(header).rstrip() + "\n"
    return "\n".join(header + [_render_subject(item) for item in result.subjects]).rstrip() + "\n"
