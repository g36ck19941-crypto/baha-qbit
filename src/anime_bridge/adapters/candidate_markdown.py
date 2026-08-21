"""Parse user checkbox decisions from an Anime Bridge candidate note."""

from __future__ import annotations

import json
import re
from datetime import date

from anime_bridge.domain import (
    AnimeCategory,
    CandidateDocument,
    CandidateSelection,
)


_TASK = re.compile(r"^- \[(?P<state>[ xX])\] \*\*(?P<title>.+?)\*\*\s*$")
_MARKER = re.compile(r"^\s*<!-- anime-bridge:item (?P<payload>\{.*\}) -->\s*$")
_BAHAMUT_SUBTRACTION = re.compile(
    r"^bahamut_subtraction:\s*true\s*$", re.IGNORECASE | re.MULTILINE
)


class CandidateParseError(ValueError):
    pass


def parse_candidate_markdown(markdown: str) -> CandidateDocument:
    lines = markdown.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    selections: list[CandidateSelection] = []

    for index, line in enumerate(lines):
        task = _TASK.match(line)
        if task is None:
            continue
        marker = None
        for lookahead in lines[index + 1 : index + 4]:
            marker = _MARKER.match(lookahead)
            if marker is not None:
                break
            if _TASK.match(lookahead):
                break
        if marker is None:
            raise CandidateParseError(
                f"Candidate task on line {index + 1} has no machine-readable marker"
            )
        try:
            payload = json.loads(marker.group("payload"))
            selection = CandidateSelection(
                checked=task.group("state").lower() == "x",
                title=task.group("title").strip(),
                bangumi_id=int(payload["bangumi_id"]),
                category=AnimeCategory.from_config_name(str(payload["category"])),
                air_date=date.fromisoformat(str(payload["air_date"])),
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise CandidateParseError(
                f"Candidate marker on line {index + 1} is invalid"
            ) from exc
        selections.append(selection)

    return CandidateDocument(
        tuple(selections),
        bahamut_subtracted=_BAHAMUT_SUBTRACTION.search(markdown) is not None,
    )

