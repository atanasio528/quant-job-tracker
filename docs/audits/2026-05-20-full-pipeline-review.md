# Full Pipeline Review - 2026-05-20

## Scope

- Configured target universe: 81 companies.
- User-requested universe: 100+ companies. The current codebase does not yet contain 100+ seeds, so this run covers every configured company but not a 100+ company list.
- Commands run:
  - `qjt collect-sources`
  - `qjt crawl`
  - `qjt eval-pending`
  - `qjt policy-report`

## Final Run

- Latest crawl run: `id=44`
- Status: `partial`
- Companies crawled: 81
- Jobs found before hard filters: 736
- Jobs stored/updated during the run: 291
- Live jobs in dashboard DB after stale closing: 269
- Latest eval run: `id=45`
- Live front-green jobs: 68
- Live experience-green jobs: 234
- Live H-1B green/yellow/red: 84 / 184 / 1

## Fixes Applied

- Added a policy-maker `Manual Update Watchlist` section and populated it with blocked/manual-update companies.
- Fixed Voloridge source from `/careers/` to the real `https://www.voloridge.com/join-our-team` posting page.
- Fixed IMC source from stale `/us/careers/jobs/` to `https://www.imc.com/us/search-careers` and added the official trading roles page as a supplemental crawl surface.
- Added a SIG adapter that uses the official `https://careers.sig.com/api/jobs` Jibe endpoint for quant research/trading/trader/ML terms.
- Added a Flow Traders adapter that uses the official Greenhouse API referenced by Flow's own job-search page.
- Fixed XTX to use the official Greenhouse board linked from its careers page.
- Fixed BlackRock to use `https://careers.blackrock.com/search-jobs?k=quant` and to accept only `/job/` links.
- Added first-layer skip rules for known non-job pages: AQR insights, Akuna what-we-do pages, Aspect insights, BAM how-we-work pages, Goldman/JPMorgan informational pages, Millennium people page, PanAgora insights, and WorldQuant ideas/foundry/university/ventures pages.

## Independent Evaluator Findings

- The crawler now works materially better for major quant-career firms that were missed before: IMC, SIG, Voloridge, XTX, Flow Traders, and BlackRock.
- The earlier D. E. Shaw title issue is fixed; stored titles no longer include `icon` prefixes or preview descriptions.
- The dashboard DB now has clean live rows from official sources only, with job links retained for application pages.
- The generic crawler is still too weak for some official dynamic portals. These should become company-specific adapters, not broader generic parsing.
- Several banks and asset managers are still configured, but the system correctly has few/no eligible rows after hard skips. For this project, these should remain lower priority than quant hedge funds and prop firms.
- Remaining first-page noise is still visible for firms whose official career pages mostly expose marketing/category links to the generic parser, including Rokos, Graham, G-Research, Man Group, Renaissance, Wolverine, Belvedere, Jump, and DRW. These are marked red/page-noise by the evaluator but need either dedicated adapters or additional firm-specific skip rules.

## Manual Update / Adapter Queue

### Bot or Provider Blocked

- Citadel: official AJAX listing works intermittently, but detail pages can hit Cloudflare. Listing rows are preserved when details are blocked.
- Citadel Securities: currently reuses Citadel-style listing/detail URLs and can hit Cloudflare/detail blocks.
- Aquatic Capital Management: official careers URL returned HTTP 403.

### Bad Seed URL / 404

- Maven Securities
- Radix Trading
- Mako Trading
- Da Vinci Derivatives
- WH Trading
- Winton
- Verition Fund Management
- ExodusPoint
- PDT Partners
- The Voleon Group
- AlphaGrep
- Marshall Wace
- Tudor Investment Corporation
- Arrowstreet Capital
- Kepos Capital
- Walleye Capital
- Paloma Partners
- Dimensional Fund Advisors
- Morgan Stanley

### Other Technical Failures

- Laurion Capital: SSL EOF from the official careers URL.
- Eisler Capital: hostname resolution failure from the configured official careers URL.

### Likely Missed Positions

- Squarepoint Capital: official open-opportunities page is dynamic and search results show role URLs; needs a dedicated parser/API discovery.
- Qube Research & Technologies: official careers page is mostly a rendered app/static shell to the local crawler; needs a browser/API adapter if live postings exist.
- Investment banks: Goldman Sachs, JPMorgan, Morgan Stanley, Citi, and Bank of America require proper official job-search API/filter adapters before results can be trusted.

## Sources Checked

- Voloridge: https://www.voloridge.com/join-our-team
- IMC: https://www.imc.com/us/search-careers and https://www.imc.com/us/careers/experienced-roles/trading
- Flow Traders: https://www.flowtraders.com/careers/job-search/
- SIG: https://careers.sig.com/ and https://careers.sig.com/api/jobs
- XTX Markets: https://www.xtxmarkets.com/careers/ and https://job-boards.greenhouse.io/xtxmarketstechnologies
- BlackRock: https://careers.blackrock.com/search-jobs?k=quant
- Squarepoint: https://www.squarepoint-capital.com/open-opportunities
- Qube Research & Technologies: https://www.qube-rt.com/careers/
