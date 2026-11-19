"""Read-only, fail-closed filtering for the public featured VIP catalogue.

Only explicitly featured premium numbers are queried. This endpoint never
returns owner identities or asserts that a remaining number is available.
"""
from vip_tier_policy import is_paid_premium_id

FEATURED_VIP_IDS = (2, 3, 4, 5, 6, 7, 8, 9, 10, 13, 786, 100, 1000)


def visible_featured_ids(conn):
    issued = {int(row[0]) for row in conn.execute(
        "SELECT rku_id FROM users WHERE rku_id = ANY(%s)",
        (list(FEATURED_VIP_IDS),),
    ).fetchall()}
    return [number for number in FEATURED_VIP_IDS
            if is_paid_premium_id(number) and number not in issued]
