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
