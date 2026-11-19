"""VIP interest-request validation only. Does not persist, reserve, allocate or charge."""
from vip_shop_preview import parse_numeric_id
from vip_tier_policy import is_paid_premium_id

SPECIAL_OWNER_REVIEW = frozenset({13, 786})


def prepare_interest_request(number_input, requester_id, request_key):
    """Validate a proposed interest request, without executing it.

    A production endpoint must authenticate the requester, rate limit, use
    idempotent storage and verify live reservation/issued inventory.
    """
    number = parse_numeric_id(number_input)
    if type(requester_id) is not int or requester_id < 1:
        raise ValueError("Authenticated requester ID required")
    if not isinstance(request_key, str) or not 8 <= len(request_key) <= 80:
        raise ValueError("Valid idempotency key required")
    if not all(c.isascii() and (c.isalnum() or c in "-_") for c in request_key):
        raise ValueError("Invalid idempotency key")
    if not is_paid_premium_id(number):
        raise ValueError("Number is not eligible for VIP interest requests")
    return {
        "number_id": number,
        "requester_id": requester_id,
        "request_key": request_key,
        "status": "draft_not_submitted",
        "requires_owner_review": number in SPECIAL_OWNER_REVIEW,
        "number_held": False,
        "payment_collected": False,
        "inventory_verified": False,
    }
