"""Identity-only connection request policy prototype.

Not connected to production endpoints. Only the server derives recipient-visible
fields; sender-provided free text, media, links and attachments are forbidden.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ConnectionRequestNotice:
    sender_rku_id: int
    recipient_rku_id: int
    message: str


def make_connection_notice(sender_rku_id: int, recipient_rku_id: int) -> ConnectionRequestNotice:
    """Return fixed text; never accept sender-supplied message content."""
    for number in (sender_rku_id, recipient_rku_id):
        if isinstance(number, bool) or not isinstance(number, int) or not 1 <= number <= 9223372036854775807:
            raise ValueError("Invalid RKU ID")
    if sender_rku_id == recipient_rku_id:
        raise ValueError("Cannot request connection with yourself")
    return ConnectionRequestNotice(
        sender_rku_id=sender_rku_id,
        recipient_rku_id=recipient_rku_id,
        message=f"RKU ID {sender_rku_id} wants to connect with you.",
    )


def validate_request_payload(payload: dict) -> bool:
    """Reject user-controlled text and media keys, even when empty.

    Request sender must be taken from authenticated session, never from payload.
    The only accepted payload field is the recipient ID.
    """
    if not isinstance(payload, dict) or set(payload) != {"recipient_rku_id"}:
        return False
    number = payload["recipient_rku_id"]
    return isinstance(number, int) and not isinstance(number, bool) and 1 <= number <= 9223372036854775807
