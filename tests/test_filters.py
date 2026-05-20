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
