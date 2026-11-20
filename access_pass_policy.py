"""RKU ONE recipient-issued Access Pass authorization policy prototype.

Pure functions only. Not an API, cryptographic token, or production feature.
The caller must authenticate the recipient and enforce transactional persistence,
revocation, sender identity binding, auditing and anti-spam quotas server-side.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum


class Permission(str, Enum):
    BUSINESS_MAIL = "business_mail"
    CHAT = "chat"
    VOICE_CALL = "voice_call"
    VIDEO_CALL = "video_call"


@dataclass(frozen=True)
class AccessPass:
    owner_id: int
    grantee_id: int
    permissions: frozenset[Permission]
    expires_at: datetime | None
    revoked: bool = False


def _valid_id(number: int) -> bool:
    return isinstance(number, int) and not isinstance(number, bool) and 1 <= number <= 9223372036854775807


def authorize(pass_record: AccessPass, *, owner_id: int, sender_id: int,
              permission: Permission, now: datetime) -> bool:
    """Fail closed: explicit permission, correct recipient/sender, not expired."""
    if not isinstance(pass_record, AccessPass):
        return False
    if not all(_valid_id(x) for x in (pass_record.owner_id, pass_record.grantee_id, owner_id, sender_id)):
        return False
    if pass_record.owner_id != owner_id or pass_record.grantee_id != sender_id:
        return False
    if pass_record.revoked or not isinstance(permission, Permission):
        return False
    if not isinstance(pass_record.permissions, frozenset) or permission not in pass_record.permissions:
        return False
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        return False
    if pass_record.expires_at is not None:
        expiry = pass_record.expires_at
        if not isinstance(expiry, datetime) or expiry.tzinfo is None or expiry.utcoffset() is None:
            return False
        if now.astimezone(timezone.utc) >= expiry.astimezone(timezone.utc):
            return False
    return True
