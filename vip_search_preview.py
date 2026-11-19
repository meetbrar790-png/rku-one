"""VIP search response builder: no database, payments, holds, or allocations.

This is a prototype only. Public HTTP exposure requires authenticated access,
rate limiting and a verified inventory/hold source.
"""
from vip_readonly_status import preview_vip_status


def vip_search_preview(number, issued_lookup):
    if isinstance(number, bool) or not isinstance(number, int) or not 1 <= number <= 1000:
        raise ValueError("VIP number must be an integer from 1 to 1000")
    result = preview_vip_status(number, issued_lookup)
    return {
        "number": result["rku_id"],
        "currency": result["currency"],
        "list_price_usd": result["list_price_usd"],
        "category": result["category"],
        "status": result["availability"],
        "availability_verified": False,
        "payment_enabled": False,
        "reservation_enabled": False,
        "allocation_enabled": False,
        "message": "Status is informational only; sale availability is not confirmed.",
    }
