from datetime import datetime
from hashlib import sha256
from pathlib import Path

from quant_job_tracker.crawler.adapters import JobCard
from quant_job_tracker.crawler.seeds import CompanySeed
from quant_job_tracker.db import create_session
from quant_job_tracker.models import Company, Job


def hash_jd(jd: str) -> str:
    return sha256(jd.encode("utf-8")).hexdigest()


def upsert_company_seed(db_path: Path, seed: CompanySeed) -> int:
    with create_session(db_path) as session:
        company = session.query(Company).filter_by(name=seed.name).one_or_none()
        if company is None:
            company = Company(
                name=seed.name,
                group=seed.group,
                career_url=seed.career_url,
                ats=seed.ats,
                active=True,
                notes=seed.notes,
            )
            session.add(company)
        else:
            company.group = seed.group
            company.career_url = seed.career_url
            company.ats = seed.ats
            company.active = True
            company.notes = seed.notes
        session.flush()
        company_id = company.id
        session.commit()
        return company_id


def upsert_crawled_job(
    db_path: Path,
    company_id: int,
    company: str,
    card: JobCard,
    jd: str,
    crawl_note: str,
) -> None:
    now = datetime.utcnow()
    new_hash = hash_jd(jd)
    with create_session(db_path) as session:
        existing = session.query(Job).filter_by(url=card.url).one_or_none()
        if existing is None:
            existing = (
                session.query(Job)
                .filter_by(company_id=company_id, jd_hash=new_hash)
                .one_or_none()
            )
        if existing:
            existing.title = card.title
            existing.loc = card.loc
            existing.url = card.url
            existing.jd = jd
            existing.jd_hash = new_hash
            existing.status = "live"
            existing.last_seen = now
            existing.closed_at = None
            existing.crawl_note = crawl_note
        else:
            session.add(
                Job(
                    company_id=company_id,
                    company=company,
                    title=card.title,
                    loc=card.loc,
                    url=card.url,
                    source="official",
                    jd=jd,
                    jd_hash=new_hash,
                    status="new",
                    first_seen=now,
                    last_seen=now,
                    crawl_note=crawl_note,
                )
            )
        session.commit()


def close_stale_jobs(db_path: Path, company_ids: list[int], cutoff: datetime) -> int:
    if not company_ids:
        return 0
    with create_session(db_path) as session:
        jobs = (
            session.query(Job)
            .filter(
                Job.company_id.in_(company_ids),
                Job.status.in_(["new", "live"]),
                Job.last_seen < cutoff,
            )
            .all()
        )
        for job in jobs:
            job.status = "closed"
            job.closed_at = cutoff
        count = len(jobs)
        session.commit()
        return count
