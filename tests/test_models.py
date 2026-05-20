from pathlib import Path

import pytest
from sqlalchemy.exc import IntegrityError

from quant_job_tracker.db import create_session, init_db
from quant_job_tracker.models import Company, Eval, Job


def test_init_db_and_insert_job(tmp_path: Path) -> None:
    db_path = tmp_path / "qjt.sqlite3"
    init_db(db_path)

    with create_session(db_path) as session:
        company = Company(name="Hudson River Trading", group="prop", career_url="https://example.com", active=True)
        session.add(company)
        session.flush()
        job = Job(
            company_id=company.id,
            company=company.name,
            title="Algorithm Developer",
            loc="New York",
            url="https://example.com/job/1",
            source="test",
            jd="Quant Researcher role",
            jd_hash="abc",
            status="new",
        )
        session.add(job)
        session.commit()

    with create_session(db_path) as session:
        saved = session.query(Job).filter_by(url="https://example.com/job/1").one()
        assert saved.company == "Hudson River Trading"
        assert saved.title == "Algorithm Developer"


def test_eval_rows_are_append_only(tmp_path: Path) -> None:
    db_path = tmp_path / "qjt.sqlite3"
    init_db(db_path)
    with create_session(db_path) as session:
        company = Company(name="Test", group="quant", career_url="https://example.com", active=True)
        session.add(company)
        session.flush()
        job = Job(company_id=company.id, company="Test", title="Quant Researcher", loc="New York", url="u", source="s", jd="jd", jd_hash="h", status="new")
        session.add(job)
        session.flush()
        session.add(Eval(job_id=job.id, front="green", h1b="yellow", exp="green", score=82, reason="Good fit", flags="visa_unclear", model="test", policy_ver="v1"))
        session.add(Eval(job_id=job.id, front="green", h1b="green", exp="green", score=90, reason="Updated", flags="", model="test", policy_ver="v2"))
        session.commit()

    with create_session(db_path) as session:
        assert session.query(Eval).count() == 2


def test_eval_requires_existing_job(tmp_path: Path) -> None:
    db_path = tmp_path / "qjt.sqlite3"
    init_db(db_path)

    with create_session(db_path) as session:
        session.add(
            Eval(
                job_id=999,
                front="green",
                h1b="yellow",
                exp="green",
                score=1,
                reason="orphan",
                flags="",
                model="test",
                policy_ver="v1",
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
