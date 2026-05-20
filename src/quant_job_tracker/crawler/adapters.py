from dataclasses import dataclass
from urllib.parse import urljoin, urlparse, urlunparse

import httpx
from bs4 import BeautifulSoup

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


@dataclass(frozen=True)
class JobCard:
    title: str
    loc: str
    url: str


class CareerPageBlockedError(RuntimeError):
    pass


class GenericAdapter:
    def parse_cards(self, base_url: str, html: str) -> list[JobCard]:
        soup = BeautifulSoup(html, "html.parser")
        cards: list[JobCard] = []
        seen_urls: set[str] = set()
        for link in soup.find_all("a", href=True):
            title = clean_card_title(link.get_text(" ", strip=True))
            if len(title) < 4:
                continue
            title_l = title.lower()
            if not any(
                term in title_l
                for term in (
                    "quant",
                    "trader",
                    "trading",
                    "research",
                    "algorithm",
                    "alpha",
                    "investment",
                    "strategy",
                    "compliance",
                )
            ):
                continue
            href = link["href"].strip()
            if not href:
                continue
            if href.startswith("#"):
                continue
            url = urljoin(base_url, href)
            parsed_url = urlparse(url)
            if parsed_url.scheme not in {"http", "https"}:
                continue
            url = urlunparse(parsed_url._replace(fragment=""))
            if url in seen_urls:
                continue
            seen_urls.add(url)
            cards.append(JobCard(title=title, loc="Unknown", url=url))
        return cards

    def fetch_html(self, url: str) -> str:
        with httpx.Client(timeout=20.0, follow_redirects=True, headers=BROWSER_HEADERS) as client:
            response = client.get(url)
            if response.status_code == 403:
                if is_cloudflare_challenge(response):
                    raise CareerPageBlockedError("blocked by Cloudflare challenge")
                raise CareerPageBlockedError("blocked by career site with HTTP 403")
            response.raise_for_status()
            return response.text

    def fetch_jd(self, url: str) -> str:
        html = self.fetch_html(url)
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        return " ".join(soup.get_text(" ", strip=True).split())


def clean_card_title(raw_title: str) -> str:
    title = " ".join(raw_title.split())
    if title.lower().startswith("icon "):
        title = title[5:].strip()
    if " : " in title:
        title = title.split(" : ", 1)[0].strip()
    return title


def clean_stored_title(raw_title: str, jd: str) -> str:
    title = clean_card_title(raw_title)
    dirty_markers = (
        " Summary:",
        " Read Post",
        " Provides ",
        " Build ",
        " Make complex",
        " Explore ",
        " is a premier ",
        " Chicago Trading Company ",
    )
    for marker in dirty_markers:
        if marker in title:
            title = title.split(marker, 1)[0].strip()
    title = collapse_repeated_title(title)

    if is_dirty_title(raw_title) and " | " in jd[:160]:
        jd_title = jd.split(" | ", 1)[0].strip()
        if 4 <= len(jd_title) <= 90:
            title = jd_title

    return title.strip(" -–|")


def is_dirty_title(title: str) -> bool:
    title_l = title.lower()
    return any(
        marker in title_l
        for marker in (
            " summary:",
            " read post",
            " provides ",
            " read more",
            " build ",
            " make complex",
            " explore ",
            " is a premier ",
        )
    )


def collapse_repeated_title(title: str) -> str:
    words = title.split()
    if len(words) % 2 != 0:
        return title
    midpoint = len(words) // 2
    if words[:midpoint] == words[midpoint:]:
        return " ".join(words[:midpoint])
    return title


def is_cloudflare_challenge(response: httpx.Response) -> bool:
    return (
        response.status_code == 403
        and response.headers.get("cf-mitigated") == "challenge"
        and "Just a moment" in response.text[:500]
    )
