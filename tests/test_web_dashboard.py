from pathlib import Path

from fastapi.testclient import TestClient

from quant_job_tracker.db import create_session, init_db
from quant_job_tracker.models import App, Company, Eval, Job, Review, Run


def add_test_job(db_path: Path) -> int:
    with create_session(db_path) as session:
        company = Company(
            name="Test Fund",
            group="quant",
            career_url="https://example.com",
            active=True,
        )
        session.add(company)
        session.flush()
        job = Job(
            company_id=company.id,
            company=company.name,
            title="Quant Researcher",
            loc="New York",
            url="https://example.com/job/1",
            source="official",
            jd="Alpha research role",
            jd_hash="abc",
            status="new",
        )
        session.add(job)
        session.commit()
        return job.id


def test_web_dashboard_lists_jobs_and_detail(tmp_path: Path) -> None:
    from quant_job_tracker.web.app import create_app

    db_path = tmp_path / "qjt.sqlite3"
    init_db(db_path)
    with create_session(db_path) as session:
        company = Company(
            name="Test Fund",
            group="quant",
            career_url="https://example.com",
            active=True,
        )
        session.add(company)
        session.flush()
        job = Job(
            company_id=company.id,
            company=company.name,
            title="Quant Researcher",
            loc="New York",
            url="https://example.com/job/1",
            source="official",
            jd="Alpha research role",
            jd_hash="abc",
            status="new",
        )
        session.add(job)
        session.flush()
        session.add(
            Eval(
                job_id=job.id,
                jd_hash=job.jd_hash,
                front="green",
                h1b="yellow",
                exp="green",
                score=85,
                reason="Strong front-office fit",
                flags="visa_unclear",
                model="test",
                policy_ver="v1",
            )
        )
        session.commit()
        job_id = job.id

    client = TestClient(create_app(db_path))

    jobs_response = client.get("/")
    assert jobs_response.status_code == 200
    assert "Quant Researcher" in jobs_response.text
    assert "visa_unclear" in jobs_response.text
    assert "<th>Official</th>" not in jobs_response.text
    assert 'href="https://example.com/job/1"' in jobs_response.text
    assert f'href="/jobs/{job_id}">not_started</a>' in jobs_response.text
    assert f'href="/jobs/{job_id}">Quant Researcher</a>' not in jobs_response.text

    detail_response = client.get(f"/jobs/{job_id}")
    assert detail_response.status_code == 200
    assert "Official posting" in detail_response.text
    assert "Strong front-office fit" in detail_response.text
    assert "Alpha research role" in detail_response.text
    assert '<article class="jd-card">' in detail_response.text
    assert "<pre>" not in detail_response.text


def test_web_dashboard_filters_eval_fields_and_status(tmp_path: Path) -> None:
    from quant_job_tracker.web.app import create_app

    db_path = tmp_path / "qjt.sqlite3"
    init_db(db_path)
    with create_session(db_path) as session:
        company = Company(
            name="Test Fund",
            group="quant",
            career_url="https://example.com",
            active=True,
        )
        session.add(company)
        session.flush()
        green_job = Job(
            company_id=company.id,
            company=company.name,
            title="Quant Trading Intern",
            loc="New York",
            url="https://example.com/job/green",
            source="official",
            jd="Trading intern",
            jd_hash="green",
            status="live",
        )
        red_job = Job(
            company_id=company.id,
            company=company.name,
            title="Risk Quant",
            loc="New York",
            url="https://example.com/job/red",
            source="official",
            jd="Risk role",
            jd_hash="red",
            status="live",
        )
        closed_job = Job(
            company_id=company.id,
            company=company.name,
            title="Closed Quant Researcher",
            loc="New York",
            url="https://example.com/job/closed",
            source="official",
            jd="Alpha research role",
            jd_hash="closed",
            status="closed",
        )
        session.add_all([green_job, red_job, closed_job])
        session.flush()
        session.add_all(
            [
                Eval(
                    job_id=green_job.id,
                    jd_hash=green_job.jd_hash,
                    front="green",
                    h1b="yellow",
                    exp="green",
                    score=80,
                    reason="Intern fit",
                    flags="",
                    model="codex-v1",
                    policy_ver="v1",
                ),
                Eval(
                    job_id=red_job.id,
                    jd_hash=red_job.jd_hash,
                    front="red",
                    h1b="yellow",
                    exp="green",
                    score=20,
                    reason="Risk",
                    flags="risk",
                    model="codex-v1",
                    policy_ver="v1",
                ),
            ]
        )
        session.commit()

    client = TestClient(create_app(db_path))

    all_response = client.get("/")
    filtered_response = client.get("/?front=green&h1b=yellow&exp=green&status=live")

    assert all_response.status_code == 200
    assert "Closed Quant Researcher" in all_response.text
    assert 'name="front"' in all_response.text
    assert filtered_response.status_code == 200
    assert "Quant Trading Intern" in filtered_response.text
    assert "Risk Quant" not in filtered_response.text
    assert "Closed Quant Researcher" not in filtered_response.text


def test_jobs_dashboard_supports_multi_select_column_filters(tmp_path: Path) -> None:
    from quant_job_tracker.web.app import create_app

    db_path = tmp_path / "qjt.sqlite3"
    init_db(db_path)
    with create_session(db_path) as session:
        company = Company(
            name="Test Fund",
            group="quant_hedge_fund",
            career_url="https://example.com",
            active=True,
        )
        session.add(company)
        session.flush()
        green_job = Job(
            company_id=company.id,
            company=company.name,
            title="Green Quant Researcher",
            loc="New York",
            url="https://example.com/job/green",
            source="official",
            jd="Alpha research role",
            jd_hash="green",
            status="live",
        )
        yellow_job = Job(
            company_id=company.id,
            company=company.name,
            title="Yellow Alpha Researcher",
            loc="Boston",
            url="https://example.com/job/yellow",
            source="official",
            jd="Alpha research role",
            jd_hash="yellow",
            status="live",
        )
        red_job = Job(
            company_id=company.id,
            company=company.name,
            title="Red Risk Quant",
            loc="Chicago",
            url="https://example.com/job/red",
            source="official",
            jd="Risk role",
            jd_hash="red",
            status="live",
        )
        session.add_all([green_job, yellow_job, red_job])
        session.flush()
        session.add_all(
            [
                Eval(
                    job_id=green_job.id,
                    jd_hash=green_job.jd_hash,
                    front="green",
                    h1b="green",
                    exp="green",
                    score=90,
                    reason="Front-office fit",
                    flags="",
                    model="codex-v1",
                    policy_ver="v1",
                ),
                Eval(
                    job_id=yellow_job.id,
                    jd_hash=yellow_job.jd_hash,
                    front="yellow",
                    h1b="yellow",
                    exp="green",
                    score=70,
                    reason="Needs review",
                    flags="",
                    model="codex-v1",
                    policy_ver="v1",
                ),
                Eval(
                    job_id=red_job.id,
                    jd_hash=red_job.jd_hash,
                    front="red",
                    h1b="yellow",
                    exp="green",
                    score=20,
                    reason="Risk role",
                    flags="risk",
                    model="codex-v1",
                    policy_ver="v1",
                ),
            ]
        )
        session.commit()

    client = TestClient(create_app(db_path))

    response = client.get("/?front=green&front=yellow")

    assert response.status_code == 200
    assert "Green Quant Researcher" in response.text
    assert "Yellow Alpha Researcher" in response.text
    assert "Red Risk Quant" not in response.text
    assert '<details class="column-filter">' in response.text
    assert 'name="front" value="green" checked' in response.text
    assert 'name="front" value="yellow" checked' in response.text


def test_jobs_dashboard_filters_by_industry_subtabs(tmp_path: Path) -> None:
    from quant_job_tracker.web.app import create_app

    db_path = tmp_path / "qjt.sqlite3"
    init_db(db_path)
    with create_session(db_path) as session:
        companies = [
            Company(
                name="Bank",
                group="sell_side_quant",
                career_url="https://bank.example.com",
                active=True,
            ),
            Company(
                name="Prop",
                group="prop",
                career_url="https://prop.example.com",
                active=True,
            ),
            Company(
                name="Hedge Fund",
                group="quant_hedge_fund",
                career_url="https://hedge.example.com",
                active=True,
            ),
            Company(
                name="Asset Manager",
                group="quant_asset_manager",
                career_url="https://asset.example.com",
                active=True,
            ),
        ]
        session.add_all(companies)
        session.flush()
        for company in companies:
            session.add(
                Job(
                    company_id=company.id,
                    company=company.name,
                    title=f"{company.name} Quant Researcher",
                    loc="New York",
                    url=f"https://example.com/{company.id}",
                    source="official",
                    jd="Alpha research role",
                    jd_hash=f"hash-{company.id}",
                    status="live",
                )
            )
        session.commit()

    client = TestClient(create_app(db_path))

    all_response = client.get("/")
    prop_response = client.get("/?industry=Prop+Trading")

    assert all_response.status_code == 200
    assert 'href="/?industry=Investment+Banks"' in all_response.text
    assert 'href="/?industry=Hedge+Funds"' in all_response.text
    assert 'href="/?industry=Prop+Trading"' in all_response.text
    assert 'href="/?industry=Asset+Management"' in all_response.text
    assert prop_response.status_code == 200
    assert "Prop Quant Researcher" in prop_response.text
    assert "Bank Quant Researcher" not in prop_response.text
    assert "Hedge Fund Quant Researcher" not in prop_response.text
    assert "Asset Manager Quant Researcher" not in prop_response.text


def test_summary_dashboard_visualizes_updates_applications_and_open_positions(
    tmp_path: Path,
) -> None:
    from quant_job_tracker.web.app import create_app

    db_path = tmp_path / "qjt.sqlite3"
    init_db(db_path)
    with create_session(db_path) as session:
        company = Company(
            name="Test Fund",
            group="quant_hedge_fund",
            career_url="https://example.com",
            active=True,
        )
        session.add(company)
        session.flush()
        live_job = Job(
            company_id=company.id,
            company=company.name,
            title="Live Quant Researcher",
            loc="New York",
            url="https://example.com/live",
            source="official",
            jd="Alpha research role",
            jd_hash="live",
            status="live",
        )
        new_job = Job(
            company_id=company.id,
            company=company.name,
            title="New Quant Trader",
            loc="Chicago",
            url="https://example.com/new",
            source="official",
            jd="Trading role",
            jd_hash="new",
            status="new",
        )
        closed_job = Job(
            company_id=company.id,
            company=company.name,
            title="Closed Quant Researcher",
            loc="Boston",
            url="https://example.com/closed",
            source="official",
            jd="Alpha research role",
            jd_hash="closed",
            status="closed",
        )
        session.add_all([live_job, new_job, closed_job])
        session.flush()
        session.add_all(
            [
                App(job_id=live_job.id, app_status="ready"),
                App(job_id=new_job.id, app_status="applied"),
                Eval(
                    job_id=live_job.id,
                    jd_hash=live_job.jd_hash,
                    front="green",
                    h1b="green",
                    exp="green",
                    score=90,
                    reason="Good fit",
                    flags="",
                    model="codex-v1",
                    policy_ver="v1",
                ),
                Eval(
                    job_id=new_job.id,
                    jd_hash=new_job.jd_hash,
                    front="yellow",
                    h1b="yellow",
                    exp="green",
                    score=75,
                    reason="Review",
                    flags="",
                    model="codex-v1",
                    policy_ver="v1",
                ),
                Run(
                    kind="crawl",
                    status="success",
                    jobs_found=12,
                    jobs_stored=2,
                    policy_ver="v1",
                    model="crawler",
                ),
            ]
        )
        session.commit()

    client = TestClient(create_app(db_path))

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert "Dashboard Summary" in response.text
    assert "Open Positions" in response.text
    assert "2</strong>" in response.text
    assert "Applications" in response.text
    assert "2</strong>" in response.text
    assert "Latest Update" in response.text
    assert "crawl · success" in response.text
    assert "Eligibility Mix" in response.text
    assert "green" in response.text
    assert "yellow" in response.text


def test_web_dashboard_paginates_collected_jobs(tmp_path: Path) -> None:
    from quant_job_tracker.web.app import create_app

    db_path = tmp_path / "qjt.sqlite3"
    init_db(db_path)
    with create_session(db_path) as session:
        company = Company(
            name="Test Fund",
            group="quant",
            career_url="https://example.com",
            active=True,
        )
        session.add(company)
        session.flush()
        for index in range(55):
            session.add(
                Job(
                    company_id=company.id,
                    company=company.name,
                    title=f"Quant Researcher {index:02d}",
                    loc="New York",
                    url=f"https://example.com/job/{index}",
                    source="official",
                    jd="Alpha research role",
                    jd_hash=f"hash-{index}",
                    status="live",
                )
            )
        session.commit()

    client = TestClient(create_app(db_path))

    first_page = client.get("/")
    second_page = client.get("/?page=2")

    assert first_page.status_code == 200
    assert "page 1 / 2" in first_page.text
    assert "Next" in first_page.text
    assert second_page.status_code == 200
    assert "page 2 / 2" in second_page.text
    assert "Previous" in second_page.text


def test_missing_job_detail_returns_404(tmp_path: Path) -> None:
    from quant_job_tracker.web.app import create_app

    db_path = tmp_path / "qjt.sqlite3"
    init_db(db_path)

    client = TestClient(create_app(db_path), raise_server_exceptions=False)

    response = client.get("/jobs/999")

    assert response.status_code == 404


def test_post_review_creates_review_and_detail_shows_it(tmp_path: Path) -> None:
    from quant_job_tracker.web.app import create_app

    db_path = tmp_path / "qjt.sqlite3"
    init_db(db_path)
    job_id = add_test_job(db_path)

    client = TestClient(create_app(db_path), follow_redirects=False)

    response = client.post(
        f"/jobs/{job_id}/review",
        data={"decision": "approved", "note": "Looks worth applying."},
    )

    assert response.status_code == 303
    assert response.headers["location"] == f"/jobs/{job_id}"
    with create_session(db_path) as session:
        review = session.query(Review).one()
        assert review.job_id == job_id
        assert review.decision == "approved"
        assert review.note == "Looks worth applying."
        assert review.reviewer == "user"

    detail_response = TestClient(create_app(db_path)).get(f"/jobs/{job_id}")
    assert detail_response.status_code == 200
    assert "approved" in detail_response.text
    assert "Looks worth applying." in detail_response.text


def test_post_pending_review_creates_review_and_detail_shows_option(tmp_path: Path) -> None:
    from quant_job_tracker.web.app import create_app

    db_path = tmp_path / "qjt.sqlite3"
    init_db(db_path)
    job_id = add_test_job(db_path)

    client = TestClient(create_app(db_path), follow_redirects=False)

    detail_before = client.get(f"/jobs/{job_id}")
    response = client.post(
        f"/jobs/{job_id}/review",
        data={"decision": "pending", "note": "Come back after sourcing deadline."},
    )

    assert detail_before.status_code == 200
    assert '<option value="pending">pending</option>' in detail_before.text
    assert response.status_code == 303
    with create_session(db_path) as session:
        review = session.query(Review).one()
        assert review.decision == "pending"
        assert review.note == "Come back after sourcing deadline."

    detail_after = TestClient(create_app(db_path)).get(f"/jobs/{job_id}")
    assert detail_after.status_code == 200
    assert "pending" in detail_after.text
    assert "Come back after sourcing deadline." in detail_after.text


def test_post_application_creates_updates_app_and_detail_shows_it(tmp_path: Path) -> None:
    from quant_job_tracker.web.app import create_app

    db_path = tmp_path / "qjt.sqlite3"
    init_db(db_path)
    job_id = add_test_job(db_path)

    client = TestClient(create_app(db_path), follow_redirects=False)

    create_response = client.post(
        f"/jobs/{job_id}/application",
        data={
            "app_status": "ready",
            "deadline": "2026-06-01",
            "priority": "high",
            "note": "Tailor resume first.",
        },
    )
    update_response = client.post(
        f"/jobs/{job_id}/application",
        data={
            "app_status": "applied",
            "deadline": "2026-06-03",
            "priority": "top",
            "note": "Submitted via portal.",
        },
    )

    assert create_response.status_code == 303
    assert update_response.status_code == 303
    with create_session(db_path) as session:
        app_row = session.query(App).one()
        assert app_row.job_id == job_id
        assert app_row.app_status == "applied"
        assert app_row.deadline == "2026-06-03"
        assert app_row.priority == "top"
        assert app_row.note == "Submitted via portal."

    detail_response = TestClient(create_app(db_path)).get(f"/jobs/{job_id}")
    assert detail_response.status_code == 200
    assert "selected>applied" in detail_response.text
    assert 'value="2026-06-03"' in detail_response.text
    assert 'value="top"' in detail_response.text
    assert "Submitted via portal." in detail_response.text


def test_post_review_and_application_reject_invalid_values(tmp_path: Path) -> None:
    from quant_job_tracker.web.app import create_app

    db_path = tmp_path / "qjt.sqlite3"
    init_db(db_path)
    job_id = add_test_job(db_path)

    client = TestClient(create_app(db_path), raise_server_exceptions=False)

    review_response = client.post(
        f"/jobs/{job_id}/review",
        data={"decision": "maybe", "note": ""},
    )
    app_response = client.post(
        f"/jobs/{job_id}/application",
        data={"app_status": "ghosted", "deadline": "", "priority": "", "note": ""},
    )

    assert review_response.status_code == 400
    assert app_response.status_code == 400


def test_run_history_lists_recent_runs(tmp_path: Path) -> None:
    from quant_job_tracker.web.app import create_app

    db_path = tmp_path / "qjt.sqlite3"
    init_db(db_path)
    with create_session(db_path) as session:
        session.add(
            Run(
                kind="eval",
                status="success",
                jobs_evaluated=3,
                policy_ver="v1",
                model="heuristic-v1",
            )
        )
        session.commit()

    client = TestClient(create_app(db_path))

    jobs_response = client.get("/")
    assert jobs_response.status_code == 200
    assert 'href="/runs"' in jobs_response.text

    runs_response = client.get("/runs")
    assert runs_response.status_code == 200
    assert "Run History" in runs_response.text
    assert "heuristic-v1" in runs_response.text
    assert "<td>3</td>" in runs_response.text


def test_job_detail_blocks_javascript_official_url(tmp_path: Path) -> None:
    from quant_job_tracker.web.app import create_app

    db_path = tmp_path / "qjt.sqlite3"
    init_db(db_path)
    with create_session(db_path) as session:
        company = Company(
            name="Test Fund",
            group="quant",
            career_url="https://example.com",
            active=True,
        )
        session.add(company)
        session.flush()
        job = Job(
            company_id=company.id,
            company=company.name,
            title="Quant Researcher",
            loc="New York",
            url="javascript:alert(1)",
            source="crawler",
            jd="Alpha research role",
            jd_hash="abc",
            status="new",
        )
        session.add(job)
        session.commit()
        job_id = job.id

    client = TestClient(create_app(db_path))

    response = client.get(f"/jobs/{job_id}")

    assert response.status_code == 200
    assert 'href="javascript:alert(1)"' not in response.text
    assert "Official link unavailable" in response.text


def test_jobs_table_blocks_javascript_official_url(tmp_path: Path) -> None:
    from quant_job_tracker.web.app import create_app

    db_path = tmp_path / "qjt.sqlite3"
    init_db(db_path)
    with create_session(db_path) as session:
        company = Company(
            name="Test Fund",
            group="quant",
            career_url="https://example.com",
            active=True,
        )
        session.add(company)
        session.flush()
        session.add(
            Job(
                company_id=company.id,
                company=company.name,
                title="Quant Researcher",
                loc="New York",
                url="javascript:alert(1)",
                source="crawler",
                jd="Alpha research role",
                jd_hash="abc",
                status="new",
            )
        )
        session.commit()

    client = TestClient(create_app(db_path))

    response = client.get("/")

    assert response.status_code == 200
    assert 'href="javascript:alert(1)"' not in response.text
    assert "Quant Researcher" in response.text


def test_job_detail_formats_stored_jd_with_sections(tmp_path: Path) -> None:
    from quant_job_tracker.web.app import create_app

    db_path = tmp_path / "qjt.sqlite3"
    init_db(db_path)
    with create_session(db_path) as session:
        company = Company(
            name="Test Fund",
            group="quant",
            career_url="https://example.com",
            active=True,
        )
        session.add(company)
        session.flush()
        job = Job(
            company_id=company.id,
            company=company.name,
            title="Quant Researcher",
            loc="New York",
            url="https://example.com/job/1",
            source="crawler",
            jd=(
                "Overview This role researches alpha signals. "
                "Responsibilities Build predictive models. Test trading hypotheses. "
                "Qualifications Python and statistics."
            ),
            jd_hash="abc",
            status="new",
        )
        session.add(job)
        session.commit()
        job_id = job.id

    client = TestClient(create_app(db_path))

    response = client.get(f"/jobs/{job_id}")

    assert response.status_code == 200
    assert '<article class="jd-card">' in response.text
    assert '<h3 class="jd-heading">Overview</h3>' in response.text
    assert '<h3 class="jd-heading">Responsibilities</h3>' in response.text
    assert '<h3 class="jd-heading">Qualifications</h3>' in response.text
    assert "<pre>" not in response.text
