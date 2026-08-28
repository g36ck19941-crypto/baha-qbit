"""Command-line interface and the future GUI's stable workflow boundary."""

from __future__ import annotations

import argparse
import getpass
import json
import sys
from dataclasses import replace
from datetime import date
from pathlib import Path
from typing import Sequence

from anime_bridge import __version__
from anime_bridge.ai.service import AnimeBridgeAIService, WRITE_CONFIRMATION
from anime_bridge.adapters.bangumi import BangumiAPIError, BangumiClient
from anime_bridge.adapters.bahamut_html import parse_mygather_html
from anime_bridge.adapters.bahamut_catalog import BahamutCatalogClient, load_bahamut_catalog
from anime_bridge.adapters.candidate_markdown import (
    CandidateParseError,
    parse_candidate_markdown,
)
from anime_bridge.adapters.qbittorrent import QBittorrentAPIError, QBittorrentClient
from anime_bridge.domain import RSSFeedDraft, RSSRuleDraft
from anime_bridge.migration import MigrationConflict, apply_migration, plan_migration
from anime_bridge.renderers import render_bahamut_review_markdown, render_candidate_markdown
from anime_bridge.settings import UserSettings, default_settings_path
from anime_bridge.storage import write_text_atomic
from anime_bridge.workflows import (
    CurrentQuarterScanner,
    ObsidianImportConflict,
    apply_import_plan,
    apply_rss_plan,
    plan_checked_import,
    plan_rss,
    RSSPlanConflict,
    subtract_bahamut_catalog,
)


def _iso_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("date must use YYYY-MM-DD") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="anime-bridge",
        description="Discover and stage the current quarter's anime.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan", help="scan Bangumi and render a candidate note")
    scan.add_argument(
        "--date",
        type=_iso_date,
        default=None,
        help="reference date for reproducible or future selected-quarter scans",
    )
    scan.add_argument(
        "--output",
        type=Path,
        default=None,
        help="candidate Markdown path (default: out/<year>-<month>-candidates.md)",
    )
    scan.add_argument(
        "--dry-run",
        action="store_true",
        help="fetch and report without writing a candidate file",
    )
    scan.add_argument(
        "--user-agent",
        default=f"AnimeBridge/{__version__} (local application)",
        help="identifiable User-Agent sent to Bangumi",
    )
    scan.add_argument(
        "--bahamut-catalog",
        "--bahamut-export",
        dest="bahamut_catalog",
        type=Path,
        default=None,
        help="current-quarter JSON exported from Bahamut's public catalog",
    )
    scan.add_argument(
        "--skip-bahamut-catalog",
        action="store_true",
        help="diagnostic only: create a gated Bangumi-only preview",
    )
    parse_bahamut = subparsers.add_parser(
        "parse-bahamut-html",
        help="offline diagnostic: parse a user-exported mygather.php HTML file",
    )
    parse_bahamut.add_argument("input", type=Path, help="UTF-8 HTML file to parse")
    parse_bahamut.add_argument(
        "--json-output", type=Path, default=None, help="optional parsed JSON path"
    )
    obsidian_import = subparsers.add_parser(
        "obsidian-import",
        help="preview or apply checked candidate items to the formal note library",
    )
    obsidian_import.add_argument("candidate", type=Path, help="candidate Markdown file")
    obsidian_import.add_argument("--vault", type=Path, required=True, help="Obsidian vault")
    obsidian_import.add_argument(
        "--formal-root", default="C/bangumi", help="vault-relative formal note root"
    )
    obsidian_import.add_argument(
        "--plan-output", type=Path, default=None, help="optional JSON preview path"
    )
    obsidian_import.add_argument(
        "--apply",
        action="store_true",
        help="write notes after preview; existing targets still cause full refusal",
    )
    qbit_check = subparsers.add_parser(
        "qbittorrent-check", help="read local qBittorrent and report API versions"
    )
    _add_qbittorrent_connection_args(qbit_check)

    rss = subparsers.add_parser(
        "qbittorrent-rss", help="preview or apply one local RSS feed and rule"
    )
    _add_qbittorrent_connection_args(rss)
    rss.add_argument("--feed-url", required=True)
    rss.add_argument("--feed-path", required=True, help="qBittorrent-relative RSS path")
    rss.add_argument("--rule-name", required=True)
    rss.add_argument("--must-contain", default="")
    rss.add_argument("--must-not-contain", default="")
    rss.add_argument("--regex", action="store_true")
    rss.add_argument("--episode-filter", default="")
    rss.add_argument("--smart-filter", action="store_true")
    rss.add_argument("--category", default="")
    rss.add_argument("--save-path", default="")
    rss.add_argument(
        "--enable-rule", action="store_true", help="enable the new rule immediately"
    )
    rss.add_argument(
        "--start-downloads",
        action="store_true",
        help="allow matched downloads to start instead of adding them paused",
    )
    rss.add_argument("--plan-output", type=Path, default=None)
    rss.add_argument("--apply", action="store_true")

    rss_batch = subparsers.add_parser(
        "qbittorrent-rss-batch",
        help="preview or apply per-anime RSS drafts from checked candidates",
    )
    _add_qbittorrent_connection_args(rss_batch)
    rss_batch.add_argument("candidate", type=Path)
    rss_batch.add_argument("--vault", type=Path, required=True)
    rss_batch.add_argument(
        "--provider",
        choices=("comicat-rsshub", "dmhy", "custom"),
        action="append",
        required=True,
        help="RSS source; repeat this option to use multiple sources per anime",
    )
    rss_batch.add_argument("--extra-term", action="append", default=[])
    rss_batch.add_argument("--custom-template", default="")
    rss_batch.add_argument("--must-contain", default="")
    rss_batch.add_argument("--must-not-contain", default="")
    rss_batch.add_argument("--episode-filter", default="")
    rss_batch.add_argument("--category", default="anime")
    rss_batch.add_argument("--save-root", default="")
    rss_batch.add_argument("--plan-output", type=Path, default=None)
    rss_batch.add_argument("--apply", action="store_true")

    migrate = subparsers.add_parser(
        "migrate", help="preview or install the portable Obsidian integration"
    )
    migrate.add_argument("--vault", type=Path, required=True, help="Obsidian vault")
    migrate.add_argument("--integration-folder", default="bangumi1")
    migrate.add_argument("--formal-root", default="C/bangumi")
    migrate.add_argument("--qbit-base-url", default="http://127.0.0.1:8080")
    migrate.add_argument(
        "--runner",
        type=Path,
        default=Path(sys.executable),
        help="packaged anime-bridge.exe path (defaults to the current executable)",
    )
    migrate.add_argument("--settings", type=Path, default=None)
    migrate.add_argument("--plan-output", type=Path, default=None)
    migrate.add_argument("--apply", action="store_true")
    return parser


def _add_qbittorrent_connection_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    parser.add_argument(
        "--username",
        default=None,
        help="WebUI username; if supplied, password is prompted without echo",
    )


def _qbit_client(args: argparse.Namespace) -> QBittorrentClient:
    client = QBittorrentClient(args.base_url)
    if args.username is not None:
        client.login(args.username, getpass.getpass("qBittorrent WebUI password: "))
    return client


def _run_scan(args: argparse.Namespace) -> int:
    reference_date = args.date or date.today()
    if args.skip_bahamut_catalog and args.bahamut_catalog is not None:
        raise ValueError("--skip-bahamut-catalog cannot be combined with --bahamut-catalog")
    scanner = CurrentQuarterScanner(BangumiClient(user_agent=args.user_agent))
    result = scanner.scan(reference_date)
    difference = None
    catalog = None
    if not args.skip_bahamut_catalog and args.bahamut_catalog is not None:
        catalog = load_bahamut_catalog(args.bahamut_catalog)
    elif not args.skip_bahamut_catalog:
        catalog = BahamutCatalogClient().fetch_current_quarter(reference_date)
    if catalog is not None:
        if (catalog.quarter_year, catalog.quarter_start_month) != (
            result.year,
            result.quarter.start_month,
        ):
            raise ValueError("Bahamut catalog does not describe the scan quarter")
        difference = subtract_bahamut_catalog(result.subjects, catalog.items)
        review_subject_ids = {match.subject.bangumi_id for match in difference.review_matches}
        review_result = replace(
            result,
            subjects=tuple(
                subject for subject in result.subjects if subject.bangumi_id in review_subject_ids
            ),
        )
        result = replace(result, subjects=difference.candidates)
        print(
            f"Bahamut catalog: {len(catalog.items)} current-quarter title(s) from "
            f"{catalog.pages_scanned} page(s); removed "
            f"{len(difference.exact_matches)} exact match(es); moved "
            f"{len(difference.review_matches)} fuzzy review match(es) to a separate note."
        )
        for warning in catalog.warnings:
            print(f"Bahamut catalog warning: {warning}", file=sys.stderr)

    output = args.output or Path("out") / (
        f"{result.year}-{result.quarter.start_month:02d}-candidates.md"
    )

    print(
        f"Found {len(result.subjects)} subjects for "
        f"{result.year} {result.quarter.cn_name} "
        "(Japan-tagged TV, Movie, WEB; OVA/Other excluded)."
    )
    print(
        f"Excluded {len(result.excluded_without_japan_tag)} subjects without "
        "Bangumi's Japan meta tag."
    )
    if args.dry_run:
        print("Dry run: no file written.")
        return 0

    write_text_atomic(
        output,
        render_candidate_markdown(
            result,
            bahamut_difference=difference,
            bahamut_catalog_count=(len(catalog.items) if catalog is not None else 0),
            bahamut_exported_at=(
                catalog.exported_at if catalog is not None else ""
            ),
        ),
    )
    print(f"Candidate preview written to: {output.resolve()}")
    if difference is not None and difference.review_matches:
        review_output = output.with_name(f"{output.stem}-复核{output.suffix}")
        write_text_atomic(
            review_output,
            render_bahamut_review_markdown(
                review_result,
                difference,
                bahamut_catalog_count=len(catalog.items),
                bahamut_exported_at=catalog.exported_at,
            ),
        )
        print(f"Bahamut review note written to: {review_output.resolve()}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "scan":
            return _run_scan(args)
        if args.command == "parse-bahamut-html":
            html = args.input.read_text(encoding="utf-8")
            page = parse_mygather_html(html)
            payload = [
                {"title": item.title, "href": item.href, "sn": item.sn}
                for item in page.items
            ]
            print(
                f"Parsed {len(payload)} Bahamut favorites; "
                f"empty marker={page.empty_collection_marker}."
            )
            if args.json_output is not None:
                write_text_atomic(
                    args.json_output,
                    json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                )
                print(f"Parsed JSON written to: {args.json_output.resolve()}")
            return 0
        if args.command == "obsidian-import":
            document = parse_candidate_markdown(args.candidate.read_text(encoding="utf-8"))
            plans = plan_checked_import(
                document,
                BangumiClient(),
                args.vault.resolve(),
                args.formal_root,
            )
            payload = [
                {
                    "bangumi_id": plan.subject.bangumi_id,
                    "title": plan.subject.display_name,
                    "target": plan.target_relative.as_posix(),
                    "conflict": plan.conflict,
                }
                for plan in plans
            ]
            print(
                f"Planned {len(plans)} formal notes; "
                f"conflicts={sum(1 for plan in plans if plan.conflict)}."
            )
            if args.plan_output is not None:
                write_text_atomic(
                    args.plan_output,
                    json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                )
                print(f"Import preview written to: {args.plan_output.resolve()}")
            if not args.apply:
                print("Preview only: no Obsidian files written. Use --apply explicitly.")
                return 0
            written = apply_import_plan(plans, args.vault.resolve())
            print(f"Wrote {len(written)} formal Obsidian notes.")
            return 0
        if args.command == "qbittorrent-check":
            version, api_version = _qbit_client(args).versions()
            print(f"Connected to qBittorrent {version}; WebUI API {api_version}.")
            return 0
        if args.command == "qbittorrent-rss":
            client = _qbit_client(args)
            feed = RSSFeedDraft(args.feed_url, args.feed_path)
            rule = RSSRuleDraft(
                name=args.rule_name,
                affected_feeds=(args.feed_url,),
                must_contain=args.must_contain,
                must_not_contain=args.must_not_contain,
                use_regex=args.regex,
                episode_filter=args.episode_filter,
                smart_filter=args.smart_filter,
                add_paused=not args.start_downloads,
                assigned_category=args.category,
                save_path=args.save_path,
                enabled=args.enable_rule,
            )
            plan = plan_rss(client, feed, rule)
            payload = {
                "feed": {"url": feed.url, "path": feed.path},
                "rule": {"name": rule.name, **rule.to_qbittorrent_definition()},
                "feed_conflict": plan.feed_conflict,
                "rule_conflict": plan.rule_conflict,
            }
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            if args.plan_output is not None:
                write_text_atomic(
                    args.plan_output,
                    json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                )
                print(f"RSS preview written to: {args.plan_output.resolve()}")
            if not args.apply:
                print("Preview only: no qBittorrent RSS state changed. Use --apply explicitly.")
                return 0
            apply_rss_plan(client, plan)
            print("RSS feed and rule created.")
            return 0
        if args.command == "qbittorrent-rss-batch":
            service = AnimeBridgeAIService(
                args.vault,
                allow_writes=args.apply,
                qbit=_qbit_client(args),
            )
            common = (
                str(args.candidate),
                tuple(args.provider),
                tuple(args.extra_term),
                args.custom_template,
                args.must_contain,
                args.must_not_contain,
                args.episode_filter,
                args.category,
                args.save_root,
            )
            preview = service.plan_candidate_rss(*common)
            print(json.dumps(preview, ensure_ascii=False, indent=2))
            if args.plan_output is not None:
                write_text_atomic(
                    args.plan_output,
                    json.dumps(preview, ensure_ascii=False, indent=2) + "\n",
                )
                print(f"RSS batch preview written to: {args.plan_output.resolve()}")
            if not args.apply:
                print("Preview only: qBittorrent was not changed. Use --apply explicitly.")
                return 0
            result = service.apply_candidate_rss(
                common[0], common[1], WRITE_CONFIRMATION, *common[2:]
            )
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        if args.command == "migrate":
            settings_path = args.settings or default_settings_path()
            settings = UserSettings(
                vault_path=str(args.vault.resolve()),
                integration_folder=args.integration_folder,
                formal_root=args.formal_root,
                qbit_base_url=args.qbit_base_url,
            )
            QBittorrentClient(settings.qbit_base_url)
            plan = plan_migration(settings, settings_path, args.runner)
            payload = plan.as_dict()
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            if args.plan_output is not None:
                write_text_atomic(
                    args.plan_output,
                    json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                )
                print(f"Migration preview written to: {args.plan_output.resolve()}")
            if not args.apply:
                print("Preview only: no plugin or settings files written. Use --apply explicitly.")
                return 0
            written = apply_migration(plan, settings, settings_path)
            print(f"Migration installed or confirmed {len(written)} files.")
            return 0
    except BangumiAPIError as exc:
        print(f"Bangumi scan failed: {exc}", file=sys.stderr)
        return 2
    except (CandidateParseError, ObsidianImportConflict, MigrationConflict) as exc:
        print(f"Obsidian import refused: {exc}", file=sys.stderr)
        return 3
    except (QBittorrentAPIError, RSSPlanConflict, ValueError) as exc:
        print(f"qBittorrent RSS operation refused: {exc}", file=sys.stderr)
        return 4
    parser.error(f"Unknown command: {args.command}")
    return 2
