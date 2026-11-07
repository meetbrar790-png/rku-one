"""Safe Stripe TEST-mode checkout planning, with no network calls or payment capture.

This module does not create Stripe sessions, take payments, or reserve IDs.
It builds a server-side USD checkout specification for future staging integration.
"""
from dataclasses import dataclass
from vip_pricing_policy import proposed_price_usd
from vip_tier_policy import is_paid_premium_id

@dataclass(frozen=True)
class SandboxCheckoutSpec:
    rku_id: int
    currency: str
    unit_amount: int
    mode: str
    adaptive_pricing_requested: bool
    test_mode_only: bool
    fulfillment_enabled: bool


def build_sandbox_checkout_spec(rku_id: int, *, issued_ids, reserved_ids) -> SandboxCheckoutSpec:
    """Produce a preview spec, NOT an authorization to sell or a Stripe API call.

    Production must re-check inventory transactionally under the shared lock,
    bind a hold to a buyer and order, and verify the payment webhook.
    """
    if not is_paid_premium_id(rku_id):
        raise ValueError("ID is not a paid VIP number")
    if rku_id in issued_ids or rku_id in reserved_ids:
        raise ValueError("ID is issued or reserved")
    price_usd = proposed_price_usd(rku_id)
    if price_usd is None or price_usd <= 0:
        raise ValueError("No payable VIP list price")
    return SandboxCheckoutSpec(
        rku_id=rku_id,
        currency="usd",
        unit_amount=price_usd * 100,
        mode="payment",
        adaptive_pricing_requested=True,
        test_mode_only=True,
        fulfillment_enabled=False,
    )


def assert_stripe_test_key(key: str) -> None:
    """Fail closed for missing/live/restricted keys. Never log the key."""
    if not isinstance(key, str) or not key.startswith("sk_test_") or len(key) <= len("sk_test_"):
        raise ValueError("A Stripe sandbox secret key is required; live keys are forbidden")
