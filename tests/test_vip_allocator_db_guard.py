"""Safety guard tests: prototype must refuse any non-test database."""
import unittest
from unittest.mock import MagicMock

from vip_allocator_prototype import allocate_free_id


class VipAllocatorDatabaseGuardTests(unittest.TestCase):
    def test_rejects_production_database_before_query(self):
        conn = MagicMock()
        conn.info.dbname = "rku_one_db"
        with self.assertRaisesRegex(ValueError, "disposable"):
            allocate_free_id(conn, "rku_users_" + "a" * 32, "rku_reserved_" + "a" * 32, "rku_seq_" + "a" * 32)
        conn.execute.assert_not_called()

    def test_rejects_missing_database_name_before_query(self):
        conn = MagicMock()
        conn.info.dbname = None
        with self.assertRaises(ValueError):
            allocate_free_id(conn, "rku_users_" + "a" * 32, "rku_reserved_" + "a" * 32, "rku_seq_" + "a" * 32)
        conn.execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()
