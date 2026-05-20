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


def test_classifier_policy_alias_can_boost_front_with_supportive_jd_evidence() -> None:
    result = HeuristicClassifier().classify(
        title="Algorithm Developer",
        jd="Build alpha signals.",
        policy="Hudson River Trading: Algorithm Developer can be front quant.",
    )

    assert result.front == "green"
    assert "title_alias" in result.flags


def test_classifier_policy_alias_boosts_front_without_policy_text_as_evidence() -> None:
    result = HeuristicClassifier().classify(
        title="Algorithm Developer",
        jd="Build signal research.",
        policy="Hudson River Trading: Algorithm Developer can be front quant.",
    )

    assert result.front == "green"
    assert "title_alias" in result.flags


def test_classifier_policy_alias_does_not_boost_front_without_supportive_jd_evidence() -> None:
    result = HeuristicClassifier().classify(
        title="Algorithm Developer",
        jd="Internal tooling role.",
        policy="Hudson River Trading: Algorithm Developer can be front quant.",
    )

    assert result.front != "green"


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


def test_classifier_marks_do_not_provide_visa_sponsorship_red() -> None:
    result = HeuristicClassifier().classify(
        title="Quant Researcher",
        jd="We do not provide visa sponsorship for this role.",
        policy="",
    )

    assert result.h1b == "red"


def test_classifier_marks_cannot_provide_visa_sponsorship_red() -> None:
    result = HeuristicClassifier().classify(
        title="Quant Researcher",
        jd="We cannot provide visa sponsorship for this role.",
        policy="",
    )

    assert result.h1b == "red"


def test_classifier_marks_visa_sponsorship_not_available_red() -> None:
    result = HeuristicClassifier().classify(
        title="Quant Researcher",
        jd="Visa sponsorship is not available for this role.",
        policy="",
    )

    assert result.h1b == "red"


def test_classifier_keeps_explicit_non_sponsorship_red_with_harmless_phrase() -> None:
    result = HeuristicClassifier().classify(
        title="Quant Researcher",
        jd="We cannot provide visa sponsorship. No sponsorship required to apply.",
        policy="",
    )

    assert result.h1b == "red"


def test_classifier_does_not_mark_no_sponsorship_required_red() -> None:
    result = HeuristicClassifier().classify(
        title="Quant Researcher",
        jd="No sponsorship required to apply.",
        policy="",
    )

    assert result.h1b != "red"


def test_classifier_marks_front_intern_roles_green() -> None:
    result = HeuristicClassifier().classify(
        title="Proprietary Trading Intern (New York) – Summer 2027",
        jd="Trading interns sit at the core of the firm and work on market-facing decisions.",
        policy="",
    )

    assert result.front == "green"
    assert result.exp == "green"


def test_classifier_does_not_let_site_boilerplate_risk_override_front_quant_title() -> None:
    result = HeuristicClassifier().classify(
        title="Quantitative Researcher (Mid-Freq)",
        jd=(
            "Develop alpha signals and predictive trading strategies. "
            "Footer: modeling and risk management appear in general company navigation."
        ),
        policy="",
    )

    assert result.front == "green"


def test_classifier_does_not_let_legal_footer_execution_services_override_front_title() -> None:
    result = HeuristicClassifier().classify(
        title="Quantitative Trader",
        jd=(
            "Market-facing trading role. Legal footer: services are provided by "
            "Jane Street Execution Services, LLC."
        ),
        policy="",
    )

    assert result.front == "green"


def test_classifier_does_not_promote_business_role_from_careers_navigation() -> None:
    result = HeuristicClassifier().classify(
        title="Business Manager",
        jd=(
            "Own team planning and coordination. Careers navigation: Engineering, "
            "Quantitative Research & Data Science, Open Roles. Footer links mention "
            "alpha and Quantitative Researcher profiles."
        ),
        policy="",
    )

    assert result.front == "red"


def test_classifier_keeps_explicit_risk_role_red_even_with_quant_title() -> None:
    result = HeuristicClassifier().classify(
        title="Quantitative Risk Researcher",
        jd="Research role focused on model validation and portfolio risk.",
        policy="",
    )

    assert result.front == "red"


def test_classifier_flags_dirty_titles_and_page_noise() -> None:
    result = HeuristicClassifier().classify(
        title="Asset Management Provides investment management solutions across all major asset classes.",
        jd="Careers in Asset Management",
        policy="",
    )

    assert result.front == "red"
    assert "title_dirty" in result.flags
    assert "page_noise" in result.flags
