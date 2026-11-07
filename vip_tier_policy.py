"""Proposed RKU ONE VIP tier policy. Pure functions; no live allocation changes.

Owner proposal: ID 1 founder-held; 2-10 VVIP; IDs 11, 13, 786
Special VVIP; other 12-100 VIP Gold; other 101-1000 VIP Silver;
1001+ normal/free.
Premium prices are denominated in USD. Exact amounts are not yet decided.
Previously issued IDs remain issued and cannot be sold again.
"""


VIP_PRICE_CURRENCY = "USD"
FREE_ID_START = 1001
SPECIAL_VVIP_IDS = frozenset({11, 13, 786})


def vip_tier(rku_id: int) -> str:
    if isinstance(rku_id, bool) or not isinstance(rku_id, int) or rku_id < 1:
        raise ValueError("RKU ID must be a positive integer")
    if rku_id == 1:
        return "founder"
    if rku_id in SPECIAL_VVIP_IDS:
        return "special_vvip"
    if rku_id <= 10:
        return "vvip"
    if rku_id <= 100:
        return "vip_gold"
    if rku_id <= 1000:
        return "vip_silver"
    return "normal"


def is_paid_premium_id(rku_id: int) -> bool:
    return vip_tier(rku_id) in {"special_vvip", "vvip", "vip_gold", "vip_silver"}


def is_available_for_sale(rku_id: int, issued_ids, reserved_ids) -> bool:
    """Inventory filter only; never a substitute for transactional DB checks."""
    return (is_paid_premium_id(rku_id)
            and rku_id not in issued_ids
            and rku_id not in reserved_ids)
