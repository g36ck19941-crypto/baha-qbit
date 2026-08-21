from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path

from anime_bridge.adapters.candidate_markdown import parse_candidate_markdown
from anime_bridge.domain import AnimeCategory, AnimeSubject
from anime_bridge.renderers import formal_note_path, render_formal_note, safe_note_filename
from anime_bridge.workflows import (
    ObsidianImportConflict,
    apply_import_plan,
    plan_checked_import,
)


def detailed_subject(subject_id: int = 10) -> AnimeSubject:
    return AnimeSubject(
        bangumi_id=subject_id,
        name="テスト／アニメ",
        name_cn="测试：动画 第二季",
        summary="正式简介。",
        air_date=date(2026, 7, 5),
        category=AnimeCategory.TV,
        cover_url="https://example.invalid/cover.jpg",
        episodes=12,
        score=7.6,
        meta_tags=("日本", "漫画改"),
        raw={
            "infobox": [
                {"key": "动画制作", "value": "Sample Studio"},
                {"key": "导演", "value": "Sample Director"},
                {"key": "音乐", "value": "Sample Composer"},
            ]
        },
    )


class FakeDetailsSource:
    def get_subject(self, subject_id, category):
        result = detailed_subject(subject_id)
        self.last_category = category
        return result


class ObsidianImportTests(unittest.TestCase):
    def test_unfiltered_candidate_is_refused(self) -> None:
        document = parse_candidate_markdown(
            '- [x] **测试**\n  <!-- anime-bridge:item {"air_date":"2026-07-05","bangumi_id":10,"category":"tv"} -->\n'
        )
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ObsidianImportConflict, "Bahamut"):
                plan_checked_import(document, FakeDetailsSource(), Path(directory))

    def test_formal_renderer_matches_existing_frontmatter_contract(self) -> None:
        subject = detailed_subject()
        content = render_formal_note(subject, recorded_on=date(2026, 8, 21))
        for field in (
            "中文名:", "日文名:", "cover:", "改编类型:", "总集数:",
            "观看状态:", "制作公司:", "监督:", "音乐:", "开播年份:",
            "开播季度:", "记录日期:", "BGM链接:", "BGM评分:", "下载路径:",
            'tags: "bangumi"',
        ):
            self.assertIn(field, content)
        self.assertIn('观看状态: "想看"', content)
        self.assertIn('开播季度: "07月新番"', content)
        self.assertIn("# 个人总结", content)

    def test_path_is_safe_and_uses_existing_quarter_layout(self) -> None:
        path = formal_note_path(detailed_subject())
        self.assertEqual(path.as_posix(), "C/bangumi/2026/07月新番/测试：动画 第二季.md")
        self.assertEqual(safe_note_filename("CON"), "CON-动画")

    def test_preview_and_apply_never_overwrite_existing_note(self) -> None:
        document = parse_candidate_markdown(
            '---\nbahamut_subtraction: true\n---\n- [x] **测试**\n  <!-- anime-bridge:item {"air_date":"2026-07-05","bangumi_id":10,"category":"tv"} -->\n'
        )
        with tempfile.TemporaryDirectory() as directory:
            vault = Path(directory)
            plans = plan_checked_import(document, FakeDetailsSource(), vault)
            self.assertEqual(len(plans), 1)
            self.assertFalse(plans[0].conflict)
            written = apply_import_plan(plans, vault)
            self.assertEqual(len(written), 1)
            original = written[0].read_text(encoding="utf-8")

            conflicting = plan_checked_import(document, FakeDetailsSource(), vault)
            self.assertTrue(conflicting[0].conflict)
            with self.assertRaises(ObsidianImportConflict):
                apply_import_plan(conflicting, vault)
            self.assertEqual(written[0].read_text(encoding="utf-8"), original)

    def test_target_appearing_after_preview_is_not_overwritten(self) -> None:
        document = parse_candidate_markdown(
            '---\nbahamut_subtraction: true\n---\n- [x] **测试**\n  <!-- anime-bridge:item {"air_date":"2026-07-05","bangumi_id":10,"category":"tv"} -->\n'
        )
        with tempfile.TemporaryDirectory() as directory:
            vault = Path(directory)
            plans = plan_checked_import(document, FakeDetailsSource(), vault)
            target = vault.joinpath(*plans[0].target_relative.parts)
            target.parent.mkdir(parents=True)
            target.write_text("用户的新文件", encoding="utf-8")
            with self.assertRaises(ObsidianImportConflict):
                apply_import_plan(plans, vault)
            self.assertEqual(target.read_text(encoding="utf-8"), "用户的新文件")


if __name__ == "__main__":
    unittest.main()
