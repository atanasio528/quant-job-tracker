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
