"""Discover public ChatGPT promotion leads from approved OpenAI pages only.

No logins, account access, billing queries, eligibility assertions or auto-purchases.
A discovered link is an unverified candidate for human review, never an active offer.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from html.parser import HTMLParser
import re
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .catalog import CatalogError, Catalog, official_url

DISCOVERY_ROOTS = (
    "https://help.openai.com/en/?q=chatgpt+promotions",
    "https://help.openai.com/en/?q=chatgpt+student+offer",
    "https://openai.com/news/",
)
_PROMO_TERMS = re.compile(
    r"(?:chatgpt.{0,70}(?:offer|promo|trial|discount|free|referral|veteran|student)|"
    r"(?:offer|promo|trial|discount|referral|veteran|student).{0,70}chatgpt)",
    re.IGNORECASE,
)
_PATH_TERMS = re.compile(
    r"(?:chatgpt.*(?:promo|trial|offer|referral|veteran|student)|"
    r"(?:promo|trial|offer|referral|veteran|student).*chatgpt)",
    re.IGNORECASE,
)


class DiscoveryError(RuntimeError):
    pass


@dataclass(frozen=True)
class Candidate:
    title: str
    url: str
    discovered_from: str
    review_status: str = "pending_review"

    def as_dict(self) -> dict:
        return asdict(self)


class _Anchors(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._label: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self._href = dict(attrs).get("href")
            self._label = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._label.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._href:
            label = " ".join(" ".join(self._label).split())
            if label:
                self.links.append((self._href, label[:180]))
            self._href = None
            self._label = []


def canonical_url(value: str) -> str:
    parsed = urlsplit(value)
    if not parsed.path.startswith(("/en/articles/", "/articles/", "/index/", "/news/")):
        raise CatalogError("Not an official article path")
    clean = urlunsplit((parsed.scheme, parsed.netloc, parsed.path.rstrip("/"), "", ""))
    return official_url(clean)


class _OfficialRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        official_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_official_html(url: str) -> str:
    """Fetch one public HTML page; restrict redirects and maximum response size."""
    official_url(url)
    request = Request(url, headers={
        "User-Agent": "ePlus-ChatGPT-Offer-Inspector/0.2 (+https://github.com/hoangsvit/open-ai)",
        "Accept": "text/html",
    })
    with build_opener(_OfficialRedirects()).open(request, timeout=12) as response:
        official_url(response.geturl())
        if "text/html" not in response.headers.get("Content-Type", "").lower():
            raise DiscoveryError("Not HTML")
        content = response.read(1_000_001)
        if len(content) > 1_000_000:
            raise DiscoveryError("HTML too large")
        return content.decode("utf-8", errors="replace")


def discover_candidates(
    catalog: Catalog,
    fetcher: Callable[[str], str] = fetch_official_html,
    roots: tuple[str, ...] = DISCOVERY_ROOTS,
    previously_seen: set[str] | None = None,
) -> tuple[list[Candidate], list[str], int]:
    known = set(previously_seen or set())
    for item in catalog.references:
        known.add(item.url.rstrip("/"))
    for item in (*catalog.offers, *catalog.archived_offers):
        known.add(item.source_url.rstrip("/"))
    suggestions: dict[str, Candidate] = {}
    errors: list[str] = []
    scanned = 0
    for source in roots:
        try:
            official_url(source)
            html = fetcher(source)
        except (CatalogError, DiscoveryError, HTTPError, URLError, OSError, TimeoutError) as exc:
            # Avoid echoing error contents, which can contain URLs or secrets.
            errors.append("Official source unavailable (" + type(exc).__name__ + ")")
            continue
        parser = _Anchors()
        parser.feed(html)
        if not parser.links:
            # A JS-only shell or blocked response may return HTTP 200, yet
            # supply no discoverable URLs. This is not a healthy scan.
            errors.append("Official source contained no parseable links (possibly JS-only)")
            continue
        scanned += 1
        relevant_links = 0
        for href, title in parser.links[:300]:
            try:
                url = canonical_url(urljoin(source, href))
            except (CatalogError, ValueError):
                continue
            if not (_PROMO_TERMS.search(title) or _PATH_TERMS.search(urlsplit(url).path)):
                continue
            relevant_links += 1
            if url in known or url in suggestions:
                continue
            suggestions[url] = Candidate(title=title, url=url, discovered_from=source)
            if len(suggestions) >= 30:
                break
        if relevant_links == 0:
            errors.append(
                "Official source had links but no promotion-related article URLs; "
                "search results may render dynamically"
            )
        if len(suggestions) >= 30:
            break
    return sorted(suggestions.values(), key=lambda item: item.url), errors, scanned
