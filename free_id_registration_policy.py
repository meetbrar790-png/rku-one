"""Free numeric ID allocation policy for the proposed RKU ONE launch.

Pure validation only: no live database access, migration, or allocation.
The production registration path is NOT yet wired to this policy.
"""
from vip_tier_policy import FREE_ID_START, vip_tier


def is_free_registration_id(rku_id: int) -> bool:
    """True only for normal/free IDs, starting at 1000."""
    return vip_tier(rku_id) == "normal"


def assert_free_registration_candidate(rku_id: int, *, issued_ids, reserved_ids) -> int:
    """Validate a candidate against a caller-provided inventory snapshot.

    NOT sufficient for production: allocation must recheck under a shared
    PostgreSQL transaction lock against authoritative live inventory.
    """
    if not is_free_registration_id(rku_id):
        raise ValueError(f"Free registration IDs must start at {FREE_ID_START}")
    if rku_id in issued_ids or rku_id in reserved_ids:
        raise ValueError("ID is already issued or reserved")
    return rku_id


def free_registration_policy_summary() -> dict:
    return {
        "free_id_start": FREE_ID_START,
        "premium_id_end": FREE_ID_START - 1,
        "live_registration_integrated": False,
        "transactional_inventory_required": True,
    }
