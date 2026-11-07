"""Offline email verification binding rules; no live account mutations.

A token must be bound to the same user and normalized email that was
present when it was issued. Email changes invalidate outstanding tokens.
"""


def normalize_verification_email(email: str) -> str:
    if not isinstance(email, str):
        raise ValueError("Email required")
    normalized = email.strip().lower()
    if not normalized or len(normalized) > 254 or "@" not in normalized:
        raise ValueError("Invalid email")
    if "\r" in normalized or "\n" in normalized or " " in normalized:
        raise ValueError("Invalid email")
    return normalized


def may_verify_email(*, token_user_id: int, current_user_id: int,
                     token_email: str, current_email: str,
                     token_is_usable: bool) -> bool:
    if type(token_user_id) is not int or type(current_user_id) is not int:
        return False
    if token_user_id < 1 or current_user_id < 1 or token_user_id != current_user_id:
        return False
    if token_is_usable is not True:
        return False
    try:
        return normalize_verification_email(token_email) == normalize_verification_email(current_email)
    except ValueError:
        return False
