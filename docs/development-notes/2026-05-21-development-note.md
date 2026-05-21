# Development Note - 2026-05-21

## Project State

Quant Job Tracker is now a local end-to-end pipeline for official-career-page quant job tracking. It has three working layers:

- crawler: collects official job cards, filters obvious noise, fetches locally stored job descriptions, and records crawl runs;
- evaluator: classifies stored jobs by `front`, `h1b`, `exp`, score, reason, and flags;
- dashboard: shows summary metrics, industry tabs, Excel-style multi-select filters, paginated job tables, application status links, and readable stored JDs.

The repo is connected to GitHub at `atanasio528/quant-job-tracker`. The latest pushed implementation commit before this note is `748b0f4` (`fix: expand BlackRock crawler coverage`).

## Current Target Universe

The curated company list has 81 targets:

- Investment Banks: 5
- Hedge Funds: 41
- Prop Trading: 30
- Asset Management: 5

The active source registry has 82 active job-source records because some companies need more than one official source surface.

## Current Local Data Snapshot

As of the latest local run:

- total stored jobs: 540
- active jobs (`new` or `live`): 520
- closed jobs: 20

Active evaluator buckets:

- `front=green`, `h1b=green`, `exp=green`: 24
- `front=green`, `h1b=yellow`, `exp=green`: 47
- `front=green`, `h1b=green`, `exp=red`: 9
- `front=green`, `h1b=yellow`, `exp=red`: 2
- `front=green`, `h1b=red`, `exp=green`: 1

The most immediately useful review set is therefore the 71 active jobs with `front=green` and `exp=green`, with H-1B either green or unclear.

No application-status records have been created yet; the application tracker is ready but empty.

## Important Fixes Completed

### Dashboard

- Added a main summary dashboard.
- Added industry subtabs: Investment Banks, Hedge Funds, Prop Trading, Asset Management.
- Added dropdown-style multi-select filters for `front`, `h1b`, `exp`, status, and application status.
- Moved official posting links onto the job title.
- Kept the local application/status page linked from the status field.
- Reformatted stored JDs into readable sections.

### Source Management

- Added `url_manager.md` as a dedicated role/policy file for official posting URLs and source verification.
- Added active source refresh logic so obsolete source URLs are deactivated instead of remaining active beside corrected URLs.
- Added policy-maker watchlist for provider-blocked or manual-update companies.

### G-Research

- Replaced the broad careers intro page with the real official posting page: `https://www.gresearch.com/vacancies/`.
- Added parser coverage for real vacancy cards only.
- Pruned old marketing/program rows such as `/nextgen/`, `/vector/`, `/teams/`, and `/news/`.
- Latest G-Research official crawl found 54 live cards, but stored 0 because none matched the current target US locations.

### JPMorgan Chase

- Replaced generic JPMorgan career pages with the official Oracle Candidate Experience portal.
- Added API-backed listing and JD fetching through Oracle recruiting endpoints.
- Latest targeted crawl found 685 listing cards and stored 185 jobs after coarse filters.
- Latest eval run evaluated 183 JPMorgan jobs.

### BlackRock

- Replaced `search-jobs?k=quant` as the only source with:
  - `https://careers.blackrock.com/search-jobs`
  - `https://careers.blackrock.com/category/students-and-graduates-jobs/45831/9022304/1`
- Added BlackRock-specific search coverage for `quant`, `quantitative`, `systematic`, and `research`.
- Added parser coverage for TalentBrew search-result cards and students/graduates category rows.
- Added San Francisco to the target location filter after identifying a clearly relevant BlackRock systematic research role.
- Stored and evaluated the missed role:
  - `Quantitative / Systematic Research, Associate`
  - `https://careers.blackrock.com/job/san-francisco/quantitative-systematic-research-associate/45831/95306345920`
  - latest label: `front=green`, `h1b=green`, `exp=green`, `score=80`
- Latest BlackRock crawl found 222 official listing cards and stored 75 jobs.

### Evaluator

- Added BlackRock front-quant aliases for `Quantitative / Systematic Research`, `Quant Research`, and `systematic research`.
- Relaxed seniority detection so title seniority matters more than generic career-path boilerplate inside a JD.
- Internship roles are allowed to be `exp=green`.

## Known Limitations

- Citadel and Citadel Securities can still block detail pages with Cloudflare. The crawler can store official listing rows, but some details may require manual saved-HTML refreshes.
- Several companies from the latest broad crawl still need URL repair, dedicated adapters, or manual source review.
- The first-layer filter is intentionally broad, so some non-front roles are stored and left for evaluator/dashboard review.
- H-1B labels are heuristic. `yellow` means the official JD did not give enough sponsorship evidence.

## Next Priorities

1. Review the 71 active `front=green`, `exp=green` jobs and create application statuses for the strongest ones.
2. Audit false positives in the current `front=green` bucket and update evaluator rules.
3. Continue source repair company-by-company for the remaining 404/provider-blocked/dynamic ATS targets.
4. Add a dashboard review queue for `front=green AND exp=green AND h1b in (green, yellow)`.
5. Add a small source-health view showing active source URL, last crawl status, stored count, and source confidence by company.
