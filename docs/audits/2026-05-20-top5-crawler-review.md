# Top 5 Crawler Review - 2026-05-20

Independent reviewer scope: Hudson River Trading, Jane Street, D. E. Shaw, Two Sigma, and Citadel.

## Live Site Evidence

- Hudson River Trading: `https://www.hudsonrivertrading.com/careers/` shows filters in static HTML and loads job cards through the official WordPress AJAX action `get_hrt_jobs_handler`.
- Jane Street: `https://www.janestreet.com/join-jane-street/open-roles/` renders an open-roles UI, but the role data comes from official JSON at `/jobs/main.json` plus `/static/position-directories.json`.
- D. E. Shaw: `https://www.deshaw.com/careers` exposes real job rows with category, location, and detail links such as `/careers/<role>-<id>`.
- Two Sigma: `https://careers.twosigma.com/careers/OpenRoles` is the real job-search portal; job detail links use `/careers/JobDetail/...` and the listing paginates with `jobOffset`.
- Citadel: `https://www.citadel.com/careers/open-opportunities/` shows live job rows in a browser, but local HTTP detail crawling is blocked by a Cloudflare challenge. The crawler should mark this as provider-blocked instead of substituting unofficial sources.

## Pre-Fix Pipeline Findings

Command:

```bash
rm -f /tmp/qjt_top5_audit.sqlite3
qjt collect-sources --db /tmp/qjt_top5_audit.sqlite3
qjt crawl --db /tmp/qjt_top5_audit.sqlite3 --limit 5
qjt eval-pending --db /tmp/qjt_top5_audit.sqlite3
```

Observed result: 33 cards found, 16 jobs stored.

Incorrect rows included:

- Jane Street stored an open-role/category page instead of job details.
- D. E. Shaw stored `/what-we-do/investment-management` as `Investment Management`.
- Two Sigma stored corporate marketing/category pages such as `Investment Management` and `Quantitative Research & Data Science`.
- Citadel stored a category page such as `/careers/quantitative-research/`; detail pages were blocked.
- HRT stored no jobs because the real job list was not in the static HTML.

Root cause: the generic adapter treated any relevant-looking link text as a job card. That worked for simple pages, but failed on app-backed career pages with navigation links, marketing links, filter links, and delayed job data.

## Fixes Made

- Added company-specific card fetchers/parsers for HRT, Jane Street, D. E. Shaw, Two Sigma, and Citadel.
- Routed HRT through the official AJAX feed and Jane Street through official JSON.
- Routed Two Sigma to the OpenRoles portal and JobDetail links, with pagination.
- Restricted D. E. Shaw to real job cards/detail slugs and extracted locations.
- Restricted Citadel to `/careers/details/` links and preserved Cloudflare blocking as a crawl issue.
- Updated URL manager and evaluator policies with the real top-five source URLs and trusted patterns.
- Fixed evaluator false positives/negatives caused by full-page boilerplate:
  - Footer text like `risk management` or `Execution Services` no longer overrides clear front-quant titles.
  - Business/admin titles are no longer promoted to `front=green` just because navigation mentions quant research.
- Bumped the evaluator model id to `heuristic-v2` so existing local databases receive fresh evaluations.
- Added narrow cleanup for known non-job URL patterns so old marketing/category rows are removed from local databases even when a provider-blocked page cannot be fully recrawled.
- Added retries for transient HTTP timeouts/network errors so one flaky detail-page request does not drop an otherwise valid job.

## Post-Fix Verification

Command:

```bash
rm -f /tmp/qjt_top5_audit_after.sqlite3
qjt collect-sources --db /tmp/qjt_top5_audit_after.sqlite3
qjt crawl --db /tmp/qjt_top5_audit_after.sqlite3 --limit 5
qjt eval-pending --db /tmp/qjt_top5_audit_after.sqlite3
```

Observed result: 398 cards found, 165 jobs stored, 165 jobs evaluated.

Stored jobs by company:

| Company | Stored jobs |
| --- | ---: |
| Hudson River Trading | 36 |
| Jane Street | 59 |
| D. E. Shaw | 50 |
| Two Sigma | 20 |
| Citadel | 0 |

Latest evaluator labels after the classifier fix:

| Company | Total | Front green | Front red |
| --- | ---: | ---: | ---: |
| D. E. Shaw | 50 | 3 | 47 |
| Hudson River Trading | 36 | 4 | 32 |
| Jane Street | 59 | 14 | 45 |
| Two Sigma | 20 | 5 | 15 |

Noise check: the post-fix database had no stored rows for `Investment Management`, `Quantitative Research & Data Science`, `Asset Management`, `what-we-do`, `businesses`, or `/careers/quantitative-research/` category URLs.

Code verification: `ruff check .` passed and `pytest` reported 93 passing tests.

## Remaining Issues

- Citadel is still blocked for local HTTP crawling. This is a provider-side challenge, not a bad URL. Keep the official source and surface the blocked status in run history.
- The generic crawler remains intentionally broad for companies without dedicated adapters. The evaluator now catches more page boilerplate, but more company-specific parsers are still needed beyond the top five.
- Some real but irrelevant jobs are still stored as `front=red`. This is acceptable for v1 because the first layer is designed to exclude obvious noise, not make final eligibility decisions.
