from pathlib import Path

from quant_job_tracker.crawler.job_sources import JOB_SOURCE_SEEDS
from quant_job_tracker.crawler.seeds import SEEDS
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


def test_real_evaluator_policy_includes_job_source_links() -> None:
    bundle = load_policy_bundle(Path("policies"), "evaluator")

    assert "Official Job Source Links" in bundle
    assert "Target Company Categories" in bundle
    assert "Investment Banks (5)" in bundle
    assert "Hedge Funds (41)" in bundle
    assert "Prop Trading (30)" in bundle
    assert "Asset Management (5)" in bundle
    assert "https://www.deshaw.com/careers" in bundle
    assert "https://careers.point72.com/" in bundle
    assert "job-boards.greenhouse.io/fiveringsllc/jobs/" in bundle
    assert "page_noise" in bundle


def test_url_manager_policy_exists_and_has_first_five_sources() -> None:
    bundle = load_policy_bundle(Path("policies"), "url_manager")

    assert "URL Manager Policy" in bundle
    assert "First Five Company Source Map" in bundle
    for company, url in [
        ("Hudson River Trading", "https://www.hudsonrivertrading.com/careers/"),
        ("Jane Street", "https://www.janestreet.com/join-jane-street/open-roles/"),
        ("D. E. Shaw", "https://www.deshaw.com/careers"),
        ("Two Sigma", "https://careers.twosigma.com/"),
        ("Citadel", "https://www.citadel.com/careers/open-opportunities/"),
    ]:
        assert company in bundle
        assert url in bundle
    assert "blocked_by_provider" in bundle
    assert "Flow Traders Correction" in bundle
    assert "https://www.flowtraders.com/careers/job-search/" in bundle


def test_real_evaluator_policy_lists_all_target_company_sources() -> None:
    bundle = load_policy_bundle(Path("policies"), "evaluator")
    source_by_company = {source.company: source for source in JOB_SOURCE_SEEDS}

    for seed in SEEDS:
        assert seed.name in bundle
        assert source_by_company[seed.name].source_url in bundle
