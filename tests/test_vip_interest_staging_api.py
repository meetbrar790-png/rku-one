import os
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from mail_auth import issue_token
from vip_interest_staging_api import app


class VipInterestStagingApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_login_required(self):
        response = self.client.post("/staging/vip/interest", json={"numeric_id": "2", "request_key": "unique-req-001"})
        self.assertEqual(response.status_code, 401)

    def test_authenticated_request_does_not_reserve(self):
        with patch.dict(os.environ, {"RKU_SESSION_SECRET": "disposable-test-secret"}):
            token = issue_token(1001)
            response = self.client.post(
                "/staging/vip/interest",
                json={"numeric_id": "1000", "request_key": "unique-req-002"},
                headers={"Authorization": "Bearer " + token},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "received_not_reserved")
        self.assertFalse(response.json()["number_held"])
        self.assertFalse(response.json()["payment_collected"])

    def test_reserved_rejected(self):
        with patch.dict(os.environ, {"RKU_SESSION_SECRET": "disposable-test-secret"}):
            token = issue_token(1001)
            response = self.client.post(
                "/staging/vip/interest",
                json={"numeric_id": "11", "request_key": "unique-req-003"},
                headers={"Authorization": "Bearer " + token},
            )
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
