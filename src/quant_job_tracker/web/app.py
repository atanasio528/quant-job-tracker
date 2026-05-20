from datetime import datetime
from html import unescape
from math import ceil
from pathlib import Path
import re
from urllib.parse import urlencode
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
ALLOWED_APP_STATUSES = {
    "not_started",
    "ready",
    "applied",
    "interview",
    "rejected",
    "offer",
    "closed",
}
LABEL_FILTERS = {"all", "green", "yellow", "red", "missing"}
STATUS_FILTERS = {"all", "new", "live", "closed"}
PAGE_SIZE = 50
JD_SECTION_HEADINGS = (
    "Preferred Qualifications",
    "Basic Qualifications",
    "Responsibilities",
    "Qualifications",
    "Requirements",
    "What you'll do",
    "What you’ll do",
    "Who you are",
    "About the role",
    "Overview",
    "Summary",
    "Location",
    "Benefits",
)


def safe_external_url(url: str) -> str | None:
    parsed = urlparse(url)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return url
    return None


def create_app(db_path: Path = DEFAULT_DB_PATH) -> FastAPI:
    init_db(db_path)
    app = FastAPI(title="Quant Job Tracker")

    @app.get("/", response_class=HTMLResponse)
    def jobs(
        request: Request,
        front: str = "all",
        h1b: str = "all",
        exp: str = "all",
        status: str = "all",
        page: int = 1,
    ):
        filters = {
            "front": _normalize_filter(front, LABEL_FILTERS),
            "h1b": _normalize_filter(h1b, LABEL_FILTERS),
            "exp": _normalize_filter(exp, LABEL_FILTERS),
            "status": _normalize_filter(status, STATUS_FILTERS),
        }
        page = max(page, 1)
        with create_session(db_path) as session:
            rows = []
            query = session.query(Job).order_by(desc(Job.last_seen))
            if filters["status"] != "all":
                query = query.filter_by(status=filters["status"])
            for job in query.all():
                latest = _preferred_eval(session, job.id)
                if not _matches_eval_filter(latest, "front", filters["front"]):
                    continue
                if not _matches_eval_filter(latest, "h1b", filters["h1b"]):
                    continue
                if not _matches_eval_filter(latest, "exp", filters["exp"]):
                    continue
                application = session.query(App).filter_by(job_id=job.id).one_or_none()
                rows.append(
                    {
                        "job": job,
                        "eval": latest,
                        "application": application,
                        "official_url": safe_external_url(job.url),
                    }
                )
        total_rows = len(rows)
        total_pages = max(ceil(total_rows / PAGE_SIZE), 1)
        page = min(page, total_pages)
        start = (page - 1) * PAGE_SIZE
        page_rows = rows[start : start + PAGE_SIZE]
        prev_query = _page_query(filters, page - 1) if page > 1 else None
        next_query = _page_query(filters, page + 1) if page < total_pages else None
        return templates.TemplateResponse(
            request,
            "jobs.html",
            {
                "rows": page_rows,
                "filters": filters,
                "label_options": ["all", "green", "yellow", "red", "missing"],
                "status_options": ["all", "new", "live", "closed"],
                "page": page,
                "total_pages": total_pages,
                "total_rows": total_rows,
                "page_size": PAGE_SIZE,
                "prev_query": prev_query,
                "next_query": next_query,
            },
        )

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
                    "jd_sections": format_jd_sections(job.jd),
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


def _preferred_eval(session, job_id: int) -> Eval | None:
    evals = session.query(Eval).filter_by(job_id=job_id).order_by(desc(Eval.created_at)).all()
    codex_eval = next((eval for eval in evals if eval.model == "codex-v1"), None)
    return codex_eval or (evals[0] if evals else None)


def _normalize_filter(value: str, allowed: set[str]) -> str:
    value = value.lower().strip()
    return value if value in allowed else "all"


def _matches_eval_filter(eval: Eval | None, field: str, selected: str) -> bool:
    if selected == "all":
        return True
    if eval is None:
        return selected == "missing"
    return getattr(eval, field) == selected


def _page_query(filters: dict[str, str], page: int) -> str:
    return urlencode({**filters, "page": page})


def format_jd_sections(jd: str | None) -> list[dict[str, object]]:
    text = unescape(" ".join((jd or "").split()))
    if not text:
        return []

    marker_pattern = "|".join(
        re.escape(heading) for heading in sorted(JD_SECTION_HEADINGS, key=len, reverse=True)
    )
    matches = list(re.finditer(rf"\b({marker_pattern})\b:?", text, flags=re.IGNORECASE))
    if not matches:
        return [{"heading": None, "paragraphs": split_readable_paragraphs(text)}]

    sections: list[dict[str, object]] = []
    intro = text[: matches[0].start()].strip(" :-")
    if intro:
        sections.append({"heading": None, "paragraphs": split_readable_paragraphs(intro)})

    for index, match in enumerate(matches):
        heading = canonical_jd_heading(match.group(1))
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[start:end].strip(" :-")
        if body:
            sections.append({"heading": heading, "paragraphs": split_readable_paragraphs(body)})

    return sections


def canonical_jd_heading(heading: str) -> str:
    normalized = " ".join(heading.split()).lower()
    for known in JD_SECTION_HEADINGS:
        if normalized == known.lower():
            return known.replace("’", "'")
    return heading.title()


def split_readable_paragraphs(text: str, max_chars: int = 650) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", text)
    paragraphs: list[str] = []
    current = ""
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if current and len(current) + len(sentence) + 1 > max_chars:
            paragraphs.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        paragraphs.append(current)
    return paragraphs or [text]
