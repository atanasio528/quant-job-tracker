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
JPMORGAN_SITE_NUMBER = "CX_1001"
JPMORGAN_BASE_URL = "https://jpmc.fa.oraclecloud.com"
JPMORGAN_UI_BASE_URL = "https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001"
JPMORGAN_SEARCH_KEYWORDS = (
    "quant",
    "quantitative research",
    "trader",
    "trading",
    "research",
)
BLACKROCK_BASE_URL = "https://careers.blackrock.com"
BLACKROCK_SEARCH_KEYWORDS = (
    "quant",
    "quantitative",
    "systematic",
    "research",
)
BLACKROCK_CATEGORY_URLS = (
    "https://careers.blackrock.com/category/students-and-graduates-jobs/45831/9022304/1",
)


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
        if (
            parsed_url.netloc == "www.hudsonrivertrading.com"
            and parsed_url.path.rstrip("/") == "/careers"
        ):
            return self.fetch_hrt_cards(url)
        if parsed_url.netloc == "careers.twosigma.com" and parsed_url.path.startswith(
            "/careers/OpenRoles"
        ):
            return self.fetch_paginated_cards(url)
        if parsed_url.netloc in {"www.citadel.com", "www.citadelsecurities.com"} and (
            parsed_url.path.rstrip("/") == "/careers/open-opportunities"
            or parsed_url.path.startswith("/careers/open-opportunities/")
        ):
            return self.fetch_citadel_cards(url)
        if parsed_url.netloc == "www.flowtraders.com" and parsed_url.path.startswith(
            "/careers/job-search"
        ):
            return self.fetch_flow_traders_cards()
        if parsed_url.netloc == "www.imc.com" and parsed_url.path.startswith("/us/search-careers"):
            return self.fetch_imc_cards(url)
        if parsed_url.netloc == "careers.sig.com":
            return self.fetch_sig_cards()
        if parsed_url.netloc == "jpmc.fa.oraclecloud.com" and parsed_url.path.startswith(
            "/hcmUI/CandidateExperience/en/sites/CX_1001/jobs"
        ):
            return self.fetch_jpmorgan_cards()
        if parsed_url.netloc == "careers.blackrock.com" and (
            parsed_url.path.startswith("/search-jobs") or parsed_url.path.startswith("/category/")
        ):
            return self.fetch_blackrock_cards()

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
        if parsed_base.netloc == "job-boards.greenhouse.io":
            return parse_greenhouse_job_board_cards(base_url, soup)
        if parsed_base.netloc == "careers.blackrock.com" and (
            parsed_base.path.startswith("/search-jobs") or parsed_base.path.startswith("/category/")
        ):
            return parse_blackrock_job_search_cards(base_url, soup)
        if parsed_base.netloc == "www.imc.com" and parsed_base.path.startswith(
            "/us/search-careers"
        ):
            return parse_imc_job_search_cards(base_url, soup)
        if parsed_base.netloc == "www.gresearch.com" and parsed_base.path.startswith("/vacancies"):
            return parse_gresearch_cards(base_url, soup)

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

    def fetch_citadel_cards(self, url: str, max_pages: int = 8) -> list[JobCard]:
        cards: list[JobCard] = []
        with httpx.Client(timeout=20.0, follow_redirects=True, headers=BROWSER_HEADERS) as client:
            page = 1
            while page <= max_pages:
                response = request_with_retries(
                    client,
                    "POST",
                    "https://www.citadel.com/wp-admin/admin-ajax.php",
                    data={
                        "selected-job-sections": "388,389,387,390",
                        "current_page": str(page),
                        "sort_order": "DESC",
                        "per_page": "10",
                        "action": "careers_listing_filter",
                    },
                    headers={"Referer": url},
                )
                if response.status_code == 403:
                    if is_cloudflare_challenge(response):
                        raise CareerPageBlockedError("blocked by Cloudflare challenge")
                    raise CareerPageBlockedError("blocked by career site with HTTP 403")
                response.raise_for_status()
                payload = response.json()
                content = str(payload.get("content") or "")
                if not content.strip():
                    break
                cards.extend(parse_citadel_cards(url, BeautifulSoup(content, "html.parser")))
                found_posts = int(payload.get("found_posts") or 0)
                post_per_page = int(
                    payload.get("post_per_page") or payload.get("number_of_post") or 10
                )
                if page * post_per_page >= found_posts:
                    break
                page += 1
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
            position_directories = {str(position_id) for position_id in positions_response.json()}

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

    def fetch_flow_traders_cards(self) -> list[JobCard]:
        with httpx.Client(timeout=20.0, follow_redirects=True, headers=BROWSER_HEADERS) as client:
            response = request_with_retries(
                client,
                "GET",
                "https://boards-api.greenhouse.io/v1/boards/flowtraders/jobs",
            )
            response.raise_for_status()
            payload = response.json()

        cards: list[JobCard] = []
        for job in payload.get("jobs", []):
            if not isinstance(job, dict):
                continue
            title = clean_card_title(str(job.get("title") or ""))
            url = str(job.get("absolute_url") or "")
            location = job.get("location")
            loc = "Unknown"
            if isinstance(location, dict):
                loc = str(location.get("name") or "Unknown")
            if title and url:
                cards.append(JobCard(title=title, loc=loc, url=normalize_url(url, "")))
        return dedupe_cards(cards)

    def fetch_imc_cards(self, url: str) -> list[JobCard]:
        cards: list[JobCard] = []
        urls = [
            url,
            "https://www.imc.com/us/careers/experienced-roles/trading",
        ]
        with httpx.Client(timeout=20.0, follow_redirects=True, headers=BROWSER_HEADERS) as client:
            for page_url in urls:
                response = request_with_retries(client, "GET", page_url)
                response.raise_for_status()
                cards.extend(
                    parse_imc_job_search_cards(
                        page_url, BeautifulSoup(response.text, "html.parser")
                    )
                )
        return dedupe_cards(cards)

    def fetch_sig_cards(self) -> list[JobCard]:
        cards: list[JobCard] = []
        keywords = (
            "quantitative research",
            "quantitative trading",
            "trader",
            "machine learning",
        )
        with httpx.Client(timeout=20.0, follow_redirects=True, headers=BROWSER_HEADERS) as client:
            for keyword in keywords:
                response = request_with_retries(
                    client,
                    "GET",
                    "https://careers.sig.com/api/jobs",
                    params={"keywords": keyword, "limit": "50"},
                )
                response.raise_for_status()
                payload = response.json()
                for row in payload.get("jobs", []):
                    data = row.get("data") if isinstance(row, dict) else None
                    if not isinstance(data, dict):
                        continue
                    title = clean_card_title(str(data.get("title") or ""))
                    slug = str(data.get("slug") or "")
                    loc = str(
                        data.get("full_location")
                        or data.get("location_name")
                        or data.get("short_location")
                        or "Unknown"
                    )
                    if title and slug:
                        cards.append(
                            JobCard(
                                title=title,
                                loc=loc,
                                url=f"https://careers.sig.com/jobs/{slug}",
                            )
                        )
        return dedupe_cards(cards)

    def fetch_jpmorgan_cards(self, page_size: int = 50, max_pages: int = 4) -> list[JobCard]:
        cards: list[JobCard] = []
        with httpx.Client(timeout=20.0, follow_redirects=True, headers=BROWSER_HEADERS) as client:
            for keyword in JPMORGAN_SEARCH_KEYWORDS:
                offset = 0
                pages = 0
                while pages < max_pages:
                    response = request_with_retries(
                        client,
                        "GET",
                        f"{JPMORGAN_BASE_URL}/hcmRestApi/resources/11.13.18.05/"
                        "recruitingCEJobRequisitions",
                        params={
                            "onlyData": "true",
                            "expand": "requisitionList.secondaryLocations",
                            "finder": (
                                "findReqs;"
                                f"siteNumber={JPMORGAN_SITE_NUMBER},"
                                f"limit={page_size},"
                                f'keyword="{keyword}",'
                                f"offset={offset}"
                            ),
                        },
                    )
                    response.raise_for_status()
                    item = first_json_item(response.json())
                    rows = item.get("requisitionList") if isinstance(item, dict) else []
                    if not isinstance(rows, list) or not rows:
                        break
                    cards.extend(jpmorgan_cards_from_rows(rows))
                    total = int(item.get("TotalJobsCount") or 0)
                    offset += page_size
                    pages += 1
                    if offset >= total:
                        break
        return dedupe_cards(cards)

    def fetch_blackrock_cards(self, max_pages_per_query: int = 20) -> list[JobCard]:
        cards: list[JobCard] = []
        with httpx.Client(timeout=20.0, follow_redirects=True, headers=BROWSER_HEADERS) as client:
            for keyword in BLACKROCK_SEARCH_KEYWORDS:
                cards.extend(
                    fetch_blackrock_search_cards(client, keyword, max_pages=max_pages_per_query)
                )
            for url in BLACKROCK_CATEGORY_URLS:
                cards.extend(fetch_blackrock_url_cards(client, url, max_pages=3))
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
        parsed_url = urlparse(url)
        if parsed_url.netloc == "jpmc.fa.oraclecloud.com" and parsed_url.path.startswith(
            "/hcmUI/CandidateExperience/en/sites/CX_1001/job/"
        ):
            return self.fetch_jpmorgan_jd(parsed_url.path.rsplit("/", 1)[-1])
        html = self.fetch_html(url)
        return html_to_text(html)

    def fetch_jpmorgan_jd(self, job_id: str) -> str:
        with httpx.Client(timeout=20.0, follow_redirects=True, headers=BROWSER_HEADERS) as client:
            response = request_with_retries(
                client,
                "GET",
                f"{JPMORGAN_BASE_URL}/hcmRestApi/resources/11.13.18.05/"
                "recruitingCEJobRequisitionDetails",
                params={
                    "expand": "all",
                    "onlyData": "true",
                    "finder": f'ById;Id="{job_id}",siteNumber={JPMORGAN_SITE_NUMBER}',
                },
            )
            response.raise_for_status()
            item = first_json_item(response.json())
        if not isinstance(item, dict):
            return ""
        fields = [
            str(item.get("Title") or ""),
            str(item.get("PrimaryLocation") or ""),
            str(item.get("ExternalDescriptionStr") or ""),
            str(item.get("CorporateDescriptionStr") or ""),
            str(item.get("OrganizationDescriptionStr") or ""),
        ]
        return html_to_text(" | ".join(field for field in fields if field))


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
        loc = next(
            (span for span in spans if "United States" in span), spans[0] if spans else "Unknown"
        )
        cards.append(JobCard(title=title, loc=loc, url=normalize_url(base_url, link["href"])))
    return dedupe_cards(cards)


def parse_citadel_cards(base_url: str, soup: BeautifulSoup) -> list[JobCard]:
    cards: list[JobCard] = []
    for link in soup.select("a.careers-listing-card[href*='/careers/details/']"):
        title = clean_card_title(
            link.get("data-position", "")
            or (link.select_one("h2").get_text(" ", strip=True) if link.select_one("h2") else "")
            or link.get_text(" ", strip=True)
        )
        loc_el = link.select_one(".careers-listing-card__location")
        loc = loc_el.get_text(" ", strip=True) if loc_el else "Unknown"
        if title:
            cards.append(JobCard(title=title, loc=loc, url=normalize_url(base_url, link["href"])))
    if cards:
        return dedupe_cards(cards)

    for link in soup.find_all("a", href=True):
        href = link["href"].strip()
        if "/careers/details/" not in href:
            continue
        title, loc = split_citadel_title_and_location(
            clean_card_title(link.get_text(" ", strip=True))
        )
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
            for span in card.select(
                ".hrt-card-meta-desktop ul.hrt-card-info-list:not(.second-list) span"
            )
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


def parse_greenhouse_job_board_cards(base_url: str, soup: BeautifulSoup) -> list[JobCard]:
    cards: list[JobCard] = []
    for row in soup.select("tr.job-post"):
        link = row.select_one("a[href*='/jobs/']")
        if link is None:
            continue
        title_el = link.select_one(".body--medium")
        loc_el = link.select_one(".body__secondary.body--metadata")
        if title_el is None:
            continue
        for tag in title_el.select(".tag-container"):
            tag.decompose()
        title = clean_card_title(title_el.get_text(" ", strip=True))
        loc = loc_el.get_text(" ", strip=True) if loc_el else "Unknown"
        if title:
            cards.append(JobCard(title=title, loc=loc, url=normalize_url(base_url, link["href"])))
    if cards:
        return dedupe_cards(cards)

    return parse_greenhouse_anchor_cards(base_url, soup)


def parse_greenhouse_anchor_cards(base_url: str, soup: BeautifulSoup) -> list[JobCard]:
    cards: list[JobCard] = []
    for link in soup.find_all("a", href=True):
        href = link["href"].strip()
        if "/jobs/" not in href:
            continue
        title = clean_card_title(link.get_text(" ", strip=True))
        if title:
            cards.append(JobCard(title=title, loc="Unknown", url=normalize_url(base_url, href)))
    return dedupe_cards(cards)


def parse_blackrock_job_search_cards(base_url: str, soup: BeautifulSoup) -> list[JobCard]:
    cards: list[JobCard] = []
    search_links = soup.select(
        "li.section3__search-results-li a.section3__search-results-a[href*='/job/']"
    )
    for link in search_links:
        title_el = link.select_one(".section3__job-title")
        title = clean_card_title(
            title_el.get_text(" ", strip=True) if title_el else link.get_text(" ", strip=True)
        )
        locations = blackrock_result_locations(link)
        loc = "; ".join(locations) if locations else "Unknown"
        if title:
            cards.append(JobCard(title=title, loc=loc, url=normalize_url(base_url, link["href"])))
    if cards:
        return dedupe_cards(cards)

    for link in soup.find_all("a", href=True):
        href = link["href"].strip()
        path = urlparse(normalize_url(base_url, href)).path
        if not path.startswith("/job/"):
            continue
        title, loc = split_blackrock_title_and_location(
            clean_card_title(link.get_text(" ", strip=True))
        )
        if title:
            cards.append(JobCard(title=title, loc=loc, url=normalize_url(base_url, href)))
    return dedupe_cards(cards)


def blackrock_result_locations(link) -> list[str]:
    locations: list[str] = []
    for info in link.select(".section3__job-information"):
        spans = info.find_all("span", recursive=False)
        if len(spans) < 2:
            continue
        label = spans[0].get_text(" ", strip=True).lower()
        if label not in {"location:", "additional locations:"}:
            continue
        value_el = info.select_one(".section3__job-info")
        value = " ".join(
            (
                value_el.get_text(" ", strip=True)
                if value_el
                else spans[-1].get_text(" ", strip=True)
            ).split()
        )
        if value:
            locations.append(value)
    return locations


def fetch_blackrock_search_cards(
    client: httpx.Client, keyword: str, max_pages: int
) -> list[JobCard]:
    cards: list[JobCard] = []
    page = 1
    while page <= max_pages:
        params = {"k": keyword}
        if page > 1:
            params["p"] = str(page)
        response = request_with_retries(
            client,
            "GET",
            f"{BLACKROCK_BASE_URL}/search-jobs",
            params=params,
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        cards.extend(parse_blackrock_job_search_cards(f"{BLACKROCK_BASE_URL}/search-jobs", soup))
        total_pages = blackrock_total_pages(soup)
        if page >= total_pages:
            break
        page += 1
    return cards


def fetch_blackrock_url_cards(client: httpx.Client, url: str, max_pages: int) -> list[JobCard]:
    cards: list[JobCard] = []
    page = 1
    while page <= max_pages:
        params = {"p": str(page)} if page > 1 else None
        response = request_with_retries(client, "GET", url, params=params)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        cards.extend(parse_blackrock_job_search_cards(url, soup))
        total_pages = blackrock_total_pages(soup)
        if page >= total_pages:
            break
        page += 1
    return cards


def blackrock_total_pages(soup: BeautifulSoup) -> int:
    result_section = soup.select_one("#search-results[data-total-pages]")
    if result_section is None:
        return 1
    try:
        return max(int(result_section.get("data-total-pages", "1")), 1)
    except ValueError:
        return 1


def parse_imc_job_search_cards(base_url: str, soup: BeautifulSoup) -> list[JobCard]:
    cards: list[JobCard] = []
    for link in soup.find_all("a", href=True):
        href = link["href"].strip()
        if "/us/careers/jobs/" not in href or href.endswith("/apply"):
            continue
        title = clean_card_title(link.get_text(" ", strip=True))
        if title:
            cards.append(JobCard(title=title, loc="Unknown", url=normalize_url(base_url, href)))
    return dedupe_cards(cards)


def parse_gresearch_cards(base_url: str, soup: BeautifulSoup) -> list[JobCard]:
    cards: list[JobCard] = []
    for link in soup.select("a.c-vacancy-result[href*='/vacancies/']"):
        title_el = link.select_one(".c-vacancy-result__title")
        loc_el = link.select_one(".c-vacancy-result__location")
        title = clean_card_title(
            title_el.get_text(" ", strip=True) if title_el else link.get_text(" ", strip=True)
        )
        loc = loc_el.get_text(" ", strip=True) if loc_el else "Unknown"
        if title:
            cards.append(JobCard(title=title, loc=loc, url=normalize_url(base_url, link["href"])))
    return dedupe_cards(cards)


def jpmorgan_cards_from_rows(rows: list[object]) -> list[JobCard]:
    cards: list[JobCard] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        job_id = str(row.get("Id") or "").strip()
        title = clean_card_title(str(row.get("Title") or ""))
        if not job_id or not title:
            continue
        locations = [str(row.get("PrimaryLocation") or "").strip()]
        secondary = row.get("secondaryLocations") or []
        if isinstance(secondary, list):
            for location in secondary:
                if isinstance(location, dict):
                    locations.append(str(location.get("Name") or "").strip())
        loc = "; ".join(location for location in locations if location) or "Unknown"
        cards.append(JobCard(title=title, loc=loc, url=f"{JPMORGAN_UI_BASE_URL}/job/{job_id}"))
    return cards


def split_blackrock_title_and_location(text: str) -> tuple[str, str]:
    if " Location: " not in text:
        return text, "Unknown"
    title, rest = text.split(" Location: ", 1)
    loc = rest.split(" Team: ", 1)[0].split(" Additional Locations: ", 1)[0].strip()
    return title.strip(), loc or "Unknown"


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


def first_json_item(payload: object) -> object:
    if not isinstance(payload, dict):
        return None
    items = payload.get("items")
    if not isinstance(items, list) or not items:
        return None
    return items[0]


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return " ".join(soup.get_text(" ", strip=True).split())


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
