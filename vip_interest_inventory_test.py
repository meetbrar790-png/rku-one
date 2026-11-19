"""Read-only VIP inventory decision helper for isolated tests.

Fail closed: lack of complete issued AND held inventories never means available.
This module performs no DB writes, reservations, allocations or payments.
"""
from vip_interest_request import prepare_interest_request

FOUNDER_AND_COMPANY = frozenset({1, 11})
OWNER_REVIEW = frozenset({13, 786})


def evaluate_vip_interest(number_input, requester_id, request_key, *, issued_ids=None, held_ids=None):
    draft = prepare_interest_request(number_input, requester_id, request_key)
    number = draft["number_id"]
    if issued_ids is None or held_ids is None:
        return {**draft, "inventory_status": "unverified", "may_submit": False}
    issued = set(issued_ids)
    held = set(held_ids)
    if number in issued:
        status = "issued"
    elif number in held or number in FOUNDER_AND_COMPANY:
        status = "held"
    elif number in OWNER_REVIEW:
        status = "owner_review_required"
    else:
        status = "unissued_unheld_in_test_snapshot"
    return {
        **draft,
        "inventory_status": status,
        "may_submit": status == "unissued_unheld_in_test_snapshot",
        "inventory_verified": False,
        "number_held": False,
        "payment_collected": False,
    }
