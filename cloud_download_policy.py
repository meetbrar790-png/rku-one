"""RKU Cloud download authorization rules.

These pure helpers do not create signed links or access object storage.
Actual downloads must recheck authenticated permissions against live metadata.
"""
from datetime import datetime, timezone


def authorize_personal_download(authenticated_id, owner_id, status):
    if type(authenticated_id) is not int or type(owner_id) is not int or authenticated_id < 1 or owner_id < 1:
        return False
    return authenticated_id == owner_id and status == "ready"


def authorize_shared_download(authenticated_id, recipient_id, status, accepted, revoked, expires_at):
    if type(authenticated_id) is not int or type(recipient_id) is not int or authenticated_id < 1 or recipient_id < 1:
        return False
    if status != "ready" or accepted is not True or revoked is not False:
        return False
    if not isinstance(expires_at, datetime) or expires_at.tzinfo is None:
        return False
    return authenticated_id == recipient_id and expires_at > datetime.now(timezone.utc)
