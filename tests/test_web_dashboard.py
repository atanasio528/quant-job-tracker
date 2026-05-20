from pathlib import Path

from fastapi.testclient import TestClient

from quant_job_tracker.db import create_session, init_db
from quant_job_tracker.models import Company, Eval, Job, Run


def test_web_dashboard_lists_jobs_and_detail(tmp_path: Path) -> None:
    from quant_job_tracker.web.app import create_app

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
        session.flush()
        job = Job(
            company_id=company.id,
            company=company.name,
            title="Quant Researcher",
            loc="New York",
            url="https://example.com/job/1",
            source="official",
            jd="Alpha research role",
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
                score=85,
                reason="Strong front-office fit",
                flags="visa_unclear",
                model="test",
                policy_ver="v1",
            )
        )
        session.commit()
        job_id = job.id

    client = TestClient(create_app(db_path))

    jobs_response = client.get("/")
    assert jobs_response.status_code == 200
    assert "Quant Researcher" in jobs_response.text
    assert "visa_unclear" in jobs_response.text

    detail_response = client.get(f"/jobs/{job_id}")
    assert detail_response.status_code == 200
    assert "Official posting" in detail_response.text
    assert "Strong front-office fit" in detail_response.text
    assert "Alpha research role" in detail_response.text


def test_missing_job_detail_returns_404(tmp_path: Path) -> None:
    from quant_job_tracker.web.app import create_app

    db_path = tmp_path / "qjt.sqlite3"
    init_db(db_path)

    client = TestClient(create_app(db_path), raise_server_exceptions=False)

    response = client.get("/jobs/999")

    assert response.status_code == 404


def test_run_history_lists_recent_runs(tmp_path: Path) -> None:
    from quant_job_tracker.web.app import create_app

    db_path = tmp_path / "qjt.sqlite3"
    init_db(db_path)
    with create_session(db_path) as session:
        session.add(
            Run(
                kind="eval",
                status="success",
                jobs_evaluated=3,
                policy_ver="v1",
                model="heuristic-v1",
            )
        )
        session.commit()

    client = TestClient(create_app(db_path))

    jobs_response = client.get("/")
    assert jobs_response.status_code == 200
    assert 'href="/runs"' in jobs_response.text

    runs_response = client.get("/runs")
    assert runs_response.status_code == 200
    assert "Run History" in runs_response.text
    assert "heuristic-v1" in runs_response.text
    assert "<td>3</td>" in runs_response.text


def test_job_detail_blocks_javascript_official_url(tmp_path: Path) -> None:
    from quant_job_tracker.web.app import create_app

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
        session.flush()
        job = Job(
            company_id=company.id,
            company=company.name,
            title="Quant Researcher",
            loc="New York",
            url="javascript:alert(1)",
            source="crawler",
            jd="Alpha research role",
            jd_hash="abc",
            status="new",
        )
        session.add(job)
        session.commit()
        job_id = job.id

    client = TestClient(create_app(db_path))

    response = client.get(f"/jobs/{job_id}")

    assert response.status_code == 200
    assert 'href="javascript:alert(1)"' not in response.text
    assert "Official link unavailable" in response.text
