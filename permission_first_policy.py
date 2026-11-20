"""RKU ONE Permission First policy prototype (not connected to production).

All unknown numeric IDs are denied direct calls and chats by default.
A connection request is a separate, rate-limited action. Enforcement must
happen server-side on every delivery, not just in the user interface.
"""
from enum import Enum


class ContactStatus(str, Enum):
    UNKNOWN = "unknown"
    PENDING = "pending"
    ALLOWED = "allowed"
    REJECTED = "rejected"
    BLOCKED = "blocked"


class Action(str, Enum):
    VOICE_CALL = "voice_call"
    VIDEO_CALL = "video_call"
    CHAT = "chat"
    CONNECTION_REQUEST = "connection_request"


def may_contact(status: ContactStatus, action: Action) -> bool:
    """Fail closed for invalid/unknown status and action values."""
    if not isinstance(status, ContactStatus) or not isinstance(action, Action):
        return False
    if status is ContactStatus.ALLOWED:
        return True
    if status is ContactStatus.UNKNOWN and action is Action.CONNECTION_REQUEST:
        return True  # Only after server-side request quotas and abuse checks.
    return False


def transition(status: ContactStatus, decision: str) -> ContactStatus:
    """Receiver-controlled decisions; caller must authenticate receiver.

    A block is not removable by the sender. A receiver can explicitly unblock
    via a separate verified account-management operation (not implemented).
    """
    if not isinstance(status, ContactStatus):
        raise ValueError("Invalid contact state")
    if decision == "block":
        return ContactStatus.BLOCKED
    if status is ContactStatus.BLOCKED:
        raise ValueError("Blocked contact requires receiver-side unblock")
    if decision == "request" and status is ContactStatus.UNKNOWN:
        return ContactStatus.PENDING
    if decision == "allow" and status in (ContactStatus.PENDING, ContactStatus.REJECTED):
        return ContactStatus.ALLOWED
    if decision == "reject" and status in (ContactStatus.PENDING, ContactStatus.ALLOWED):
        return ContactStatus.REJECTED
    raise ValueError("Invalid transition")
