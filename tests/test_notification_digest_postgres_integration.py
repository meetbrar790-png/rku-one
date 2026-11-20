"""Real disposable PostgreSQL tests for notification digest aggregation.

Requires RKU_VIP_TEST_DATABASE_URL and staging_db_preflight validation.
Creates and drops an isolated random schema; never touches production tables.
"""
import os
import threading
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from notification_digest_db_staging import count_unknown_request, claim_digest_once
from staging_db_preflight import assert_disposable_staging_url


@unittest.skipUnless(os.environ.get('RKU_VIP_TEST_DATABASE_URL'), 'Disposable PostgreSQL URL required')
class NotificationDigestPostgresIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.url = os.environ['RKU_VIP_TEST_DATABASE_URL']
        assert_disposable_staging_url(cls.url)
        cls.schema = 'digest_ci_' + uuid.uuid4().hex
        with psycopg.connect(cls.url, autocommit=True) as conn:
            conn.execute(f'CREATE SCHEMA "{cls.schema}"')
            conn.execute(f'SET search_path TO "{cls.schema}"')
            conn.execute(Path('sql/staging_notification_digest.sql').read_text())

    @classmethod
    def tearDownClass(cls):
        with psycopg.connect(cls.url, autocommit=True) as conn:
            conn.execute(f'DROP SCHEMA IF EXISTS "{cls.schema}" CASCADE')

    @classmethod
    def connection(cls):
        conn = psycopg.connect(cls.url)
        conn.execute(f'SET search_path TO "{cls.schema}"')
        return conn

    def test_concurrent_requests_count_exactly(self):
        now = datetime(2026, 11, 20, 12, tzinfo=timezone.utc)
        def increment(_):
            with self.connection() as conn:
                return count_unknown_request(conn, 25, now)
        with ThreadPoolExecutor(max_workers=8) as pool:
            counts = list(pool.map(increment, range(80)))
        self.assertEqual(sorted(counts), list(range(1, 81)))

    def test_only_one_worker_claims_digest(self):
        now = datetime(2026, 11, 20, 12, tzinfo=timezone.utc)
        with self.connection() as conn:
            count_unknown_request(conn, 26, now)
        def claim(_):
            with self.connection() as conn:
                return claim_digest_once(conn, 26, now)
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(claim, range(24)))
        self.assertEqual(results.count(True), 1)
        self.assertEqual(results.count(False), 23)


if __name__ == '__main__':
    unittest.main()
