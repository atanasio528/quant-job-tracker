from dataclasses import dataclass
from urllib.parse import urljoin

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
        for link in soup.find_all("a", href=True):
            title = " ".join(link.get_text(" ", strip=True).split())
            if len(title) < 4:
                continue
            title_l = title.lower()
            if not any(
                term in title_l
                for term in (
                    "quant",
                    "trader",
                    "research",
                    "algorithm",
                    "alpha",
                    "investment",
                    "strategy",
                    "compliance",
                )
            ):
                continue
            cards.append(JobCard(title=title, loc="Unknown", url=urljoin(base_url, link["href"])))
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
