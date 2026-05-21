from pydantic import BaseModel, Field


FRONT_ALIAS_SUPPORT_TERMS = [
    "alpha",
    "predictive",
    "trading strategy",
    "quant researcher",
    "signal",
    "systematic",
]


class EvalResult(BaseModel):
    front: str
    h1b: str
    exp: str
    score: int = Field(ge=0, le=100)
    reason: str
    flags: str = ""


class HeuristicClassifier:
    def classify(self, title: str, jd: str, policy: str) -> EvalResult:
        text = f"{title}\n{jd}".lower()
        front_title_green_terms = [
            "alpha",
            "ai researcher",
            "machine learning researcher",
            "quant researcher",
            "quant research",
            "quantitative researcher",
            "quantitative / systematic research",
            "quant trader",
            "quantitative trader",
            "research scientist",
            "statistical arbitrage",
            "systematic research",
            "trader",
            "trading analyst",
            "trading strategy",
        ]
        front_red_terms = [
            "risk",
            "model validation",
            "execution services",
            "portfolio analytics",
            "software engineer",
            "data engineer",
        ]
        jd_front_red_terms = [
            "model validation",
            "execution services",
            "portfolio analytics",
            "portfolio risk",
            "risk model",
        ]
        visa_green_terms = [
            "sponsorship available",
            "visa sponsorship",
            "h-1b",
            "h1b",
            "cpt",
            "opt",
        ]
        visa_red_terms = [
            "us citizen",
            "u.s. citizen",
            "green card",
            "permanent resident",
            "visa sponsorship is not available",
            "sponsorship is not available",
            "do not provide visa sponsorship",
            "cannot provide visa sponsorship",
            "will not provide visa sponsorship",
            "will not sponsor",
            "cannot sponsor",
            "unable to sponsor",
            "no visa sponsorship",
        ]
        senior_title_terms = [
            "vp ",
            "vice president",
            "director",
            "head of",
        ]
        senior_jd_terms = [
            "lead a team",
            "8+ years",
            "7+ years",
            "6+ years",
            "5+ years",
        ]

        title_lower = title.lower()
        jd_lower = jd.lower()
        policy_lower = policy.lower()
        page_noise_terms = [
            " read more",
            " read post",
            " provides investment management",
            "research archive",
            "life at ",
            "required disclosures",
            "chief investment officer",
        ]
        dirty_title = any(term in title_lower for term in (" summary:", " read post", " provides "))
        page_noise = any(term in title_lower for term in page_noise_terms)
        front_intern = any(
            term in title_lower for term in ("intern", "graduate", "campus")
        ) and any(
            term in title_lower for term in ("quant", "trading", "trader", "research", "alpha")
        )
        has_policy_title_alias = _policy_allows_front_alias(title_lower, policy_lower)
        has_front_alias_support = any(term in jd_lower for term in FRONT_ALIAS_SUPPORT_TERMS)

        front = (
            "green"
            if any(term in title_lower for term in front_title_green_terms) or front_intern
            else "red"
        )
        if front == "red" and has_policy_title_alias and has_front_alias_support:
            front = "green"
        has_front_red_title_evidence = any(term in title_lower for term in front_red_terms)
        has_front_red_jd_evidence = front == "red" and any(
            term in jd_lower for term in jd_front_red_terms
        )
        has_front_red_evidence = has_front_red_title_evidence or has_front_red_jd_evidence
        if has_front_red_evidence or page_noise:
            front = "red"

        has_visa_red = any(term in text for term in visa_red_terms)
        if not has_visa_red and "no sponsorship required" not in text:
            has_visa_red = "no sponsorship" in text
        if has_visa_red:
            h1b = "red"
        elif any(term in text for term in visa_green_terms):
            h1b = "green"
        else:
            h1b = "yellow"
        exp = (
            "red"
            if any(term in title_lower for term in senior_title_terms)
            or any(term in jd_lower for term in senior_jd_terms)
            else "green"
        )
        if front_intern:
            exp = "green"

        score = 50
        if front == "green":
            score += 30
        if h1b == "red":
            score -= 25
        if exp == "red":
            score -= 25
        score = max(0, min(100, score))

        flags = []
        if h1b == "yellow":
            flags.append("visa_unclear")
        if exp == "red":
            flags.append("senior")
        if has_policy_title_alias:
            flags.append("title_alias")
        if dirty_title:
            flags.append("title_dirty")
        if page_noise:
            flags.append("page_noise")

        return EvalResult(
            front=front,
            h1b=h1b,
            exp=exp,
            score=score,
            reason=f"front={front}, h1b={h1b}, exp={exp} based on title and JD evidence",
            flags=",".join(flags),
        )


def _policy_allows_front_alias(title_lower: str, policy_lower: str) -> bool:
    return (
        "algorithm developer" in title_lower
        and "algorithm developer" in policy_lower
        and "front quant" in policy_lower
    )
