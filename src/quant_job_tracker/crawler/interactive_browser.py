from collections.abc import Callable
from typing import Protocol
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from quant_job_tracker.crawler.adapters import (
    CareerPageBlockedError,
    GenericAdapter,
    JobCard,
)

CITADEL_HOSTS = {"www.citadel.com", "www.citadelsecurities.com"}


class BrowserSession(Protocol):
    def fetch_html(self, url: str) -> str: ...

    def close(self) -> None: ...


class InteractiveBrowserAdapter:
    def __init__(
        self,
        fallback: GenericAdapter | None = None,
        browser: BrowserSession | None = None,
    ) -> None:
        self.fallback = fallback or GenericAdapter()
        self.browser = browser or SeleniumBrowserSession()
        self.parser = self.fallback if hasattr(self.fallback, "parse_cards") else GenericAdapter()

    def fetch_cards(self, url: str) -> list[JobCard]:
        try:
            return self.fallback.fetch_cards(url)
        except CareerPageBlockedError:
            if not is_supported_interactive_url(url):
                raise
            html = self.browser.fetch_html(url)
            return self.parser.parse_cards(url, html)

    def fetch_jd(self, url: str) -> str:
        try:
            return self.fallback.fetch_jd(url)
        except CareerPageBlockedError:
            if not is_supported_interactive_url(url):
                raise
            html = self.browser.fetch_html(url)
            return html_to_text(html)

    def close(self) -> None:
        self.browser.close()


class ManualChallengeSession:
    def __init__(
        self,
        get_html: Callable[[str], tuple[str, str]],
        wait_for_user: Callable[[str], None],
    ) -> None:
        self.get_html = get_html
        self.wait_for_user = wait_for_user

    def fetch_html(self, url: str) -> str:
        html, title = self.get_html(url)
        if not looks_like_cloudflare_challenge(html, title):
            return html

        self.wait_for_user(
            "Cloudflare challenge detected. Please solve it in the browser, "
            "then return here and press Enter."
        )
        html, title = self.get_html(url)
        if looks_like_cloudflare_challenge(html, title):
            raise CareerPageBlockedError("Cloudflare challenge still visible after manual step")
        return html

    def close(self) -> None:
        return None


class SeleniumBrowserSession:
    def __init__(
        self,
        output_fn: Callable[[str], None] = print,
        input_fn: Callable[[str], str] = input,
    ) -> None:
        self.output_fn = output_fn
        self.input_fn = input_fn
        self._driver = None

    def fetch_html(self, url: str) -> str:
        driver = self._get_driver()
        driver.get(url)
        html, title = self._current_html()
        if not looks_like_cloudflare_challenge(html, title):
            return html

        self.output_fn(
            "\nCloudflare challenge detected for "
            f"{url}\nPlease solve it in the browser window, then come back here."
        )
        self.input_fn("Press Enter after you finish the browser challenge...")
        html, title = self._current_html()
        if looks_like_cloudflare_challenge(html, title):
            raise CareerPageBlockedError("Cloudflare challenge still visible after manual step")
        return html

    def close(self) -> None:
        if self._driver is not None:
            self._driver.quit()
            self._driver = None

    def _get_driver(self):
        if self._driver is not None:
            return self._driver
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "Selenium is required for --interactive-browser. "
                "Install it with: python3 -m pip install selenium"
            ) from exc

        options = Options()
        options.add_argument("--start-maximized")
        self._driver = webdriver.Chrome(options=options)
        return self._driver

    def _current_html(self) -> tuple[str, str]:
        driver = self._get_driver()
        return driver.page_source, driver.title


def is_supported_interactive_url(url: str) -> bool:
    return urlparse(url).netloc in CITADEL_HOSTS


def looks_like_cloudflare_challenge(html: str, title: str) -> bool:
    text = f"{title}\n{html[:5000]}".lower()
    return any(
        marker in text
        for marker in (
            "just a moment",
            "cf-mitigated",
            "checking if the site connection is secure",
            "verify you are human",
            "cloudflare",
        )
    )


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return " ".join(soup.get_text(" ", strip=True).split())
