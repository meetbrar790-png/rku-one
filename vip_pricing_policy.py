"""Proposed launch list prices for RKU ONE numeric IDs in USD.

Business proposal only. No checkout, payment or live ID allocation.
Prices are one-time list prices, excluding any applicable tax.
Never offer an already-issued ID for sale. ID 1 and ID 11 are not for sale.
"""
from vip_tier_policy import is_available_for_sale, vip_tier

CURRENCY = "USD"
SPECIAL_PRICES_USD = {
    2: 9999, 3: 7999, 4: 5999, 5: 4999, 6: 3999,
    7: 7777, 8: 6999, 9: 4999, 10: 5999,
    13: 4999, 786: 4999, 100: 1499,
}


def proposed_price_usd(rku_id: int):
    """Return USD integer list price; None for founder/company reserved."""
    tier = vip_tier(rku_id)
    if tier in {"founder", "company_reserved"}:
        return None
    if tier == "normal":
        return 0
    if rku_id in SPECIAL_PRICES_USD:
        return SPECIAL_PRICES_USD[rku_id]
    if tier == "vip_gold":
        return 499
    if tier == "vip_silver":
        return 199
    raise ValueError("Missing price for premium tier")


def sale_quote_usd(rku_id: int, issued_ids, reserved_ids):
    """Informational only, never a purchase or reservation authorization."""
    if not is_available_for_sale(rku_id, issued_ids, reserved_ids):
        return None
    return proposed_price_usd(rku_id)
