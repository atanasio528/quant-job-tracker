def build_evaluator_prompt(policy: str, title: str, company: str, loc: str, jd: str) -> str:
    return f"""Use the policy below to classify this job.

POLICY:
{policy}

JOB:
Company: {company}
Title: {title}
Location: {loc}
JD:
{jd}

Return JSON with keys: front, h1b, exp, score, reason, flags.
"""
