"""Staging-only adapter for testing the real API endpoint with VIP-aware allocation.

Not imported by production api.py or registration.py. No live DB access.
"""
from staging_db_preflight import assert_disposable_staging_url
from vip_full_registration_test_service import register_test_user
from registration import password_hash
import psycopg


def staged_vip_register(url, users_table, reservations_table, sequence_name,
                        email, password):
    assert_disposable_staging_url(url)
    if not isinstance(password, str) or not 12 <= len(password) <= 256:
        raise ValueError("Valid password of 12 to 256 characters required")
    if not isinstance(email, str) or not email.strip() or len(email) > 254:
        raise ValueError("Valid email required")
    hashed = password_hash.hash(password)
    with psycopg.connect(url) as conn:
        rku_id, normalized_email = register_test_user(
            conn, users_table, reservations_table, sequence_name, email, hashed)
    return {"rku_id": rku_id, "email": normalized_email}
