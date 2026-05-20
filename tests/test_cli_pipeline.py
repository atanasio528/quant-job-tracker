from pathlib import Path

from quant_job_tracker.crawler.adapters import JobCard
from quant_job_tracker.crawler.service import upsert_crawled_job
from quant_job_tracker.db import create_session, init_db
from quant_job_tracker.models import Company, Job


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
    upsert_crawled_job(
        db_path,
        company_id,
        "Test Fund",
        card,
        "Alpha research JD updated",
        "kept",
    )

    with create_session(db_path) as session:
        jobs = session.query(Job).all()
        assert len(jobs) == 1
        assert jobs[0].jd == "Alpha research JD updated"
