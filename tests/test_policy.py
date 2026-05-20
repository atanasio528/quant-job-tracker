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
