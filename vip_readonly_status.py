"""Conservative read-only VIP status logic. Not wired to production routes.

Issued ID checks alone cannot establish sale availability because separate holds,
manual reservations and owner approvals are not connected.
"""
from vip_price_catalogue import catalogue_entry
from vip_tier_policy import is_paid_premium_id


def preview_vip_status(number, issued_lookup):
    """Return a non-authoritative status without modifying any inventory."""
    if isinstance(number, bool) or not isinstance(number, int) or not 1 <= number <= 1000:
        raise ValueError("VIP number must be between 1 and 1000")
    entry = catalogue_entry(number)
    if not is_paid_premium_id(number):
        entry["availability"] = "reserved_not_for_sale"
    elif issued_lookup(number):
        entry["availability"] = "issued_not_for_sale"
    else:
        entry["availability"] = "unverified"
    entry["request_enabled"] = False
    entry["sale_enabled"] = False
    entry["number_held"] = False
    return entry


def issued_id_exists_readonly(conn, number):
    """One parameterized SELECT; does not reserve or allocate."""
    row = conn.execute(
        "SELECT EXISTS(SELECT 1 FROM users WHERE rku_id=%s)", (number,)
    ).fetchone()
    return bool(row[0])
