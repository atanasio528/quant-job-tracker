# Quant Job Tracker V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local quant job tracker that crawls official career pages, stores broad but relevant JDs, classifies jobs for front-quant/H-1B/junior fit, and exposes a compact dashboard for review and application tracking.

**Architecture:** Use a Python monolith with clear internal modules: `crawler`, `evaluator`, `policy`, `db`, `web`, and `cli`. SQLite is the source of truth. The first release ships a vertical slice with seeded firms, ATS adapters, policy markdown files, deterministic tests, a CLI pipeline, and a FastAPI/Jinja dashboard.

**Tech Stack:** Python 3.11+, FastAPI, Jinja2, SQLAlchemy 2, SQLite, Typer, Pydantic, httpx, BeautifulSoup4, pytest, respx.

---

## File Structure

Create this structure:

```text
quant-job-tracker/
  pyproject.toml
  README.md
  .gitignore
  data/.gitkeep
  policies/shared.md
  policies/crawler.md
  policies/evaluator.md
  policies/policy_maker.md
  src/quant_job_tracker/__init__.py
  src/quant_job_tracker/cli.py
  src/quant_job_tracker/config.py
  src/quant_job_tracker/db.py
  src/quant_job_tracker/models.py
  src/quant_job_tracker/policy.py
  src/quant_job_tracker/crawler/__init__.py
  src/quant_job_tracker/crawler/filters.py
  src/quant_job_tracker/crawler/seeds.py
  src/quant_job_tracker/crawler/adapters.py
  src/quant_job_tracker/crawler/service.py
  src/quant_job_tracker/evaluator/__init__.py
  src/quant_job_tracker/evaluator/classifier.py
  src/quant_job_tracker/evaluator/prompts.py
  src/quant_job_tracker/web/__init__.py
  src/quant_job_tracker/web/app.py
  src/quant_job_tracker/web/templates/base.html
  src/quant_job_tracker/web/templates/jobs.html
  src/quant_job_tracker/web/templates/job_detail.html
  tests/test_filters.py
  tests/test_models.py
  tests/test_policy.py
  tests/test_adapters.py
  tests/test_classifier.py
  tests/test_policy_maker.py
  tests/test_cli_pipeline.py
```

## Task 1: Project Scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `README.md`
- Create: `data/.gitkeep`
- Create: `src/quant_job_tracker/__init__.py`

- [ ] **Step 1: Create package metadata**

Write `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=69", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "quant-job-tracker"
version = "0.1.0"
description = "Local crawler, evaluator, and dashboard for front quant job applications."
requires-python = ">=3.11"
dependencies = [
  "beautifulsoup4>=4.12.3",
  "fastapi>=0.111.0",
  "httpx>=0.27.0",
  "jinja2>=3.1.4",
  "pydantic>=2.7.0",
  "python-multipart>=0.0.9",
  "sqlalchemy>=2.0.30",
  "typer>=0.12.3",
  "uvicorn>=0.30.0"
]

[project.optional-dependencies]
dev = [
  "pytest>=8.2.0",
  "respx>=0.21.1",
  "ruff>=0.5.0"
]

[project.scripts]
qjt = "quant_job_tracker.cli:app"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py311"
```

- [ ] **Step 2: Create ignore rules**

Write `.gitignore`:

```gitignore
.venv/
__pycache__/
.pytest_cache/
.ruff_cache/
*.pyc
data/*.db
data/*.sqlite
data/*.sqlite3
.env
```

- [ ] **Step 3: Create README**

Write `README.md`:

````markdown
# Quant Job Tracker

Local crawler, evaluator, and dashboard for front quant job applications.

V1 focuses on official career pages, US locations relevant to New York, Boston, Florida, New Jersey, and Chicago, and front quant roles suitable for an H-1B holder with 1 year of experience.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

Run the dashboard:

```bash
qjt init-db
qjt web
```
````

- [ ] **Step 4: Create package marker**

Write `src/quant_job_tracker/__init__.py`:

```python
__all__ = ["__version__"]

__version__ = "0.1.0"
```

- [ ] **Step 5: Run scaffold checks**

Run:

```bash
python -m pip install -e ".[dev]"
pytest
```

Expected: pytest collects no tests or passes once later tests exist.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml .gitignore README.md data/.gitkeep src/quant_job_tracker/__init__.py
git commit -m "chore: scaffold quant job tracker"
```

## Task 2: Policy Files

**Files:**
- Create: `policies/shared.md`
- Create: `policies/crawler.md`
- Create: `policies/evaluator.md`
- Create: `policies/policy_maker.md`
- Create: `src/quant_job_tracker/policy.py`
- Test: `tests/test_policy.py`

- [ ] **Step 1: Write failing policy loader tests**

Write `tests/test_policy.py`:

```python
from pathlib import Path

from quant_job_tracker.policy import load_policy_bundle


def test_load_policy_bundle_combines_shared_and_role(tmp_path: Path) -> None:
    policy_dir = tmp_path / "policies"
    policy_dir.mkdir()
    (policy_dir / "shared.md").write_text("# Shared\nTarget locations\n", encoding="utf-8")
    (policy_dir / "evaluator.md").write_text("# Evaluator\nClassify jobs\n", encoding="utf-8")

    bundle = load_policy_bundle(policy_dir, "evaluator")

    assert "Target locations" in bundle
    assert "Classify jobs" in bundle
    assert bundle.index("# Shared") < bundle.index("# Evaluator")


def test_load_policy_bundle_rejects_unknown_role(tmp_path: Path) -> None:
    policy_dir = tmp_path / "policies"
    policy_dir.mkdir()
    (policy_dir / "shared.md").write_text("# Shared\n", encoding="utf-8")

    try:
        load_policy_bundle(policy_dir, "missing")
    except FileNotFoundError as exc:
        assert "missing.md" in str(exc)
    else:
        raise AssertionError("Expected FileNotFoundError")
```

- [ ] **Step 2: Run failing test**

Run:

```bash
pytest tests/test_policy.py -v
```

Expected: FAIL because `quant_job_tracker.policy` does not exist.

- [ ] **Step 3: Implement policy loader**

Write `src/quant_job_tracker/policy.py`:

```python
from pathlib import Path


def load_policy_bundle(policy_dir: Path, role: str) -> str:
    shared_path = policy_dir / "shared.md"
    role_path = policy_dir / f"{role}.md"

    shared = shared_path.read_text(encoding="utf-8")
    role_text = role_path.read_text(encoding="utf-8")

    return f"{shared.rstrip()}\n\n---\n\n{role_text.rstrip()}\n"
```

- [ ] **Step 4: Create shared policy**

Write `policies/shared.md`:

```markdown
# Shared Quant Job Policy

## Candidate

- H-1B holder
- 1 year of work experience
- Relaxed junior bar

## Target Locations

Keep roles open to New York, Boston, Florida, New Jersey, or Chicago. Remote roles are acceptable only when they are open to one of those locations.

## Fields

- `front`: `green` or `red`
- `h1b`: `green`, `yellow`, or `red`
- `exp`: `green` or `red`
- `score`: integer from `0` to `100`
- `reason`: concise evidence-based explanation
- `flags`: compact tags
- `review`: `pending`, `approved`, `rejected`, or `needs_review`

## Front Quant Green

Quant Researcher, Alpha Researcher, Quant Trader, Algorithmic Trader, and firm-specific aliases that clearly involve alpha, signal research, systematic trading strategy research, or direct trading PnL research.

## Front Quant Red

Risk, model validation, execution services, transaction cost analysis, portfolio analytics, generic software engineering, data engineering, DevOps, operations, compliance, legal, HR, sales, client service, and middle-office roles.

## H-1B

`green`: appears adequate for an H-1B holder.

`yellow`: authorization language is unclear.

`red`: explicitly requires US citizenship, permanent residency, green card, or no sponsorship.

## Experience

`green`: reasonable to apply with 1 year of experience under a relaxed bar.

`red`: clearly too senior, including VP+ bank roles, team lead/head roles, PM-only roles, or explicit 5+ year requirements.

## Known Aliases

- Hudson River Trading: `Algorithm Developer` can be front quant when the JD says `Quant Researcher`, alpha, predictive modeling, or trading strategy research.
```

- [ ] **Step 5: Create crawler policy**

Write `policies/crawler.md`:

```markdown
# Crawler Policy

The crawler collects broadly from official company career pages.

Hard filters should only remove obvious noise. Keep ambiguous investment, trading, quant, research, and strategy jobs for evaluator review.

Reject obvious non-target functions: HR, legal, accounting, compliance, sales, client service, facilities, office management, DevOps, data engineering, security engineering, model risk, risk management, execution services, and generic software engineering.
```

- [ ] **Step 6: Create evaluator policy**

Write `policies/evaluator.md`:

```markdown
# Evaluator Policy

Read the full job description and classify the role. Do not rely only on title.

Return JSON with exactly these keys: `front`, `h1b`, `exp`, `score`, `reason`, `flags`.

Prefer keeping edge cases visible with honest low scores over silently rejecting unusual titles. Use `h1b=yellow` when sponsorship language is missing or unclear.
```

- [ ] **Step 7: Create policy maker policy**

Write `policies/policy_maker.md`:

```markdown
# Policy Maker Policy

Review crawler and evaluator results. Improve policies using evidence from false positives, false negatives, and reviewed jobs.

Do not make hard filters aggressive unless a pattern is consistently irrelevant. Add firm-specific aliases only when job descriptions support the mapping.
```

- [ ] **Step 8: Run policy tests**

Run:

```bash
pytest tests/test_policy.py -v
```

Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add policies src/quant_job_tracker/policy.py tests/test_policy.py
git commit -m "feat: add markdown policy system"
```

## Task 3: Database Models

**Files:**
- Create: `src/quant_job_tracker/config.py`
- Create: `src/quant_job_tracker/models.py`
- Create: `src/quant_job_tracker/db.py`
- Test: `tests/test_models.py`

- [ ] **Step 1: Write failing model tests**

Write `tests/test_models.py`:

```python
from pathlib import Path

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
```

- [ ] **Step 2: Run failing tests**

Run:

```bash
pytest tests/test_models.py -v
```

Expected: FAIL because DB modules do not exist.

- [ ] **Step 3: Implement config**

Write `src/quant_job_tracker/config.py`:

```python
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_DB_PATH = DATA_DIR / "quant_job_tracker.sqlite3"
POLICY_DIR = PROJECT_ROOT / "policies"
```

- [ ] **Step 4: Implement models**

Write `src/quant_job_tracker/models.py`:

```python
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    group: Mapped[str] = mapped_column(String(80))
    career_url: Mapped[str] = mapped_column(Text)
    ats: Mapped[str | None] = mapped_column(String(80), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    jobs: Mapped[list["Job"]] = relationship(back_populates="company_ref")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    company: Mapped[str] = mapped_column(String(200), index=True)
    title: Mapped[str] = mapped_column(String(300), index=True)
    loc: Mapped[str] = mapped_column(String(300), index=True)
    url: Mapped[str] = mapped_column(Text, unique=True)
    source: Mapped[str] = mapped_column(String(120))
    jd: Mapped[str] = mapped_column(Text)
    jd_hash: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(40), default="new", index=True)
    first_seen: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    crawl_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    company_ref: Mapped[Company] = relationship(back_populates="jobs")
    evals: Mapped[list["Eval"]] = relationship(back_populates="job")


class Eval(Base):
    __tablename__ = "evals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), index=True)
    front: Mapped[str] = mapped_column(String(20), index=True)
    h1b: Mapped[str] = mapped_column(String(20), index=True)
    exp: Mapped[str] = mapped_column(String(20), index=True)
    score: Mapped[int] = mapped_column(Integer, index=True)
    reason: Mapped[str] = mapped_column(Text)
    flags: Mapped[str] = mapped_column(Text, default="")
    model: Mapped[str] = mapped_column(String(120))
    policy_ver: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job: Mapped[Job] = relationship(back_populates="evals")


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), index=True)
    decision: Mapped[str] = mapped_column(String(40), index=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewer: Mapped[str] = mapped_column(String(80), default="user")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class App(Base):
    __tablename__ = "apps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), unique=True, index=True)
    app_status: Mapped[str] = mapped_column(String(40), default="not_started", index=True)
    deadline: Mapped[str | None] = mapped_column(String(40), nullable=True)
    priority: Mapped[str | None] = mapped_column(String(40), nullable=True)
    applied_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    contact: Mapped[str | None] = mapped_column(Text, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kind: Mapped[str] = mapped_column(String(40), index=True)
    status: Mapped[str] = mapped_column(String(40), index=True)
    jobs_found: Mapped[int] = mapped_column(Integer, default=0)
    jobs_stored: Mapped[int] = mapped_column(Integer, default=0)
    jobs_evaluated: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    policy_ver: Mapped[str] = mapped_column(String(80), default="v1")
    model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

- [ ] **Step 5: Implement DB helpers**

Write `src/quant_job_tracker/db.py`:

```python
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from quant_job_tracker.models import Base


def engine_for(db_path: Path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{db_path}", future=True)


def init_db(db_path: Path) -> None:
    engine = engine_for(db_path)
    Base.metadata.create_all(engine)


@contextmanager
def create_session(db_path: Path) -> Iterator[Session]:
    engine = engine_for(db_path)
    with Session(engine) as session:
        yield session
```

- [ ] **Step 6: Run model tests**

Run:

```bash
pytest tests/test_models.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/quant_job_tracker/config.py src/quant_job_tracker/models.py src/quant_job_tracker/db.py tests/test_models.py
git commit -m "feat: add sqlite data model"
```

## Task 4: Crawler Filters and Seeds

**Files:**
- Create: `src/quant_job_tracker/crawler/__init__.py`
- Create: `src/quant_job_tracker/crawler/filters.py`
- Create: `src/quant_job_tracker/crawler/seeds.py`
- Test: `tests/test_filters.py`

- [ ] **Step 1: Write failing filter tests**

Write `tests/test_filters.py`:

```python
from quant_job_tracker.crawler.filters import keep_job_card


def test_keep_front_quant_alias() -> None:
    keep, note = keep_job_card("Hudson River Trading", "Algorithm Developer", "New York")
    assert keep is True
    assert "kept" in note


def test_reject_obvious_noise() -> None:
    keep, note = keep_job_card("AQR", "Compliance Analyst", "New York")
    assert keep is False
    assert "compliance" in note


def test_reject_wrong_location() -> None:
    keep, note = keep_job_card("Jane Street", "Quantitative Trader", "London")
    assert keep is False
    assert "location" in note


def test_keep_ambiguous_research_role() -> None:
    keep, note = keep_job_card("Point72", "Research Analyst", "New York")
    assert keep is True
    assert "ambiguous" in note
```

- [ ] **Step 2: Run failing filter tests**

Run:

```bash
pytest tests/test_filters.py -v
```

Expected: FAIL because crawler filters do not exist.

- [ ] **Step 3: Implement filters**

Write `src/quant_job_tracker/crawler/filters.py`:

```python
TARGET_LOCATION_TERMS = {
    "new york",
    "nyc",
    "boston",
    "florida",
    "miami",
    "palm beach",
    "new jersey",
    "jersey city",
    "chicago",
    "remote",
    "united states",
}

NOISE_TERMS = {
    "accounting",
    "client service",
    "compliance",
    "data engineer",
    "devops",
    "facilities",
    "human resources",
    "hr ",
    "legal",
    "model risk",
    "office manager",
    "operations",
    "recruiter",
    "risk management",
    "sales",
    "security engineer",
    "software engineer",
    "tax",
}

AMBIGUOUS_KEEP_TERMS = {
    "alpha",
    "algorithm",
    "investment",
    "quant",
    "research",
    "strategy",
    "systematic",
    "trader",
    "trading",
}


def keep_job_card(company: str, title: str, loc: str) -> tuple[bool, str]:
    title_l = title.lower()
    loc_l = loc.lower()

    if not any(term in loc_l for term in TARGET_LOCATION_TERMS):
        return False, "rejected: location outside target US markets"

    for term in NOISE_TERMS:
        if term in title_l:
            return False, f"rejected: obvious noise term '{term}'"

    if any(term in title_l for term in AMBIGUOUS_KEEP_TERMS):
        return True, "kept: ambiguous or relevant quant/trading/research signal"

    return True, "kept: broad crawler policy preserves non-noise roles for evaluator"
```

- [ ] **Step 4: Implement seed list**

Write `src/quant_job_tracker/crawler/seeds.py`:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class CompanySeed:
    name: str
    group: str
    career_url: str
    ats: str | None = None
    notes: str | None = None


SEEDS: list[CompanySeed] = [
    CompanySeed("Hudson River Trading", "prop", "https://www.hudsonrivertrading.com/careers/", "generic", "HRT Algorithm Developer may mean Quant Researcher."),
    CompanySeed("Jane Street", "prop", "https://www.janestreet.com/join-jane-street/open-roles/", "generic"),
    CompanySeed("D. E. Shaw", "quant_hedge_fund", "https://www.deshaw.com/careers", "generic"),
    CompanySeed("Two Sigma", "quant_hedge_fund", "https://www.twosigma.com/careers/", "generic"),
    CompanySeed("Citadel", "multi_manager", "https://www.citadel.com/careers/open-opportunities/", "generic"),
    CompanySeed("Citadel Securities", "market_maker", "https://www.citadelsecurities.com/careers/open-opportunities/", "generic"),
    CompanySeed("Point72", "multi_manager", "https://point72.com/careers/", "generic"),
    CompanySeed("Cubist Systematic Strategies", "quant_hedge_fund", "https://point72.com/cubist/careers/", "generic"),
    CompanySeed("Millennium Management", "multi_manager", "https://www.mlp.com/careers/", "generic"),
    CompanySeed("Balyasny Asset Management", "multi_manager", "https://www.bamfunds.com/careers/", "generic"),
    CompanySeed("Squarepoint Capital", "quant_hedge_fund", "https://www.squarepoint-capital.com/careers", "generic"),
    CompanySeed("Qube Research & Technologies", "quant_hedge_fund", "https://www.qube-rt.com/careers/", "generic"),
]
```

- [ ] **Step 5: Run filter tests**

Run:

```bash
pytest tests/test_filters.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/quant_job_tracker/crawler tests/test_filters.py
git commit -m "feat: add crawler filters and seeds"
```

## Task 5: ATS Adapters

**Files:**
- Create: `src/quant_job_tracker/crawler/adapters.py`
- Test: `tests/test_adapters.py`

- [ ] **Step 1: Write failing adapter tests**

Write `tests/test_adapters.py`:

```python
import httpx
import respx

from quant_job_tracker.crawler.adapters import GenericAdapter, JobCard


def test_generic_adapter_extracts_links_from_html() -> None:
    html = """
    <html><body>
      <a href="/jobs/1">Quantitative Researcher</a>
      <a href="/jobs/2">Compliance Analyst</a>
    </body></html>
    """
    adapter = GenericAdapter()
    cards = adapter.parse_cards("https://example.com/careers", html)

    assert JobCard(title="Quantitative Researcher", loc="Unknown", url="https://example.com/jobs/1") in cards
    assert JobCard(title="Compliance Analyst", loc="Unknown", url="https://example.com/jobs/2") in cards


@respx.mock
def test_generic_adapter_fetches_jd() -> None:
    respx.get("https://example.com/jobs/1").mock(return_value=httpx.Response(200, text="<main>Alpha research role</main>"))
    adapter = GenericAdapter()

    jd = adapter.fetch_jd("https://example.com/jobs/1")

    assert "Alpha research role" in jd
```

- [ ] **Step 2: Run failing adapter tests**

Run:

```bash
pytest tests/test_adapters.py -v
```

Expected: FAIL because adapters do not exist.

- [ ] **Step 3: Implement generic adapter**

Write `src/quant_job_tracker/crawler/adapters.py`:

```python
from dataclasses import dataclass
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup


@dataclass(frozen=True)
class JobCard:
    title: str
    loc: str
    url: str


class GenericAdapter:
    def parse_cards(self, base_url: str, html: str) -> list[JobCard]:
        soup = BeautifulSoup(html, "html.parser")
        cards: list[JobCard] = []
        for link in soup.find_all("a", href=True):
            title = " ".join(link.get_text(" ", strip=True).split())
            if len(title) < 4:
                continue
            title_l = title.lower()
            if not any(term in title_l for term in ("quant", "trader", "research", "algorithm", "alpha", "investment", "strategy", "compliance")):
                continue
            cards.append(JobCard(title=title, loc="Unknown", url=urljoin(base_url, link["href"])))
        return cards

    def fetch_html(self, url: str) -> str:
        with httpx.Client(timeout=20.0, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.text

    def fetch_jd(self, url: str) -> str:
        html = self.fetch_html(url)
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        return " ".join(soup.get_text(" ", strip=True).split())
```

- [ ] **Step 4: Run adapter tests**

Run:

```bash
pytest tests/test_adapters.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/quant_job_tracker/crawler/adapters.py tests/test_adapters.py
git commit -m "feat: add generic career page adapter"
```

## Task 6: Crawler Service

**Files:**
- Create: `src/quant_job_tracker/crawler/service.py`
- Test: `tests/test_cli_pipeline.py`

- [ ] **Step 1: Write failing service smoke test**

Write `tests/test_cli_pipeline.py`:

```python
from pathlib import Path

from quant_job_tracker.crawler.adapters import JobCard
from quant_job_tracker.crawler.service import upsert_crawled_job
from quant_job_tracker.db import create_session, init_db
from quant_job_tracker.models import Company, Job


def test_upsert_crawled_job_creates_and_updates(tmp_path: Path) -> None:
    db_path = tmp_path / "qjt.sqlite3"
    init_db(db_path)
    with create_session(db_path) as session:
        company = Company(name="Test Fund", group="quant", career_url="https://example.com", active=True)
        session.add(company)
        session.commit()
        company_id = company.id

    card = JobCard(title="Quant Researcher", loc="New York", url="https://example.com/job/1")
    upsert_crawled_job(db_path, company_id, "Test Fund", card, "Alpha research JD", "kept")
    upsert_crawled_job(db_path, company_id, "Test Fund", card, "Alpha research JD updated", "kept")

    with create_session(db_path) as session:
        jobs = session.query(Job).all()
        assert len(jobs) == 1
        assert jobs[0].jd == "Alpha research JD updated"
```

- [ ] **Step 2: Run failing service test**

Run:

```bash
pytest tests/test_cli_pipeline.py -v
```

Expected: FAIL because crawler service does not exist.

- [ ] **Step 3: Implement crawler service**

Write `src/quant_job_tracker/crawler/service.py`:

```python
from datetime import datetime
from hashlib import sha256
from pathlib import Path

from quant_job_tracker.crawler.adapters import JobCard
from quant_job_tracker.db import create_session
from quant_job_tracker.models import Job


def hash_jd(jd: str) -> str:
    return sha256(jd.encode("utf-8")).hexdigest()


def upsert_crawled_job(
    db_path: Path,
    company_id: int,
    company: str,
    card: JobCard,
    jd: str,
    crawl_note: str,
) -> None:
    now = datetime.utcnow()
    with create_session(db_path) as session:
        existing = session.query(Job).filter_by(url=card.url).one_or_none()
        if existing:
            existing.title = card.title
            existing.loc = card.loc
            existing.jd = jd
            existing.jd_hash = hash_jd(jd)
            existing.status = "live"
            existing.last_seen = now
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
                    jd_hash=hash_jd(jd),
                    status="new",
                    first_seen=now,
                    last_seen=now,
                    crawl_note=crawl_note,
                )
            )
        session.commit()
```

- [ ] **Step 4: Run service test**

Run:

```bash
pytest tests/test_cli_pipeline.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/quant_job_tracker/crawler/service.py tests/test_cli_pipeline.py
git commit -m "feat: store crawled jobs"
```

## Task 7: Evaluator Classifier

**Files:**
- Create: `src/quant_job_tracker/evaluator/__init__.py`
- Create: `src/quant_job_tracker/evaluator/classifier.py`
- Create: `src/quant_job_tracker/evaluator/prompts.py`
- Test: `tests/test_classifier.py`

- [ ] **Step 1: Write failing classifier tests**

Write `tests/test_classifier.py`:

```python
from quant_job_tracker.evaluator.classifier import HeuristicClassifier


def test_classifier_marks_front_quant_green() -> None:
    result = HeuristicClassifier().classify(
        title="Algorithm Developer",
        jd="This Quant Researcher role develops alpha signals and predictive trading strategies.",
        policy="HRT Algorithm Developer can be front quant.",
    )

    assert result.front == "green"
    assert result.exp == "green"
    assert result.score >= 70


def test_classifier_marks_green_card_requirement_red() -> None:
    result = HeuristicClassifier().classify(
        title="Quant Researcher",
        jd="Applicants must be US citizens or green card holders. No sponsorship.",
        policy="",
    )

    assert result.h1b == "red"


def test_classifier_marks_senior_role_exp_red() -> None:
    result = HeuristicClassifier().classify(
        title="VP Quant Research",
        jd="Requires 8+ years of experience leading a team.",
        policy="",
    )

    assert result.exp == "red"
```

- [ ] **Step 2: Run failing classifier tests**

Run:

```bash
pytest tests/test_classifier.py -v
```

Expected: FAIL because evaluator modules do not exist.

- [ ] **Step 3: Implement prompt builder**

Write `src/quant_job_tracker/evaluator/prompts.py`:

```python
def build_evaluator_prompt(policy: str, title: str, company: str, loc: str, jd: str) -> str:
    return f"""Use the policy below to classify this job.

POLICY:
{policy}

JOB:
Company: {company}
Title: {title}
Location: {loc}
JD:
{jd}

Return JSON with keys: front, h1b, exp, score, reason, flags.
"""
```

- [ ] **Step 4: Implement heuristic classifier**

Write `src/quant_job_tracker/evaluator/classifier.py`:

```python
from pydantic import BaseModel, Field


class EvalResult(BaseModel):
    front: str
    h1b: str
    exp: str
    score: int = Field(ge=0, le=100)
    reason: str
    flags: str = ""


class HeuristicClassifier:
    def classify(self, title: str, jd: str, policy: str) -> EvalResult:
        text = f"{title}\n{jd}\n{policy}".lower()
        front_green_terms = ["alpha", "quant researcher", "quantitative researcher", "quant trader", "quantitative trader", "trading strategy", "predictive"]
        front_red_terms = ["risk", "model validation", "execution services", "portfolio analytics", "software engineer", "data engineer"]
        visa_red_terms = ["us citizen", "u.s. citizen", "green card", "permanent resident", "no sponsorship"]
        senior_terms = ["vp ", "vice president", "director", "head of", "lead a team", "8+ years", "7+ years", "6+ years", "5+ years"]

        front = "green" if any(term in text for term in front_green_terms) else "red"
        if any(term in text for term in front_red_terms):
            front = "red"

        h1b = "red" if any(term in text for term in visa_red_terms) else "yellow"
        exp = "red" if any(term in text for term in senior_terms) else "green"

        score = 50
        if front == "green":
            score += 30
        if h1b == "red":
            score -= 25
        if exp == "red":
            score -= 25
        score = max(0, min(100, score))

        flags = []
        if h1b == "yellow":
            flags.append("visa_unclear")
        if exp == "red":
            flags.append("senior")
        if "algorithm developer" in title.lower():
            flags.append("title_alias")

        return EvalResult(
            front=front,
            h1b=h1b,
            exp=exp,
            score=score,
            reason=f"front={front}, h1b={h1b}, exp={exp} based on title and JD evidence",
            flags=",".join(flags),
        )
```

- [ ] **Step 5: Run classifier tests**

Run:

```bash
pytest tests/test_classifier.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/quant_job_tracker/evaluator tests/test_classifier.py
git commit -m "feat: add evaluator classifier"
```

## Task 8: CLI Pipeline

**Files:**
- Create: `src/quant_job_tracker/cli.py`
- Modify: `tests/test_cli_pipeline.py`

- [ ] **Step 1: Add CLI import smoke test**

Append to `tests/test_cli_pipeline.py`:

```python
def test_cli_app_imports() -> None:
    from quant_job_tracker.cli import app

    assert app.info.name == "qjt"
```

- [ ] **Step 2: Run failing CLI test**

Run:

```bash
pytest tests/test_cli_pipeline.py::test_cli_app_imports -v
```

Expected: FAIL because `cli.py` does not exist.

- [ ] **Step 3: Implement CLI**

Write `src/quant_job_tracker/cli.py`:

```python
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
```

- [ ] **Step 4: Run CLI tests**

Run:

```bash
pytest tests/test_cli_pipeline.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/quant_job_tracker/cli.py tests/test_cli_pipeline.py
git commit -m "feat: add cli pipeline commands"
```

## Task 9: Web Dashboard

**Files:**
- Create: `src/quant_job_tracker/web/__init__.py`
- Create: `src/quant_job_tracker/web/app.py`
- Create: `src/quant_job_tracker/web/templates/base.html`
- Create: `src/quant_job_tracker/web/templates/jobs.html`
- Create: `src/quant_job_tracker/web/templates/job_detail.html`

- [ ] **Step 1: Implement FastAPI app**

Write `src/quant_job_tracker/web/app.py`:

```python
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import desc

from quant_job_tracker.config import DEFAULT_DB_PATH
from quant_job_tracker.db import create_session, init_db
from quant_job_tracker.models import Eval, Job

TEMPLATE_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


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
        return templates.TemplateResponse("jobs.html", {"request": request, "rows": rows})

    @app.get("/jobs/{job_id}", response_class=HTMLResponse)
    def job_detail(request: Request, job_id: int):
        with create_session(db_path) as session:
            job = session.query(Job).filter_by(id=job_id).one()
            evals = session.query(Eval).filter_by(job_id=job_id).order_by(desc(Eval.created_at)).all()
            return templates.TemplateResponse("job_detail.html", {"request": request, "job": job, "evals": evals})

    return app
```

- [ ] **Step 2: Implement base template**

Write `src/quant_job_tracker/web/templates/base.html`:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Quant Job Tracker</title>
    <style>
      body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 0; color: #172026; background: #f6f8fa; }
      header { background: #12212f; color: white; padding: 14px 24px; }
      main { padding: 24px; }
      table { width: 100%; border-collapse: collapse; background: white; }
      th, td { padding: 10px 12px; border-bottom: 1px solid #e5e8eb; text-align: left; font-size: 14px; }
      th { background: #eef2f5; font-weight: 650; }
      a { color: #075985; text-decoration: none; }
      .pill { border-radius: 999px; padding: 3px 8px; font-size: 12px; font-weight: 700; }
      .green { background: #d9fbe5; color: #075e2b; }
      .yellow { background: #fff4c2; color: #765900; }
      .red { background: #ffe1df; color: #8a1f17; }
      .muted { color: #66717c; }
      pre { white-space: pre-wrap; background: white; padding: 16px; border: 1px solid #e5e8eb; }
    </style>
  </head>
  <body>
    <header><strong>Quant Job Tracker</strong></header>
    <main>{% block content %}{% endblock %}</main>
  </body>
</html>
```

- [ ] **Step 3: Implement jobs table**

Write `src/quant_job_tracker/web/templates/jobs.html`:

```html
{% extends "base.html" %}
{% block content %}
<h1>Jobs</h1>
<table>
  <thead>
    <tr>
      <th>Company</th><th>Title</th><th>Location</th><th>Front</th><th>H-1B</th><th>Exp</th><th>Score</th><th>Flags</th>
    </tr>
  </thead>
  <tbody>
  {% for row in rows %}
    <tr>
      <td>{{ row.job.company }}</td>
      <td><a href="/jobs/{{ row.job.id }}">{{ row.job.title }}</a></td>
      <td>{{ row.job.loc }}</td>
      {% if row.eval %}
        <td><span class="pill {{ row.eval.front }}">{{ row.eval.front }}</span></td>
        <td><span class="pill {{ row.eval.h1b }}">{{ row.eval.h1b }}</span></td>
        <td><span class="pill {{ row.eval.exp }}">{{ row.eval.exp }}</span></td>
        <td>{{ row.eval.score }}</td>
        <td class="muted">{{ row.eval.flags }}</td>
      {% else %}
        <td colspan="5" class="muted">not evaluated</td>
      {% endif %}
    </tr>
  {% endfor %}
  </tbody>
</table>
{% endblock %}
```

- [ ] **Step 4: Implement job detail**

Write `src/quant_job_tracker/web/templates/job_detail.html`:

```html
{% extends "base.html" %}
{% block content %}
<p><a href="/">Back to jobs</a></p>
<h1>{{ job.title }}</h1>
<p><strong>{{ job.company }}</strong> · {{ job.loc }} · <a href="{{ job.url }}">Official posting</a></p>

<h2>Evaluations</h2>
{% for eval in evals %}
  <p>
    <span class="pill {{ eval.front }}">front {{ eval.front }}</span>
    <span class="pill {{ eval.h1b }}">h1b {{ eval.h1b }}</span>
    <span class="pill {{ eval.exp }}">exp {{ eval.exp }}</span>
    <strong>{{ eval.score }}</strong>
  </p>
  <p>{{ eval.reason }}</p>
{% endfor %}

<h2>Stored JD</h2>
<pre>{{ job.jd }}</pre>
{% endblock %}
```

- [ ] **Step 5: Run web smoke command**

Run:

```bash
qjt init-db
python -c "from quant_job_tracker.web.app import create_app; app = create_app(); print(app.title)"
```

Expected output includes `Quant Job Tracker`.

- [ ] **Step 6: Commit**

```bash
git add src/quant_job_tracker/web
git commit -m "feat: add job dashboard"
```

## Task 10: Policy Maker and Run History

**Files:**
- Create: `src/quant_job_tracker/evaluator/policy_maker.py`
- Modify: `src/quant_job_tracker/cli.py`
- Modify: `src/quant_job_tracker/web/app.py`
- Modify: `src/quant_job_tracker/web/templates/base.html`
- Create: `src/quant_job_tracker/web/templates/runs.html`
- Test: `tests/test_policy_maker.py`

- [ ] **Step 1: Write failing policy maker test**

Write `tests/test_policy_maker.py`:

```python
from quant_job_tracker.evaluator.policy_maker import suggest_policy_updates


def test_policy_maker_suggests_alias_review() -> None:
    suggestions = suggest_policy_updates(
        [
            {"title": "Algorithm Developer", "company": "Hudson River Trading", "front": "green", "flags": "title_alias"},
            {"title": "Risk Quant", "company": "Bank", "front": "red", "flags": "risk"},
        ]
    )

    assert "Hudson River Trading" in suggestions
    assert "title alias" in suggestions.lower()
```

- [ ] **Step 2: Run failing policy maker test**

Run:

```bash
pytest tests/test_policy_maker.py -v
```

Expected: FAIL because `policy_maker.py` does not exist.

- [ ] **Step 3: Implement policy maker suggestions**

Write `src/quant_job_tracker/evaluator/policy_maker.py`:

```python
def suggest_policy_updates(rows: list[dict[str, str]]) -> str:
    alias_rows = [row for row in rows if "title_alias" in row.get("flags", "")]
    risk_rows = [row for row in rows if "risk" in row.get("flags", "")]

    lines = ["# Policy Maker Suggestions", ""]
    if alias_rows:
        lines.append("## Title Aliases")
        for row in alias_rows:
            lines.append(
                f"- Review title alias for {row.get('company', 'Unknown')}: "
                f"`{row.get('title', 'Unknown')}` classified as `{row.get('front', 'unknown')}`."
            )
        lines.append("")
    if risk_rows:
        lines.append("## Hard Filter Candidates")
        lines.append("- Risk-related titles appeared in rejected rows; keep `risk` terms in crawler hard-noise policy.")
        lines.append("")
    if len(lines) == 2:
        lines.append("No policy changes suggested from the current reviewed rows.")
    return "\n".join(lines).rstrip() + "\n"
```

- [ ] **Step 4: Extend CLI with run logging and policy maker report**

Modify `src/quant_job_tracker/cli.py` to include `Run`, `desc`, and the new command:

```python
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
        session.add(Run(kind="eval", status="success", jobs_evaluated=count, model="heuristic-v1", policy_ver="v1"))
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
```

- [ ] **Step 5: Extend web app with run history route**

Modify `src/quant_job_tracker/web/app.py` so it imports `Run` and adds this route inside `create_app`:

```python
    @app.get("/runs", response_class=HTMLResponse)
    def runs(request: Request):
        with create_session(db_path) as session:
            rows = session.query(Run).order_by(desc(Run.created_at)).limit(100).all()
        return templates.TemplateResponse("runs.html", {"request": request, "rows": rows})
```

- [ ] **Step 6: Add navigation link**

In `src/quant_job_tracker/web/templates/base.html`, replace the header with:

```html
    <header>
      <strong>Quant Job Tracker</strong>
      <nav style="display:inline-flex; gap:14px; margin-left:24px;">
        <a style="color:white;" href="/">Jobs</a>
        <a style="color:white;" href="/runs">Run History</a>
      </nav>
    </header>
```

- [ ] **Step 7: Add run history template**

Write `src/quant_job_tracker/web/templates/runs.html`:

```html
{% extends "base.html" %}
{% block content %}
<h1>Run History</h1>
<table>
  <thead>
    <tr>
      <th>Time</th><th>Kind</th><th>Status</th><th>Found</th><th>Stored</th><th>Evaluated</th><th>Policy</th><th>Model</th><th>Error</th>
    </tr>
  </thead>
  <tbody>
  {% for run in rows %}
    <tr>
      <td>{{ run.created_at }}</td>
      <td>{{ run.kind }}</td>
      <td>{{ run.status }}</td>
      <td>{{ run.jobs_found }}</td>
      <td>{{ run.jobs_stored }}</td>
      <td>{{ run.jobs_evaluated }}</td>
      <td>{{ run.policy_ver }}</td>
      <td>{{ run.model or "" }}</td>
      <td class="muted">{{ run.error or "" }}</td>
    </tr>
  {% endfor %}
  </tbody>
</table>
{% endblock %}
```

- [ ] **Step 8: Run tests**

Run:

```bash
pytest tests/test_policy_maker.py tests/test_cli_pipeline.py -v
```

Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add src/quant_job_tracker/evaluator/policy_maker.py src/quant_job_tracker/cli.py src/quant_job_tracker/web tests/test_policy_maker.py
git commit -m "feat: add policy maker report and run history"
```

## Task 11: Final Verification

**Files:**
- Modify only if verification reveals a defect.

- [ ] **Step 1: Run full tests**

Run:

```bash
pytest -v
```

Expected: PASS.

- [ ] **Step 2: Run lint**

Run:

```bash
ruff check .
```

Expected: PASS.

- [ ] **Step 3: Initialize local DB**

Run:

```bash
qjt init-db
```

Expected output includes `Initialized`.

- [ ] **Step 4: Start dashboard manually**

Run:

```bash
qjt web
```

Expected: FastAPI starts on `http://127.0.0.1:8000`.

- [ ] **Step 5: Commit verification fixes if needed**

If files changed:

```bash
git add .
git commit -m "fix: address v1 verification issues"
```

If no files changed, do not create an empty commit.

## Self-Review

Spec coverage:

- Official career page crawling: Tasks 4, 5, 6.
- Broad negative filtering: Task 4.
- JD storage in local DB: Tasks 3 and 6.
- Evaluator labels `front`, `h1b`, `exp`, `score`, `reason`, `flags`: Task 7.
- Markdown role policies: Task 2.
- Dashboard: Task 9.
- Application tracking schema: Task 3.
- Run history is implemented in Task 10.
- Policy maker report is implemented in Task 10, with future automation left for later once real eval data exists.

Placeholder scan:

- No banned planning tokens or undefined future steps are required for V1 execution.

Type consistency:

- DB model fields match the spec and dashboard templates.
- Classifier output fields match `Eval` fields.
- CLI command names match README examples.
