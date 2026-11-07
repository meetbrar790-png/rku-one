"""Staging preflight must reject live and remote database URLs."""
import unittest
from staging_db_preflight import assert_disposable_staging_url


class StagingDatabasePreflightTests(unittest.TestCase):
    def test_allows_disposable_loopback(self):
        for url in (
            "postgresql://test:secret@127.0.0.1:5432/rku_one_vip_test",
            "postgres://test:secret@localhost/rku_one_vip_test",
            "postgresql://test:secret@[::1]:5432/rku_one_vip_test",
        ):
            with self.subTest(url=url):
                self.assertIsNone(assert_disposable_staging_url(url))

    def test_rejects_production_and_remote_urls(self):
        urls = (
            "postgresql://test:secret@127.0.0.1/rku_one",
            "postgresql://test:secret@rku-one-db.internal/rku_one_vip_test",
            "postgresql://test:secret@8.8.8.8/rku_one_vip_test",
            "postgresql://test:secret@127.0.0.1/rku_one_vip_test?host=remote",
            "postgresql://test:secret@127.0.0.1/rku_one_vip_test?options=-csearch_path%3Dpublic",
            "postgresql://test@127.0.0.1/rku_one_vip_test",
            "postgresql://test:secret@127.0.0.1/",
            "postgresql://test:secret@127.0.0.1/rku_one_vip_test#ignored",
            "https://test:secret@127.0.0.1/rku_one_vip_test",
            "",
        )
        for url in urls:
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    assert_disposable_staging_url(url)


if __name__ == "__main__":
    unittest.main()
