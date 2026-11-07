"""Public-facing proposed VIP price catalogue, without sale or availability claims.

The caller must never interpret a price as an available inventory item.
Production inventory, payment verification and allocation are NOT connected.
"""
from vip_pricing_policy import CURRENCY, proposed_price_usd
from vip_tier_policy import vip_tier

TIER_LABELS = {
    "founder": "Founder — not for sale",
    "company_reserved": "Company — not for sale",
    "vvip": "VVIP",
    "special_vvip": "Special VVIP",
    "vip_gold": "VIP Gold",
    "vip_silver": "VIP Silver",
    "normal": "Free",
}


def catalogue_entry(rku_id: int) -> dict:
    tier = vip_tier(rku_id)
    price = proposed_price_usd(rku_id)
    return {
        "rku_id": rku_id,
        "category": TIER_LABELS[tier],
        "currency": CURRENCY,
        "list_price_usd": price,
        "sale_enabled": False,
        "availability": "not_verified",
    }


def catalogue_summary() -> dict:
    return {
        "currency": CURRENCY,
        "sale_enabled": False,
        "founder_id": 1,
        "company_reserved_id": 11,
        "special_vvip_ids": [13, 786],
        "paid_id_range": [2, 1000],
        "free_id_start": 1001,
        "price_status": "proposed",
        "inventory_status": "not_verified",
    }
