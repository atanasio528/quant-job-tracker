from dataclasses import dataclass


@dataclass(frozen=True)
class CompanySeed:
    name: str
    group: str
    career_url: str
    ats: str | None = None
    notes: str | None = None


SEEDS: list[CompanySeed] = [
    CompanySeed(
        "Hudson River Trading",
        "prop",
        "https://www.hudsonrivertrading.com/careers/",
        "generic",
        "HRT Algorithm Developer may mean Quant Researcher.",
    ),
    CompanySeed(
        "Jane Street",
        "prop",
        "https://www.janestreet.com/join-jane-street/open-roles/",
        "generic",
    ),
    CompanySeed("D. E. Shaw", "quant_hedge_fund", "https://www.deshaw.com/careers", "generic"),
    CompanySeed("Two Sigma", "quant_hedge_fund", "https://www.twosigma.com/careers/", "generic"),
    CompanySeed("Citadel", "multi_manager", "https://www.citadel.com/careers/open-opportunities/", "generic"),
    CompanySeed(
        "Citadel Securities",
        "market_maker",
        "https://www.citadelsecurities.com/careers/open-opportunities/",
        "generic",
    ),
    CompanySeed("Point72", "multi_manager", "https://point72.com/careers/", "generic"),
    CompanySeed(
        "Cubist Systematic Strategies",
        "quant_hedge_fund",
        "https://point72.com/cubist/careers/",
        "generic",
    ),
    CompanySeed("Millennium Management", "multi_manager", "https://www.mlp.com/careers/", "generic"),
    CompanySeed("Balyasny Asset Management", "multi_manager", "https://www.bamfunds.com/careers/", "generic"),
    CompanySeed(
        "Squarepoint Capital",
        "quant_hedge_fund",
        "https://www.squarepoint-capital.com/careers",
        "generic",
    ),
    CompanySeed(
        "Qube Research & Technologies",
        "quant_hedge_fund",
        "https://www.qube-rt.com/careers/",
        "generic",
    ),
]
