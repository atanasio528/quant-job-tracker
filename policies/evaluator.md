# Evaluator Policy

Read the full job description and classify the role. Do not rely only on title.

Return JSON with exactly these keys: `front`, `h1b`, `exp`, `score`, `reason`, `flags`.

Prefer keeping edge cases visible with honest low scores over silently rejecting unusual titles. Use `h1b=yellow` when sponsorship language is missing or unclear.
