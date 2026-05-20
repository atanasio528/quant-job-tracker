from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import desc

from quant_job_tracker.config import DEFAULT_DB_PATH
from quant_job_tracker.db import create_session, init_db
from quant_job_tracker.models import Eval, Job, Run

TEMPLATE_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


def safe_external_url(url: str) -> str | None:
    parsed = urlparse(url)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return url
    return None


def create_app(db_path: Path = DEFAULT_DB_PATH) -> FastAPI:
    init_db(db_path)
    app = FastAPI(title="Quant Job Tracker")

    @app.get("/", response_class=HTMLResponse)
    def jobs(request: Request):
        with create_session(db_path) as session:
            rows = []
            for job in session.query(Job).order_by(desc(Job.last_seen)).limit(200).all():
                latest = (
                    session.query(Eval)
                    .filter_by(job_id=job.id)
                    .order_by(desc(Eval.created_at))
                    .first()
                )
                rows.append({"job": job, "eval": latest})
        return templates.TemplateResponse(request, "jobs.html", {"rows": rows})

    @app.get("/jobs/{job_id}", response_class=HTMLResponse)
    def job_detail(request: Request, job_id: int):
        with create_session(db_path) as session:
            job = session.query(Job).filter_by(id=job_id).one_or_none()
            if job is None:
                raise HTTPException(status_code=404, detail="Job not found")
            evals = (
                session.query(Eval).filter_by(job_id=job_id).order_by(desc(Eval.created_at)).all()
            )
            return templates.TemplateResponse(
                request,
                "job_detail.html",
                {"job": job, "evals": evals, "official_url": safe_external_url(job.url)},
            )

    @app.get("/runs", response_class=HTMLResponse)
    def runs(request: Request):
        with create_session(db_path) as session:
            rows = session.query(Run).order_by(desc(Run.created_at)).limit(100).all()
        return templates.TemplateResponse(request, "runs.html", {"rows": rows})

    return app
