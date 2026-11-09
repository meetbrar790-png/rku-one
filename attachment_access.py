"""Private attachment access rules, independent of storage provider.

This module intentionally does not expose upload/download HTTP endpoints.
All storage objects must remain private; callers must authenticate users and
verify that the attachment belongs to the requested message before issuing
short-lived storage access grants.
"""
from dataclasses import dataclass
from secrets import token_urlsafe

@dataclass(frozen=True)
class AttachmentRecord:
    object_key: str
    message_id: int
    sender_id: int
    recipient_id: int


def require_attachment_access(record: AttachmentRecord, *, requester_id: int, message_id: int) -> None:
    """Fail closed on cross-message or cross-user attachment requests."""
    if type(requester_id) is not int or requester_id <= 0:
        raise PermissionError("Authentication required")
    if type(message_id) is not int or message_id <= 0:
        raise PermissionError("Invalid message")
    if message_id != record.message_id:
        raise PermissionError("Attachment not part of requested message")
    if requester_id not in (record.sender_id, record.recipient_id):
        raise PermissionError("Not authorized to access attachment")


def new_private_object_key() -> str:
    """Opaque storage key; never embed names, emails, or predictable user IDs."""
    return "mail-attachments/" + token_urlsafe(32)


def require_private_storage_configuration(*, bucket_is_private: bool, encryption_enabled: bool) -> None:
    """Prevent enabling storage unless baseline confidentiality controls exist."""
    if bucket_is_private is not True or encryption_enabled is not True:
        raise RuntimeError("Private encrypted object storage required")
