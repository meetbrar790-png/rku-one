import unittest
from attachment_storage_config import PrivateObjectStorageConfig, required_storage_environment

class StorageConfigurationTests(unittest.TestCase):
    def config(self, **changes):
        data = dict(endpoint_url="https://storage.example.com", bucket_name="rku-private-attachments", region="auto", access_key_id="test-key", secret_access_key="test-secret", server_side_encryption=True)
        data.update(changes)
        return PrivateObjectStorageConfig(**data)

    def test_valid_private_config(self):
        self.config().validate()
        self.assertEqual(len(required_storage_environment()), 5)

    def test_reject_http_and_url_credentials(self):
        for endpoint in ("http://storage.example.com", "https://name:pass@storage.example.com", "https://storage.example.com/?token=secret", "https://storage.example.com/path"):
            with self.assertRaises(ValueError):
                self.config(endpoint_url=endpoint).validate()

    def test_reject_missing_credentials_and_disabled_encryption(self):
        for kwargs in (dict(access_key_id=""), dict(secret_access_key=""), dict(server_side_encryption=False), dict(bucket_name="INVALID_BUCKET")):
            with self.assertRaises(ValueError):
                self.config(**kwargs).validate()

if __name__ == "__main__":
    unittest.main()
