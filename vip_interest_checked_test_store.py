"""Fail-closed integration of disposable VIP interest storage and test inventory.

No production inventory access. The caller must provide BOTH complete disposable
issued and held snapshots. This is not a live availability or reservation service.
"""
from vip_interest_inventory_test import evaluate_vip_interest
from vip_interest_test_store import record_test_interest


def record_checked_test_interest(connection, number_input, requester_id, request_key,
                                 *, issued_ids=None, held_ids=None):
    check = evaluate_vip_interest(
        number_input, requester_id, request_key,
        issued_ids=issued_ids, held_ids=held_ids,
    )
    if not check["may_submit"]:
        raise ValueError("VIP test request blocked: " + check["inventory_status"])
    result = record_test_interest(connection, number_input, requester_id, request_key)
    return {
        **result,
        "inventory_status": check["inventory_status"],
        "inventory_verified": False,
        "number_held": False,
        "payment_collected": False,
    }
