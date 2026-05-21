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
from quant_job_tracker.crawler.categories import CANONICAL_CATEGORIES, GROUP_TO_CATEGORY
from quant_job_tracker.db import create_session, init_db
from quant_job_tracker.models import App, Eval, Job, Review, Run

TEMPLATE_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))
ALLOWED_REVIEW_DECISIONS = {"approved", "pending", "rejected", "needs_review"}
APP_STATUS_OPTIONS = (
    "not_started",
    "ready",
    "applied",
    "interview",
    "offer",
    "rejected",
    "closed",
)
ALLOWED_APP_STATUSES = set(APP_STATUS_OPTIONS)
LABEL_FILTER_OPTIONS = ("green", "yellow", "red", "missing")
STATUS_FILTER_OPTIONS = ("new", "live", "closed")
LABEL_FILTERS = set(LABEL_FILTER_OPTIONS)
STATUS_FILTERS = set(STATUS_FILTER_OPTIONS)
INDUSTRY_ALL = "All"
INDUSTRY_OPTIONS = (INDUSTRY_ALL, *CANONICAL_CATEGORIES)
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
        page: int = 1,
    ):
        filters = {
            "front": _parse_multi_filter(request, "front", LABEL_FILTERS),
            "h1b": _parse_multi_filter(request, "h1b", LABEL_FILTERS),
            "exp": _parse_multi_filter(request, "exp", LABEL_FILTERS),
            "status": _parse_multi_filter(request, "status", STATUS_FILTERS),
            "app_status": _parse_multi_filter(request, "app_status", set(APP_STATUS_OPTIONS)),
        }
        industry = _parse_industry_filter(request)
        page = max(page, 1)
        with create_session(db_path) as session:
            rows = []
            query = session.query(Job).order_by(desc(Job.last_seen))
            if filters["status"]:
                query = query.filter(Job.status.in_(filters["status"]))
            for job in query.all():
                category = industry_for_group(job.company_ref.group if job.company_ref else "")
                if industry != INDUSTRY_ALL and category != industry:
                    continue
                latest = _preferred_eval(session, job.id)
                if not _matches_eval_filter(latest, "front", filters["front"]):
                    continue
                if not _matches_eval_filter(latest, "h1b", filters["h1b"]):
                    continue
                if not _matches_eval_filter(latest, "exp", filters["exp"]):
                    continue
                application = session.query(App).filter_by(job_id=job.id).one_or_none()
                app_status = application.app_status if application else "not_started"
                if filters["app_status"] and app_status not in filters["app_status"]:
                    continue
                rows.append(
                    {
                        "job": job,
                        "eval": latest,
                        "application": application,
                        "app_status": app_status,
                        "industry": category,
                        "official_url": safe_external_url(job.url),
                    }
                )
        total_rows = len(rows)
        total_pages = max(ceil(total_rows / PAGE_SIZE), 1)
        page = min(page, total_pages)
        start = (page - 1) * PAGE_SIZE
        page_rows = rows[start : start + PAGE_SIZE]
        prev_query = _page_query(filters, industry, page - 1) if page > 1 else None
        next_query = _page_query(filters, industry, page + 1) if page < total_pages else None
        controls = filter_controls(filters, industry)
        return templates.TemplateResponse(
            request,
            "jobs.html",
            {
                "rows": page_rows,
                "filters": filters,
                "filter_controls": controls,
                "filter_control_by_name": {control["name"]: control for control in controls},
                "industry": industry,
                "industry_tabs": industry_tabs(filters, industry),
                "page": page,
                "total_pages": total_pages,
                "total_rows": total_rows,
                "page_size": PAGE_SIZE,
                "prev_query": prev_query,
                "next_query": next_query,
            },
        )

    @app.get("/dashboard", response_class=HTMLResponse)
    def dashboard(request: Request):
        with create_session(db_path) as session:
            jobs = session.query(Job).all()
            applications = session.query(App).all()
            latest_run = session.query(Run).order_by(desc(Run.created_at)).first()
            open_jobs = [job for job in jobs if job.status in {"new", "live"}]
            open_by_industry = {industry: 0 for industry in CANONICAL_CATEGORIES}
            status_counts = {status: 0 for status in STATUS_FILTER_OPTIONS}
            app_counts = {status: 0 for status in APP_STATUS_OPTIONS}
            front_counts = {label: 0 for label in LABEL_FILTER_OPTIONS}
            for job in jobs:
                if job.status in status_counts:
                    status_counts[job.status] += 1
                if job.status in {"new", "live"}:
                    industry = industry_for_group(job.company_ref.group if job.company_ref else "")
                    if industry in open_by_industry:
                        open_by_industry[industry] += 1
                    latest = _preferred_eval(session, job.id)
                    if latest and latest.front in front_counts:
                        front_counts[latest.front] += 1
                    elif not latest:
                        front_counts["missing"] += 1
            for application in applications:
                if application.app_status in app_counts:
                    app_counts[application.app_status] += 1
            return templates.TemplateResponse(
                request,
                "dashboard.html",
                {
                    "open_positions": len(open_jobs),
                    "applications": len(applications),
                    "latest_run": latest_run,
                    "status_counts": status_counts,
                    "industry_counts": open_by_industry,
                    "app_counts": app_counts,
                    "front_counts": front_counts,
                    "max_industry_count": max(open_by_industry.values(), default=1) or 1,
                    "max_app_count": max(app_counts.values(), default=1) or 1,
                    "max_front_count": max(front_counts.values(), default=1) or 1,
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
                    "app_statuses": APP_STATUS_OPTIONS,
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


def _parse_multi_filter(request: Request, name: str, allowed: set[str]) -> set[str]:
    selected = set()
    for value in request.query_params.getlist(name):
        value = value.lower().strip()
        if value in allowed:
            selected.add(value)
    return selected


def _parse_industry_filter(request: Request) -> str:
    industry = request.query_params.get("industry", INDUSTRY_ALL).strip()
    return industry if industry in CANONICAL_CATEGORIES else INDUSTRY_ALL


def _matches_eval_filter(eval: Eval | None, field: str, selected: set[str]) -> bool:
    if not selected:
        return True
    if eval is None:
        return "missing" in selected
    return getattr(eval, field) in selected


def _page_query(filters: dict[str, set[str]], industry: str, page: int) -> str:
    return _query_string(filters, industry=industry, page=page)


def _query_string(
    filters: dict[str, set[str]],
    industry: str = INDUSTRY_ALL,
    page: int | None = None,
) -> str:
    params: list[tuple[str, str]] = []
    for name, values in filters.items():
        params.extend((name, value) for value in sorted(values))
    if industry != INDUSTRY_ALL:
        params.append(("industry", industry))
    if page is not None:
        params.append(("page", str(page)))
    return urlencode(params)


def filter_controls(filters: dict[str, set[str]], industry: str) -> list[dict[str, object]]:
    return [
        _filter_control("front", "Front", LABEL_FILTER_OPTIONS, filters, industry),
        _filter_control("h1b", "H-1B", LABEL_FILTER_OPTIONS, filters, industry),
        _filter_control("exp", "Exp", LABEL_FILTER_OPTIONS, filters, industry),
        _filter_control("status", "Status", STATUS_FILTER_OPTIONS, filters, industry),
        _filter_control("app_status", "App", APP_STATUS_OPTIONS, filters, industry),
    ]


def _filter_control(
    name: str,
    label: str,
    options: tuple[str, ...],
    filters: dict[str, set[str]],
    industry: str,
) -> dict[str, object]:
    selected = filters[name]
    summary = ", ".join(sorted(selected)) if selected else "All"
    clear_filters = {key: values for key, values in filters.items() if key != name}
    clear_query = _query_string(clear_filters, industry=industry)
    return {
        "name": name,
        "label": label,
        "options": options,
        "selected": selected,
        "summary": summary,
        "clear_href": f"/?{clear_query}" if clear_query else "/",
    }


def industry_tabs(filters: dict[str, set[str]], current: str) -> list[dict[str, object]]:
    tabs = []
    for industry in INDUSTRY_OPTIONS:
        query = _query_string(filters, industry=industry)
        tabs.append(
            {
                "label": industry,
                "active": industry == current,
                "href": f"/?{query}" if query else "/",
            }
        )
    return tabs


def industry_for_group(group: str) -> str:
    return GROUP_TO_CATEGORY.get(group, "Hedge Funds")


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
