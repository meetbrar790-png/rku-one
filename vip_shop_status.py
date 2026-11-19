"""Conservative, read-only VIP status lookup.

An absent ID in users does NOT imply availability: holds and reserved inventory
are not connected. Never use this endpoint as sale authorization.
"""
from vip_shop_preview import parse_numeric_id, number_preview


def status_snapshot(value, issued_lookup):
    number = parse_numeric_id(value)
    entry = number_preview(number)
    if entry["category"] in ("Founder — not for sale", "Company — not for sale"):
        entry["availability"] = "reserved"
    elif entry["category"] == "Free":
        entry["availability"] = "free_registration_policy"
    elif issued_lookup(number):
        entry["availability"] = "issued"
    else:
        entry["availability"] = "unknown"
    entry["sale_enabled"] = False
    entry["request_enabled"] = False
    return entry


def is_issued_in_users(conn, number):
    """Read-only issued-ID query; no migration, lock or write."""
    row = conn.execute("SELECT EXISTS(SELECT 1 FROM users WHERE rku_id=%s)", (number,)).fetchone()
    return bool(row[0])
