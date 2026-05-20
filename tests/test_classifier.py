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


def test_classifier_does_not_use_policy_as_job_evidence() -> None:
    result = HeuristicClassifier().classify(
        title="Quant Researcher",
        jd="This role develops alpha signals and predictive trading strategies.",
        policy="Risk, green card, and 5+ years are policy examples, not job evidence.",
    )

    assert result.front == "green"
    assert result.h1b != "red"
    assert result.exp == "green"


def test_classifier_marks_h1b_supportive_language_green() -> None:
    result = HeuristicClassifier().classify(
        title="Quant Researcher",
        jd="Visa sponsorship is available for this role.",
        policy="",
    )

    assert result.h1b == "green"


def test_classifier_does_not_mark_no_sponsorship_required_red() -> None:
    result = HeuristicClassifier().classify(
        title="Quant Researcher",
        jd="No sponsorship required to apply.",
        policy="",
    )

    assert result.h1b != "red"
