"""Command-line interface and the future GUI's stable workflow boundary."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Sequence

from anime_bridge import __version__
from anime_bridge.adapters.bangumi import BangumiAPIError, BangumiClient
from anime_bridge.adapters.bahamut_html import parse_mygather_html
from anime_bridge.renderers import render_candidate_markdown
from anime_bridge.storage import write_text_atomic
from anime_bridge.workflows import CurrentQuarterScanner


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
    parse_bahamut = subparsers.add_parser(
        "parse-bahamut-html",
        help="offline diagnostic: parse a user-exported mygather.php HTML file",
    )
    parse_bahamut.add_argument("input", type=Path, help="UTF-8 HTML file to parse")
    parse_bahamut.add_argument(
        "--json-output", type=Path, default=None, help="optional parsed JSON path"
    )
    return parser


def _run_scan(args: argparse.Namespace) -> int:
    reference_date = args.date or date.today()
    scanner = CurrentQuarterScanner(BangumiClient(user_agent=args.user_agent))
    result = scanner.scan(reference_date)
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

    write_text_atomic(output, render_candidate_markdown(result))
    print(f"Candidate preview written to: {output.resolve()}")
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
    except BangumiAPIError as exc:
        print(f"Bangumi scan failed: {exc}", file=sys.stderr)
        return 2
    parser.error(f"Unknown command: {args.command}")
    return 2
