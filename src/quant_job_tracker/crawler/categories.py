CANONICAL_CATEGORIES = (
    "Investment Banks",
    "Hedge Funds",
    "Prop Trading",
    "Asset Management",
)

GROUP_TO_CATEGORY = {
    "sell_side_quant": "Investment Banks",
    "quant_hedge_fund": "Hedge Funds",
    "multi_manager": "Hedge Funds",
    "prop": "Prop Trading",
    "market_maker": "Prop Trading",
    "quant_asset_manager": "Asset Management",
}


def category_for_group(group: str) -> str:
    return GROUP_TO_CATEGORY[group]
