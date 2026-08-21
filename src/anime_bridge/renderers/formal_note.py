"""Render formal notes compatible with the existing Obsidian animation Base."""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import PurePosixPath
from typing import Any, Iterable, Mapping

from anime_bridge.domain import AnimeSubject, Quarter


_INVALID_FILENAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
}


def safe_note_filename(value: str, max_length: int = 120) -> str:
    cleaned = _INVALID_FILENAME.sub("-", value).strip().rstrip(". ")
    cleaned = re.sub(r"\s+", " ", cleaned)
    if not cleaned:
        cleaned = "未命名动画"
    if cleaned.upper() in _RESERVED_NAMES:
        cleaned = f"{cleaned}-动画"
    return cleaned[:max_length].rstrip(". ")


def formal_note_path(subject: AnimeSubject, formal_root: str = "C/bangumi") -> PurePosixPath:
    quarter = Quarter.containing(subject.air_date)
    return (
        PurePosixPath(formal_root)
        / str(subject.air_date.year)
        / quarter.folder_name()
        / f"{safe_note_filename(subject.display_name)}.md"
    )


def _yaml(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _flatten(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        if value.strip():
            yield value.strip()
    elif isinstance(value, Mapping):
        if "v" in value:
            yield from _flatten(value["v"])
        else:
            for nested in value.values():
                yield from _flatten(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _flatten(nested)


def _infobox_values(subject: AnimeSubject, keys: set[str]) -> tuple[str, ...]:
    infobox = subject.raw.get("infobox") if isinstance(subject.raw, Mapping) else None
    if not isinstance(infobox, list):
        return ()
    values: list[str] = []
    for row in infobox:
        if isinstance(row, Mapping) and str(row.get("key") or "") in keys:
            values.extend(_flatten(row.get("value")))
    return tuple(dict.fromkeys(values))


def _adaptation(subject: AnimeSubject) -> str:
    mapping = (
        ("漫画改", "漫画改编"),
        ("小说改", "小说改编"),
        ("游戏改", "游戏改编"),
        ("原创", "原创动画"),
    )
    for tag, label in mapping:
        if tag in subject.meta_tags:
            return label
    return "其他"


def render_formal_note(subject: AnimeSubject, recorded_on: date | None = None) -> str:
    record_date = recorded_on or date.today()
    quarter = Quarter.containing(subject.air_date)
    companies = "、".join(
        _infobox_values(subject, {"动画制作", "動畫製作", "制作", "製作"})
    ) or "未知"
    directors = "、".join(
        _infobox_values(subject, {"导演", "導演", "监督", "監督"})
    ) or "未知"
    music = "、".join(_infobox_values(subject, {"音乐", "音樂"})) or "未知"
    episodes = "未知" if subject.episodes is None else str(subject.episodes)
    score = "未知" if subject.score is None else f"{subject.score:g}"
    fields = [
        ("中文名", subject.display_name),
        ("日文名", subject.name or "未知"),
        ("cover", subject.cover_url or "未知"),
        ("改编类型", _adaptation(subject)),
        ("总集数", episodes),
        ("观看状态", "想看"),
        ("制作公司", companies),
        ("监督", directors),
        ("音乐", music),
        ("开播年份", str(subject.air_date.year)),
        ("开播季度", quarter.folder_name()),
        ("记录日期", record_date.strftime("%Y%m%d")),
        ("BGM链接", subject.bangumi_url),
        ("BGM评分", score),
        ("下载路径", "无"),
        ("tags", "bangumi"),
    ]
    lines = ["---", *(f"{key}: {_yaml(value)}" for key, value in fields), "---", ""]
    lines.extend(
        [
            "**已观看集数**： 0",
            "**观看网址**： ",
            "",
            "# 动画信息",
            f"> [!bookinfo|noicon]+ **{subject.display_name}**",
        ]
    )
    if subject.cover_url:
        lines.append(f"> ![bookcover|400]({subject.cover_url})")
    lines.extend(
        [
            ">",
            "| 项目 | 内容 |",
            "|:------|:------------------------------------------|",
            f"| 中文名 | {subject.display_name} |",
            f"| 日文名 | {subject.name or '未知'} |",
            f"| 开播日期 | {subject.air_date.isoformat()} |",
            f"| 改编类型 | {_adaptation(subject)} |",
            f"| 动画集数 | {subject.category.label} 共 {episodes} 话 |",
            f"| 制作公司 | {companies} |",
            f"| 制作监督 | {directors} |",
            f"| 音乐 | {music} |",
            "| 观看状态 | 想看 |",
            f"| 记录日期 | {record_date.strftime('%Y%m%d')} |",
            f"| BGM 地址 | [{subject.display_name}]({subject.bangumi_url}) |",
            f"| BGM 评分 | {score} |",
            "",
            "## 简介",
            "",
            subject.summary or "暂无简介。",
            "",
            "# 个人总结",
            "",
            "<!-- 在这里写下您对这部动画的感想和评价 -->",
            "",
        ]
    )
    return "\n".join(lines)
