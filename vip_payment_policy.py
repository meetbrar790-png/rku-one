"""Offline VIP payment confirmation policy; no real payments or database writes.

Provider verification must occur server-side through a trusted API or
signature-verified webhook before invoking this policy.
"""

def may_allocate_paid_vip(*, reservation_state, payment_verified, payment_reference_matches,
                          reservation_owner_matches, issued, expired):
    if reservation_state not in {"reserved", "allocated", "cancelled"}:
        raise ValueError("Unknown reservation state")
    flags = (payment_verified, payment_reference_matches,
             reservation_owner_matches, issued, expired)
    if any(type(flag) is not bool for flag in flags):
        raise ValueError("Payment and reservation checks must be boolean")
    return (reservation_state == "reserved"
            and payment_verified
            and payment_reference_matches
            and reservation_owner_matches
            and not issued
            and not expired)
