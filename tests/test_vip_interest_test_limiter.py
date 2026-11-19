import unittest
from vip_interest_test_limiter import TestOnlyInterestLimiter


class TestOnlyInterestLimiterTests(unittest.TestCase):
    def setUp(self):
        self.now = 0
        self.limiter = TestOnlyInterestLimiter(max_requests=2, window_seconds=60, clock=lambda: self.now)

    def test_limit_and_window_reset(self):
        self.assertTrue(self.limiter.allow(1001))
        self.assertTrue(self.limiter.allow(1001))
        self.assertFalse(self.limiter.allow(1001))
        self.now = 60
        self.assertTrue(self.limiter.allow(1001))

    def test_users_have_separate_buckets(self):
        self.limiter.allow(1001)
        self.limiter.allow(1001)
        self.assertTrue(self.limiter.allow(1002))
        self.assertFalse(self.limiter.allow(1001))

    def test_invalid_identity_rejected(self):
        for requester in (0, -1, True, "1001"):
            with self.subTest(requester=requester), self.assertRaises(ValueError):
                self.limiter.allow(requester)


if __name__ == "__main__":
    unittest.main()
