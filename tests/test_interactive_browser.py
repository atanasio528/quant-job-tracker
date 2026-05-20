import pytest

from quant_job_tracker.crawler.adapters import CareerPageBlockedError, JobCard
from quant_job_tracker.crawler.interactive_browser import (
    InteractiveBrowserAdapter,
    ManualChallengeSession,
    looks_like_cloudflare_challenge,
)


class BlockedFallback:
    def fetch_cards(self, url: str) -> list[JobCard]:
        raise CareerPageBlockedError("blocked by Cloudflare challenge")

    def fetch_jd(self, url: str) -> str:
        raise CareerPageBlockedError("blocked by Cloudflare challenge")


class FakeBrowserSession:
    def __init__(self, html_by_url: dict[str, str]) -> None:
        self.html_by_url = html_by_url
        self.urls: list[str] = []
        self.closed = False

    def fetch_html(self, url: str) -> str:
        self.urls.append(url)
        return self.html_by_url[url]

    def close(self) -> None:
        self.closed = True


def test_interactive_adapter_uses_browser_for_blocked_citadel_cards() -> None:
    session = FakeBrowserSession(
        {
            "https://www.citadel.com/careers/open-opportunities/": """
            <html><body>
              <a href="/careers/details/quantitative-researcher-phd-intern-us/">
                Quantitative Researcher – PhD Intern (US) Greenwich, Miami, New York Apply Now
              </a>
            </body></html>
            """
        }
    )
    adapter = InteractiveBrowserAdapter(fallback=BlockedFallback(), browser=session)

    cards = adapter.fetch_cards("https://www.citadel.com/careers/open-opportunities/")

    assert cards == [
        JobCard(
            title="Quantitative Researcher – PhD Intern (US)",
            loc="Greenwich, Miami, New York",
            url="https://www.citadel.com/careers/details/quantitative-researcher-phd-intern-us/",
        )
    ]
    assert session.urls == ["https://www.citadel.com/careers/open-opportunities/"]


def test_interactive_adapter_uses_browser_for_blocked_citadel_jd() -> None:
    session = FakeBrowserSession(
        {
            "https://www.citadel.com/careers/details/quantitative-researcher-phd-intern-us/": """
            <html>
              <head><style>.hidden{}</style></head>
              <body><h1>Quantitative Researcher</h1><script>ignore()</script><p>Alpha role.</p></body>
            </html>
            """
        }
    )
    adapter = InteractiveBrowserAdapter(fallback=BlockedFallback(), browser=session)

    jd = adapter.fetch_jd(
        "https://www.citadel.com/careers/details/quantitative-researcher-phd-intern-us/"
    )

    assert jd == "Quantitative Researcher Alpha role."


def test_interactive_adapter_does_not_use_browser_for_non_citadel_block() -> None:
    session = FakeBrowserSession({"https://example.com/careers": "<html></html>"})
    adapter = InteractiveBrowserAdapter(fallback=BlockedFallback(), browser=session)

    with pytest.raises(CareerPageBlockedError):
        adapter.fetch_cards("https://example.com/careers")

    assert session.urls == []


def test_interactive_adapter_closes_browser_session() -> None:
    session = FakeBrowserSession({})
    adapter = InteractiveBrowserAdapter(fallback=BlockedFallback(), browser=session)

    adapter.close()

    assert session.closed is True


def test_looks_like_cloudflare_challenge_detects_challenge_html() -> None:
    assert looks_like_cloudflare_challenge("<title>Just a moment...</title>", "Just a moment...")
    assert looks_like_cloudflare_challenge("<html><body>cf-mitigated challenge</body></html>", "")
    assert not looks_like_cloudflare_challenge("<html><body>Open Opportunities</body></html>", "")


def test_manual_challenge_session_prompts_once_and_returns_after_challenge_clears() -> None:
    prompts: list[str] = []
    enters = 0
    html_pages = [
        "<html><title>Just a moment...</title></html>",
        "<html><body>Open Opportunities</body></html>",
    ]

    def get_html(url: str) -> tuple[str, str]:
        html = html_pages.pop(0)
        title = "Just a moment..." if "Just a moment" in html else "Open Opportunities"
        return html, title

    def wait_for_user(prompt: str) -> None:
        nonlocal enters
        prompts.append(prompt)
        enters += 1

    session = ManualChallengeSession(get_html=get_html, wait_for_user=wait_for_user)

    html = session.fetch_html("https://www.citadel.com/careers/open-opportunities/")

    assert html == "<html><body>Open Opportunities</body></html>"
    assert enters == 1
    assert "Please solve it in the browser" in prompts[0]


def test_manual_challenge_session_raises_if_challenge_remains() -> None:
    def get_html(url: str) -> tuple[str, str]:
        return "<html><title>Just a moment...</title></html>", "Just a moment..."

    session = ManualChallengeSession(get_html=get_html, wait_for_user=lambda prompt: None)

    with pytest.raises(CareerPageBlockedError, match="still visible"):
        session.fetch_html("https://www.citadel.com/careers/open-opportunities/")
