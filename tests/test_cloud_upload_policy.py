"""Cloud upload integrity checks without any storage access."""
import unittest
from cloud_upload_policy import prepare_upload_intent, can_finalize_upload


class CloudUploadPolicyTests(unittest.TestCase):
    def test_prepare_upload_has_pending_state(self):
        result = prepare_upload_intent(1, "photo.jpg", 1024, "image/jpeg")
        self.assertEqual(result["status"], "pending")
        self.assertEqual(result["owner_id"], 1)
        self.assertTrue(result["object_key"].startswith("owners/1/"))

    def test_prepare_upload_rejects_bad_filename(self):
        with self.assertRaises(ValueError):
            prepare_upload_intent(1, "../secret.jpg", 100, "image/jpeg")

    def test_matching_owner_size_and_hash_can_finalize(self):
        checksum = "a" * 64
        self.assertTrue(can_finalize_upload(1, 1, 100, 100, checksum, checksum))

    def test_other_owner_cannot_finalize(self):
        checksum = "a" * 64
        self.assertFalse(can_finalize_upload(2, 1, 100, 100, checksum, checksum))

    def test_wrong_size_cannot_finalize(self):
        checksum = "a" * 64
        self.assertFalse(can_finalize_upload(1, 1, 100, 101, checksum, checksum))

    def test_wrong_checksum_cannot_finalize(self):
        self.assertFalse(can_finalize_upload(1, 1, 100, 100, "a" * 64, "b" * 64))

    def test_invalid_checksum_cannot_finalize(self):
        self.assertFalse(can_finalize_upload(1, 1, 100, 100, "x" * 64, "x" * 64))


if __name__ == "__main__":
    unittest.main()
