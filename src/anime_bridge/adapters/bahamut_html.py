"""Pure parser for the logged-in Bahamut `mygather.php` document.

The parser deliberately accepts HTML text rather than credentials or cookies.
Browser-session acquisition remains a separate adapter and can be replaced when
Bahamut changes authentication behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import parse_qs, urljoin, urlparse

from anime_bridge.domain import BahamutFavorite


BAHAMUT_BASE_URL = "https://ani.gamer.com.tw/"
EMPTY_COLLECTION_MARKER = "目前沒有訂閱內容"


@dataclass(frozen=True, slots=True)
class BahamutFavoritesPage:
    items: tuple[BahamutFavorite, ...]
    empty_collection_marker: bool


class _MyGatherParser(HTMLParser):
    def __init__(self, page: int | None) -> None:
        super().__init__(convert_charrefs=True)
        self.page = page
        self.stack: list[tuple[str, frozenset[str]]] = []
        self.current_href: str | None = None
        self.current_title_parts: list[str] = []
        self.items: list[BahamutFavorite] = []
        self.all_text_parts: list[str] = []

    def _inside_theme_list(self) -> bool:
        return any("theme-list-block" in classes for _, classes in self.stack)

    def _inside_theme_name(self) -> bool:
        return any("theme-name" in classes for _, classes in self.stack)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        classes = frozenset((attributes.get("class") or "").split())
        self.stack.append((tag, classes))
        if tag == "a" and self._inside_theme_list():
            self._finish_anchor()
            self.current_href = attributes.get("href") or ""
            self.current_title_parts = []

    def handle_data(self, data: str) -> None:
        self.all_text_parts.append(data)
        if self.current_href is not None and self._inside_theme_name():
            self.current_title_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.current_href is not None:
            self._finish_anchor()
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break

    def close(self) -> None:
        self._finish_anchor()
        super().close()

    def _finish_anchor(self) -> None:
        if self.current_href is None:
            return
        title = " ".join("".join(self.current_title_parts).split())
        if title:
            absolute_href = urljoin(BAHAMUT_BASE_URL, self.current_href)
            self.items.append(
                BahamutFavorite(
                    title=title,
                    href=absolute_href,
                    sn=_extract_sn(absolute_href),
                    page=self.page,
                )
            )
        self.current_href = None
        self.current_title_parts = []


def _extract_sn(href: str) -> int | None:
    values = parse_qs(urlparse(href).query).get("sn") or []
    if not values:
        return None
    try:
        return int(values[-1])
    except ValueError:
        return None


def parse_mygather_html(html: str, page: int | None = None) -> BahamutFavoritesPage:
    parser = _MyGatherParser(page)
    parser.feed(html)
    parser.close()
    page_text = "".join(parser.all_text_parts)
    deduplicated: dict[tuple[str, str], BahamutFavorite] = {}
    for item in parser.items:
        deduplicated.setdefault((item.title, item.href), item)
    return BahamutFavoritesPage(
        items=tuple(deduplicated.values()),
        empty_collection_marker=EMPTY_COLLECTION_MARKER in page_text,
    )

