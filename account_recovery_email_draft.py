"""Safe password reset email draft builder (not a mail sender).

The reset URL must be constructed by a trusted server with an approved
HTTPS origin. The raw token belongs only in the one-time link sent to the
verified account email; never log it or include it in analytics.
"""
from urllib.parse import quote, urlsplit

from account_recovery_policy import RESET_TTL, hash_reset_token


def build_reset_email(*, recipient_email: str, token: str, app_origin: str) -> dict:
    """Return a message for future authenticated email delivery; sends nothing."""
    if not isinstance(recipient_email, str) or not recipient_email.strip():
        raise ValueError("Recipient email required")
    recipient = recipient_email.strip().lower()
    if len(recipient) > 254 or "\r" in recipient or "\n" in recipient or "@" not in recipient:
        raise ValueError("Invalid recipient")
    hash_reset_token(token)  # Validate token shape without exposing it.
    if not isinstance(app_origin, str):
        raise ValueError("Approved HTTPS origin required")
    parts = urlsplit(app_origin)
    if (parts.scheme != "https" or not parts.hostname or parts.username or parts.password
            or parts.path not in ("", "/") or parts.query or parts.fragment):
        raise ValueError("Only a trusted HTTPS origin is permitted")
    # The origin MUST be supplied from server-side trusted configuration,
    # never from a Host header or untrusted user input.
    origin = app_origin.rstrip("/")
    link = origin + "/reset-password?token=" + quote(token, safe="")
    return {
        "to": recipient,
        "subject": "RKU ONE — Reset your password",
        "text": (
            "A password reset was requested for your RKU ONE account.\n\n"
            "Use this link within 20 minutes:\n"
            + link
            + "\n\nIf you did not request this, ignore this message. "
            "Do not share this link with anyone.\n"
        ),
        "ttl_minutes": int(RESET_TTL.total_seconds() // 60),
        "delivery_enabled": False,
    }
