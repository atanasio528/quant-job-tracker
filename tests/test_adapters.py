import httpx
import respx

from quant_job_tracker.crawler.adapters import CareerPageBlockedError, GenericAdapter, JobCard


def test_generic_adapter_extracts_links_from_html() -> None:
    html = """
    <html><body>
      <a href="/jobs/1">Quantitative Researcher</a>
      <a href="/jobs/2">Compliance Analyst</a>
    </body></html>
    """
    adapter = GenericAdapter()
    cards = adapter.parse_cards("https://example.com/careers", html)

    assert JobCard(
        title="Quantitative Researcher", loc="Unknown", url="https://example.com/jobs/1"
    ) in cards
    assert JobCard(
        title="Compliance Analyst", loc="Unknown", url="https://example.com/jobs/2"
    ) in cards


def test_generic_adapter_ignores_non_http_links_with_relevant_keywords() -> None:
    html = """
    <html><body>
      <a href="mailto:jobs@example.com">Quantitative Researcher</a>
      <a href=" mailto:quant@example.com">Quant Developer</a>
      <a href="javascript:alert('apply')">Alpha Research Analyst</a>
      <a href=" javascript:void(0)">Quant Portfolio Researcher</a>
      <a href="#open-roles">Investment Strategy Associate</a>
      <a href="/jobs/1">Quant Trader</a>
    </body></html>
    """
    adapter = GenericAdapter()
    cards = adapter.parse_cards("https://example.com/careers", html)

    assert cards == [
        JobCard(title="Quant Trader", loc="Unknown", url="https://example.com/jobs/1")
    ]


def test_generic_adapter_ignores_blank_hrefs_with_relevant_keywords() -> None:
    html = """
    <html><body>
      <a href="">Quantitative Researcher</a>
      <a href="   ">Quantitative Researcher</a>
      <a href="/jobs/1">Quant Trader</a>
    </body></html>
    """
    adapter = GenericAdapter()
    cards = adapter.parse_cards("https://example.com/careers", html)

    assert cards == [
        JobCard(title="Quant Trader", loc="Unknown", url="https://example.com/jobs/1")
    ]


def test_generic_adapter_deduplicates_cards_by_absolute_url() -> None:
    html = """
    <html><body>
      <a href="/jobs/1">Quantitative Researcher</a>
      <a href="https://example.com/jobs/1">Senior Quant Researcher</a>
      <a href="/jobs/2">Algorithm Trader</a>
    </body></html>
    """
    adapter = GenericAdapter()
    cards = adapter.parse_cards("https://example.com/careers", html)

    assert cards == [
        JobCard(
            title="Quantitative Researcher",
            loc="Unknown",
            url="https://example.com/jobs/1",
        ),
        JobCard(title="Algorithm Trader", loc="Unknown", url="https://example.com/jobs/2"),
    ]


def test_generic_adapter_deduplicates_fragment_variants() -> None:
    html = """
    <html><body>
      <a href="/jobs/1">Quantitative Researcher</a>
      <a href="/jobs/1#apply">Senior Quant Researcher</a>
    </body></html>
    """
    adapter = GenericAdapter()
    cards = adapter.parse_cards("https://example.com/careers", html)

    assert cards == [
        JobCard(
            title="Quantitative Researcher",
            loc="Unknown",
            url="https://example.com/jobs/1",
        )
    ]


def test_generic_adapter_cleans_card_icon_and_preview_description() -> None:
    html = """
    <html><body>
      <a href="/careers/proprietary-trading-intern-new-york-summer-2027-5731">
        icon Proprietary Trading Intern (New York) – Summer 2027 : The D. E. Shaw group seeks talented individuals with unique perspectives to join the firm as proprietary trading interns.
      </a>
    </body></html>
    """
    adapter = GenericAdapter()
    cards = adapter.parse_cards("https://www.deshaw.com/careers", html)

    assert cards == [
        JobCard(
            title="Proprietary Trading Intern (New York) – Summer 2027",
            loc="Unknown",
            url="https://www.deshaw.com/careers/proprietary-trading-intern-new-york-summer-2027-5731",
        )
    ]


@respx.mock
def test_generic_adapter_fetches_jd() -> None:
    respx.get("https://example.com/jobs/1").mock(
        return_value=httpx.Response(200, text="<main>Alpha research role</main>")
    )
    adapter = GenericAdapter()

    jd = adapter.fetch_jd("https://example.com/jobs/1")

    assert "Alpha research role" in jd


@respx.mock
def test_generic_adapter_sends_browser_headers() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        assert "Mozilla/5.0" in request.headers["user-agent"]
        assert "text/html" in request.headers["accept"]
        assert request.headers["accept-language"].startswith("en-US")
        return httpx.Response(200, text="<main>Quant Researcher</main>")

    respx.get("https://example.com/careers").mock(side_effect=respond)
    adapter = GenericAdapter()

    html = adapter.fetch_html("https://example.com/careers")

    assert "Quant Researcher" in html


@respx.mock
def test_generic_adapter_raises_blocked_for_cloudflare_challenge() -> None:
    respx.get("https://example.com/careers").mock(
        return_value=httpx.Response(
            403,
            headers={"cf-mitigated": "challenge"},
            text="<!doctype html><title>Just a moment...</title>",
        )
    )
    adapter = GenericAdapter()

    try:
        adapter.fetch_html("https://example.com/careers")
    except CareerPageBlockedError as exc:
        assert "Cloudflare" in str(exc)
    else:
        raise AssertionError("expected CareerPageBlockedError")


@respx.mock
def test_generic_adapter_raises_blocked_for_plain_403() -> None:
    respx.get("https://example.com/careers").mock(
        return_value=httpx.Response(403, text="403 - Forbidden")
    )
    adapter = GenericAdapter()

    try:
        adapter.fetch_html("https://example.com/careers")
    except CareerPageBlockedError as exc:
        assert "HTTP 403" in str(exc)
    else:
        raise AssertionError("expected CareerPageBlockedError")
