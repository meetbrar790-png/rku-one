"""Security regression checks for the isolated staging VIP interest endpoint.

These call the handler directly, with no HTTP server, production DB, or payments.
"""
import base64
import hashlib
import hmac
import json
import os
import time
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from mail_auth import issue_token
from vip_interest_staging_api import InterestInput, submit_staging_interest, limiter


class VipStagingSecurityTests(unittest.TestCase):
    def setUp(self):
        limiter._history.clear()
        self.secret = patch.dict(os.environ, {"RKU_SESSION_SECRET": "isolated-test-only-secret"})
        self.secret.start()
        self.addCleanup(self.secret.stop)

    def submit(self, number, key, token):
        return submit_staging_interest(
            InterestInput(numeric_id=number, request_key=key),
            authorization="Bearer " + token,
        )

    def test_invalid_signature_denied(self):
        token = issue_token(1001)
        payload, signature = token.split(".", 1)
        bad = payload + "." + ("0" if signature[0] != "0" else "1") + signature[1:]
        with self.assertRaises(HTTPException) as error:
            self.submit("1000", "security-test-key-a", bad)
        self.assertEqual(error.exception.status_code, 401)

    def test_expired_token_denied(self):
        payload = base64.urlsafe_b64encode(
            json.dumps({"id": 1001, "exp": int(time.time()) - 100}).encode()
        ).decode().rstrip("=")
        signature = hmac.new(
            os.environ["RKU_SESSION_SECRET"].encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()
        with self.assertRaises(HTTPException) as error:
            self.submit("1000", "security-test-key-b", payload + "." + signature)
        self.assertEqual(error.exception.status_code, 401)

    def test_same_key_replay_is_idempotent(self):
        token = issue_token(1001)
        first = self.submit("1000", "security-test-key-c", token)
        second = self.submit("1000", "security-test-key-c", token)
        self.assertEqual(first, second)
        self.assertFalse(first["number_held"])
        self.assertFalse(first["payment_collected"])

    def test_key_reuse_for_different_number_denied(self):
        token = issue_token(1001)
        self.submit("1000", "security-test-key-d", token)
        with self.assertRaises(HTTPException) as error:
            self.submit("2", "security-test-key-d", token)
        self.assertEqual(error.exception.status_code, 400)

    def test_reserved_and_free_numbers_denied(self):
        token = issue_token(1001)
        for number in ("1", "11", "1001", "1002"):
            with self.subTest(number=number):
                with self.assertRaises(HTTPException) as error:
                    self.submit(number, "security-test-key-" + number, token)
                self.assertEqual(error.exception.status_code, 400)

    def test_invalid_idempotency_key_denied(self):
        token = issue_token(1001)
        with self.assertRaises(HTTPException) as error:
            self.submit("1000", "bad key !", token)
        self.assertEqual(error.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
