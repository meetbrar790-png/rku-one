"""Stripe Checkout TEST session request builder; no API/network calls.

Future staging-only server code may submit this payload to Stripe after
authenticating a buyer, placing an atomic VIP hold, and verifying inventory.
Do not wire this directly into production registration or fulfillment.
"""
from urllib.parse import urlsplit
from stripe_sandbox_checkout_plan import build_sandbox_checkout_spec, assert_stripe_test_key


def _assert_local_staging_url(url: str) -> None:
    if not isinstance(url, str):
        raise ValueError("Local staging URL required")
    parts = urlsplit(url)
    if (parts.scheme != "http" or parts.hostname not in {"localhost", "127.0.0.1"}
            or not parts.port or parts.username or parts.password
            or parts.fragment or parts.query or not parts.path.startswith("/")):
        raise ValueError("Only loopback HTTP staging URLs are permitted")


def build_test_checkout_request(
    rku_id: int, *, issued_ids, reserved_ids, test_secret_key: str,
    success_url: str, cancel_url: str, test_order_reference: str,
) -> dict:
    """Build data for a Stripe TEST Checkout Session; does not send it.

    The reference is test-only, not a verified paid order. Do not use this
    builder as an inventory lock or payment fulfillment authorization.
    """
    assert_stripe_test_key(test_secret_key)
    _assert_local_staging_url(success_url)
    _assert_local_staging_url(cancel_url)
    if (not isinstance(test_order_reference, str)
            or not test_order_reference.startswith("test_")
            or len(test_order_reference) > 100
            or not test_order_reference[5:].replace("_", "").replace("-", "").isalnum()):
        raise ValueError("A simple test-only order reference is required")
    spec = build_sandbox_checkout_spec(
        rku_id, issued_ids=issued_ids, reserved_ids=reserved_ids
    )
    return {
        "mode": spec.mode,
        "success_url": success_url,
        "cancel_url": cancel_url,
        "client_reference_id": test_order_reference,
        "line_items": [{
            "price_data": {
                "currency": spec.currency,
                "unit_amount": spec.unit_amount,
                "product_data": {"name": f"RKU ONE VIP ID {rku_id} (TEST)"},
            },
            "quantity": 1,
        }],
        "metadata": {
            "rku_id": str(rku_id),
            "test_order_reference": test_order_reference,
            "environment": "test",
        },
    }
