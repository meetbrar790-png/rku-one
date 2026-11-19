"""Staging-only authentication and rate-limit regression tests.

Calls the handler directly. No server, production inventory, or payment access.
"""
import os
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from mail_auth import issue_token
from vip_interest_staging_api import InterestInput, limiter, submit_staging_interest


class VipStagingAuthLimitTests(unittest.TestCase):
    def setUp(self):
        limiter._history.clear()
        secret = patch.dict(os.environ, {"RKU_SESSION_SECRET": "isolated-auth-limit-secret"})
        secret.start()
        self.addCleanup(secret.stop)

    def submit(self, authorization, key, number="1000"):
        return submit_staging_interest(
            InterestInput(numeric_id=number, request_key=key),
            authorization=authorization,
        )

    def test_missing_token_is_rejected_before_rate_limit(self):
        with self.assertRaises(HTTPException) as error:
            self.submit(None, "auth-limit-no-token")
        self.assertEqual(error.exception.status_code, 401)
        self.assertEqual(dict(limiter._history), {})

    def test_bad_bearer_token_rejected(self):
        with self.assertRaises(HTTPException) as error:
            self.submit("Bearer not-a-valid-token", "auth-limit-bad-token")
        self.assertEqual(error.exception.status_code, 401)

    def test_sixth_authenticated_request_is_limited(self):
        token = "Bearer " + issue_token(1001)
        for index in range(5):
            result = self.submit(token, "limit-test-key-%02d" % index)
            self.assertEqual(result["status"], "received_not_reserved")
            self.assertFalse(result["number_held"])
            self.assertFalse(result["payment_collected"])
        with self.assertRaises(HTTPException) as error:
            self.submit(token, "limit-test-key-06")
        self.assertEqual(error.exception.status_code, 429)

    def test_limiter_separates_authenticated_requesters(self):
        first = "Bearer " + issue_token(1001)
        second = "Bearer " + issue_token(1002)
        for index in range(5):
            self.submit(first, "separate-user-%02d" % index)
        result = self.submit(second, "separate-user-other")
        self.assertEqual(result["status"], "received_not_reserved")


if __name__ == "__main__":
    unittest.main()
