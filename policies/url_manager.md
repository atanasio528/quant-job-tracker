# URL Manager Policy

The URL manager owns company-by-company job-source discovery before crawler changes. Its job is to give the crawler a small, trusted map of where official live job postings actually appear, and to give the evaluator enough URL context to flag bad rows.

## Responsibilities

- Find and maintain official career/job-posting URLs for every target company.
- Prefer official company domains and ATS pages linked from official career pages.
- Record `source_url`, `trusted_url_patterns`, `reject_url_patterns`, `confidence`, `verification_status`, and short crawl notes.
- Mark bot-blocked or dynamically rendered pages as `blocked_by_provider` instead of replacing them with unofficial mirrors.
- Never approve blog posts, insight pages, strategy pages, business overview pages, PDFs, investor pages, LinkedIn-only pages, or search-engine snippets as job sources.
- Give crawler notes that explain how to reach postings when the source page needs filters, pagination, embedded ATS data, or browser rendering.

## Collection Workflow

1. Start from the company name in `SEEDS` and the current row in `JOB_SOURCE_SEEDS`.
2. Open the official homepage or official careers page first.
3. Follow links labeled `Open Roles`, `Job Search`, `Careers`, `Join Us`, `Opportunities`, `Students`, `Graduates`, or equivalent.
4. Confirm the final source page exposes actual role titles, locations, job cards, application links, or an official ATS search interface.
5. Capture one source URL that other roles can revisit directly. If the direct job-search page is stable, use it as `source_url`; otherwise use the parent career page and document the navigation path.
6. Record trusted detail patterns only after seeing real job-card or detail links.
7. Record reject patterns for nearby non-job pages that the generic crawler could mistake for jobs.
8. If ordinary HTTP crawling returns 403/404 while a browser can view the page, keep the official source and set `verification_status=blocked_by_provider`.
9. Hand off the source map to the crawler, then review sampled crawler rows with the evaluator for `not_job_page`, `title_dirty`, and `needs_better_adapter` flags.

## Field Conventions

- `source_url`: the canonical official page to crawl or open first.
- `entry_url`: optional parent page when users must navigate from a broader careers page.
- `trusted_url_patterns`: URL substrings that can identify valid job list/detail pages.
- `reject_url_patterns`: URL substrings that should not be treated as jobs.
- `confidence`: `high`, `medium`, `low`, or `blocked`.
- `verification_status`: `verified_live`, `verified_dynamic`, `blocked_by_provider`, `needs_manual_review`, or `retired`.
- `crawl_note`: one short sentence about page structure or crawler constraints.

## First Five Company Source Map

### Hudson River Trading

- Category: Prop Trading
- Source URL: https://www.hudsonrivertrading.com/careers/
- Trusted URL patterns: `/careers/`, `boards.greenhouse.io/hrttalentcommunity`
- Reject URL patterns: `/tech-blog/`, `/about/`, `/offices/`
- Confidence: high
- Verification status: verified_dynamic
- Crawl note: The careers page renders filters statically and loads jobs through the official WordPress AJAX action `get_hrt_jobs_handler`; Greenhouse links may be talent-community links, so keep official HRT career-page context when classifying rows.

### Jane Street

- Category: Prop Trading
- Source URL: https://www.janestreet.com/join-jane-street/open-roles/
- Trusted URL patterns: `/join-jane-street/open-roles/`
- Reject URL patterns: `/tech-talks/`, `/blog/`, `/programs-and-events/`
- Confidence: high
- Verification status: verified_live
- Crawl note: Job filters are query parameters on the same open-roles page; do not treat filter pages as separate companies or duplicate sources.

### D. E. Shaw

- Category: Hedge Funds
- Source URL: https://www.deshaw.com/careers
- Trusted URL patterns: `/careers/`, `/careers/<role>-<id>`, `apply.deshaw.com`
- Reject URL patterns: `/about/`, `/what-we-do/`, `/recruiting-fraud/`
- Confidence: high
- Verification status: verified_live
- Crawl note: Role cards on the careers page link to detail pages such as `/careers/quantitative-analyst-2636`; titles may be prefixed by icon text and must be cleaned.

### Two Sigma

- Category: Hedge Funds
- Source URL: https://careers.twosigma.com/careers/OpenRoles
- Entry URL: https://www.twosigma.com/careers/
- Trusted URL patterns: `careers.twosigma.com`, `/careers/OpenRoles`, `/careers/JobDetail/`
- Reject URL patterns: `www.twosigma.com/businesses/`, `www.twosigma.com/articles/`, `www.twosigma.com/insights/`
- Confidence: high
- Verification status: verified_live
- Crawl note: The real posting surface is the OpenRoles careers portal; crawl `jobOffset` pagination and keep only `/careers/JobDetail/` detail links.

### Citadel

- Category: Hedge Funds
- Source URL: https://www.citadel.com/careers/open-opportunities/
- Trusted URL patterns: `/careers/open-opportunities/`, `/careers/details/`
- Reject URL patterns: `/news/`, `/what-we-do/`, `/career-perspectives/`
- Confidence: blocked
- Verification status: blocked_by_provider
- Crawl note: The official open-opportunities page lists jobs and detail links, but local HTTP crawling can hit 403; use browser/manual verification or a dedicated adapter instead of switching to unofficial sources.

## Flow Traders Correction

- Category: Prop Trading
- Entry URL: https://www.flowtraders.com/careers/
- Source URL: https://www.flowtraders.com/careers/job-search/
- Trusted URL patterns: `/careers/job-search/`, `/careers/`
- Reject URL patterns: `/careers/jobs`, `/news/`, `/investors/`, `/foundation/`
- Confidence: medium
- Verification status: verified_dynamic
- Crawl note: `/careers/jobs` can return 404. The official path is to open the careers page, use `Job Search`, then search/filter relevant roles on `/careers/job-search/`.

## Full-Run Verified Source Fixes

### IMC Trading

- Category: Prop Trading
- Source URL: https://www.imc.com/us/search-careers
- Supplemental URL: https://www.imc.com/us/careers/experienced-roles/trading
- Trusted URL patterns: `/us/search-careers`, `/us/careers/jobs/`
- Reject URL patterns: `/us/strategic-investments`, `/us/careers/benefits`, `/us/careers/recruitment-process`
- Confidence: high
- Verification status: verified_live
- Crawl note: The main search page exposes only a partial first-page set; combine it with the official trading roles page to capture quant researcher and trader roles.

### Susquehanna International Group

- Category: Prop Trading
- Source URL: https://careers.sig.com/
- API URL: https://careers.sig.com/api/jobs
- Trusted URL patterns: `/api/jobs`, `/jobs/`
- Reject URL patterns: `/what-we-do/`, `/who-we-are/`, `/privacy/`
- Confidence: high
- Verification status: verified_dynamic
- Crawl note: The rendered Jibe app hides job cards from static parsing. Query the official API with quant research/trading/trader/ML terms, then use `/jobs/<slug>` detail URLs.

### Voloridge

- Category: Hedge Funds
- Source URL: https://www.voloridge.com/join-our-team
- Trusted URL patterns: `/join-our-team`, `voloridge-investment-management.hiringthing.com/job/`
- Reject URL patterns: `/careers/`
- Confidence: high
- Verification status: verified_live
- Crawl note: The old `/careers/` URL is only an intro/404-style page; the live job cards are on `Join Our Team` and link to HiringThing.

### XTX Markets

- Category: Prop Trading
- Entry URL: https://www.xtxmarkets.com/careers/
- Source URL: https://job-boards.greenhouse.io/xtxmarketstechnologies
- Trusted URL patterns: `job-boards.greenhouse.io/xtxmarketstechnologies/jobs/`
- Reject URL patterns: `/careers/` marketing anchors without job IDs
- Confidence: high
- Verification status: verified_live
- Crawl note: The official careers page links to the Greenhouse board; parse Greenhouse rows to keep title and location separate.

### BlackRock

- Category: Asset Management
- Source URL: https://careers.blackrock.com/search-jobs?k=quant
- Trusted URL patterns: `careers.blackrock.com/search-jobs`, `careers.blackrock.com/job/`
- Reject URL patterns: `/blog-`, `/from-hackathon`, `/career-development`
- Confidence: medium
- Verification status: verified_live
- Crawl note: The homepage promotes career blog posts that look keyword-relevant; use the official quant search URL and only accept `/job/` detail links.
