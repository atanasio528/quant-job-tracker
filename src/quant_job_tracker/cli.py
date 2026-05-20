from pathlib import Path

import typer
import uvicorn

from quant_job_tracker.config import DEFAULT_DB_PATH, POLICY_DIR
from quant_job_tracker.db import create_session, init_db as create_tables
from quant_job_tracker.evaluator.classifier import HeuristicClassifier
from quant_job_tracker.models import Eval, Job
from quant_job_tracker.policy import load_policy_bundle

app = typer.Typer(name="qjt")


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
                    model="heuristic-v1",
                    policy_ver="v1",
                )
            )
            count += 1
        session.commit()
    typer.echo(f"Evaluated {count} jobs")


@app.command()
def web(host: str = "127.0.0.1", port: int = 8000) -> None:
    uvicorn.run("quant_job_tracker.web.app:create_app", factory=True, host=host, port=port, reload=True)
