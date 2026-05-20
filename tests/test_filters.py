from quant_job_tracker.crawler.filters import keep_job_card


def test_keep_front_quant_alias() -> None:
    keep, note = keep_job_card("Hudson River Trading", "Algorithm Developer", "New York")
    assert keep is True
    assert "kept" in note


def test_reject_obvious_noise() -> None:
    keep, note = keep_job_card("AQR", "Compliance Analyst", "New York")
    assert keep is False
    assert "compliance" in note


def test_reject_hard_noise_even_with_quant_signal() -> None:
    hard_noise_titles = [
        "Quant Compliance Analyst",
        "Quant Risk Management Analyst",
        "Quantitative Software Engineer",
    ]

    for title in hard_noise_titles:
        keep, note = keep_job_card("Some Fund", title, "New York")
        assert keep is False, title
        assert "noise" in note


def test_keep_mixed_noise_and_relevant_signal() -> None:
    keep, note = keep_job_card("Point72", "Software Engineer, Macro Quant Analytics", "New York")
    assert keep is True
    assert "relevant" in note or "ambiguous" in note


def test_reject_wrong_location() -> None:
    keep, note = keep_job_card("Jane Street", "Quantitative Trader", "London")
    assert keep is False
    assert "location" in note


def test_keep_unknown_location_for_evaluator_review() -> None:
    keep, note = keep_job_card("Some Fund", "Quant Researcher", "Unknown")
    assert keep is True
    assert "unknown location" in note
    assert "evaluator review" in note


def test_keep_blank_location_for_evaluator_review() -> None:
    keep, note = keep_job_card("Some Fund", "Systematic Trader", "")
    assert keep is True
    assert "unknown location" in note
    assert "evaluator review" in note


def test_keep_ambiguous_research_role() -> None:
    keep, note = keep_job_card("Point72", "Research Analyst", "New York")
    assert keep is True
    assert "ambiguous" in note


def test_reject_human_resources_noise_without_bare_hr_substring() -> None:
    keep, note = keep_job_card("Some Firm", "Human Resources Analyst", "New York")
    assert keep is False
    assert "human resources" in note
