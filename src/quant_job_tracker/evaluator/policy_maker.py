def suggest_policy_updates(rows: list[dict[str, str]]) -> str:
    alias_rows = [row for row in rows if "title_alias" in row.get("flags", "")]
    risk_rows = [row for row in rows if "risk" in row.get("flags", "")]
    adapter_rows = [
        row
        for row in rows
        if any(
            flag in row.get("flags", "")
            for flag in (
                "not_job_page",
                "needs_better_adapter",
                "career_category",
                "seed_noise",
                "page_noise",
                "title_dirty",
            )
        )
    ]
    quant_dev_rows = [row for row in rows if "quant_dev_excluded" in row.get("flags", "")]
    portfolio_rows = [row for row in rows if "portfolio_manager" in row.get("flags", "")]
    location_rows = [row for row in rows if "wrong_location" in row.get("flags", "")]
    manual_rows = [
        row
        for row in rows
        if any(
            flag in row.get("flags", "")
            for flag in (
                "manual_update",
                "blocked_by_provider",
                "detail_blocked",
                "needs_manual_review",
            )
        )
    ]

    lines = ["# Policy Maker Suggestions", ""]
    if alias_rows:
        lines.append("## Title Aliases")
        for row in alias_rows:
            lines.append(
                f"- Review title alias for {row.get('company', 'Unknown')}: "
                f"`{row.get('title', 'Unknown')}` classified as `{row.get('front', 'unknown')}`."
            )
        lines.append("")
    if risk_rows:
        lines.append("## Hard Filter Candidates")
        lines.append(
            "- Risk-related titles appeared in rejected rows; keep `risk` terms in crawler hard-noise policy."
        )
        lines.append("")
    if adapter_rows:
        lines.append("## Crawler Adapter Improvements")
        companies = sorted({row.get("company", "Unknown") for row in adapter_rows})
        lines.append(
            "- Many stored rows are company pages, category pages, or noisy seed pages. "
            f"Prioritize ATS-specific adapters or tighter seed URLs for: {', '.join(companies)}."
        )
        lines.append("")
    if quant_dev_rows:
        lines.append("## Front Quant Boundary")
        lines.append(
            "- Quant development / systems development rows were rejected by Codex review. "
            "Keep them out of front-quant green unless the JD shows alpha research or trading decision ownership."
        )
        lines.append("")
    if portfolio_rows:
        lines.append("## Portfolio Roles")
        lines.append(
            "- Portfolio manager rows appeared in rejected results. Keep PM/portfolio ownership roles "
            "outside the junior front-quant target set."
        )
        lines.append("")
    if location_rows:
        lines.append("## Location Filters")
        lines.append(
            "- Wrong-location rows reached evaluation. Improve adapters to extract location from job detail pages "
            "before evaluation when job cards have unknown locations."
        )
        lines.append("")
    if manual_rows:
        lines.append("## Manual Update Watchlist")
        companies = sorted({row.get("company", "Unknown") for row in manual_rows})
        lines.append(
            "- Official sources need manual refresh, saved HTML, or a dedicated adapter for: "
            f"{', '.join(companies)}."
        )
        lines.append(
            "- Keep these companies visible in the dashboard, but do not treat blocked detail pages as evidence "
            "that the role is closed or ineligible."
        )
        lines.append("")
    if len(lines) == 2:
        lines.append("No policy changes suggested from the current reviewed rows.")
    return "\n".join(lines).rstrip() + "\n"
