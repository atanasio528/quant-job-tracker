from quant_job_tracker.evaluator.policy_maker import suggest_policy_updates


def test_policy_maker_suggests_alias_review() -> None:
    suggestions = suggest_policy_updates(
        [
            {
                "title": "Algorithm Developer",
                "company": "Hudson River Trading",
                "front": "green",
                "flags": "title_alias",
            },
            {"title": "Risk Quant", "company": "Bank", "front": "red", "flags": "risk"},
        ]
    )

    assert "Hudson River Trading" in suggestions
    assert "title alias" in suggestions.lower()


def test_policy_maker_suggests_adapter_and_boundary_updates() -> None:
    suggestions = suggest_policy_updates(
        [
            {
                "title": "Open Roles",
                "company": "Jane Street",
                "front": "red",
                "flags": "not_job_page,needs_better_adapter",
            },
            {
                "title": "Quant Systems Developer",
                "company": "D. E. Shaw",
                "front": "red",
                "flags": "quant_dev_excluded",
            },
            {
                "title": "Quantitative Portfolio Manager",
                "company": "Cubist Systematic Strategies",
                "front": "red",
                "flags": "portfolio_manager,too_senior",
            },
        ]
    )

    assert "Crawler Adapter Improvements" in suggestions
    assert "Front Quant Boundary" in suggestions
    assert "Portfolio Roles" in suggestions
