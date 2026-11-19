import os
import unittest
from unittest.mock import patch
from fastapi import HTTPException
from mail_auth import issue_token
from vip_interest_staging_api import InterestInput, submit_staging_interest


class VipInterestStagingApiTests(unittest.TestCase):
    def test_login_required(self):
        with self.assertRaises(HTTPException) as ctx:
            submit_staging_interest(InterestInput(numeric_id="2", request_key="unique-req-001"), authorization=None)
        self.assertEqual(ctx.exception.status_code, 401)

    def test_authenticated_request_does_not_reserve(self):
        with patch.dict(os.environ, {"RKU_SESSION_SECRET": "disposable-test-secret"}):
            token = issue_token(1001)
            result = submit_staging_interest(
                InterestInput(numeric_id="1000", request_key="unique-req-002"),
                authorization="Bearer " + token,
            )
        self.assertEqual(result["status"], "received_not_reserved")
        self.assertFalse(result["number_held"])
        self.assertFalse(result["payment_collected"])

    def test_reserved_rejected(self):
        with patch.dict(os.environ, {"RKU_SESSION_SECRET": "disposable-test-secret"}):
            token = issue_token(1001)
            with self.assertRaises(HTTPException) as ctx:
                submit_staging_interest(
                    InterestInput(numeric_id="11", request_key="unique-req-003"),
                    authorization="Bearer " + token,
                )
        self.assertEqual(ctx.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
