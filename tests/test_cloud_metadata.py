"""Cloud metadata tests; no production database or object storage."""
import unittest
from uuid import uuid4
from cloud_metadata import CLOUD_FILES_SCHEMA, metadata_for_owner


class CloudMetadataTests(unittest.TestCase):
    def test_lookup_scoped_to_authenticated_owner(self):
        file_id = uuid4()
        query, params = metadata_for_owner(1, file_id)
        self.assertIn("owner_id = %s", query)
        self.assertIn("status = 'ready'", query)
        self.assertEqual(params, (1, file_id))

    def test_reject_invalid_owner(self):
        with self.assertRaises(ValueError):
            metadata_for_owner(0, uuid4())

    def test_reject_invalid_file_id(self):
        with self.assertRaises(ValueError):
            metadata_for_owner(1, "../file")

    def test_schema_enforces_owner_and_private_object_key(self):
        self.assertIn("REFERENCES users(rku_id)", CLOUD_FILES_SCHEMA)
        self.assertIn("object_key TEXT NOT NULL UNIQUE", CLOUD_FILES_SCHEMA)

    def test_schema_limits_size_and_states(self):
        self.assertIn("size_bytes <= 26214400", CLOUD_FILES_SCHEMA)
        self.assertIn("'pending', 'ready', 'deleted'", CLOUD_FILES_SCHEMA)


if __name__ == "__main__":
    unittest.main()
