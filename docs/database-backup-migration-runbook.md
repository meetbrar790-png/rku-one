# RKU ONE — database backup and migration runbook

**Status: instructions only. No backup has been created or verified.**

## Deadline
The current Render free PostgreSQL instance is scheduled to expire on **2026-12-01 at 15:43:31 UTC**. Complete a verified backup and a tested recovery or migration **well before** that date. Never assume free instance expiration is automatically reversible.

## Owner-controlled secure backup
1. Sign in to the official Render dashboard using your own account and open **rku-one-db**. Confirm the instance, expiration and any supported backup/export options in the dashboard.
2. If a built-in snapshot/export is available, use it and verify that a restorable copy exists. Do not assume a free plan includes backups.
3. Otherwise, on a trusted private computer with the PostgreSQL client installed, use the connection instructions displayed in Render to run **pg_dump**. Prefer Render's private/internal connection where supported, or a documented secure TLS connection; do not open database access to the entire internet.
4. Keep database credentials and connection URLs out of chat, GitHub, logs and screenshots. Use a local protected environment variable or secure credential prompt. Never commit a dump.
5. Use a custom-format dump, for example: `pg_dump --format=custom --no-owner --no-acl --file=rku-one-backup.dump` with connection details supplied securely through your local PostgreSQL environment. The command alone will not work until local authentication/connection is configured.
6. Encrypt the dump and store it in a private, access-controlled location separate from the Render service. Verify the file exists and is nonempty; record the date and a SHA-256 checksum privately.
7. Restore the dump to a **separate test database** using `pg_restore`. Check schema, row counts and critical application flows. Do not restore over production.
8. Arrange a supported replacement database and migration plan before expiration; take a final fresh backup before switching `DATABASE_URL`. Obtain owner approval before any paid plan, DNS change, credential rotation, or production cutover.

## Acceptance criteria
- [ ] Owner confirms an encrypted backup exists off Render
- [ ] Owner confirms a separate restore test succeeded
- [ ] User/account IDs and counts match in test restore
- [ ] App read/write tests pass against test restore
- [ ] Production migration/cutover separately approved and completed
- [ ] New database expiration/backup schedule verified

**Important:** GitHub automated unit tests do not validate production database backup or recovery. This runbook does not create any backup.
