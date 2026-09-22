"""Build provider-specific RSS drafts from checked anime candidates."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote, quote_plus, urlsplit

from anime_bridge.domain import CandidateDocument, RSSFeedDraft, RSSRuleDraft


@dataclass(frozen=True, slots=True)
class RSSSourceProvider:
    key: str
    label: str
    template: str
    query_style: str
    operational_note: str


@dataclass(frozen=True, slots=True)
class CandidateRSSDraft:
    bangumi_id: int
    title: str
    providers: tuple[str, ...]
    search_terms: tuple[str, ...]
    feeds: tuple[RSSFeedDraft, ...]
    rule: RSSRuleDraft


PROVIDERS = {
    "comicat-rsshub": RSSSourceProvider(
        key="comicat-rsshub",
        label="Comicat via RSSHub",
        template="https://rsshub.app/comicat/search/{query}",
        query_style="path-plus",
        operational_note=(
            "Public rsshub.app may require browser verification; use an accessible "
            "or self-hosted RSSHub template when qBittorrent cannot refresh it."
        ),
    ),
    "dmhy": RSSSourceProvider(
        key="dmhy",
        label="动漫花园关键词 RSS",
        template="https://share.dmhy.org/topics/rss/rss.xml?keyword={query}",
        query_style="query",
        operational_note="Direct keyword RSS; availability depends on the local network.",
    ),
}


def provider_catalog() -> tuple[RSSSourceProvider, ...]:
    return tuple(PROVIDERS.values())


def build_feed_url(
    provider_key: str,
    terms: tuple[str, ...],
    *,
    custom_template: str = "",
) -> str:
    cleaned = _clean_terms(terms)
    if not cleaned:
        raise ValueError("At least one RSS search term is required")
    if provider_key not in PROVIDERS and provider_key != "custom":
        raise ValueError(f"Unsupported RSS provider: {provider_key}")
    if custom_template.strip():
        template = custom_template.strip()
        style = "path-plus" if provider_key == "comicat-rsshub" else "query"
        if "{query}" not in template:
            raise ValueError("Custom RSS template must contain {query}")
    elif provider_key == "custom":
        raise ValueError("Custom RSS provider requires a template containing {query}")
    else:
        try:
            provider = PROVIDERS[provider_key]
        except KeyError as exc:
            raise ValueError(f"Unsupported RSS provider: {provider_key}") from exc
        template = provider.template
        style = provider.query_style
    joined = "+".join(cleaned)
    encoded = quote(joined, safe="+") if style == "path-plus" else quote_plus(" ".join(cleaned))
    url = template.replace("{query}", encoded)
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("RSS source URL must be credential-free HTTPS")
    return url


def build_candidate_rss_drafts(
    document: CandidateDocument,
    provider_keys: str | tuple[str, ...],
    *,
    extra_terms: tuple[str, ...] = (),
    custom_template: str = "",
    feed_root: str = "AnimeBridge",
    must_contain: str = "",
    must_not_contain: str = "",
    episode_filter: str = "",
    category: str = "anime",
    save_root: str = "",
) -> tuple[CandidateRSSDraft, ...]:
    if not document.bahamut_subtracted:
        raise ValueError(
            "RSS batch refused because this candidate note has not completed "
            "Bahamut current-quarter catalog subtraction"
        )
    root = _relative_component(feed_root, allow_slash=True)
    keys = (provider_keys,) if isinstance(provider_keys, str) else provider_keys
    keys = tuple(dict.fromkeys(key.strip() for key in keys if key.strip()))
    if not keys:
        raise ValueError("At least one RSS source is required")
    templates = tuple(
        line.strip() for line in custom_template.splitlines() if line.strip()
    )
    if "custom" in keys and not templates:
        raise ValueError("Custom RSS provider requires at least one HTTPS template")
    result: list[CandidateRSSDraft] = []
    seen_rules: set[str] = set()
    for selection in document.checked:
        terms = _clean_terms((selection.title, *extra_terms))
        title_component = _relative_component(selection.title)
        rule_name = title_component
        if rule_name in seen_rules:
            rule_name = f"{title_component} [{selection.bangumi_id}]"
        if rule_name in seen_rules:
            raise ValueError("Candidate RSS drafts contain duplicate targets")
        seen_rules.add(rule_name)
        feeds: list[RSSFeedDraft] = []
        labels: list[str] = []
        for key in keys:
            source_templates = templates if key == "custom" else ("",)
            for index, template in enumerate(source_templates, start=1):
                url = build_feed_url(key, terms, custom_template=template)
                label = key if len(source_templates) == 1 else f"{key}-{index}"
                feeds.append(
                    RSSFeedDraft(
                        url=url,
                        path=(
                            f"{root}/{selection.air_date.year}-{selection.air_date.month:02d}"
                            f"/{title_component}/{label}"
                        ),
                    )
                )
                labels.append(label)
        save_path = ""
        if save_root.strip():
            root_path = Path(save_root).expanduser()
            if not root_path.is_absolute():
                raise ValueError("RSS batch save root must be an absolute path")
            save_path = str(root_path / title_component)
        rule = RSSRuleDraft(
            name=rule_name,
            affected_feeds=tuple(feed.url for feed in feeds),
            must_contain=must_contain,
            must_not_contain=must_not_contain,
            episode_filter=episode_filter,
            smart_filter=bool(episode_filter),
            add_paused=True,
            assigned_category=category,
            save_path=save_path,
            enabled=False,
        )
        result.append(
            CandidateRSSDraft(
                bangumi_id=selection.bangumi_id,
                title=selection.title,
                providers=tuple(labels),
                search_terms=terms,
                feeds=tuple(feeds),
                rule=rule,
            )
        )
    return tuple(result)


def _clean_terms(values: tuple[str, ...]) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        cleaned = " ".join(str(value or "").split())
        if cleaned and cleaned not in result:
            result.append(cleaned)
    if sum(len(term) for term in result) > 300:
        raise ValueError("RSS search terms are too long")
    return tuple(result)


def _relative_component(value: str, *, allow_slash: bool = False) -> str:
    cleaned = " ".join(str(value or "").split()).strip(" .")
    if allow_slash:
        parts = [_relative_component(part) for part in cleaned.replace("\\", "/").split("/")]
        if not parts or any(not part for part in parts):
            raise ValueError("RSS feed root must be a relative path")
        return "/".join(parts)
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", cleaned).strip(" .")
    if cleaned in {"", ".", ".."}:
        raise ValueError("RSS title cannot form a safe path component")
    return cleaned[:80]
