# RKU ONE isolated API staging plan

**Status:** design and safety gates only. No staging deployment or production change authorized.

## Goal
Exercise the actual FastAPI `/register` endpoint, login and dependent account
features against a *separate* PostgreSQL database with disposable test
accounts, while rehearsing VIP reservation/registration invariants.

## Current gap
- `api.py` calls `registration.register_user`.
- That production function inserts into `users` via its identity sequence.
- The guarded VIP test services are not called by the real API.
- Therefore a passing isolated allocator test does not establish that live
  registration respects VIP reservations.

## Required isolated staging environment
1. Provision a dedicated staging PostgreSQL database and separate backend
   service; never point staging to Render production `DATABASE_URL`.
2. Give staging unique credentials, signing keys, origins, domains and logs.
   Do not copy live passwords or real personal data.
3. Explicitly disable outgoing emails, payment collection, cloud uploads,
   public indexing and live webhooks.
4. Run a preflight check that refuses production DB name, host and service
   identifiers before any schema setup or test inserts.
5. Create a synthetic issued ID 1 and VIP reservation for ID 2, then
   verify registration allocates ID 3 using the **actual staged API**.
6. Exercise duplicate email, simultaneous signup/hold, retries, login,
   profile, contacts and internal mail. Assert no duplicate ID, orphaned
   reservation or partial account.
7. Inject failures before commit and after commit; check idempotency and
   that a sequence gap never causes an issued ID to be reused.
8. Collect sanitized CI logs and a pass/fail report; delete disposable
   test data and credentials after rehearsal.

## Hard stop
Do not switch live registration to VIP-aware allocation, migrate the live
schema, deploy staging services, connect a payment gateway, or change paid
Render plans without a separate reviewed implementation and owner approval.

## Acceptance criteria
- A fully separate database is verified before any writes.
- Real staged API endpoints, not only service-level mocks, pass.
- All registration/VIP reservation invariants hold under concurrency.
- Existing login, mail, profile and contacts still pass.
- Backup and rollback are rehearsed with no ID reassignment.
- Live deployment remains blocked pending explicit approval.
