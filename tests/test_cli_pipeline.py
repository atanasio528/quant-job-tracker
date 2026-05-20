from datetime import datetime, timedelta
from pathlib import Path

import httpx
from typer.testing import CliRunner

from quant_job_tracker.crawler.adapters import JobCard
from quant_job_tracker.crawler.categories import CANONICAL_CATEGORIES, category_for_group
from quant_job_tracker.crawler.job_sources import JOB_SOURCE_SEEDS
from quant_job_tracker.crawler.seeds import CompanySeed
from quant_job_tracker.crawler.seeds import SEEDS
from quant_job_tracker.crawler.service import close_stale_jobs, hash_jd, upsert_crawled_job
from quant_job_tracker.db import create_session, init_db
from quant_job_tracker.models import Company, CompanyJobSource, Eval, Job, Run


runner = CliRunner()


def test_cli_app_imports() -> None:
    from quant_job_tracker.cli import app

    assert app.info.name == "qjt"


def test_init_db_command_creates_sqlite_file(tmp_path: Path) -> None:
    from quant_job_tracker.cli import app

    db_path = tmp_path / "qjt.sqlite3"

    result = runner.invoke(app, ["init-db", "--db", str(db_path)])

    assert result.exit_code == 0
    assert "Initialized" in result.output
    assert db_path.exists()


def test_collect_sources_command_stores_curated_job_sources(tmp_path: Path) -> None:
    from quant_job_tracker.cli import app

    db_path = tmp_path / "qjt.sqlite3"

    result = runner.invoke(app, ["collect-sources", "--db", str(db_path)])

    assert result.exit_code == 0
    assert "Stored" in result.output
    with create_session(db_path) as session:
        assert session.query(CompanyJobSource).count() > 0
        deshaw = session.query(CompanyJobSource).filter_by(company="D. E. Shaw").one()
        assert deshaw.source_url == "https://www.deshaw.com/careers"
        assert "/careers/" in deshaw.url_patterns
        flow = session.query(CompanyJobSource).filter_by(company="Flow Traders").one()
        assert flow.source_url == "https://www.flowtraders.com/careers/job-search/"
        assert "/careers/job-search/" in flow.url_patterns
        two_sigma = session.query(CompanyJobSource).filter_by(company="Two Sigma").one()
        assert two_sigma.source_url == "https://careers.twosigma.com/careers/OpenRoles"
        assert "/careers/JobDetail/" in two_sigma.url_patterns


def test_collect_sources_command_retires_stale_source_urls(tmp_path: Path) -> None:
    from quant_job_tracker.cli import app

    db_path = tmp_path / "qjt.sqlite3"
    init_db(db_path)
    with create_session(db_path) as session:
        for company_name, stale_url in [
            ("Flow Traders", "https://www.flowtraders.com/careers/jobs"),
            ("Two Sigma", "https://www.twosigma.com/careers/"),
        ]:
            company = Company(
                name=company_name,
                group="prop",
                career_url=stale_url,
                active=True,
            )
            session.add(company)
            session.flush()
            session.add(
                CompanyJobSource(
                    company_id=company.id,
                    company=company_name,
                    source_url=stale_url,
                    source_type="official_careers",
                    url_patterns="/careers/",
                    active=True,
                )
            )
        session.commit()

    result = runner.invoke(app, ["collect-sources", "--db", str(db_path)])

    assert result.exit_code == 0
    with create_session(db_path) as session:
        flow_active = (
            session.query(CompanyJobSource).filter_by(company="Flow Traders", active=True).all()
        )
        assert [row.source_url for row in flow_active] == [
            "https://www.flowtraders.com/careers/job-search/"
        ]
        two_sigma_active = (
            session.query(CompanyJobSource).filter_by(company="Two Sigma", active=True).all()
        )
        assert [row.source_url for row in two_sigma_active] == [
            "https://careers.twosigma.com/careers/OpenRoles"
        ]


def test_sources_command_lists_stored_job_sources(tmp_path: Path) -> None:
    from quant_job_tracker.cli import app

    db_path = tmp_path / "qjt.sqlite3"
    runner.invoke(app, ["collect-sources", "--db", str(db_path)])

    result = runner.invoke(app, ["sources", "--db", str(db_path)])

    assert result.exit_code == 0
    assert "D. E. Shaw" in result.output
    assert "Hedge Funds" in result.output
    assert "official_careers" in result.output


def test_job_source_seeds_cover_all_target_companies() -> None:
    source_companies = {source.company for source in JOB_SOURCE_SEEDS}
    seed_companies = {seed.name for seed in SEEDS}

    assert seed_companies <= source_companies


def test_canonical_categories_partition_all_target_companies() -> None:
    counts = {category: 0 for category in CANONICAL_CATEGORIES}
    for seed in SEEDS:
        counts[category_for_group(seed.group)] += 1

    assert counts == {
        "Investment Banks": 5,
        "Hedge Funds": 41,
        "Prop Trading": 30,
        "Asset Management": 5,
    }


def test_known_non_job_patterns_cover_observed_false_positive_urls() -> None:
    from quant_job_tracker.cli import KNOWN_NON_JOB_URL_PATTERNS_BY_COMPANY, is_known_non_job_url

    false_positive_urls = {
        "AQR Capital Management": "https://www.aqr.com/Insights/Research",
        "Akuna Capital": "https://akunacapital.com/what-we-do/quant/",
        "Aspect Capital": "https://www.aspectcapital.com/insight/rcm-alternatives-podcast-with-christopher-reeve/",
        "Balyasny Asset Management": "https://www.bamfunds.com/how-we-work/investment",
        "Goldman Sachs": "https://www.goldmansachs.com/careers/our-firm/asset-management",
        "JPMorgan Chase": "https://www.jpmorgan.com/insights/global-research",
        "Millennium Management": "https://www.mlp.com/people/investment-professionals/",
        "PanAgora Asset Management": "https://www.panagora.com/insights/?scrolled=1",
        "WorldQuant": "https://www.worldquant.com/ideas/worldquant-announces-completion-of-inaugural-global-alphathon-competition/",
    }

    for company, url in false_positive_urls.items():
        patterns = KNOWN_NON_JOB_URL_PATTERNS_BY_COMPANY[company]
        assert any(pattern in url for pattern in patterns), company
        assert is_known_non_job_url(company, url) is True

    assert (
        is_known_non_job_url("IMC Trading", "https://www.imc.com/us/careers/jobs/4382558101")
        is False
    )
    assert is_known_non_job_url("WorldQuant", "https://www.worldquantfoundry.com/") is True
    assert is_known_non_job_url("WorldQuant", "https://www.wqu.edu/") is True
    assert is_known_non_job_url("WorldQuant", "https://worldquantventures.com/") is True


def test_eval_pending_command_is_idempotent_for_current_eval(tmp_path: Path) -> None:
    from quant_job_tracker.cli import app

    db_path = tmp_path / "qjt.sqlite3"
    init_result = runner.invoke(app, ["init-db", "--db", str(db_path)])
    assert init_result.exit_code == 0

    jd = "Alpha quant researcher role with predictive trading strategy work and H-1B sponsorship available."
    with create_session(db_path) as session:
        company = Company(
            name="Test Fund",
            group="quant",
            career_url="https://example.com",
            active=True,
        )
        session.add(company)
        session.flush()
        session.add(
            Job(
                company_id=company.id,
                company=company.name,
                title="Quant Researcher",
                loc="New York",
                url="https://example.com/job/1",
                source="official",
                jd=jd,
                jd_hash=hash_jd(jd),
                status="new",
            )
        )
        session.commit()

    first = runner.invoke(app, ["eval-pending", "--db", str(db_path)])
    second = runner.invoke(app, ["eval-pending", "--db", str(db_path)])

    assert first.exit_code == 0
    assert "Evaluated 1 jobs" in first.output
    assert second.exit_code == 0
    assert "Evaluated 0 jobs" in second.output
    with create_session(db_path) as session:
        assert session.query(Eval).count() == 1
        runs = session.query(Run).order_by(Run.id).all()
        assert len(runs) == 2
        assert runs[0].kind == "eval"
        assert runs[0].status == "success"
        assert runs[0].jobs_evaluated == 1
        assert runs[0].model == "heuristic-v2"
        assert runs[0].policy_ver == "v1"
        assert runs[1].jobs_evaluated == 0


def test_eval_pending_repairs_dirty_titles_and_reevaluates(tmp_path: Path) -> None:
    from quant_job_tracker.cli import app

    db_path = tmp_path / "qjt.sqlite3"
    init_db(db_path)
    jd = "Senior Analyst, Equity Data Science | PanAgora Careers"
    dirty_title = (
        "Senior Analyst, Equity Data Science Summary: PanAgora seeks to integrate a Sr. "
        "Analyst to work closely with the Alpha Research team. Read Post"
    )
    with create_session(db_path) as session:
        company = Company(
            name="PanAgora Asset Management",
            group="quant",
            career_url="https://example.com",
            active=True,
        )
        session.add(company)
        session.flush()
        job = Job(
            company_id=company.id,
            company=company.name,
            title=dirty_title,
            loc="Unknown",
            url="https://example.com/job/1",
            source="official",
            jd=jd,
            jd_hash=hash_jd(jd),
            status="live",
        )
        session.add(job)
        session.flush()
        session.add(
            Eval(
                job_id=job.id,
                jd_hash=job.jd_hash,
                front="red",
                h1b="yellow",
                exp="green",
                score=50,
                reason="old",
                flags="title_dirty",
                model="heuristic-v1",
                policy_ver="v1",
            )
        )
        session.commit()

    result = runner.invoke(app, ["eval-pending", "--db", str(db_path)])

    assert result.exit_code == 0
    assert "Evaluated 1 jobs" in result.output
    with create_session(db_path) as session:
        job = session.query(Job).one()
        assert job.title == "Senior Analyst, Equity Data Science"
        assert session.query(Eval).count() == 2


def test_crawl_command_fetches_filters_stores_and_records_run(tmp_path: Path, monkeypatch) -> None:
    from quant_job_tracker import cli

    db_path = tmp_path / "qjt.sqlite3"
    seed = CompanySeed(
        name="Test Fund",
        group="quant",
        career_url="https://example.com/careers",
        ats="generic",
        notes="seed note",
    )

    class FakeAdapter:
        def fetch_html(self, url: str) -> str:
            assert url == seed.career_url
            return "<html>careers</html>"

        def parse_cards(self, base_url: str, html: str) -> list[JobCard]:
            assert base_url == seed.career_url
            assert html == "<html>careers</html>"
            return [
                JobCard(
                    title="Quant Researcher",
                    loc="Unknown",
                    url="https://example.com/jobs/quant",
                ),
                JobCard(
                    title="Quant Researcher",
                    loc="London",
                    url="https://example.com/jobs/london",
                ),
            ]

        def fetch_jd(self, url: str) -> str:
            assert url == "https://example.com/jobs/quant"
            return "Alpha research role with systematic trading work."

    monkeypatch.setattr(cli, "SEEDS", [seed])
    monkeypatch.setattr(cli, "GenericAdapter", FakeAdapter)

    result = runner.invoke(cli.app, ["crawl", "--db", str(db_path), "--limit", "1"])

    assert result.exit_code == 0
    assert "Crawled 1 companies, found 2 jobs, stored 1 jobs" in result.output
    with create_session(db_path) as session:
        company = session.query(Company).one()
        assert company.name == "Test Fund"
        assert company.group == "quant"
        assert company.career_url == seed.career_url
        assert company.ats == "generic"
        assert company.active is True
        assert company.notes == "seed note"

        job = session.query(Job).one()
        assert job.company_id == company.id
        assert job.title == "Quant Researcher"
        assert job.loc == "Unknown"
        assert job.url == "https://example.com/jobs/quant"
        assert job.jd == "Alpha research role with systematic trading work."

        run = session.query(Run).one()
        assert run.kind == "crawl"
        assert run.status == "success"
        assert run.jobs_found == 2
        assert run.jobs_stored == 1
        assert run.policy_ver == "v1"
        assert run.model is None
        assert run.error is None


def test_crawl_command_breaks_out_blocked_career_pages(tmp_path: Path, monkeypatch) -> None:
    from quant_job_tracker import cli

    db_path = tmp_path / "qjt.sqlite3"
    seed = CompanySeed(
        name="Blocked Fund",
        group="quant",
        career_url="https://example.com/careers",
        ats="generic",
    )

    class FakeAdapter:
        def fetch_html(self, url: str) -> str:
            assert url == seed.career_url
            raise cli.CareerPageBlockedError("blocked by Cloudflare challenge")

    monkeypatch.setattr(cli, "SEEDS", [seed])
    monkeypatch.setattr(cli, "GenericAdapter", FakeAdapter)

    result = runner.invoke(cli.app, ["crawl", "--db", str(db_path), "--limit", "1"])

    assert result.exit_code == 0
    assert "Crawled 1 companies, found 0 jobs, stored 0 jobs" in result.output
    with create_session(db_path) as session:
        company = session.query(Company).one()
        assert company.name == "Blocked Fund"
        run = session.query(Run).one()
        assert run.status == "partial"
        assert run.error is not None
        assert "Bot crawling prohibited / 403" in run.error
        assert "Blocked Fund: blocked by Cloudflare challenge" in run.error


def test_crawl_command_prunes_known_bad_job_urls_even_when_company_is_blocked(
    tmp_path: Path, monkeypatch
) -> None:
    from quant_job_tracker import cli

    db_path = tmp_path / "qjt.sqlite3"
    seed = CompanySeed(
        name="Citadel",
        group="multi_manager",
        career_url="https://www.citadel.com/careers/open-opportunities/",
        ats="generic",
    )
    init_db(db_path)
    with create_session(db_path) as session:
        company = Company(
            name="Citadel",
            group="multi_manager",
            career_url=seed.career_url,
            active=True,
        )
        session.add(company)
        session.flush()
        bad_job = Job(
            company_id=company.id,
            company=company.name,
            title="Quantitative Research",
            loc="Unknown",
            url="https://www.citadel.com/careers/quantitative-research/",
            source="official",
            jd="Marketing page",
            jd_hash="bad",
            status="live",
        )
        session.add(bad_job)
        session.flush()
        session.add(
            Eval(
                job_id=bad_job.id,
                jd_hash=bad_job.jd_hash,
                front="red",
                h1b="yellow",
                exp="green",
                score=50,
                reason="old false positive",
                flags="page_noise",
                model="heuristic-v1",
                policy_ver="v1",
            )
        )
        session.commit()

    class FakeAdapter:
        def fetch_html(self, url: str) -> str:
            assert url == seed.career_url
            raise cli.CareerPageBlockedError("blocked by Cloudflare challenge")

    monkeypatch.setattr(cli, "SEEDS", [seed])
    monkeypatch.setattr(cli, "GenericAdapter", FakeAdapter)

    result = runner.invoke(cli.app, ["crawl", "--db", str(db_path), "--limit", "1"])

    assert result.exit_code == 0
    with create_session(db_path) as session:
        assert session.query(Job).count() == 0
        assert session.query(Eval).count() == 0
        run = session.query(Run).one()
        assert run.status == "partial"
        assert "Bot crawling prohibited / 403" in (run.error or "")


def test_crawl_command_uses_interactive_browser_adapter(tmp_path: Path, monkeypatch) -> None:
    from quant_job_tracker import cli

    db_path = tmp_path / "qjt.sqlite3"
    seed = CompanySeed(
        name="Citadel",
        group="multi_manager",
        career_url="https://www.citadel.com/careers/open-opportunities/",
        ats="generic",
    )
    events: list[str] = []

    class FakeGenericAdapter:
        pass

    class FakeInteractiveBrowserAdapter:
        def __init__(self, fallback: object) -> None:
            events.append(f"fallback={fallback.__class__.__name__}")

        def fetch_cards(self, url: str) -> list[JobCard]:
            assert url == seed.career_url
            return [
                JobCard(
                    title="Quantitative Researcher – PhD Intern (US)",
                    loc="New York",
                    url="https://www.citadel.com/careers/details/quantitative-researcher-phd-intern-us/",
                )
            ]

        def fetch_jd(self, url: str) -> str:
            assert url.endswith("/quantitative-researcher-phd-intern-us/")
            return "Quantitative researcher intern role with alpha research."

        def close(self) -> None:
            events.append("closed")

    monkeypatch.setattr(cli, "SEEDS", [seed])
    monkeypatch.setattr(cli, "GenericAdapter", FakeGenericAdapter)
    monkeypatch.setattr(
        cli, "InteractiveBrowserAdapter", FakeInteractiveBrowserAdapter, raising=False
    )

    result = runner.invoke(
        cli.app, ["crawl", "--db", str(db_path), "--limit", "1", "--interactive-browser"]
    )

    assert result.exit_code == 0
    assert "Crawled 1 companies, found 1 jobs, stored 1 jobs" in result.output
    assert events == ["fallback=FakeGenericAdapter", "closed"]
    with create_session(db_path) as session:
        job = session.query(Job).one()
        assert job.company == "Citadel"
        assert job.title == "Quantitative Researcher – PhD Intern (US)"


def test_crawl_command_stores_citadel_listing_when_detail_is_blocked(
    tmp_path: Path, monkeypatch
) -> None:
    from quant_job_tracker import cli

    db_path = tmp_path / "qjt.sqlite3"
    seed = CompanySeed(
        name="Citadel",
        group="multi_manager",
        career_url="https://www.citadel.com/careers/open-opportunities/",
        ats="generic",
    )

    class FakeAdapter:
        def fetch_cards(self, url: str) -> list[JobCard]:
            assert url == seed.career_url
            return [
                JobCard(
                    title="Quantitative Researcher – PhD Intern (US)",
                    loc="Greenwich, Miami, New York",
                    url="https://www.citadel.com/careers/details/quantitative-researcher-phd-intern-us/",
                )
            ]

        def fetch_jd(self, url: str) -> str:
            raise cli.CareerPageBlockedError("blocked by Cloudflare challenge")

    monkeypatch.setattr(cli, "SEEDS", [seed])
    monkeypatch.setattr(cli, "GenericAdapter", FakeAdapter)

    result = runner.invoke(cli.app, ["crawl", "--db", str(db_path), "--limit", "1"])

    assert result.exit_code == 0
    assert "Crawled 1 companies, found 1 jobs, stored 1 jobs" in result.output
    with create_session(db_path) as session:
        job = session.query(Job).one()
        assert job.company == "Citadel"
        assert job.title == "Quantitative Researcher – PhD Intern (US)"
        assert "Detail page blocked by provider" in job.jd
        assert "official listing row" in (job.crawl_note or "")
        run = session.query(Run).one()
        assert run.status == "partial"
        assert "Detail page blocked; stored official listing row" in (run.error or "")


def test_import_saved_html_stores_jobs_from_official_listing(tmp_path: Path) -> None:
    from quant_job_tracker.cli import app

    db_path = tmp_path / "qjt.sqlite3"
    html_path = tmp_path / "citadel.html"
    html_path.write_text(
        """
        <html><body>
          <a href="/careers/details/quantitative-researcher-phd-intern-us/">
            Quantitative Researcher – PhD Intern (US) Greenwich, Miami, New York Apply Now
          </a>
        </body></html>
        """,
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "import-saved-html",
            "--db",
            str(db_path),
            "--company",
            "Citadel",
            "--url",
            "https://www.citadel.com/careers/open-opportunities/",
            "--html",
            str(html_path),
        ],
    )

    assert result.exit_code == 0
    assert "Imported 1 jobs from saved HTML" in result.output
    with create_session(db_path) as session:
        job = session.query(Job).one()
        assert job.company == "Citadel"
        assert job.title == "Quantitative Researcher – PhD Intern (US)"
        assert job.loc == "Greenwich, Miami, New York"
        assert job.url == (
            "https://www.citadel.com/careers/details/quantitative-researcher-phd-intern-us/"
        )
        assert "Imported from saved official HTML" in job.crawl_note
        run = session.query(Run).one()
        assert run.kind == "manual_import"
        assert run.status == "success"
        assert run.jobs_found == 1
        assert run.jobs_stored == 1


def test_import_saved_html_fetches_official_ajax_when_saved_shell_has_empty_listing(
    tmp_path: Path, monkeypatch
) -> None:
    from quant_job_tracker import cli
    from quant_job_tracker.cli import app

    db_path = tmp_path / "qjt.sqlite3"
    html_path = tmp_path / "citadel.html"
    html_path.write_text(
        """
        <html><body>
          <form id="ajax-careers-search-filter" action="https://www.citadel.com/wp-admin/admin-ajax.php">
            <input type="hidden" name="action" value="careers_listing_filter" />
          </form>
          <div id="careers-table-filter-wrap"></div>
        </body></html>
        """,
        encoding="utf-8",
    )

    class FakeAdapter:
        def parse_cards(self, base_url: str, html: str) -> list[JobCard]:
            return []

        def fetch_cards(self, url: str) -> list[JobCard]:
            assert url == "https://www.citadel.com/careers/open-opportunities/"
            return [
                JobCard(
                    title="Quantitative Researcher – PhD Intern (US)",
                    loc="Greenwich, Miami, New York",
                    url="https://www.citadel.com/careers/details/quantitative-researcher-phd-intern-us/",
                )
            ]

    monkeypatch.setattr(cli, "GenericAdapter", FakeAdapter)

    result = runner.invoke(
        app,
        [
            "import-saved-html",
            "--db",
            str(db_path),
            "--company",
            "Citadel",
            "--url",
            "https://www.citadel.com/careers/open-opportunities/",
            "--html",
            str(html_path),
        ],
    )

    assert result.exit_code == 0
    assert "Imported 1 jobs from saved HTML" in result.output


def test_crawl_command_breaks_out_404_seed_urls(tmp_path: Path, monkeypatch) -> None:
    from quant_job_tracker import cli

    db_path = tmp_path / "qjt.sqlite3"
    seed = CompanySeed(
        name="Missing Fund",
        group="quant",
        career_url="https://example.com/missing",
        ats="generic",
    )

    class FakeAdapter:
        def fetch_html(self, url: str) -> str:
            request = httpx.Request("GET", url)
            response = httpx.Response(404, request=request)
            raise httpx.HTTPStatusError("not found", request=request, response=response)

    monkeypatch.setattr(cli, "SEEDS", [seed])
    monkeypatch.setattr(cli, "GenericAdapter", FakeAdapter)

    result = runner.invoke(cli.app, ["crawl", "--db", str(db_path), "--limit", "1"])

    assert result.exit_code == 0
    with create_session(db_path) as session:
        run = session.query(Run).one()
        assert run.status == "partial"
        assert run.error is not None
        assert "Bad seed URL / 404" in run.error
        assert "Missing Fund: 404 Not Found" in run.error


def test_eval_pending_reuses_eval_for_unchanged_jd_after_recrawl(tmp_path: Path) -> None:
    from quant_job_tracker.cli import app

    db_path = tmp_path / "qjt.sqlite3"
    init_db(db_path)
    with create_session(db_path) as session:
        company = Company(
            name="Test Fund",
            group="quant",
            career_url="https://example.com",
            active=True,
        )
        session.add(company)
        session.commit()
        company_id = company.id

    card = JobCard(title="Quant Researcher", loc="New York", url="https://example.com/job/1")
    jd = "Alpha quant researcher role with predictive trading strategy work and H-1B sponsorship available."
    upsert_crawled_job(db_path, company_id, "Test Fund", card, jd, "first")

    first = runner.invoke(app, ["eval-pending", "--db", str(db_path)])
    assert first.exit_code == 0
    assert "Evaluated 1 jobs" in first.output

    with create_session(db_path) as session:
        job = session.query(Job).one()
        job.last_seen = datetime.utcnow() + timedelta(seconds=1)
        session.commit()

    unchanged = runner.invoke(app, ["eval-pending", "--db", str(db_path)])
    assert unchanged.exit_code == 0
    assert "Evaluated 0 jobs" in unchanged.output
    with create_session(db_path) as session:
        assert session.query(Eval).count() == 1
        latest_run = session.query(Run).order_by(Run.id.desc()).first()
        assert latest_run is not None
        assert latest_run.jobs_evaluated == 0

    upsert_crawled_job(
        db_path,
        company_id,
        "Test Fund",
        card,
        "Updated Alpha quant researcher JD with portfolio construction research.",
        "changed",
    )
    changed = runner.invoke(app, ["eval-pending", "--db", str(db_path)])

    assert changed.exit_code == 0
    assert "Evaluated 1 jobs" in changed.output
    with create_session(db_path) as session:
        assert session.query(Eval).count() == 2


def test_policy_report_command_suggests_policy_updates(tmp_path: Path) -> None:
    from quant_job_tracker.cli import app

    db_path = tmp_path / "qjt.sqlite3"
    init_db(db_path)
    with create_session(db_path) as session:
        company = Company(
            name="Hudson River Trading",
            group="quant",
            career_url="https://example.com",
            active=True,
        )
        session.add(company)
        session.flush()
        job = Job(
            company_id=company.id,
            company=company.name,
            title="Algorithm Developer",
            loc="New York",
            url="https://example.com/job/1",
            source="official",
            jd="Developer role",
            jd_hash="abc",
            status="new",
        )
        session.add(job)
        session.flush()
        session.add(
            Eval(
                job_id=job.id,
                jd_hash=job.jd_hash,
                front="green",
                h1b="yellow",
                exp="green",
                score=80,
                reason="Alias fit",
                flags="title_alias",
                model="test",
                policy_ver="v1",
            )
        )
        session.commit()

    result = runner.invoke(app, ["policy-report", "--db", str(db_path)])

    assert result.exit_code == 0
    assert "Hudson River Trading" in result.output
    assert "title alias" in result.output.lower()


def test_upsert_crawled_job_creates_and_updates(tmp_path: Path) -> None:
    db_path = tmp_path / "qjt.sqlite3"
    init_db(db_path)
    with create_session(db_path) as session:
        company = Company(
            name="Test Fund",
            group="quant",
            career_url="https://example.com",
            active=True,
        )
        session.add(company)
        session.commit()
        company_id = company.id

    card = JobCard(title="Quant Researcher", loc="New York", url="https://example.com/job/1")
    upsert_crawled_job(db_path, company_id, "Test Fund", card, "Alpha research JD", "kept")

    with create_session(db_path) as session:
        job = session.query(Job).one()
        job.status = "closed"
        job.closed_at = datetime.utcnow() - timedelta(days=1)
        first_seen = job.first_seen
        original_last_seen = job.last_seen
        session.commit()

    upsert_crawled_job(
        db_path,
        company_id,
        "Test Fund",
        card,
        "Alpha research JD updated",
        "updated note",
    )

    with create_session(db_path) as session:
        jobs = session.query(Job).all()
        assert len(jobs) == 1
        job = jobs[0]
        assert job.jd == "Alpha research JD updated"
        assert job.jd_hash == hash_jd("Alpha research JD updated")
        assert job.first_seen == first_seen
        assert job.last_seen > original_last_seen
        assert job.status == "live"
        assert job.crawl_note == "updated note"
        assert job.closed_at is None


def test_upsert_crawled_job_dedupes_same_company_by_jd_hash(tmp_path: Path) -> None:
    db_path = tmp_path / "qjt.sqlite3"
    init_db(db_path)
    with create_session(db_path) as session:
        company = Company(
            name="Test Fund",
            group="quant",
            career_url="https://example.com",
            active=True,
        )
        other_company = Company(
            name="Other Fund",
            group="quant",
            career_url="https://other.example.com",
            active=True,
        )
        session.add_all([company, other_company])
        session.commit()
        company_id = company.id
        other_company_id = other_company.id

    jd = "Alpha research JD"
    upsert_crawled_job(
        db_path,
        company_id,
        "Test Fund",
        JobCard(title="Quant Researcher", loc="New York", url="https://example.com/job/1"),
        jd,
        "first",
    )
    upsert_crawled_job(
        db_path,
        company_id,
        "Test Fund",
        JobCard(
            title="Quant Researcher", loc="Remote", url="https://example.com/job/1?src=canonical"
        ),
        jd,
        "second",
    )
    upsert_crawled_job(
        db_path,
        other_company_id,
        "Other Fund",
        JobCard(title="Quant Researcher", loc="Chicago", url="https://other.example.com/job/1"),
        jd,
        "other",
    )

    with create_session(db_path) as session:
        jobs = session.query(Job).order_by(Job.company_id).all()
        assert len(jobs) == 2

        same_company_job = jobs[0]
        assert same_company_job.company_id == company_id
        assert same_company_job.url == "https://example.com/job/1?src=canonical"
        assert same_company_job.loc == "Remote"
        assert same_company_job.crawl_note == "second"

        other_company_job = jobs[1]
        assert other_company_job.company_id == other_company_id
        assert other_company_job.url == "https://other.example.com/job/1"


def test_close_stale_jobs_closes_only_selected_company_jobs(tmp_path: Path) -> None:
    db_path = tmp_path / "qjt.sqlite3"
    init_db(db_path)
    cutoff = datetime.utcnow()
    with create_session(db_path) as session:
        company = Company(
            name="Test Fund",
            group="quant",
            career_url="https://example.com",
            active=True,
        )
        other_company = Company(
            name="Other Fund",
            group="quant",
            career_url="https://other.example.com",
            active=True,
        )
        session.add_all([company, other_company])
        session.flush()
        session.add_all(
            [
                Job(
                    company_id=company.id,
                    company="Test Fund",
                    title="Old Quant Researcher",
                    loc="New York",
                    url="https://example.com/old",
                    source="official",
                    jd="old",
                    jd_hash="old",
                    status="live",
                    last_seen=cutoff - timedelta(minutes=5),
                ),
                Job(
                    company_id=company.id,
                    company="Test Fund",
                    title="Fresh Quant Researcher",
                    loc="New York",
                    url="https://example.com/fresh",
                    source="official",
                    jd="fresh",
                    jd_hash="fresh",
                    status="live",
                    last_seen=cutoff + timedelta(minutes=5),
                ),
                Job(
                    company_id=other_company.id,
                    company="Other Fund",
                    title="Other Quant Researcher",
                    loc="New York",
                    url="https://other.example.com/old",
                    source="official",
                    jd="other",
                    jd_hash="other",
                    status="live",
                    last_seen=cutoff - timedelta(minutes=5),
                ),
            ]
        )
        session.commit()
        company_id = company.id

    closed = close_stale_jobs(db_path, [company_id], cutoff)

    assert closed == 1
    with create_session(db_path) as session:
        statuses = {job.title: job.status for job in session.query(Job).all()}
        assert statuses == {
            "Old Quant Researcher": "closed",
            "Fresh Quant Researcher": "live",
            "Other Quant Researcher": "live",
        }
