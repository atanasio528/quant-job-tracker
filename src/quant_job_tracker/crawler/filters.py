TARGET_LOCATION_TERMS = {
    "new york",
    "nyc",
    "boston",
    "florida",
    "miami",
    "palm beach",
    "new jersey",
    "jersey city",
    "chicago",
    "remote",
    "united states",
}

NOISE_TERMS = {
    "accounting",
    "client service",
    "compliance",
    "data engineer",
    "devops",
    "facilities",
    "human resources",
    "legal",
    "model risk",
    "office manager",
    "operations",
    "recruit",
    "recruiter",
    "risk management",
    "sales",
    "security engineer",
    "software engineer",
    "tax",
}

AMBIGUOUS_KEEP_TERMS = {
    "alpha",
    "algorithm",
    "investment",
    "quant",
    "research",
    "strategy",
    "systematic",
    "trader",
    "trading",
}


def keep_job_card(company: str, title: str, loc: str) -> tuple[bool, str]:
    title_l = title.lower()
    loc_l = loc.lower()

    if not any(term in loc_l for term in TARGET_LOCATION_TERMS):
        return False, "rejected: location outside target US markets"

    has_relevant_signal = any(term in title_l for term in AMBIGUOUS_KEEP_TERMS)
    if has_relevant_signal:
        return True, "kept: ambiguous or relevant quant/trading/research signal"

    for term in NOISE_TERMS:
        if term in title_l:
            return False, f"rejected: obvious noise term '{term}'"

    return True, "kept: broad crawler policy preserves non-noise roles for evaluator"
