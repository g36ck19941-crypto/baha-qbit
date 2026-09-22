"""Bounded read-only validation for public RSS endpoints."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from xml.etree import ElementTree


@dataclass(frozen=True, slots=True)
class RSSProbeResult:
    url: str
    available: bool
    detail: str


class HTTPRSSProbe:
    """Fetch only a small public response; never uses cookies or credentials."""

    def probe(self, url: str) -> RSSProbeResult:
        request = Request(url, headers={"User-Agent": "AnimeBridge/0.16 RSS probe"})
        try:
            with urlopen(request, timeout=12) as response:
                body = response.read(256 * 1024)
                content_type = response.headers.get_content_type()
        except HTTPError as exc:
            return RSSProbeResult(url, False, f"HTTP {exc.code}")
        except (URLError, TimeoutError, OSError) as exc:
            return RSSProbeResult(url, False, f"连接失败：{type(exc).__name__}")
        if content_type not in {"application/rss+xml", "application/atom+xml", "application/xml", "text/xml"}:
            return RSSProbeResult(url, False, f"不是 RSS 内容（{content_type}）")
        try:
            root = ElementTree.fromstring(body)
        except ElementTree.ParseError:
            return RSSProbeResult(url, False, "RSS XML 解析失败")
        if root.tag.rsplit("}", 1)[-1] not in {"rss", "feed", "rdf"}:
            return RSSProbeResult(url, False, "XML 根节点不是 RSS/Atom")
        return RSSProbeResult(url, True, "RSS/Atom 已验证")
