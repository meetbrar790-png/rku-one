"""Read-only VIP shop preview policy. Never asserts live availability or accepts money.

The caller must query authoritative server inventory before any future reservation.
"""
from vip_price_catalogue import catalogue_entry

FEATURED_IDS = (2, 3, 7, 10, 13, 100, 786, 1000)
MAX_ID_DIGITS = 18


def parse_numeric_id(value):
    """Canonical positive decimal ID; reject booleans, signs and leading zeros."""
    if isinstance(value, bool):
        raise ValueError("Invalid numeric ID")
    if isinstance(value, int):
        number = value
    elif isinstance(value, str) and value.isascii() and value.isdecimal():
        if len(value) > MAX_ID_DIGITS or (len(value) > 1 and value.startswith("0")):
            raise ValueError("Invalid numeric ID")
        number = int(value)
    else:
        raise ValueError("Invalid numeric ID")
    if not 1 <= number < 10 ** MAX_ID_DIGITS:
        raise ValueError("Invalid numeric ID")
    return number


def number_preview(value):
    """Return proposed price with deliberately unknown inventory state."""
    number = parse_numeric_id(value)
    entry = catalogue_entry(number)
    entry["request_enabled"] = False
    entry["request_status"] = "not_implemented"
    entry["availability"] = "not_verified"
    entry["notice"] = (
        "Preview only. No live inventory check, hold, purchase or payment. "
        "Contact support to express interest; no number is guaranteed."
    )
    return entry


def featured_previews():
    return [number_preview(number) for number in FEATURED_IDS]
