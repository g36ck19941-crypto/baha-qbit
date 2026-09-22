"""Obsidian-compatible candidate document renderer."""

from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING

from anime_bridge import __version__
from anime_bridge.domain import AnimeSubject

if TYPE_CHECKING:
    from anime_bridge.workflows.bahamut_difference import BahamutDifferenceResult
    from anime_bridge.workflows.current_quarter import CurrentQuarterResult


def _yaml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _blockquote(text: str) -> str:
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not cleaned:
        return "> 暂无简介"
    return "\n".join(f"> {line}" if line else ">" for line in cleaned.splitlines())


def _render_subject(subject: AnimeSubject, review_match: object | None = None) -> str:
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
    if review_match is not None:
        favorite = review_match.favorite
        favorite_title = " ".join(favorite.title.split()) if favorite is not None else "未知"
        review_metadata = json.dumps(
            {
                "bangumi_id": subject.bangumi_id,
                "favorite_href": favorite.href if favorite is not None else "",
                "favorite_title": favorite_title,
                "score": round(review_match.score, 6),
                "subject_title": review_match.subject_title or subject.display_name,
            },
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        lines.append(f"  <!-- anime-bridge:bahamut-review {review_metadata} -->")
        lines.append(
            f"  - ⚠ 巴哈标题待人工确认：{favorite_title}（相似度 {review_match.score:.0%}，未自动排除）"
        )
    if subject.cover_url:
        lines.append(f"  - 封面：![{subject.display_name}|180]({subject.cover_url})")
    lines.extend(["", _blockquote(subject.summary), ""])
    return "\n".join(lines)


def render_candidate_markdown(
    result: "CurrentQuarterResult",
    generated_at: datetime | None = None,
    *,
    bahamut_difference: "BahamutDifferenceResult | None" = None,
    bahamut_catalog_count: int = 0,
    bahamut_exported_at: str = "",
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
        f"bahamut_subtraction: {'true' if bahamut_difference is not None else 'false'}",
        f"bahamut_scope: {'current-quarter-catalog' if bahamut_difference is not None else 'not-run'}",
        "formal_imported: false",
        "tags:",
        "  - anime-bridge-candidates",
        "---",
        "",
        f"# {result.year} {result.quarter.cn_name}动画候选",
        "",
    ]
    if bahamut_difference is None:
        header.extend([
            "> [!warning] 预览阶段",
            "> 本文件尚未执行动画疯当季目录差集。请勿把它当作最终待选清单。",
            "> 正式入库与批量 RSS 会拒绝此文件。请先用浏览器助手同步动画疯公开当季目录。",
            "",
        ])
        review_by_subject: dict[int, object] = {}
    else:
        header.extend([
            "> [!success] 动画疯当季目录差集已执行",
            f"> 动画疯当季上架：{bahamut_catalog_count}；自动移除精确匹配：{len(bahamut_difference.exact_matches)}；待人工确认：{len(bahamut_difference.review_matches)}。",
            f"> 目录同步时间：{bahamut_exported_at or '未提供'}。相似度复核条目已移至独立复核笔记，不会自动入库。",
            "",
        ])
        review_by_subject = {}
    header.extend([
        f"差集后候选 **{len(result.subjects)}** 个。",
        f"另有 **{len(result.excluded_without_japan_tag)}** 个条目因缺少 `日本` 元标签而未纳入。",
        "",
        "<!-- anime-bridge:items-start -->",
    ])
    if not result.subjects:
        header.extend(["当前没有发现符合规则的条目。", "<!-- anime-bridge:items-end -->"])
        return "\n".join(header).rstrip() + "\n"
    return "\n".join(
        header
        + [_render_subject(item, review_by_subject.get(item.bangumi_id)) for item in result.subjects]
        + ["<!-- anime-bridge:items-end -->"]
    ).rstrip() + "\n"


def render_bahamut_review_markdown(
    result: "CurrentQuarterResult",
    bahamut_difference: "BahamutDifferenceResult",
    generated_at: datetime | None = None,
    *,
    bahamut_catalog_count: int = 0,
    bahamut_exported_at: str = "",
) -> str:
    """Render fuzzy title matches in a separate, non-importable note."""

    timestamp = generated_at or datetime.now().astimezone()
    header = [
        "---",
        "anime_bridge_document: bahamut-review",
        f"anime_bridge_version: {_yaml_quote(__version__)}",
        f"quarter: {_yaml_quote(result.identifier)}",
        f"generated_at: {_yaml_quote(timestamp.isoformat(timespec='seconds'))}",
        "formal_imported: false",
        "tags:",
        "  - anime-bridge-bahamut-review",
        "---",
        "",
        f"# {result.year} {result.quarter.cn_name}动画疯相似度复核",
        "",
        "> [!warning] 需要人工确认",
        f"> 目录条目：{bahamut_catalog_count}；相似度复核：{len(bahamut_difference.review_matches)}；目录同步时间：{bahamut_exported_at or '未提供'}。",
        "> 这些条目不会出现在安全候选笔记，也不会自动排除或入库。确认同一作品后，请手动决定后续操作。",
        "",
    ]
    for match in bahamut_difference.review_matches:
        subject = match.subject
        favorite = match.favorite
        favorite_title = " ".join(favorite.title.split()) if favorite is not None else "未知"
        item_metadata = json.dumps(
            {"air_date": subject.air_date.isoformat(), "bangumi_id": subject.bangumi_id, "category": subject.category.config_name},
            ensure_ascii=False, separators=(",", ":"), sort_keys=True,
        )
        review_metadata = json.dumps(
            {
                "bangumi_id": subject.bangumi_id,
                "favorite_href": favorite.href if favorite is not None else "",
                "favorite_title": favorite_title,
                "score": round(match.score, 6),
                "subject_title": match.subject_title or subject.display_name,
            },
            ensure_ascii=False, separators=(",", ":"), sort_keys=True,
        )
        header.extend([
            f"## ☐ {subject.display_name}",
            f"<!-- anime-bridge:item {item_metadata} -->",
            f"- 日文名：{subject.name or '未知'}",
            f"- 条目：[{subject.bangumi_url}]({subject.bangumi_url})",
            f"- 巴哈姆特标题：{favorite_title}",
            f"- 巴哈姆特链接：[{favorite.href if favorite is not None else '未知'}]({favorite.href if favorite is not None else '#'})",
            f"- 相似度：{match.score:.0%}",
            f"<!-- anime-bridge:bahamut-review {review_metadata} -->",
        ])
        if subject.cover_url:
            header.append(f"- 封面：![{subject.display_name}|180]({subject.cover_url})")
        header.extend(["", _blockquote(subject.summary), ""])
    return "\n".join(header).rstrip() + "\n"
