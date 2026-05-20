import httpx
import respx

from quant_job_tracker.crawler.adapters import (
    CareerPageBlockedError,
    GenericAdapter,
    JobCard,
    clean_stored_title,
)


def test_generic_adapter_extracts_links_from_html() -> None:
    html = """
    <html><body>
      <a href="/jobs/1">Quantitative Researcher</a>
      <a href="/jobs/2">Compliance Analyst</a>
    </body></html>
    """
    adapter = GenericAdapter()
    cards = adapter.parse_cards("https://example.com/careers", html)

    assert (
        JobCard(title="Quantitative Researcher", loc="Unknown", url="https://example.com/jobs/1")
        in cards
    )
    assert (
        JobCard(title="Compliance Analyst", loc="Unknown", url="https://example.com/jobs/2")
        in cards
    )


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

    assert cards == [JobCard(title="Quant Trader", loc="Unknown", url="https://example.com/jobs/1")]


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

    assert cards == [JobCard(title="Quant Trader", loc="Unknown", url="https://example.com/jobs/1")]


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


def test_adapter_parses_deshaw_real_job_cards_and_locations() -> None:
    html = """
    <html><body>
      <a href="/what-we-do/investment-management">Investment Management</a>
      <div class="job" data-job-id="5731">
        <div class="information">
          <p class="category">Trading</p>
          <span class="location">New York</span>
        </div>
        <div class="description-wrapper">
          <a id="job-description-a-tag" href="/careers/proprietary-trading-intern-new-york-summer-2027-5731">
            <span class="job-display-name">Proprietary Trading Intern (New York) – Summer 2027</span>
          </a>
        </div>
      </div>
    </body></html>
    """
    adapter = GenericAdapter()

    cards = adapter.parse_cards("https://www.deshaw.com/careers", html)

    assert cards == [
        JobCard(
            title="Proprietary Trading Intern (New York) – Summer 2027",
            loc="New York",
            url="https://www.deshaw.com/careers/proprietary-trading-intern-new-york-summer-2027-5731",
        )
    ]


def test_adapter_parses_two_sigma_open_roles_and_ignores_marketing_links() -> None:
    html = """
    <html><body>
      <a href="https://www.twosigma.com/businesses/investment-management/">Investment Management</a>
      <article class="article article--result">
        <h3 class="article__header__text__title">
          <a class="link" href="https://careers.twosigma.com/careers/JobDetail/New-York-New-York-United-States-Data-Scientist-Campus-Full-Time/13662">
            Data Scientist - Campus Full-Time
          </a>
        </h3>
        <div class="article__header__content__text">
          <span class="paragraph_inner-span">United States - NY New York</span>
          <span class="paragraph_inner-span">Data Science</span>
          <span class="paragraph_inner-span">Early Careers</span>
        </div>
      </article>
    </body></html>
    """
    adapter = GenericAdapter()

    cards = adapter.parse_cards("https://careers.twosigma.com/careers/OpenRoles", html)

    assert cards == [
        JobCard(
            title="Data Scientist - Campus Full-Time",
            loc="United States - NY New York",
            url="https://careers.twosigma.com/careers/JobDetail/New-York-New-York-United-States-Data-Scientist-Campus-Full-Time/13662",
        )
    ]


def test_adapter_parses_greenhouse_job_board_rows_with_locations() -> None:
    html = """
    <html><body>
      <table>
        <tr class="job-post">
          <td class="cell">
            <a href="https://job-boards.greenhouse.io/xtxmarketstechnologies/jobs/6274458003">
              <p class="body body--medium">AI Research Internship - XTY Labs</p>
              <p class="body body__secondary body--metadata">New York</p>
            </a>
          </td>
        </tr>
        <tr class="job-post">
          <td class="cell">
            <a href="https://job-boards.greenhouse.io/xtxmarketstechnologies/jobs/7727030003">
              <p class="body body--medium">Software Engineer - Trading Data Technology</p>
              <p class="body body__secondary body--metadata">London, England, United Kingdom</p>
            </a>
          </td>
        </tr>
      </table>
    </body></html>
    """
    adapter = GenericAdapter()

    cards = adapter.parse_cards("https://job-boards.greenhouse.io/xtxmarketstechnologies", html)

    assert cards == [
        JobCard(
            title="AI Research Internship - XTY Labs",
            loc="New York",
            url="https://job-boards.greenhouse.io/xtxmarketstechnologies/jobs/6274458003",
        ),
        JobCard(
            title="Software Engineer - Trading Data Technology",
            loc="London, England, United Kingdom",
            url="https://job-boards.greenhouse.io/xtxmarketstechnologies/jobs/7727030003",
        ),
    ]


def test_adapter_parses_blackrock_job_search_and_rejects_career_blogs() -> None:
    html = """
    <html><body>
      <a href="/job/new-york/security-modeling-quant-developer-associate/45831/1">
        Security Modeling Quant Developer - Associate
        Location: New York, NY
        Team: Financial Engineering
      </a>
      <a href="/blog-samara-cohen-chief-investment-officer-eii">
        Samara Cohen: BlackRock's Newly Named Chief Investment Officer of EII
      </a>
    </body></html>
    """
    adapter = GenericAdapter()

    cards = adapter.parse_cards("https://careers.blackrock.com/search-jobs/quant", html)

    assert cards == [
        JobCard(
            title="Security Modeling Quant Developer - Associate",
            loc="New York, NY",
            url="https://careers.blackrock.com/job/new-york/security-modeling-quant-developer-associate/45831/1",
        )
    ]


def test_adapter_parses_imc_job_search_and_rejects_marketing_links() -> None:
    html = """
    <html><body>
      <a href="/us/strategic-investments">Strategic Investments</a>
      <a href="/us/careers/jobs/4382558101">
        Quantitative Researcher – Equities
        Experienced
        Trading
        Chicago, New York
      </a>
    </body></html>
    """
    adapter = GenericAdapter()

    cards = adapter.parse_cards("https://www.imc.com/us/search-careers", html)

    assert cards == [
        JobCard(
            title="Quantitative Researcher – Equities Experienced Trading Chicago, New York",
            loc="Unknown",
            url="https://www.imc.com/us/careers/jobs/4382558101",
        )
    ]


@respx.mock
def test_adapter_fetches_imc_search_and_trading_surfaces() -> None:
    search_html = """
    <html><body>
      <a href="/us/careers/jobs/4608590101">Graduate Broker Trader Graduate Trading Chicago</a>
    </body></html>
    """
    trading_html = """
    <html><body>
      <a href="/us/careers/jobs/4382558101">
        Quantitative Researcher – Equities Experienced Trading Chicago, New York
      </a>
      <a href="/us/careers/jobs/4608590101">Graduate Broker Trader Graduate Trading Chicago</a>
    </body></html>
    """
    respx.get("https://www.imc.com/us/search-careers").mock(
        return_value=httpx.Response(200, text=search_html)
    )
    respx.get("https://www.imc.com/us/careers/experienced-roles/trading").mock(
        return_value=httpx.Response(200, text=trading_html)
    )
    adapter = GenericAdapter()

    cards = adapter.fetch_cards("https://www.imc.com/us/search-careers")

    assert cards == [
        JobCard(
            title="Graduate Broker Trader Graduate Trading Chicago",
            loc="Unknown",
            url="https://www.imc.com/us/careers/jobs/4608590101",
        ),
        JobCard(
            title="Quantitative Researcher – Equities Experienced Trading Chicago, New York",
            loc="Unknown",
            url="https://www.imc.com/us/careers/jobs/4382558101",
        ),
    ]


@respx.mock
def test_adapter_fetches_sig_jobs_from_official_api() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        keyword = request.url.params.get("keywords")
        jobs = {
            "quantitative research": [
                {
                    "data": {
                        "slug": "9438",
                        "title": "Quantitative Researcher – Master's: 2026",
                        "full_location": "New York, New York, United States",
                    }
                }
            ],
            "trader": [
                {
                    "data": {
                        "slug": "10717",
                        "title": "Quantitative Trader Internship: Summer 2027",
                        "full_location": "Bala Cynwyd (Philadelphia Area), Pennsylvania, United States",
                    }
                }
            ],
        }.get(keyword, [])
        return httpx.Response(200, json={"jobs": jobs})

    respx.get("https://careers.sig.com/api/jobs").mock(side_effect=respond)
    adapter = GenericAdapter()

    cards = adapter.fetch_cards("https://careers.sig.com/")

    assert cards == [
        JobCard(
            title="Quantitative Researcher – Master's: 2026",
            loc="New York, New York, United States",
            url="https://careers.sig.com/jobs/9438",
        ),
        JobCard(
            title="Quantitative Trader Internship: Summer 2027",
            loc="Bala Cynwyd (Philadelphia Area), Pennsylvania, United States",
            url="https://careers.sig.com/jobs/10717",
        ),
    ]


@respx.mock
def test_adapter_fetches_flow_traders_from_official_greenhouse_api() -> None:
    respx.get("https://boards-api.greenhouse.io/v1/boards/flowtraders/jobs").mock(
        return_value=httpx.Response(
            200,
            json={
                "jobs": [
                    {
                        "title": "Trading Intern",
                        "absolute_url": "https://job-boards.greenhouse.io/flowtraders/jobs/1",
                        "location": {"name": "New York"},
                    },
                    {
                        "title": "Business Support Analyst",
                        "absolute_url": "https://job-boards.greenhouse.io/flowtraders/jobs/2",
                        "location": {"name": "Amsterdam"},
                    },
                ]
            },
        )
    )
    adapter = GenericAdapter()

    cards = adapter.fetch_cards("https://www.flowtraders.com/careers/job-search/")

    assert cards == [
        JobCard(
            title="Trading Intern",
            loc="New York",
            url="https://job-boards.greenhouse.io/flowtraders/jobs/1",
        ),
        JobCard(
            title="Business Support Analyst",
            loc="Amsterdam",
            url="https://job-boards.greenhouse.io/flowtraders/jobs/2",
        ),
    ]


def test_adapter_parses_citadel_detail_links_only() -> None:
    html = """
    <html><body>
      <a href="/careers/quantitative-research/">Quantitative Research</a>
      <a href="/careers/details/quantitative-researcher-phd-intern-us/">
        Quantitative Researcher – PhD Intern (US) Greenwich, Miami, New York Apply Now
      </a>
    </body></html>
    """
    adapter = GenericAdapter()

    cards = adapter.parse_cards("https://www.citadel.com/careers/open-opportunities/", html)

    assert cards == [
        JobCard(
            title="Quantitative Researcher – PhD Intern (US)",
            loc="Greenwich, Miami, New York",
            url="https://www.citadel.com/careers/details/quantitative-researcher-phd-intern-us/",
        )
    ]


def test_adapter_parses_citadel_ajax_listing_cards() -> None:
    html = """
    <html><body>
      <a
        class="careers-listing-card js-career-card js-apply-now"
        href="https://www.citadel.com/careers/details/quantitative-researcher-phd-intern-us/"
        data-position="Quantitative Researcher – PhD Intern (US)"
      >
        <div class="careers-listing-card__title">
          <h2>Quantitative Researcher – PhD Intern (US)</h2>
        </div>
        <span class="careers-listing-card__location">Greenwich, Miami, New York</span>
        <span>Apply Now</span>
      </a>
    </body></html>
    """
    adapter = GenericAdapter()

    cards = adapter.parse_cards("https://www.citadel.com/careers/open-opportunities/", html)

    assert cards == [
        JobCard(
            title="Quantitative Researcher – PhD Intern (US)",
            loc="Greenwich, Miami, New York",
            url="https://www.citadel.com/careers/details/quantitative-researcher-phd-intern-us/",
        )
    ]


@respx.mock
def test_adapter_fetches_citadel_cards_from_official_ajax() -> None:
    first_page = """
    <div class="career-listing__container">
      <a class="careers-listing-card" href="https://www.citadel.com/careers/details/quantitative-researcher-phd-intern-us/" data-position="Quantitative Researcher – PhD Intern (US)">
        <span class="careers-listing-card__location">Greenwich, Miami, New York</span>
      </a>
    </div>
    """
    second_page = """
    <div class="career-listing__container">
      <a class="careers-listing-card" href="https://www.citadel.com/careers/details/quantitative-research-analyst-intern-bs-ms-us/" data-position="Quantitative Research Analyst Intern – BS/MS (US)">
        <span class="careers-listing-card__location">Miami, New York</span>
      </a>
    </div>
    """
    route = respx.post("https://www.citadel.com/wp-admin/admin-ajax.php").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "number_of_post": 1,
                    "found_posts": 2,
                    "post_per_page": 1,
                    "page_number": 1,
                    "content": first_page,
                },
            ),
            httpx.Response(
                200,
                json={
                    "number_of_post": 1,
                    "found_posts": 2,
                    "post_per_page": 1,
                    "page_number": 2,
                    "content": second_page,
                },
            ),
        ]
    )
    adapter = GenericAdapter()

    cards = adapter.fetch_cards("https://www.citadel.com/careers/open-opportunities/")

    assert cards == [
        JobCard(
            title="Quantitative Researcher – PhD Intern (US)",
            loc="Greenwich, Miami, New York",
            url="https://www.citadel.com/careers/details/quantitative-researcher-phd-intern-us/",
        ),
        JobCard(
            title="Quantitative Research Analyst Intern – BS/MS (US)",
            loc="Miami, New York",
            url="https://www.citadel.com/careers/details/quantitative-research-analyst-intern-bs-ms-us/",
        ),
    ]
    assert route.call_count == 2


@respx.mock
def test_adapter_fetches_jane_street_jobs_from_official_json() -> None:
    respx.get("https://www.janestreet.com/jobs/main.json").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "id": 1,
                    "position": "Quantitative Trader",
                    "category": "Trading, Research, and Machine Learning",
                    "availability": "Full-Time: New Grad",
                    "city": "NYC",
                },
                {
                    "id": 2,
                    "position": "Unlisted Role",
                    "category": "Technology",
                    "availability": "Full-Time: Experienced",
                    "city": "LDN",
                },
            ],
        )
    )
    respx.get("https://www.janestreet.com/static/position-directories.json").mock(
        return_value=httpx.Response(200, json=["1"])
    )
    adapter = GenericAdapter()

    cards = adapter.fetch_cards("https://www.janestreet.com/join-jane-street/open-roles/")

    assert cards == [
        JobCard(
            title="Quantitative Trader",
            loc="New York",
            url="https://www.janestreet.com/join-jane-street/position/1/",
        )
    ]


@respx.mock
def test_adapter_fetches_hrt_jobs_from_official_ajax() -> None:
    career_html = """
    <html><body>
      <div class="hrt-card-wrapper" data-filters-settings='{"meta_data":[],"settings":{"hide_job_id":true}}'></div>
    </body></html>
    """
    card_html = """
    <div class="hrt-card-item">
      <div class="hrt-card-title-wrap">
        <a class="hrt-card-title" href="https://www.hudsonrivertrading.com/hrt-job/algorithm-developer/">Algorithm Developer</a>
      </div>
      <div class="hrt-card-meta-desktop">
        <ul class="hrt-card-info-list">
          <li class="hrt-card-info-item"><span>New York</span></li>
          <li class="hrt-card-info-item"><span>Chicago</span></li>
        </ul>
        <ul class="hrt-card-info-list second-list">
          <li class="hrt-card-info-item"><span>Strategy Development</span></li>
        </ul>
      </div>
    </div>
    """
    respx.get("https://www.hudsonrivertrading.com/careers/").mock(
        return_value=httpx.Response(200, text=career_html)
    )
    respx.post("https://www.hudsonrivertrading.com/wp-admin/admin-ajax.php").mock(
        return_value=httpx.Response(200, json=[{"content": card_html}])
    )
    adapter = GenericAdapter()

    cards = adapter.fetch_cards("https://www.hudsonrivertrading.com/careers/")

    assert cards == [
        JobCard(
            title="Algorithm Developer",
            loc="New York, Chicago",
            url="https://www.hudsonrivertrading.com/hrt-job/algorithm-developer/",
        )
    ]


@respx.mock
def test_adapter_retries_transient_fetch_html_timeout() -> None:
    route = respx.get("https://example.com/jobs/quant").mock(
        side_effect=[
            httpx.ConnectTimeout("handshake timed out"),
            httpx.Response(200, text="<html>Quant Researcher</html>"),
        ]
    )
    adapter = GenericAdapter()

    html = adapter.fetch_html("https://example.com/jobs/quant")

    assert html == "<html>Quant Researcher</html>"
    assert route.call_count == 2


def test_clean_stored_title_strips_summary_preview() -> None:
    title = (
        "Senior Analyst, Equity Data Science Summary: PanAgora seeks to integrate a Sr. "
        "Analyst to work closely with the Alpha Research team. Read Post"
    )
    jd = "Senior Analyst, Equity Data Science | PanAgora Careers"

    assert clean_stored_title(title, jd) == "Senior Analyst, Equity Data Science"


def test_clean_stored_title_strips_marketing_copy() -> None:
    title = (
        "Asset Management Provides investment management solutions across all major asset "
        "classes to a diverse set of institutional and individual clients."
    )
    jd = "Careers in Asset Management | Goldman Sachs"

    assert clean_stored_title(title, jd) == "Careers in Asset Management"


def test_clean_stored_title_strips_category_marketing_copy() -> None:
    title = (
        "Quantitative Research Quantitative Research Build predictive models to better "
        "understand dynamic global markets. Explore Working as a Quantitative Researcher"
    )
    jd = "Quantitative Research | Citadel"

    assert clean_stored_title(title, jd) == "Quantitative Research"


def test_clean_stored_title_strips_company_description_copy() -> None:
    title = (
        "Senior Quantitative Trader - Delta One Trading & Quant Chicago Trading Company "
        "(CTC) is a premier proprietary trading firm specializing in options market making"
    )
    jd = "Senior Quantitative Trader - Delta One Trading & Quant | Chicago Trading Company"

    assert clean_stored_title(title, jd) == "Senior Quantitative Trader - Delta One Trading & Quant"


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
