import re
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
    def fetch_cards(self, url: str) -> list[JobCard]:
        parsed_url = urlparse(url)
        if parsed_url.netloc == "www.janestreet.com" and parsed_url.path.startswith(
            "/join-jane-street/open-roles"
        ):
            return self.fetch_jane_street_cards(url)
        if parsed_url.netloc == "www.hudsonrivertrading.com" and parsed_url.path.rstrip(
            "/"
        ) == "/careers":
            return self.fetch_hrt_cards(url)
        if parsed_url.netloc == "careers.twosigma.com" and parsed_url.path.startswith(
            "/careers/OpenRoles"
        ):
            return self.fetch_paginated_cards(url)

        html = self.fetch_html(url)
        return self.parse_cards(url, html)

    def parse_cards(self, base_url: str, html: str) -> list[JobCard]:
        soup = BeautifulSoup(html, "html.parser")
        parsed_base = urlparse(base_url)
        if parsed_base.netloc == "www.deshaw.com" and parsed_base.path.startswith("/careers"):
            return parse_deshaw_cards(base_url, soup)
        if parsed_base.netloc == "careers.twosigma.com":
            return parse_two_sigma_cards(base_url, soup)
        if parsed_base.netloc in {"www.citadel.com", "www.citadelsecurities.com"}:
            return parse_citadel_cards(base_url, soup)

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

    def fetch_paginated_cards(self, url: str, max_pages: int = 8) -> list[JobCard]:
        cards: list[JobCard] = []
        seen_pages: set[str] = set()
        pages_to_visit = [url]
        while pages_to_visit and len(seen_pages) < max_pages:
            page_url = pages_to_visit.pop(0)
            if page_url in seen_pages:
                continue
            seen_pages.add(page_url)
            html = self.fetch_html(page_url)
            soup = BeautifulSoup(html, "html.parser")
            cards.extend(self.parse_cards(page_url, html))
            for link in soup.find_all("a", href=True):
                href = urljoin(page_url, link["href"].strip())
                parsed_href = urlparse(href)
                href = urlunparse(parsed_href._replace(fragment=""))
                if (
                    parsed_href.netloc == "careers.twosigma.com"
                    and parsed_href.path.rstrip("/") == "/careers/OpenRoles"
                    and "jobOffset=" in parsed_href.query
                    and href not in seen_pages
                    and href not in pages_to_visit
                ):
                    pages_to_visit.append(href)
        return dedupe_cards(cards)

    def fetch_jane_street_cards(self, url: str) -> list[JobCard]:
        base = "https://www.janestreet.com"
        with httpx.Client(timeout=20.0, follow_redirects=True, headers=BROWSER_HEADERS) as client:
            jobs_response = request_with_retries(client, "GET", f"{base}/jobs/main.json")
            jobs_response.raise_for_status()
            jobs = jobs_response.json()
            positions_response = request_with_retries(
                client, "GET", f"{base}/static/position-directories.json"
            )
            positions_response.raise_for_status()
            position_directories = {
                str(position_id) for position_id in positions_response.json()
            }

        cards: list[JobCard] = []
        for job in jobs:
            job_id = str(job.get("id", ""))
            if job_id not in position_directories:
                continue
            title = str(job.get("position") or "").strip()
            if not title:
                continue
            city = str(job.get("city") or "").strip()
            loc = JANE_STREET_CITY_NAMES.get(city, city or "Unknown")
            cards.append(
                JobCard(
                    title=title,
                    loc=loc,
                    url=urljoin(url, f"/join-jane-street/position/{job_id}/"),
                )
            )
        return cards

    def fetch_hrt_cards(self, url: str) -> list[JobCard]:
        html = self.fetch_html(url)
        soup = BeautifulSoup(html, "html.parser")
        wrapper = soup.select_one(".hrt-card-wrapper")
        setting = wrapper.get("data-filters-settings", "") if wrapper else ""
        with httpx.Client(timeout=20.0, follow_redirects=True, headers=BROWSER_HEADERS) as client:
            response = request_with_retries(
                client,
                "POST",
                "https://www.hudsonrivertrading.com/wp-admin/admin-ajax.php",
                data={
                    "action": "get_hrt_jobs_handler",
                    "data[search]": "",
                    "setting": setting,
                },
                headers={"Referer": url},
            )
            if response.status_code == 403:
                raise CareerPageBlockedError("blocked by career site with HTTP 403")
            response.raise_for_status()
            rows = response.json()

        cards: list[JobCard] = []
        if not isinstance(rows, list):
            return cards
        for row in rows:
            if not isinstance(row, dict):
                continue
            content = str(row.get("content") or "")
            if content:
                cards.extend(parse_hrt_cards(url, BeautifulSoup(content, "html.parser")))
        return dedupe_cards(cards)

    def fetch_html(self, url: str) -> str:
        with httpx.Client(timeout=20.0, follow_redirects=True, headers=BROWSER_HEADERS) as client:
            response = request_with_retries(client, "GET", url)
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


JANE_STREET_CITY_NAMES = {
    "NYC": "New York",
    "LDN": "London",
    "HKG": "Hong Kong",
    "AMS": "Amsterdam",
    "CHI": "Chicago",
    "SGP": "Singapore",
    "MUM": "Mumbai",
    "SHA": "Shanghai",
    "SF": "San Francisco",
    "ATX": "Austin",
    "NYC/HKG": "New York/Hong Kong",
}


def parse_deshaw_cards(base_url: str, soup: BeautifulSoup) -> list[JobCard]:
    cards: list[JobCard] = []
    for job in soup.select("div.job[data-job-id]"):
        title_el = job.select_one(".job-display-name")
        link = job.select_one("a#job-description-a-tag[href], a[href*='/careers/']")
        if title_el is None or link is None:
            continue
        href = link.get("href", "").strip()
        title = clean_card_title(title_el.get_text(" ", strip=True))
        loc_el = job.select_one(".information .location")
        loc = loc_el.get_text(" ", strip=True) if loc_el else "Unknown"
        if title and href:
            cards.append(JobCard(title=title, loc=loc, url=normalize_url(base_url, href)))
    if cards:
        return dedupe_cards(cards)

    for link in soup.find_all("a", href=True):
        href = link["href"].strip()
        url = normalize_url(base_url, href)
        path = urlparse(url).path
        if not re.fullmatch(r"/careers/[^/]+-\d+", path):
            continue
        title = clean_card_title(link.get_text(" ", strip=True))
        if title:
            cards.append(JobCard(title=title, loc="Unknown", url=url))
    return dedupe_cards(cards)


def parse_two_sigma_cards(base_url: str, soup: BeautifulSoup) -> list[JobCard]:
    cards: list[JobCard] = []
    for article in soup.select("article.article"):
        link = article.select_one("a.link[href*='/careers/JobDetail/']")
        if link is None:
            continue
        title = clean_card_title(link.get_text(" ", strip=True))
        spans = [
            span.get_text(" ", strip=True)
            for span in article.select(".paragraph_inner-span")
            if span.get_text(" ", strip=True)
        ]
        loc = next((span for span in spans if "United States" in span), spans[0] if spans else "Unknown")
        cards.append(JobCard(title=title, loc=loc, url=normalize_url(base_url, link["href"])))
    return dedupe_cards(cards)


def parse_citadel_cards(base_url: str, soup: BeautifulSoup) -> list[JobCard]:
    cards: list[JobCard] = []
    for link in soup.find_all("a", href=True):
        href = link["href"].strip()
        if "/careers/details/" not in href:
            continue
        title, loc = split_citadel_title_and_location(clean_card_title(link.get_text(" ", strip=True)))
        if title:
            cards.append(JobCard(title=title, loc=loc, url=normalize_url(base_url, href)))
    return dedupe_cards(cards)


def parse_hrt_cards(base_url: str, soup: BeautifulSoup) -> list[JobCard]:
    cards: list[JobCard] = []
    for card in soup.select(".hrt-card-item"):
        link = card.select_one("a.hrt-card-title[href]")
        if link is None:
            continue
        title = clean_card_title(link.get_text(" ", strip=True))
        locations = [
            span.get_text(" ", strip=True)
            for span in card.select(".hrt-card-meta-desktop ul.hrt-card-info-list:not(.second-list) span")
            if span.get_text(" ", strip=True)
        ]
        cards.append(
            JobCard(
                title=title,
                loc=", ".join(locations) if locations else "Unknown",
                url=normalize_url(base_url, link["href"]),
            )
        )
    return dedupe_cards(cards)


def split_citadel_title_and_location(text: str) -> tuple[str, str]:
    text = text.removesuffix("Apply Now").strip()
    for marker in (" (US)", " (Europe)", " (Asia)", " (Australia)"):
        if marker in text:
            title, loc = text.split(marker, 1)
            return f"{title.strip()}{marker}", loc.strip() or "Unknown"
    return text, "Unknown"


def normalize_url(base_url: str, href: str) -> str:
    parsed_url = urlparse(urljoin(base_url, href.strip()))
    return urlunparse(parsed_url._replace(fragment=""))


def dedupe_cards(cards: list[JobCard]) -> list[JobCard]:
    deduped: list[JobCard] = []
    seen_urls: set[str] = set()
    for card in cards:
        if card.url in seen_urls:
            continue
        seen_urls.add(card.url)
        deduped.append(card)
    return deduped


def request_with_retries(
    client: httpx.Client, method: str, url: str, max_attempts: int = 3, **kwargs: object
) -> httpx.Response:
    retryable = (httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError)
    last_exc: Exception | None = None
    for _attempt in range(max_attempts):
        try:
            return client.request(method, url, **kwargs)
        except retryable as exc:
            last_exc = exc
    if last_exc is not None:
        raise last_exc
    raise RuntimeError("request retry loop exited unexpectedly")


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
