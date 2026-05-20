# Policy Maker Policy

Review crawler and evaluator results. Improve policies using evidence from false positives, false negatives, and reviewed jobs.

Do not make hard filters aggressive unless a pattern is consistently irrelevant. Add firm-specific aliases only when job descriptions support the mapping.

## Manual Update Watchlist

Use this section for companies where the official source is real but the local crawler cannot yet collect complete job descriptions without a manual step, saved HTML, cookies, or a dedicated adapter. Mark rows with `manual_update`, `blocked_by_provider`, `detail_blocked`, or `needs_manual_review` so the evaluator and dashboard do not confuse source limitations with candidate ineligibility.

Current watchlist:

- Citadel: official listing AJAX works, but detail pages can return Cloudflare challenges to local HTTP. Keep listing rows from the official source and manually refresh details when needed.
- Citadel Securities: official open-opportunities source can be provider-blocked. Use the same manual-update review pattern until a dedicated working source adapter is verified.
- Aquatic Capital Management: official careers URL returned HTTP 403 to the local crawler on the 2026-05-20 full run.
- Laurion Capital: official careers URL failed with an SSL EOF error on the 2026-05-20 full run.
- Eisler Capital: official careers hostname did not resolve in the local crawler on the 2026-05-20 full run.

Latest full-run URL review queue:

- Bad seed URL / 404: Maven Securities, Radix Trading, Mako Trading, Da Vinci Derivatives, WH Trading, Winton, Verition Fund Management, ExodusPoint, PDT Partners, The Voleon Group, AlphaGrep, Marshall Wace, Tudor Investment Corporation, Arrowstreet Capital, Kepos Capital, Walleye Capital, Paloma Partners, Dimensional Fund Advisors, Morgan Stanley.
- Needs dedicated dynamic/manual adapter: Squarepoint Capital, Qube Research & Technologies, Millennium Management, Balyasny Asset Management, Akuna Capital, AQR Capital Management, Aspect Capital, Goldman Sachs, JPMorgan Chase, Citi, Bank of America.

When reviewing full-pipeline runs, add companies to this watchlist if:

- the official careers URL is verified but local crawling returns provider 403, challenge pages, or empty app shells;
- the crawler stores listing-level rows because detail pages are blocked;
- the source requires saved rendered HTML from a normal browser;
- the company uses an ATS or embedded job app that needs a dedicated adapter before results can be trusted.
