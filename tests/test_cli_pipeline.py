from datetime import datetime, timedelta
from pathlib import Path

from typer.testing import CliRunner

from quant_job_tracker.crawler.adapters import JobCard
from quant_job_tracker.crawler.seeds import CompanySeed
from quant_job_tracker.crawler.service import hash_jd, upsert_crawled_job
from quant_job_tracker.db import create_session, init_db
from quant_job_tracker.models import Company, Eval, Job, Run


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
        assert runs[0].model == "heuristic-v1"
        assert runs[0].policy_ver == "v1"
        assert runs[1].jobs_evaluated == 0


def test_crawl_command_fetches_filters_stores_and_records_run(
    tmp_path: Path, monkeypatch
) -> None:
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
        JobCard(title="Quant Researcher", loc="Remote", url="https://example.com/job/1?src=canonical"),
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
