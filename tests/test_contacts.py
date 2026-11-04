"""Tests for private contacts input validation."""
import unittest
from unittest.mock import patch
from contacts import save_contact


class ContactsTests(unittest.TestCase):
    def test_cannot_add_self(self):
        with patch("contacts.get_connection") as db:
            with self.assertRaises(ValueError):
                save_contact(1, 1, "Me")
            db.assert_not_called()

    def test_invalid_contact_id(self):
        with patch("contacts.get_connection") as db:
            with self.assertRaises(ValueError):
                save_contact(1, 0, "Bad")
            db.assert_not_called()

    def test_out_of_range_bigint_id(self):
        with patch("contacts.get_connection") as db:
            with self.assertRaises(ValueError):
                save_contact(1, 9223372036854775808, "Bad ID")
            db.assert_not_called()

    def test_contact_id_cannot_be_boolean(self):
        with patch("contacts.get_connection") as db:
            with self.assertRaises(ValueError):
                save_contact(1, True, "Bad ID")
            db.assert_not_called()

    def test_long_nickname(self):
        with patch("contacts.get_connection") as db:
            with self.assertRaises(ValueError):
                save_contact(1, 2, "a" * 81)
            db.assert_not_called()


if __name__ == "__main__":
    unittest.main()
