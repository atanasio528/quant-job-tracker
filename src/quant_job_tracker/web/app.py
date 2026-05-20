from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import desc

from quant_job_tracker.config import DEFAULT_DB_PATH
from quant_job_tracker.db import create_session, init_db
from quant_job_tracker.models import App, Eval, Job, Review, Run

TEMPLATE_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))
ALLOWED_REVIEW_DECISIONS = {"approved", "pending", "rejected", "needs_review"}
ALLOWED_APP_STATUSES = {"not_started", "ready", "applied", "interview", "rejected", "offer", "closed"}


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
                application = session.query(App).filter_by(job_id=job.id).one_or_none()
                rows.append({"job": job, "eval": latest, "application": application})
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
            application = session.query(App).filter_by(job_id=job_id).one_or_none()
            reviews = (
                session.query(Review)
                .filter_by(job_id=job_id)
                .order_by(desc(Review.created_at))
                .limit(20)
                .all()
            )
            return templates.TemplateResponse(
                request,
                "job_detail.html",
                {
                    "job": job,
                    "evals": evals,
                    "application": application,
                    "app_statuses": sorted(ALLOWED_APP_STATUSES),
                    "reviews": reviews,
                    "review_decisions": sorted(ALLOWED_REVIEW_DECISIONS),
                    "official_url": safe_external_url(job.url),
                },
            )

    @app.post("/jobs/{job_id}/review")
    def save_review(job_id: int, decision: str = Form(...), note: str = Form("")):
        with create_session(db_path) as session:
            job = session.query(Job).filter_by(id=job_id).one_or_none()
            if job is None:
                raise HTTPException(status_code=404, detail="Job not found")
            if decision not in ALLOWED_REVIEW_DECISIONS:
                raise HTTPException(status_code=400, detail="Invalid review decision")
            session.add(
                Review(
                    job_id=job_id,
                    decision=decision,
                    note=note or None,
                    reviewer="user",
                )
            )
            session.commit()
        return RedirectResponse(url=f"/jobs/{job_id}", status_code=303)

    @app.post("/jobs/{job_id}/application")
    def save_application(
        job_id: int,
        app_status: str = Form(...),
        deadline: str = Form(""),
        priority: str = Form(""),
        note: str = Form(""),
    ):
        with create_session(db_path) as session:
            job = session.query(Job).filter_by(id=job_id).one_or_none()
            if job is None:
                raise HTTPException(status_code=404, detail="Job not found")
            if app_status not in ALLOWED_APP_STATUSES:
                raise HTTPException(status_code=400, detail="Invalid application status")
            application = session.query(App).filter_by(job_id=job_id).one_or_none()
            if application is None:
                application = App(job_id=job_id)
                session.add(application)
            application.app_status = app_status
            application.deadline = deadline or None
            application.priority = priority or None
            application.note = note or None
            application.updated_at = datetime.utcnow()
            session.commit()
        return RedirectResponse(url=f"/jobs/{job_id}", status_code=303)

    @app.get("/runs", response_class=HTMLResponse)
    def runs(request: Request):
        with create_session(db_path) as session:
            rows = session.query(Run).order_by(desc(Run.created_at)).limit(100).all()
        return templates.TemplateResponse(request, "runs.html", {"rows": rows})

    return app
