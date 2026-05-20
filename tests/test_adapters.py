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


@respx.mock
def test_generic_adapter_fetches_jd() -> None:
    respx.get("https://example.com/jobs/1").mock(
        return_value=httpx.Response(200, text="<main>Alpha research role</main>")
    )
    adapter = GenericAdapter()

    jd = adapter.fetch_jd("https://example.com/jobs/1")

    assert "Alpha research role" in jd
