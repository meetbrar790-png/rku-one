"""Download policy tests, isolated from real files and accounts."""
import unittest
from datetime import datetime, timedelta, timezone
from cloud_download_policy import authorize_personal_download, authorize_shared_download


class CloudDownloadPolicyTests(unittest.TestCase):
    def test_owner_can_download_ready_file(self):
        self.assertTrue(authorize_personal_download(1, 1, "ready"))

    def test_other_user_cannot_download_private_file(self):
        self.assertFalse(authorize_personal_download(2, 1, "ready"))

    def test_pending_file_cannot_be_downloaded(self):
        self.assertFalse(authorize_personal_download(1, 1, "pending"))

    def test_deleted_file_cannot_be_downloaded(self):
        self.assertFalse(authorize_personal_download(1, 1, "deleted"))

    def test_accepted_unexpired_share_can_download(self):
        expiry = datetime.now(timezone.utc) + timedelta(minutes=10)
        self.assertTrue(authorize_shared_download(2, 2, "ready", True, False, expiry))

    def test_wrong_recipient_denied(self):
        expiry = datetime.now(timezone.utc) + timedelta(minutes=10)
        self.assertFalse(authorize_shared_download(3, 2, "ready", True, False, expiry))

    def test_revoked_share_denied(self):
        expiry = datetime.now(timezone.utc) + timedelta(minutes=10)
        self.assertFalse(authorize_shared_download(2, 2, "ready", True, True, expiry))

    def test_expired_share_denied(self):
        expiry = datetime.now(timezone.utc) - timedelta(seconds=1)
        self.assertFalse(authorize_shared_download(2, 2, "ready", True, False, expiry))

    def test_unaccepted_share_denied(self):
        expiry = datetime.now(timezone.utc) + timedelta(minutes=10)
        self.assertFalse(authorize_shared_download(2, 2, "ready", False, False, expiry))


if __name__ == "__main__":
    unittest.main()
