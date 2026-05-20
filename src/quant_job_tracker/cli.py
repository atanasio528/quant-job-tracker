from datetime import datetime
from pathlib import Path

import typer
import uvicorn
from sqlalchemy import desc

from quant_job_tracker.config import DEFAULT_DB_PATH, POLICY_DIR
from quant_job_tracker.crawler.adapters import CareerPageBlockedError, GenericAdapter
from quant_job_tracker.crawler.filters import keep_job_card
from quant_job_tracker.crawler.seeds import SEEDS, CompanySeed
from quant_job_tracker.crawler.service import close_stale_jobs, upsert_company_seed, upsert_crawled_job
from quant_job_tracker.db import create_session, init_db as create_tables
from quant_job_tracker.evaluator.classifier import HeuristicClassifier
from quant_job_tracker.evaluator.policy_maker import suggest_policy_updates
from quant_job_tracker.models import Eval, Job, Run
from quant_job_tracker.policy import load_policy_bundle

app = typer.Typer(name="qjt")
EVAL_MODEL = "heuristic-v1"
POLICY_VER = "v1"


@app.command()
def init_db(db: Path = DEFAULT_DB_PATH) -> None:
    create_tables(db)
    typer.echo(f"Initialized {db}")


def _crawl_seeds(
    db: Path, seeds: list[CompanySeed], limit: int | None = None
) -> tuple[int, int, int, str | None]:
    adapter = GenericAdapter()
    selected_seeds = seeds[:limit] if limit is not None else seeds
    crawl_started = datetime.utcnow()
    successful_company_ids: list[int] = []
    companies_crawled = 0
    jobs_found = 0
    jobs_stored = 0
    errors: list[str] = []

    for seed in selected_seeds:
        try:
            company_id = upsert_company_seed(db, seed)
            companies_crawled += 1
            html = adapter.fetch_html(seed.career_url)
            cards = adapter.parse_cards(seed.career_url, html)
            successful_company_ids.append(company_id)
        except CareerPageBlockedError:
            continue
        except Exception as exc:
            errors.append(f"{seed.name}: {exc}")
            continue

        jobs_found += len(cards)
        for card in cards:
            keep, crawl_note = keep_job_card(seed.name, card.title, card.loc)
            if not keep:
                continue
            try:
                jd = adapter.fetch_jd(card.url)
                upsert_crawled_job(db, company_id, seed.name, card, jd, crawl_note)
                jobs_stored += 1
            except CareerPageBlockedError:
                continue
            except Exception as exc:
                errors.append(f"{seed.name} {card.url}: {exc}")

    close_stale_jobs(db, successful_company_ids, crawl_started)
    return companies_crawled, jobs_found, jobs_stored, "\n".join(errors) if errors else None


@app.command()
def crawl(db: Path = DEFAULT_DB_PATH, limit: int | None = None) -> None:
    create_tables(db)
    companies_crawled, jobs_found, jobs_stored, error = _crawl_seeds(db, SEEDS, limit)
    with create_session(db) as session:
        session.add(
            Run(
                kind="crawl",
                status="success" if error is None else "partial",
                jobs_found=jobs_found,
                jobs_stored=jobs_stored,
                policy_ver=POLICY_VER,
                model=None,
                error=error,
            )
        )
        session.commit()
    typer.echo(f"Crawled {companies_crawled} companies, found {jobs_found} jobs, stored {jobs_stored} jobs")


@app.command()
def eval_pending(db: Path = DEFAULT_DB_PATH) -> None:
    policy = load_policy_bundle(POLICY_DIR, "evaluator")
    classifier = HeuristicClassifier()
    with create_session(db) as session:
        jobs = session.query(Job).filter(Job.status.in_(["new", "live"])).all()
        count = 0
        for job in jobs:
            current_eval = (
                session.query(Eval.id)
                .filter(
                    Eval.job_id == job.id,
                    Eval.model == EVAL_MODEL,
                    Eval.policy_ver == POLICY_VER,
                    Eval.jd_hash == job.jd_hash,
                )
                .first()
            )
            if current_eval is not None:
                continue

            result = classifier.classify(job.title, job.jd, policy)
            session.add(
                Eval(
                    job_id=job.id,
                    jd_hash=job.jd_hash,
                    front=result.front,
                    h1b=result.h1b,
                    exp=result.exp,
                    score=result.score,
                    reason=result.reason,
                    flags=result.flags,
                    model=EVAL_MODEL,
                    policy_ver=POLICY_VER,
                )
            )
            count += 1
        session.add(
            Run(
                kind="eval",
                status="success",
                jobs_evaluated=count,
                model=EVAL_MODEL,
                policy_ver=POLICY_VER,
            )
        )
        session.commit()
    typer.echo(f"Evaluated {count} jobs")


@app.command()
def policy_report(db: Path = DEFAULT_DB_PATH) -> None:
    with create_session(db) as session:
        evals = session.query(Eval).order_by(desc(Eval.created_at)).limit(100).all()
        rows = [
            {
                "title": eval.job.title,
                "company": eval.job.company,
                "front": eval.front,
                "flags": eval.flags,
            }
            for eval in evals
        ]
    typer.echo(suggest_policy_updates(rows))


@app.command()
def web(host: str = "127.0.0.1", port: int = 8000) -> None:
    uvicorn.run("quant_job_tracker.web.app:create_app", factory=True, host=host, port=port, reload=True)
