"""Private file sharing policy for future RKU Cloud.

Pure validation only. No sharing endpoints, grants, or live file access
are enabled. Every grant must eventually be stored transactionally and
checked against authenticated file ownership.
"""
from datetime import datetime, timezone


def validate_share_request(owner_id, recipient_id, file_owner_id):
    for value in (owner_id, recipient_id, file_owner_id):
        if type(value) is not int or not 1 <= value <= 9223372036854775807:
            raise ValueError("Valid RKU IDs required")
    if owner_id != file_owner_id:
        raise PermissionError("Only the file owner can share")
    if owner_id == recipient_id:
        raise ValueError("Cannot share a file with yourself")
    return {"owner_id": owner_id, "recipient_id": recipient_id}


def can_download_share(authenticated_id, recipient_id, expires_at, revoked=False, accepted=False):
    if type(authenticated_id) is not int or type(recipient_id) is not int or authenticated_id < 1 or recipient_id < 1:
        return False
    if type(revoked) is not bool or type(accepted) is not bool or revoked or not accepted:
        return False
    if not isinstance(expires_at, datetime) or expires_at.tzinfo is None:
        return False
    return authenticated_id == recipient_id and expires_at > datetime.now(timezone.utc)
