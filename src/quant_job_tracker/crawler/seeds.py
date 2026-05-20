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
    CompanySeed(
        "Two Sigma", "quant_hedge_fund", "https://careers.twosigma.com/careers/OpenRoles", "generic"
    ),
    CompanySeed(
        "Citadel", "multi_manager", "https://www.citadel.com/careers/open-opportunities/", "generic"
    ),
    CompanySeed(
        "Citadel Securities",
        "market_maker",
        "https://www.citadelsecurities.com/careers/open-opportunities/",
        "generic",
    ),
    CompanySeed("Point72", "multi_manager", "https://careers.point72.com/", "generic"),
    CompanySeed(
        "Cubist Systematic Strategies",
        "quant_hedge_fund",
        "https://point72.com/cubist/",
        "generic",
        "Official Cubist page; jobs may be listed under Point72 careers.",
    ),
    CompanySeed(
        "Millennium Management", "multi_manager", "https://www.mlp.com/careers/", "generic"
    ),
    CompanySeed(
        "Balyasny Asset Management", "multi_manager", "https://www.bamfunds.com/careers/", "generic"
    ),
    CompanySeed(
        "Squarepoint Capital",
        "quant_hedge_fund",
        "https://www.squarepoint-capital.com/open-opportunities",
        "generic",
    ),
    CompanySeed(
        "Qube Research & Technologies",
        "quant_hedge_fund",
        "https://www.qube-rt.com/careers/",
        "generic",
    ),
    CompanySeed(
        "Susquehanna International Group",
        "prop",
        "https://careers.sig.com/",
        "generic",
    ),
    CompanySeed(
        "Optiver",
        "prop",
        "https://optiver.com/working-at-optiver/career-opportunities/",
        "generic",
    ),
    CompanySeed("IMC Trading", "prop", "https://www.imc.com/us/search-careers", "generic"),
    CompanySeed("DRW", "prop", "https://drw.com/work-at-drw/listings", "generic"),
    CompanySeed("Jump Trading", "prop", "https://www.jumptrading.com/careers/", "generic"),
    CompanySeed(
        "Tower Research Capital",
        "prop",
        "https://www.tower-research.com/open-positions/",
        "generic",
    ),
    CompanySeed(
        "XTX Markets",
        "market_maker",
        "https://job-boards.greenhouse.io/xtxmarketstechnologies",
        "generic",
    ),
    CompanySeed("Virtu Financial", "market_maker", "https://www.virtu.com/careers/", "generic"),
    CompanySeed(
        "Flow Traders",
        "market_maker",
        "https://www.flowtraders.com/careers/job-search/",
        "generic",
    ),
    CompanySeed("Akuna Capital", "prop", "https://akunacapital.com/careers", "generic"),
    CompanySeed(
        "Chicago Trading Company",
        "prop",
        "https://www.chicagotrading.com/careers/",
        "generic",
    ),
    CompanySeed("Five Rings", "prop", "https://fiverings.com/careers/", "generic"),
    CompanySeed(
        "Old Mission",
        "prop",
        "https://www.oldmissioncapital.com/careers/",
        "generic",
    ),
    CompanySeed(
        "Belvedere Trading",
        "prop",
        "https://www.belvederetrading.com/careers/",
        "generic",
    ),
    CompanySeed(
        "Maven Securities",
        "prop",
        "https://www.mavensecurities.com/careers/",
        "generic",
    ),
    CompanySeed(
        "TransMarket Group",
        "prop",
        "https://www.transmarketgroup.com/careers/",
        "generic",
    ),
    CompanySeed("Quantlab", "prop", "https://www.quantlab.com/careers/", "generic"),
    CompanySeed("Wolverine Trading", "prop", "https://www.wolve.com/careers/", "generic"),
    CompanySeed(
        "Headlands Technologies",
        "prop",
        "https://www.headlandstech.com/careers/",
        "generic",
    ),
    CompanySeed("Radix Trading", "prop", "https://radixtrading.co/careers/", "generic"),
    CompanySeed("Mako Trading", "prop", "https://www.mako.com/careers/", "generic"),
    CompanySeed(
        "Da Vinci Derivatives",
        "prop",
        "https://davinciderivatives.com/careers/",
        "generic",
    ),
    CompanySeed(
        "Eclipse Trading",
        "prop",
        "https://www.eclipsetrading.com/careers/",
        "generic",
    ),
    CompanySeed("Group One Trading", "prop", "https://www.group1.com/careers/", "generic"),
    CompanySeed("Peak6", "prop", "https://www.peak6.com/careers/", "generic"),
    CompanySeed("WH Trading", "prop", "https://www.whtrading.com/careers/", "generic"),
    CompanySeed("All Options", "prop", "https://alloptions.nl/careers/", "generic"),
    CompanySeed(
        "Renaissance Technologies",
        "quant_hedge_fund",
        "https://www.rentec.com/Careers.action",
        "generic",
    ),
    CompanySeed(
        "AQR Capital Management", "quant_hedge_fund", "https://www.aqr.com/careers", "generic"
    ),
    CompanySeed("Man Group", "quant_hedge_fund", "https://www.man.com/careers", "generic"),
    CompanySeed("Winton", "quant_hedge_fund", "https://www.winton.com/careers", "generic"),
    CompanySeed("WorldQuant", "quant_hedge_fund", "https://www.worldquant.com/careers/", "generic"),
    CompanySeed("G-Research", "quant_hedge_fund", "https://www.gresearch.com/careers/", "generic"),
    CompanySeed(
        "Capula Investment Management",
        "quant_hedge_fund",
        "https://www.capulaglobal.com/careers/",
        "generic",
    ),
    CompanySeed("Schonfeld", "multi_manager", "https://www.schonfeld.com/careers/", "generic"),
    CompanySeed(
        "Verition Fund Management",
        "multi_manager",
        "https://www.verition.com/careers/",
        "generic",
    ),
    CompanySeed("ExodusPoint", "multi_manager", "https://www.exoduspoint.com/careers/", "generic"),
    CompanySeed(
        "PDT Partners", "quant_hedge_fund", "https://www.pdtpartners.com/careers/", "generic"
    ),
    CompanySeed(
        "The Voleon Group", "quant_hedge_fund", "https://www.voleon.com/careers", "generic"
    ),
    CompanySeed("Trexquant", "quant_hedge_fund", "https://www.trexquant.com/careers/", "generic"),
    CompanySeed("AlphaGrep", "quant_hedge_fund", "https://www.alpha-grep.com/careers/", "generic"),
    CompanySeed("CFM", "quant_hedge_fund", "https://www.cfm.com/join-us/", "generic"),
    CompanySeed(
        "Systematica Investments",
        "quant_hedge_fund",
        "https://www.systematica.com/careers/",
        "generic",
    ),
    CompanySeed(
        "Aspect Capital", "quant_hedge_fund", "https://www.aspectcapital.com/careers/", "generic"
    ),
    CompanySeed(
        "Graham Capital Management",
        "quant_hedge_fund",
        "https://www.grahamcapital.com/careers/",
        "generic",
    ),
    CompanySeed(
        "Brevan Howard", "quant_hedge_fund", "https://www.brevanhoward.com/careers/", "generic"
    ),
    CompanySeed("Marshall Wace", "quant_hedge_fund", "https://www.mwam.com/careers/", "generic"),
    CompanySeed(
        "Rokos Capital Management",
        "quant_hedge_fund",
        "https://www.rokoscapital.com/careers/",
        "generic",
    ),
    CompanySeed(
        "Tudor Investment Corporation",
        "quant_hedge_fund",
        "https://www.tudor.com/careers/",
        "generic",
    ),
    CompanySeed(
        "Aquatic Capital Management", "quant_hedge_fund", "https://aquatic.com/careers/", "generic"
    ),
    CompanySeed(
        "Voloridge",
        "quant_hedge_fund",
        "https://www.voloridge.com/join-our-team",
        "generic",
    ),
    CompanySeed(
        "Arrowstreet Capital",
        "quant_asset_manager",
        "https://www.arrowstreetcapital.com/careers/",
        "generic",
    ),
    CompanySeed(
        "Kepos Capital", "quant_hedge_fund", "https://www.keposcapital.com/careers/", "generic"
    ),
    CompanySeed(
        "Walleye Capital", "multi_manager", "https://www.walleyecapital.com/careers/", "generic"
    ),
    CompanySeed("Paloma Partners", "multi_manager", "https://www.paloma.com/careers/", "generic"),
    CompanySeed(
        "Laurion Capital", "multi_manager", "https://www.laurioncapital.com/careers/", "generic"
    ),
    CompanySeed(
        "Eisler Capital", "multi_manager", "https://www.eislercapital.com/careers/", "generic"
    ),
    CompanySeed("LMR Partners", "multi_manager", "https://www.lmrpartners.com/careers/", "generic"),
    CompanySeed("Quadrature", "quant_hedge_fund", "https://quadrature.ai/careers/", "generic"),
    CompanySeed(
        "Teza Technologies", "quant_hedge_fund", "https://www.teza.com/careers/", "generic"
    ),
    CompanySeed(
        "BlackRock",
        "quant_asset_manager",
        "https://careers.blackrock.com/search-jobs?k=quant",
        "generic",
    ),
    CompanySeed(
        "Acadian Asset Management",
        "quant_asset_manager",
        "https://www.acadian-asset.com/careers",
        "generic",
    ),
    CompanySeed(
        "PanAgora Asset Management",
        "quant_asset_manager",
        "https://www.panagora.com/careers/",
        "generic",
    ),
    CompanySeed(
        "Dimensional Fund Advisors",
        "quant_asset_manager",
        "https://www.dimensional.com/us-en/careers",
        "generic",
    ),
    CompanySeed(
        "Goldman Sachs", "sell_side_quant", "https://www.goldmansachs.com/careers/", "generic"
    ),
    CompanySeed(
        "JPMorgan Chase", "sell_side_quant", "https://careers.jpmorgan.com/us/en/home", "generic"
    ),
    CompanySeed(
        "Morgan Stanley",
        "sell_side_quant",
        "https://www.morganstanley.com/people-opportunities/careers",
        "generic",
    ),
    CompanySeed("Citi", "sell_side_quant", "https://jobs.citi.com/", "generic"),
    CompanySeed(
        "Bank of America", "sell_side_quant", "https://careers.bankofamerica.com/", "generic"
    ),
]
