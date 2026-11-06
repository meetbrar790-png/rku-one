"""RKU Cloud policy tests: no storage or production account access."""
import unittest
from cloud_policy import validate_upload, private_object_key, require_owner, MAX_UPLOAD_BYTES


class CloudPolicyTests(unittest.TestCase):
    def test_valid_image_upload_metadata(self):
        result = validate_upload(1, "photo.jpg", 1024, "image/jpeg")
        self.assertEqual(result["owner_id"], 1)

    def test_rejects_path_traversal_filename(self):
        with self.assertRaises(ValueError):
            validate_upload(1, "../private.txt", 1024, "text/plain")

    def test_rejects_windows_path_filename(self):
        with self.assertRaises(ValueError):
            validate_upload(1, "folder\\secret.txt", 1024, "text/plain")

    def test_rejects_oversized_upload(self):
        with self.assertRaises(ValueError):
            validate_upload(1, "photo.png", MAX_UPLOAD_BYTES + 1, "image/png")

    def test_rejects_unsupported_mime(self):
        with self.assertRaises(ValueError):
            validate_upload(1, "program.exe", 100, "application/x-msdownload")

    def test_rejects_invalid_owner(self):
        with self.assertRaises(ValueError):
            validate_upload(0, "photo.png", 100, "image/png")

    def test_random_object_keys_do_not_expose_filename(self):
        first = private_object_key(1)
        second = private_object_key(1)
        self.assertTrue(first.startswith("owners/1/"))
        self.assertNotEqual(first, second)

    def test_owner_can_access_own_file(self):
        self.assertTrue(require_owner(1, 1))

    def test_different_owner_is_denied(self):
        with self.assertRaises(PermissionError):
            require_owner(2, 1)

    def test_invalid_owner_is_denied(self):
        with self.assertRaises(PermissionError):
            require_owner(0, 1)


if __name__ == "__main__":
    unittest.main()
