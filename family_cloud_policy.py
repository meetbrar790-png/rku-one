"""Pure RKU Family Cloud access policy (not connected to live storage).

Membership does not grant access to personal files. Invitations must be
accepted before shared family workspace access is allowed.
"""
ROLES = frozenset({"owner", "adult", "limited"})


def validate_family_invitation(inviter_id, invitee_id, inviter_role):
    if type(inviter_id) is not int or type(invitee_id) is not int or inviter_id < 1 or invitee_id < 1:
        raise ValueError("Valid RKU IDs required")
    if inviter_id == invitee_id:
        raise ValueError("Cannot invite yourself")
    if inviter_role not in ("owner", "adult"):
        raise PermissionError("Not allowed to invite members")
    return {"inviter_id": inviter_id, "invitee_id": invitee_id, "accepted": False}


def can_access_family_file(member_id, workspace_members, file_scope, invited_accepted):
    if type(member_id) is not int or member_id < 1 or type(invited_accepted) is not bool or not invited_accepted:
        return False
    if file_scope != "family":
        return False
    role = workspace_members.get(member_id)
    return role in ROLES


def can_manage_family_members(role):
    return role == "owner"
