"""Pure cloud sharing policy tests; never use production files."""
import unittest
from datetime import datetime, timedelta, timezone

from cloud_sharing_policy import validate_share_request, can_download_share


class CloudSharingPolicyTests(unittest.TestCase):
    def test_owner_can_request_share(self):
        self.assertEqual(validate_share_request(1, 2, 1)["recipient_id"], 2)

    def test_nonowner_cannot_share(self):
        with self.assertRaises(PermissionError):
            validate_share_request(2, 3, 1)

    def test_cannot_share_with_self(self):
        with self.assertRaises(ValueError):
            validate_share_request(1, 1, 1)

    def test_invalid_recipient_rejected(self):
        with self.assertRaises(ValueError):
            validate_share_request(1, 0, 1)

    def test_accepted_recipient_before_expiry_can_download(self):
        expires = datetime.now(timezone.utc) + timedelta(hours=1)
        self.assertTrue(can_download_share(2, 2, expires, accepted=True))

    def test_unaccepted_share_denied(self):
        expires = datetime.now(timezone.utc) + timedelta(hours=1)
        self.assertFalse(can_download_share(2, 2, expires))

    def test_wrong_recipient_denied(self):
        expires = datetime.now(timezone.utc) + timedelta(hours=1)
        self.assertFalse(can_download_share(3, 2, expires, accepted=True))

    def test_expired_share_denied(self):
        expires = datetime.now(timezone.utc) - timedelta(seconds=1)
        self.assertFalse(can_download_share(2, 2, expires, accepted=True))

    def test_revoked_share_denied(self):
        expires = datetime.now(timezone.utc) + timedelta(hours=1)
        self.assertFalse(can_download_share(2, 2, expires, revoked=True, accepted=True))

    def test_naive_expiration_denied(self):
        self.assertFalse(can_download_share(2, 2, datetime.now(), accepted=True))


if __name__ == "__main__":
    unittest.main()
