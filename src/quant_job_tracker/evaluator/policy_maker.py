def suggest_policy_updates(rows: list[dict[str, str]]) -> str:
    alias_rows = [row for row in rows if "title_alias" in row.get("flags", "")]
    risk_rows = [row for row in rows if "risk" in row.get("flags", "")]

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
    if len(lines) == 2:
        lines.append("No policy changes suggested from the current reviewed rows.")
    return "\n".join(lines).rstrip() + "\n"
