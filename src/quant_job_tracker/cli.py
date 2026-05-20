from datetime import datetime
from pathlib import Path

import typer
import uvicorn
import httpx
from sqlalchemy import desc

from quant_job_tracker.config import DEFAULT_DB_PATH, POLICY_DIR
from quant_job_tracker.crawler.adapters import CareerPageBlockedError, GenericAdapter, clean_stored_title
from quant_job_tracker.crawler.categories import category_for_group
from quant_job_tracker.crawler.filters import keep_job_card
from quant_job_tracker.crawler.interactive_browser import InteractiveBrowserAdapter, html_to_text
from quant_job_tracker.crawler.job_sources import JOB_SOURCE_SEEDS
from quant_job_tracker.crawler.seeds import SEEDS, CompanySeed
from quant_job_tracker.crawler.service import (
    close_stale_jobs,
    prune_jobs_matching_url_patterns,
    upsert_company_job_source,
    upsert_company_seed,
    upsert_crawled_job,
)
from quant_job_tracker.db import create_session, init_db as create_tables
from quant_job_tracker.evaluator.classifier import HeuristicClassifier
from quant_job_tracker.evaluator.policy_maker import suggest_policy_updates
from quant_job_tracker.models import Eval, Job, Run
from quant_job_tracker.policy import load_policy_bundle

app = typer.Typer(name="qjt")
EVAL_MODEL = "heuristic-v2"
POLICY_VER = "v1"
KNOWN_NON_JOB_URL_PATTERNS_BY_COMPANY = {
    "Citadel": (
        "https://www.citadel.com/what-we-do/",
        "https://www.citadel.com/careers/quantitative-research/",
    ),
    "Citadel Securities": (
        "https://www.citadelsecurities.com/what-we-do/",
        "https://www.citadelsecurities.com/careers/quantitative-research/",
    ),
    "D. E. Shaw": ("https://www.deshaw.com/what-we-do/",),
    "Two Sigma": (
        "https://www.twosigma.com/businesses/",
        "https://www.twosigma.com/careers/quantitative-research-data-science/",
    ),
}


@app.command()
def init_db(db: Path = DEFAULT_DB_PATH) -> None:
    create_tables(db)
    typer.echo(f"Initialized {db}")


def _crawl_seeds(
    db: Path,
    seeds: list[CompanySeed],
    limit: int | None = None,
    interactive_browser: bool = False,
) -> tuple[int, int, int, str | None]:
    base_adapter = GenericAdapter()
    adapter = InteractiveBrowserAdapter(base_adapter) if interactive_browser else base_adapter
    selected_seeds = seeds[:limit] if limit is not None else seeds
    crawl_started = datetime.utcnow()
    successful_company_ids: list[int] = []
    companies_crawled = 0
    jobs_found = 0
    jobs_stored = 0
    issues: dict[str, list[str]] = {"bad_seed_url": [], "bot_blocked": [], "other": []}

    try:
        for seed in selected_seeds:
            try:
                company_id = upsert_company_seed(db, seed)
                prune_jobs_matching_url_patterns(
                    db, company_id, KNOWN_NON_JOB_URL_PATTERNS_BY_COMPANY.get(seed.name, ())
                )
                companies_crawled += 1
                if hasattr(adapter, "fetch_cards"):
                    cards = adapter.fetch_cards(seed.career_url)
                else:
                    html = adapter.fetch_html(seed.career_url)
                    cards = adapter.parse_cards(seed.career_url, html)
                successful_company_ids.append(company_id)
            except CareerPageBlockedError as exc:
                issues["bot_blocked"].append(f"{seed.name}: {exc}")
                continue
            except Exception as exc:
                _record_crawl_issue(issues, seed.name, exc)
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
                except CareerPageBlockedError as exc:
                    if seed.name in {"Citadel", "Citadel Securities"}:
                        jd = blocked_detail_listing_jd(seed.name, card)
                        upsert_crawled_job(
                            db,
                            company_id,
                            seed.name,
                            card,
                            jd,
                            "kept: official listing row; detail blocked by provider",
                        )
                        jobs_stored += 1
                        issues["bot_blocked"].append(
                            f"{seed.name} {card.url}: Detail page blocked; "
                            "stored official listing row"
                        )
                        continue
                    issues["bot_blocked"].append(f"{seed.name} {card.url}: {exc}")
                    continue
                except Exception as exc:
                    _record_crawl_issue(issues, f"{seed.name} {card.url}", exc)

        close_stale_jobs(db, successful_company_ids, crawl_started)
        return companies_crawled, jobs_found, jobs_stored, _format_crawl_issues(issues)
    finally:
        close = getattr(adapter, "close", None)
        if callable(close):
            close()


def _record_crawl_issue(issues: dict[str, list[str]], source: str, exc: Exception) -> None:
    if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 404:
        issues["bad_seed_url"].append(f"{source}: 404 Not Found")
    else:
        issues["other"].append(f"{source}: {exc}")


def _format_crawl_issues(issues: dict[str, list[str]]) -> str | None:
    sections = []
    labels = {
        "bad_seed_url": "Bad seed URL / 404",
        "bot_blocked": "Bot crawling prohibited / 403",
        "other": "Other crawl errors",
    }
    for key in ("bad_seed_url", "bot_blocked", "other"):
        rows = issues[key]
        if rows:
            sections.append(labels[key] + "\n" + "\n".join(f"- {row}" for row in rows))
    return "\n\n".join(sections) if sections else None


@app.command()
def crawl(
    db: Path = DEFAULT_DB_PATH,
    limit: int | None = None,
    interactive_browser: bool = typer.Option(
        False,
        "--interactive-browser",
        help="Use a visible Selenium browser for supported provider-blocked official pages.",
    ),
) -> None:
    create_tables(db)
    companies_crawled, jobs_found, jobs_stored, error = _crawl_seeds(
        db, SEEDS, limit, interactive_browser
    )
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


@app.command("import-saved-html")
def import_saved_html(
    db: Path = DEFAULT_DB_PATH,
    company: str = typer.Option(..., "--company", help="Target company name."),
    url: str = typer.Option(..., "--url", help="Official URL the HTML was saved from."),
    html: Path = typer.Option(..., "--html", help="Saved HTML file from your normal browser."),
) -> None:
    create_tables(db)
    seed = _seed_for_company(company, url)
    company_id = upsert_company_seed(db, seed)
    prune_jobs_matching_url_patterns(
        db, company_id, KNOWN_NON_JOB_URL_PATTERNS_BY_COMPANY.get(seed.name, ())
    )
    html_source = html.read_text(encoding="utf-8")
    adapter = GenericAdapter()
    cards = adapter.parse_cards(url, html_source)
    used_ajax_listing = False
    if not cards and company in {"Citadel", "Citadel Securities"}:
        cards = adapter.fetch_cards(url)
        used_ajax_listing = True
    jd = html_to_text(html_source)
    jobs_stored = 0
    for card in cards:
        keep, crawl_note = keep_job_card(seed.name, card.title, card.loc)
        if not keep:
            continue
        jd_for_card = blocked_detail_listing_jd(seed.name, card) if used_ajax_listing else jd
        upsert_crawled_job(
            db,
            company_id,
            seed.name,
            card,
            jd_for_card,
            f"Imported from saved official HTML. {crawl_note}",
        )
        jobs_stored += 1
    with create_session(db) as session:
        session.add(
            Run(
                kind="manual_import",
                status="success",
                jobs_found=len(cards),
                jobs_stored=jobs_stored,
                policy_ver=POLICY_VER,
                model=None,
            )
        )
        session.commit()
    typer.echo(f"Imported {jobs_stored} jobs from saved HTML")


def _seed_for_company(company: str, fallback_url: str) -> CompanySeed:
    for seed in SEEDS:
        if seed.name == company:
            return seed
    return CompanySeed(company, "unknown", fallback_url, "saved_html")


def blocked_detail_listing_jd(company: str, card) -> str:
    return (
        f"{card.title} | {company} official listing. Location: {card.loc}. "
        f"Official detail URL: {card.url}. Detail page blocked by provider during crawl; "
        "use the official link for the full job description."
    )


@app.command()
def collect_sources(db: Path = DEFAULT_DB_PATH) -> None:
    create_tables(db)
    for seed in SEEDS:
        upsert_company_seed(db, seed)
    count = 0
    for source in JOB_SOURCE_SEEDS:
        upsert_company_job_source(db, source)
        count += 1
    typer.echo(f"Stored {count} company job sources")


@app.command()
def sources(db: Path = DEFAULT_DB_PATH) -> None:
    create_tables(db)
    from quant_job_tracker.models import Company, CompanyJobSource

    with create_session(db) as session:
        rows = (
            session.query(CompanyJobSource, Company)
            .join(Company, Company.id == CompanyJobSource.company_id)
            .filter(CompanyJobSource.active.is_(True))
            .order_by(CompanyJobSource.company)
            .all()
        )
        for row, company in rows:
            category = category_for_group(company.group) if company.group != "unknown" else "Unknown"
            typer.echo(
                f"{row.company}\t{category}\t{row.source_type}\t{row.confidence}\t{row.source_url}"
            )


@app.command()
def eval_pending(db: Path = DEFAULT_DB_PATH) -> None:
    policy = load_policy_bundle(POLICY_DIR, "evaluator")
    classifier = HeuristicClassifier()
    with create_session(db) as session:
        jobs = session.query(Job).filter(Job.status.in_(["new", "live"])).all()
        count = 0
        for job in jobs:
            cleaned_title = clean_stored_title(job.title, job.jd)
            title_changed = cleaned_title != job.title
            if title_changed:
                job.title = cleaned_title
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
            if current_eval is not None and not title_changed:
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
