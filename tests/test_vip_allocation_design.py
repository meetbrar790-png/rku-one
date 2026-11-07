"""Offline checks for proposed VIP SQL; no live database changes."""
import unittest

from vip_allocation_design import (
    ALLOCATION_LOCK_SQL,
    VIP_RESERVATION_SCHEMA_SQL,
    proposed_reservation_insert_sql,
)


class VipAllocationDesignTests(unittest.TestCase):
    def test_lock_is_transaction_scoped(self):
        self.assertIn("pg_advisory_xact_lock", ALLOCATION_LOCK_SQL)

    def test_reservation_id_is_unique(self):
        self.assertIn("rku_id BIGINT PRIMARY KEY", VIP_RESERVATION_SCHEMA_SQL)

    def test_reservation_key_is_unique(self):
        self.assertIn("reservation_key UUID NOT NULL UNIQUE", VIP_RESERVATION_SCHEMA_SQL)

    def test_payment_reference_unique(self):
        self.assertIn("payment_reference TEXT UNIQUE", VIP_RESERVATION_SCHEMA_SQL)

    def test_proposed_insert_never_overwrites_existing(self):
        query = proposed_reservation_insert_sql().as_string()
        self.assertIn("ON CONFLICT (rku_id) DO NOTHING", query)
        self.assertNotIn("DO UPDATE", query)


if __name__ == "__main__":
    unittest.main()
