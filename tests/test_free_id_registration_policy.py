import unittest
from free_id_registration_policy import (
    assert_free_registration_candidate, is_free_registration_id,
    free_registration_policy_summary,
)

class FreeIdRegistrationPolicyTests(unittest.TestCase):
    def test_all_premium_and_reserved_ids_are_excluded(self):
        for rku_id in range(1, 1001):
            with self.subTest(rku_id=rku_id):
                self.assertFalse(is_free_registration_id(rku_id))
                with self.assertRaises(ValueError):
                    assert_free_registration_candidate(rku_id, issued_ids=set(), reserved_ids=set())

    def test_free_id_boundary_and_large_numbers(self):
        for rku_id in (1001, 1002, 2000, 9999999999):
            with self.subTest(rku_id=rku_id):
                self.assertTrue(is_free_registration_id(rku_id))
                self.assertEqual(
                    assert_free_registration_candidate(rku_id, issued_ids=set(), reserved_ids=set()),
                    rku_id,
                )

    def test_never_reissue_issued_or_reserved_free_ids(self):
        with self.assertRaises(ValueError):
            assert_free_registration_candidate(1001, issued_ids={1001}, reserved_ids=set())
        with self.assertRaises(ValueError):
            assert_free_registration_candidate(1000, issued_ids=set(), reserved_ids={1001})

    def test_invalid_values_rejected(self):
        for value in (0, -1, True, 1.5, "1000", None):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    is_free_registration_id(value)

    def test_not_claimed_as_live(self):
        summary = free_registration_policy_summary()
        self.assertEqual(summary["free_id_start"], 1001)
        self.assertFalse(summary["live_registration_integrated"])
        self.assertTrue(summary["transactional_inventory_required"])

if __name__ == "__main__":
    unittest.main()
