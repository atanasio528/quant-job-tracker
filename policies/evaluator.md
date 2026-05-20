# Evaluator Policy

Read the full job description and classify the role. Do not rely only on title.

Return JSON with exactly these keys: `front`, `h1b`, `exp`, `score`, `reason`, `flags`.

Prefer keeping edge cases visible with honest low scores over silently rejecting unusual titles. Use `h1b=yellow` when sponsorship language is missing or unclear.

## Official Job Source Links

Use these source links and trusted URL patterns when deciding whether a crawled row came from a real company job-posting surface. If a stored row points to a blog, insight article, product page, PDF, business overview, or unrelated external domain, flag it as `page_noise`, `title_dirty`, `not_job_page`, or `needs_better_adapter`.

- Hudson River Trading: https://www.hudsonrivertrading.com/careers/ | trusted patterns: `/careers/`, `greenhouse.io`. Official careers page; role details are surfaced from the HRT careers experience.
- Jane Street: https://www.janestreet.com/join-jane-street/open-roles/ | trusted patterns: `/join-jane-street/open-roles/`. Official open roles page; querystring filters are categories, not separate job details.
- D. E. Shaw: https://www.deshaw.com/careers | trusted patterns: `/careers/`, `/recruit/jobs/`. Official careers page; job detail URLs use `/careers/<role>-<id>`.
- Two Sigma: https://www.twosigma.com/careers/ | trusted patterns: `/careers/`. Official careers page; reject `/businesses/` and article pages.
- Citadel: https://www.citadel.com/careers/open-opportunities/ | trusted patterns: `/careers/details/`, `/careers/open-opportunities/`. Official open opportunities page; job postings use `/careers/details/`.
- Citadel Securities: https://www.citadelsecurities.com/careers/open-opportunities/ | trusted patterns: `/careers/details/`, `/careers/open-opportunities/`. Official open opportunities page; job postings use `/careers/details/`.
- Point72: https://careers.point72.com/ | trusted patterns: `careers.point72.com`, `CSJobDetail`, `CSCareerSearch`. Official careers portal; reject `point72.com` marketing/category links.
- Cubist Systematic Strategies: https://careers.point72.com/ | trusted patterns: `careers.point72.com`, `CSJobDetail`, `CSCareerSearch`, `focus=Systematic`. Cubist roles are listed through Point72 careers.
- Millennium Management: https://www.mlp.com/careers/ | trusted patterns: `mlp.eightfold.ai/careers`, `pid=`. Official careers page links into Millennium's Eightfold job portal.
- Squarepoint Capital: https://www.squarepoint-capital.com/open-opportunities | trusted patterns: `/open-opportunities`. Official open opportunities page.
- Susquehanna International Group: https://careers.sig.com/ | trusted patterns: `careers.sig.com`. Official SIG careers portal.
- Optiver: https://optiver.com/working-at-optiver/career-opportunities/ | trusted patterns: `/working-at-optiver/career-opportunities/`. Official career opportunities page; reject `/career-hub/` article links.
- DRW: https://drw.com/work-at-drw/listings | trusted patterns: `/work-at-drw/listings/`, `/work-at-drw/listings`. Official DRW listings page.
- Jump Trading: https://www.jumptrading.com/careers/ | trusted patterns: `/careers/`. Official careers page; reject `/trading` and homepage links.
- Tower Research Capital: https://www.tower-research.com/open-positions/ | trusted patterns: `/open-positions/`, `tower-research.com/careers`. Official open positions page.
- Akuna Capital: https://akunacapital.com/careers | trusted patterns: `/careers`. Official careers page; reject `/what-we-do/` links.
- Chicago Trading Company: https://www.chicagotrading.com/careers/ | trusted patterns: `/posting?req=`. Official CTC job postings use `/posting?req=`.
- Five Rings: https://fiverings.com/careers/ | trusted patterns: `job-boards.greenhouse.io/fiveringsllc/jobs/`. Official careers page links to Greenhouse job details.
- Group One Trading: https://www.group1.com/careers/ | trusted patterns: `group1.applicantpro.com/jobs/`. Official careers page links to ApplicantPro job details.
- Renaissance Technologies: https://www.rentec.com/Careers.action | trusted patterns: `Careers.action?jobs=true&selectedPosition=`. Official Rentec careers page exposes selectedPosition job links.
- WorldQuant: https://www.worldquant.com/careers/ | trusted patterns: `/career-listing/?id=`. Official careers page; reject ideas, ventures, foundry, and university links.
- Capula Investment Management: https://www.capulaglobal.com/careers/ | trusted patterns: `capula-investment-management-ltd.workable.com/jobs/`. Official careers page links to Workable job details.
- PanAgora Asset Management: https://www.panagora.com/careers/ | trusted patterns: `/careers/`. Official careers page; reject `/insights/` research archive links.
- Goldman Sachs: https://www.goldmansachs.com/careers/ | trusted patterns: `/careers/`. Official Goldman Sachs careers page; current generic crawler needs tighter role search.
- JPMorgan Chase: https://careers.jpmorgan.com/us/en/home | trusted patterns: `careers.jpmorgan.com`, `/jobs/`. Official JPMorgan careers portal; reject `jpmorgan.com` insights pages.
- Morgan Stanley: https://www.morganstanley.com/careers/career-opportunities-search | trusted patterns: `/careers/career-opportunities-search`. Official Morgan Stanley career opportunities search page.
- Citi: https://jobs.citi.com/ | trusted patterns: `jobs.citi.com`. Official Citi jobs portal.
- Bank of America: https://careers.bankofamerica.com/ | trusted patterns: `careers.bankofamerica.com`. Official Bank of America careers portal.
