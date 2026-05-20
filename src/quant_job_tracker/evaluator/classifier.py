from pydantic import BaseModel, Field


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
        front_green_terms = [
            "alpha",
            "quant researcher",
            "quantitative researcher",
            "quant trader",
            "quantitative trader",
            "trading strategy",
            "predictive",
        ]
        front_red_terms = [
            "risk",
            "model validation",
            "execution services",
            "portfolio analytics",
            "software engineer",
            "data engineer",
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
            "no sponsorship",
            "do not provide visa sponsorship",
            "cannot provide visa sponsorship",
            "will not provide visa sponsorship",
            "will not sponsor",
            "cannot sponsor",
            "unable to sponsor",
        ]
        visa_red_exemptions = [
            "no sponsorship required",
        ]
        senior_terms = [
            "vp ",
            "vice president",
            "director",
            "head of",
            "lead a team",
            "8+ years",
            "7+ years",
            "6+ years",
            "5+ years",
        ]

        front = "green" if any(term in text for term in front_green_terms) else "red"
        if any(term in text for term in front_red_terms):
            front = "red"

        has_visa_red = any(term in text for term in visa_red_terms) and not any(
            term in text for term in visa_red_exemptions
        )
        if has_visa_red:
            h1b = "red"
        elif any(term in text for term in visa_green_terms):
            h1b = "green"
        else:
            h1b = "yellow"
        exp = "red" if any(term in text for term in senior_terms) else "green"

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
        if "algorithm developer" in title.lower():
            flags.append("title_alias")

        return EvalResult(
            front=front,
            h1b=h1b,
            exp=exp,
            score=score,
            reason=f"front={front}, h1b={h1b}, exp={exp} based on title and JD evidence",
            flags=",".join(flags),
        )
