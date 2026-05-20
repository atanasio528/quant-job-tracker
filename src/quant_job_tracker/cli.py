from pathlib import Path

import typer
import uvicorn
from sqlalchemy import desc

from quant_job_tracker.config import DEFAULT_DB_PATH, POLICY_DIR
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
                    Eval.created_at >= job.last_seen,
                )
                .first()
            )
            if current_eval is not None:
                continue

            result = classifier.classify(job.title, job.jd, policy)
            session.add(
                Eval(
                    job_id=job.id,
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
