"""Pure VIP-number policy helpers; no database writes or reservations.

These functions validate *proposed* VIP inventory. They do not assert that
any number is available, owned, reserved, or purchasable.
"""
from collections.abc import Iterable

MAX_RKU_ID = 2**63 - 1


def validate_numeric_id(value: int) -> int:
    """Accept positive BIGINT IDs, excluding bool (which is an int subclass)."""
    if type(value) is not int or not 1 <= value <= MAX_RKU_ID:
        raise ValueError("RKU ID must be a positive signed 64-bit integer")
    return value


def proposed_vip_inventory(candidates: Iterable[int], issued_ids: Iterable[int]) -> tuple[int, ...]:
    """Return sorted unissued candidates for *review*, never a reservation.

    Existing IDs always win. This is an offline snapshot only: availability
    must be rechecked under a database transaction at allocation time.
    """
    issued = {validate_numeric_id(value) for value in issued_ids}
    proposed = {validate_numeric_id(value) for value in candidates}
    return tuple(sorted(proposed - issued))
