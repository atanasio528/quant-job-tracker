# Evaluator Policy

Read the full job description and classify the role. Do not rely only on title.

Return JSON with exactly these keys: `front`, `h1b`, `exp`, `score`, `reason`, `flags`.

Prefer keeping edge cases visible with honest low scores over silently rejecting unusual titles. Use `h1b=yellow` when sponsorship language is missing or unclear.

## Official Job Source Links

Use these source links and trusted URL patterns when deciding whether a crawled row came from a real company job-posting surface. If a stored row points to a blog, insight article, product page, PDF, business overview, or unrelated external domain, flag it as `page_noise`, `title_dirty`, `not_job_page`, or `needs_better_adapter`.

## Target Company Categories

Every target company must belong to exactly one of these evaluator categories. Use the category when reviewing source quality and when explaining crawler false positives.

### Investment Banks (5)
- Goldman Sachs: https://www.goldmansachs.com/careers/
- JPMorgan Chase: https://careers.jpmorgan.com/us/en/home
- Morgan Stanley: https://www.morganstanley.com/careers/career-opportunities-search
- Citi: https://jobs.citi.com/
- Bank of America: https://careers.bankofamerica.com/

### Hedge Funds (41)
- D. E. Shaw: https://www.deshaw.com/careers
- Two Sigma: https://careers.twosigma.com/careers/OpenRoles
- Citadel: https://www.citadel.com/careers/open-opportunities/
- Point72: https://careers.point72.com/
- Cubist Systematic Strategies: https://careers.point72.com/
- Millennium Management: https://www.mlp.com/careers/
- Balyasny Asset Management: https://www.bamfunds.com/careers/
- Squarepoint Capital: https://www.squarepoint-capital.com/open-opportunities
- Qube Research & Technologies: https://www.qube-rt.com/careers/
- Renaissance Technologies: https://www.rentec.com/Careers.action
- AQR Capital Management: https://www.aqr.com/careers
- Man Group: https://www.man.com/careers
- Winton: https://www.winton.com/careers
- WorldQuant: https://www.worldquant.com/careers/
- G-Research: https://www.gresearch.com/careers/
- Capula Investment Management: https://www.capulaglobal.com/careers/
- Schonfeld: https://www.schonfeld.com/careers/
- Verition Fund Management: https://www.verition.com/careers/
- ExodusPoint: https://www.exoduspoint.com/careers/
- PDT Partners: https://www.pdtpartners.com/careers/
- The Voleon Group: https://www.voleon.com/careers
- Trexquant: https://www.trexquant.com/careers/
- AlphaGrep: https://www.alpha-grep.com/careers/
- CFM: https://www.cfm.com/join-us/
- Systematica Investments: https://www.systematica.com/careers/
- Aspect Capital: https://www.aspectcapital.com/careers/
- Graham Capital Management: https://www.grahamcapital.com/careers/
- Brevan Howard: https://www.brevanhoward.com/careers/
- Marshall Wace: https://www.mwam.com/careers/
- Rokos Capital Management: https://www.rokoscapital.com/careers/
- Tudor Investment Corporation: https://www.tudor.com/careers/
- Aquatic Capital Management: https://aquatic.com/careers/
- Voloridge: https://www.voloridge.com/join-our-team
- Kepos Capital: https://www.keposcapital.com/careers/
- Walleye Capital: https://www.walleyecapital.com/careers/
- Paloma Partners: https://www.paloma.com/careers/
- Laurion Capital: https://www.laurioncapital.com/careers/
- Eisler Capital: https://www.eislercapital.com/careers/
- LMR Partners: https://www.lmrpartners.com/careers/
- Quadrature: https://quadrature.ai/careers/
- Teza Technologies: https://www.teza.com/careers/

### Prop Trading (30)
- Hudson River Trading: https://www.hudsonrivertrading.com/careers/
- Jane Street: https://www.janestreet.com/join-jane-street/open-roles/
- Citadel Securities: https://www.citadelsecurities.com/careers/open-opportunities/
- Susquehanna International Group: https://careers.sig.com/
- Optiver: https://optiver.com/working-at-optiver/career-opportunities/
- IMC Trading: https://www.imc.com/us/search-careers
- DRW: https://drw.com/work-at-drw/listings
- Jump Trading: https://www.jumptrading.com/careers/
- Tower Research Capital: https://www.tower-research.com/open-positions/
- XTX Markets: https://job-boards.greenhouse.io/xtxmarketstechnologies
- Virtu Financial: https://www.virtu.com/careers/
- Flow Traders: https://www.flowtraders.com/careers/job-search/
- Akuna Capital: https://akunacapital.com/careers
- Chicago Trading Company: https://www.chicagotrading.com/careers/
- Five Rings: https://fiverings.com/careers/
- Old Mission: https://www.oldmissioncapital.com/careers/
- Belvedere Trading: https://www.belvederetrading.com/careers/
- Maven Securities: https://www.mavensecurities.com/careers/
- TransMarket Group: https://www.transmarketgroup.com/careers/
- Quantlab: https://www.quantlab.com/careers/
- Wolverine Trading: https://www.wolve.com/careers/
- Headlands Technologies: https://www.headlandstech.com/careers/
- Radix Trading: https://radixtrading.co/careers/
- Mako Trading: https://www.mako.com/careers/
- Da Vinci Derivatives: https://davinciderivatives.com/careers/
- Eclipse Trading: https://www.eclipsetrading.com/careers/
- Group One Trading: https://www.group1.com/careers/
- Peak6: https://www.peak6.com/careers/
- WH Trading: https://www.whtrading.com/careers/
- All Options: https://alloptions.nl/careers/

### Asset Management (5)
- Arrowstreet Capital: https://www.arrowstreetcapital.com/careers/
- BlackRock: https://careers.blackrock.com/search-jobs?k=quant
- Acadian Asset Management: https://www.acadian-asset.com/careers
- PanAgora Asset Management: https://www.panagora.com/careers/
- Dimensional Fund Advisors: https://www.dimensional.com/us-en/careers

- Hudson River Trading: https://www.hudsonrivertrading.com/careers/ | trusted patterns: `/careers/`, `greenhouse.io`. Official careers page; role details are surfaced from the HRT careers experience.
- Jane Street: https://www.janestreet.com/join-jane-street/open-roles/ | trusted patterns: `/join-jane-street/open-roles/`. Official open roles page; querystring filters are categories, not separate job details.
- D. E. Shaw: https://www.deshaw.com/careers | trusted patterns: `/careers/`, `/recruit/jobs/`. Official careers page; job detail URLs use `/careers/<role>-<id>`.
- Two Sigma: https://careers.twosigma.com/careers/OpenRoles | trusted patterns: `careers.twosigma.com`, `/careers/OpenRoles`, `/careers/JobDetail/`. Official OpenRoles portal; reject `twosigma.com` `/businesses/` and article pages.
- Citadel: https://www.citadel.com/careers/open-opportunities/ | trusted patterns: `/careers/details/`, `/careers/open-opportunities/`. Official open opportunities page; job postings use `/careers/details/`.
- Citadel Securities: https://www.citadelsecurities.com/careers/open-opportunities/ | trusted patterns: `/careers/details/`, `/careers/open-opportunities/`. Official open opportunities page; job postings use `/careers/details/`.
- Point72: https://careers.point72.com/ | trusted patterns: `careers.point72.com`, `CSJobDetail`, `CSCareerSearch`. Official careers portal; reject `point72.com` marketing/category links.
- Cubist Systematic Strategies: https://careers.point72.com/ | trusted patterns: `careers.point72.com`, `CSJobDetail`, `CSCareerSearch`, `focus=Systematic`. Cubist roles are listed through Point72 careers.
- Millennium Management: https://www.mlp.com/careers/ | trusted patterns: `mlp.eightfold.ai/careers`, `pid=`. Official careers page links into Millennium's Eightfold job portal.
- Squarepoint Capital: https://www.squarepoint-capital.com/open-opportunities | trusted patterns: `/open-opportunities`. Official open opportunities page.
- Susquehanna International Group: https://careers.sig.com/ | trusted patterns: `careers.sig.com`, `/api/jobs`, `/jobs/`. Official SIG careers portal; the crawler uses the official Jibe `/api/jobs` endpoint for quant search terms.
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
- Balyasny Asset Management: https://www.bamfunds.com/careers/ | trusted patterns: `/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- Qube Research & Technologies: https://www.qube-rt.com/careers/ | trusted patterns: `/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- IMC Trading: https://www.imc.com/us/search-careers | trusted patterns: `/us/search-careers`, `/us/careers/jobs/`. Official IMC job-search page; job detail links use `/us/careers/jobs/`.
- XTX Markets: https://job-boards.greenhouse.io/xtxmarketstechnologies | trusted patterns: `job-boards.greenhouse.io/xtxmarketstechnologies/jobs/`. Official XTX careers page links to this Greenhouse board.
- Virtu Financial: https://www.virtu.com/careers/ | trusted patterns: `/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- Flow Traders: https://www.flowtraders.com/careers/job-search/ | trusted patterns: `/careers/job-search/`, `/careers/`. Official job-search surface linked from the careers page; `/careers/jobs` can return 404.
- Old Mission: https://www.oldmissioncapital.com/careers/ | trusted patterns: `/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- Belvedere Trading: https://www.belvederetrading.com/careers/ | trusted patterns: `/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- Maven Securities: https://www.mavensecurities.com/careers/ | trusted patterns: `/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- TransMarket Group: https://www.transmarketgroup.com/careers/ | trusted patterns: `/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- Quantlab: https://www.quantlab.com/careers/ | trusted patterns: `/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- Wolverine Trading: https://www.wolve.com/careers/ | trusted patterns: `/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- Headlands Technologies: https://www.headlandstech.com/careers/ | trusted patterns: `/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- Radix Trading: https://radixtrading.co/careers/ | trusted patterns: `/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- Mako Trading: https://www.mako.com/careers/ | trusted patterns: `/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- Da Vinci Derivatives: https://davinciderivatives.com/careers/ | trusted patterns: `/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- Eclipse Trading: https://www.eclipsetrading.com/careers/ | trusted patterns: `/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- Peak6: https://www.peak6.com/careers/ | trusted patterns: `/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- WH Trading: https://www.whtrading.com/careers/ | trusted patterns: `/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- All Options: https://alloptions.nl/careers/ | trusted patterns: `/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- AQR Capital Management: https://www.aqr.com/careers | trusted patterns: `/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- Man Group: https://www.man.com/careers | trusted patterns: `/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- Winton: https://www.winton.com/careers | trusted patterns: `/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- G-Research: https://www.gresearch.com/careers/ | trusted patterns: `/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- Schonfeld: https://www.schonfeld.com/careers/ | trusted patterns: `/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- Verition Fund Management: https://www.verition.com/careers/ | trusted patterns: `/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- ExodusPoint: https://www.exoduspoint.com/careers/ | trusted patterns: `/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- PDT Partners: https://www.pdtpartners.com/careers/ | trusted patterns: `/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- The Voleon Group: https://www.voleon.com/careers | trusted patterns: `/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- Trexquant: https://www.trexquant.com/careers/ | trusted patterns: `/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- AlphaGrep: https://www.alpha-grep.com/careers/ | trusted patterns: `/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- CFM: https://www.cfm.com/join-us/ | trusted patterns: `/join-us`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- Systematica Investments: https://www.systematica.com/careers/ | trusted patterns: `/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- Aspect Capital: https://www.aspectcapital.com/careers/ | trusted patterns: `/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- Graham Capital Management: https://www.grahamcapital.com/careers/ | trusted patterns: `/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- Brevan Howard: https://www.brevanhoward.com/careers/ | trusted patterns: `/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- Marshall Wace: https://www.mwam.com/careers/ | trusted patterns: `/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- Rokos Capital Management: https://www.rokoscapital.com/careers/ | trusted patterns: `/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- Tudor Investment Corporation: https://www.tudor.com/careers/ | trusted patterns: `/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- Aquatic Capital Management: https://aquatic.com/careers/ | trusted patterns: `/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- Voloridge: https://www.voloridge.com/join-our-team | trusted patterns: `/join-our-team`, `voloridge-investment-management.hiringthing.com/job/`. Official join-our-team page; live job postings link to HiringThing.
- Arrowstreet Capital: https://www.arrowstreetcapital.com/careers/ | trusted patterns: `/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- Kepos Capital: https://www.keposcapital.com/careers/ | trusted patterns: `/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- Walleye Capital: https://www.walleyecapital.com/careers/ | trusted patterns: `/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- Paloma Partners: https://www.paloma.com/careers/ | trusted patterns: `/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- Laurion Capital: https://www.laurioncapital.com/careers/ | trusted patterns: `/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- Eisler Capital: https://www.eislercapital.com/careers/ | trusted patterns: `/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- LMR Partners: https://www.lmrpartners.com/careers/ | trusted patterns: `/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- Quadrature: https://quadrature.ai/careers/ | trusted patterns: `/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- Teza Technologies: https://www.teza.com/careers/ | trusted patterns: `/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- BlackRock: https://careers.blackrock.com/search-jobs?k=quant | trusted patterns: `careers.blackrock.com/search-jobs`, `careers.blackrock.com/job/`. Official BlackRock jobs search scoped to quant; reject career blog links.
- Acadian Asset Management: https://www.acadian-asset.com/careers | trusted patterns: `/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
- Dimensional Fund Advisors: https://www.dimensional.com/us-en/careers | trusted patterns: `/us-en/careers`. Official careers source from target seed list; URL structure needs evaluator review before hard crawler validation.
