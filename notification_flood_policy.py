"""Isolated notification flood protection policy prototype.

No push delivery or production integration. This pure decision function is not
an anti-DDoS control: server-side admission, deduplication and atomic counters
are required before deployment.
"""
from dataclasses import dataclass
from enum import Enum


class NotificationKind(str, Enum):
    TRUSTED_MESSAGE = "trusted_message"
    UNKNOWN_REQUEST = "unknown_request"
    VERIFIED_BUSINESS_MAIL = "verified_business_mail"
    VERIFIED_OFFICIAL_MAIL = "verified_official_mail"
    SECURITY_ALERT = "security_alert"


class PrivacyMode(str, Enum):
    PROTECTED = "protected"
    STRICT = "strict"


class Delivery(str, Enum):
    PUSH = "push"
    DIGEST = "digest"
    SILENT_INBOX = "silent_inbox"


@dataclass(frozen=True)
class NotificationContext:
    mode: PrivacyMode
    kind: NotificationKind
    sender_is_allowed: bool
    unknown_digest_already_scheduled: bool = False


def delivery_for(context: NotificationContext) -> Delivery:
    """Default unknown requests to silent inbox, never per-request push."""
    if not isinstance(context, NotificationContext):
        return Delivery.SILENT_INBOX
    if not isinstance(context.mode, PrivacyMode) or not isinstance(context.kind, NotificationKind):
        return Delivery.SILENT_INBOX
    if not isinstance(context.sender_is_allowed, bool) or not isinstance(context.unknown_digest_already_scheduled, bool):
        return Delivery.SILENT_INBOX
    if context.kind is NotificationKind.UNKNOWN_REQUEST:
        if context.mode is PrivacyMode.PROTECTED and not context.unknown_digest_already_scheduled:
            return Delivery.DIGEST
        return Delivery.SILENT_INBOX
    if context.kind is NotificationKind.SECURITY_ALERT:
        return Delivery.PUSH  # Caller must independently authenticate and dedupe alerts.
    if context.kind is NotificationKind.TRUSTED_MESSAGE:
        return Delivery.PUSH if context.sender_is_allowed else Delivery.SILENT_INBOX
    # Verification alone does not authorize a push to a recipient.
    return Delivery.PUSH if context.sender_is_allowed else Delivery.SILENT_INBOX
