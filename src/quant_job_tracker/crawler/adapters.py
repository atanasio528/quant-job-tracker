from dataclasses import dataclass
from urllib.parse import urljoin, urlparse, urlunparse

import httpx
from bs4 import BeautifulSoup


@dataclass(frozen=True)
class JobCard:
    title: str
    loc: str
    url: str


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
        with httpx.Client(timeout=20.0, follow_redirects=True) as client:
            response = client.get(url)
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
