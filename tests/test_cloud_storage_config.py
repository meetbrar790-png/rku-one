"""Storage configuration validation tests; no external service used."""
import unittest
from cloud_storage_config import validate_storage_configuration


def sample():
    return {
        "RKU_STORAGE_ENDPOINT": "https://storage.example.com",
        "RKU_STORAGE_BUCKET": "rku-private-files",
        "RKU_STORAGE_ACCESS_KEY": "test-access-key",
        "RKU_STORAGE_SECRET_KEY": "test-only-secret-key",
    }


class CloudStorageConfigTests(unittest.TestCase):
    def test_valid_configuration_returns_no_secrets(self):
        result = validate_storage_configuration(sample())
        self.assertTrue(result["configured"])
        self.assertNotIn("RKU_STORAGE_SECRET_KEY", result)
        self.assertNotIn("RKU_STORAGE_ACCESS_KEY", result)

    def test_missing_credentials_rejected(self):
        config = sample()
        del config["RKU_STORAGE_SECRET_KEY"]
        with self.assertRaises(ValueError):
            validate_storage_configuration(config)

    def test_http_endpoint_rejected(self):
        config = sample()
        config["RKU_STORAGE_ENDPOINT"] = "http://storage.example.com"
        with self.assertRaises(ValueError):
            validate_storage_configuration(config)

    def test_embedded_password_rejected(self):
        config = sample()
        config["RKU_STORAGE_ENDPOINT"] = "https://user:pass@storage.example.com"
        with self.assertRaises(ValueError):
            validate_storage_configuration(config)

    def test_invalid_bucket_rejected(self):
        config = sample()
        config["RKU_STORAGE_BUCKET"] = "../other"
        with self.assertRaises(ValueError):
            validate_storage_configuration(config)

    def test_endpoint_query_rejected(self):
        config = sample()
        config["RKU_STORAGE_ENDPOINT"] = "https://storage.example.com?token=secret"
        with self.assertRaises(ValueError):
            validate_storage_configuration(config)


if __name__ == "__main__":
    unittest.main()
