import httpx
import respx

from quant_job_tracker.crawler.adapters import GenericAdapter, JobCard


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
      <a href="javascript:alert('apply')">Alpha Research Analyst</a>
      <a href="#open-roles">Investment Strategy Associate</a>
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


@respx.mock
def test_generic_adapter_fetches_jd() -> None:
    respx.get("https://example.com/jobs/1").mock(
        return_value=httpx.Response(200, text="<main>Alpha research role</main>")
    )
    adapter = GenericAdapter()

    jd = adapter.fetch_jd("https://example.com/jobs/1")

    assert "Alpha research role" in jd
