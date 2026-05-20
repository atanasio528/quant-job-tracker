from dataclasses import dataclass


@dataclass(frozen=True)
class CompanyJobSourceSeed:
    company: str
    source_url: str
    source_type: str
    url_patterns: tuple[str, ...]
    notes: str
    confidence: str = "high"


JOB_SOURCE_SEEDS: tuple[CompanyJobSourceSeed, ...] = (
    CompanyJobSourceSeed(
        "Hudson River Trading",
        "https://www.hudsonrivertrading.com/careers/",
        "official_careers",
        ("/careers/", "greenhouse.io"),
        "Official careers page; role details are surfaced from the HRT careers experience.",
    ),
    CompanyJobSourceSeed(
        "Jane Street",
        "https://www.janestreet.com/join-jane-street/open-roles/",
        "official_careers",
        ("/join-jane-street/open-roles/",),
        "Official open roles page; querystring filters are categories, not separate job details.",
    ),
    CompanyJobSourceSeed(
        "D. E. Shaw",
        "https://www.deshaw.com/careers",
        "official_careers",
        ("/careers/", "/recruit/jobs/"),
        "Official careers page; job detail URLs use /careers/<role>-<id>.",
    ),
    CompanyJobSourceSeed(
        "Two Sigma",
        "https://www.twosigma.com/careers/",
        "official_careers",
        ("/careers/",),
        "Official careers page; reject /businesses/ and article pages.",
    ),
    CompanyJobSourceSeed(
        "Citadel",
        "https://www.citadel.com/careers/open-opportunities/",
        "official_careers",
        ("/careers/details/", "/careers/open-opportunities/"),
        "Official open opportunities page; job postings use /careers/details/.",
    ),
    CompanyJobSourceSeed(
        "Citadel Securities",
        "https://www.citadelsecurities.com/careers/open-opportunities/",
        "official_careers",
        ("/careers/details/", "/careers/open-opportunities/"),
        "Official open opportunities page; job postings use /careers/details/.",
    ),
    CompanyJobSourceSeed(
        "Point72",
        "https://careers.point72.com/",
        "official_careers",
        ("careers.point72.com", "CSJobDetail", "CSCareerSearch"),
        "Official careers portal; reject point72.com marketing/category links.",
    ),
    CompanyJobSourceSeed(
        "Cubist Systematic Strategies",
        "https://careers.point72.com/",
        "official_careers",
        ("careers.point72.com", "CSJobDetail", "CSCareerSearch", "focus=Systematic"),
        "Cubist roles are listed through Point72 careers.",
    ),
    CompanyJobSourceSeed(
        "Millennium Management",
        "https://www.mlp.com/careers/",
        "official_careers",
        ("mlp.eightfold.ai/careers", "pid="),
        "Official careers page links into Millennium's Eightfold job portal.",
    ),
    CompanyJobSourceSeed(
        "Squarepoint Capital",
        "https://www.squarepoint-capital.com/open-opportunities",
        "official_careers",
        ("/open-opportunities",),
        "Official open opportunities page.",
    ),
    CompanyJobSourceSeed(
        "Susquehanna International Group",
        "https://careers.sig.com/",
        "official_careers",
        ("careers.sig.com",),
        "Official SIG careers portal.",
    ),
    CompanyJobSourceSeed(
        "Optiver",
        "https://optiver.com/working-at-optiver/career-opportunities/",
        "official_careers",
        ("/working-at-optiver/career-opportunities/",),
        "Official career opportunities page; reject /career-hub/ article links.",
    ),
    CompanyJobSourceSeed(
        "DRW",
        "https://drw.com/work-at-drw/listings",
        "official_careers",
        ("/work-at-drw/listings/", "/work-at-drw/listings"),
        "Official DRW listings page.",
    ),
    CompanyJobSourceSeed(
        "Jump Trading",
        "https://www.jumptrading.com/careers/",
        "official_careers",
        ("/careers/",),
        "Official careers page; reject /trading and homepage links.",
    ),
    CompanyJobSourceSeed(
        "Tower Research Capital",
        "https://www.tower-research.com/open-positions/",
        "official_careers",
        ("/open-positions/", "tower-research.com/careers"),
        "Official open positions page.",
    ),
    CompanyJobSourceSeed(
        "Akuna Capital",
        "https://akunacapital.com/careers",
        "official_careers",
        ("/careers",),
        "Official careers page; reject /what-we-do/ links.",
    ),
    CompanyJobSourceSeed(
        "Chicago Trading Company",
        "https://www.chicagotrading.com/careers/",
        "official_careers",
        ("/posting?req=",),
        "Official CTC job postings use /posting?req=.",
    ),
    CompanyJobSourceSeed(
        "Five Rings",
        "https://fiverings.com/careers/",
        "ats_job_board",
        ("job-boards.greenhouse.io/fiveringsllc/jobs/",),
        "Official careers page links to Greenhouse job details.",
    ),
    CompanyJobSourceSeed(
        "Group One Trading",
        "https://www.group1.com/careers/",
        "ats_job_board",
        ("group1.applicantpro.com/jobs/",),
        "Official careers page links to ApplicantPro job details.",
    ),
    CompanyJobSourceSeed(
        "Renaissance Technologies",
        "https://www.rentec.com/Careers.action",
        "official_careers",
        ("Careers.action?jobs=true&selectedPosition=",),
        "Official Rentec careers page exposes selectedPosition job links.",
    ),
    CompanyJobSourceSeed(
        "WorldQuant",
        "https://www.worldquant.com/careers/",
        "official_careers",
        ("/career-listing/?id=",),
        "Official careers page; reject ideas, ventures, foundry, and university links.",
    ),
    CompanyJobSourceSeed(
        "Capula Investment Management",
        "https://www.capulaglobal.com/careers/",
        "ats_job_board",
        ("capula-investment-management-ltd.workable.com/jobs/",),
        "Official careers page links to Workable job details.",
    ),
    CompanyJobSourceSeed(
        "PanAgora Asset Management",
        "https://www.panagora.com/careers/",
        "official_careers",
        ("/careers/",),
        "Official careers page; reject /insights/ research archive links.",
    ),
    CompanyJobSourceSeed(
        "Goldman Sachs",
        "https://www.goldmansachs.com/careers/",
        "official_careers",
        ("/careers/",),
        "Official Goldman Sachs careers page; current generic crawler needs tighter role search.",
        "medium",
    ),
    CompanyJobSourceSeed(
        "JPMorgan Chase",
        "https://careers.jpmorgan.com/us/en/home",
        "official_careers",
        ("careers.jpmorgan.com", "/jobs/"),
        "Official JPMorgan careers portal; reject jpmorgan.com insights pages.",
    ),
    CompanyJobSourceSeed(
        "Morgan Stanley",
        "https://www.morganstanley.com/careers/career-opportunities-search",
        "official_careers",
        ("/careers/career-opportunities-search",),
        "Official Morgan Stanley career opportunities search page.",
        "medium",
    ),
    CompanyJobSourceSeed(
        "Citi",
        "https://jobs.citi.com/",
        "official_careers",
        ("jobs.citi.com",),
        "Official Citi jobs portal.",
    ),
    CompanyJobSourceSeed(
        "Bank of America",
        "https://careers.bankofamerica.com/",
        "official_careers",
        ("careers.bankofamerica.com",),
        "Official Bank of America careers portal.",
    ),
)
