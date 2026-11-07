# RKU ONE VIP registration — production readiness review (2026-11-08)

**Decision: NO-GO for live VIP reservations or sales.** This review records
test evidence; it does not authorize a deployment, migration or purchase.

## Verified in GitHub Actions
- Backend test workflow passed on the latest reviewed commit.
- Disposable PostgreSQL workflow passed on the preceding commit, including
  staged API handler registration and concurrent VIP-aware signups.
- Tests exercise synthetic issued ID 1, reserved VIP ID 2 and allocations
  of IDs 3 and 4, including duplicate email rejection.
- URL and actual PostgreSQL connection identity checks run before DB tests.
- These tests are not a proof of production deployment readiness.

## Implementation boundary
- The production `registration.register_user` still inserts directly into
  `users` with the identity sequence. It does **not** call the VIP-aware
  allocator or check a reservation ledger.
- `staging_vip_api_adapter.py` is staging-only and is injected into the
  API handler by test mocking; the production API is unchanged.
- The test-only allocator and reservation service require disposable
  `*_vip_test` databases and random object names.
- No real payment provider, webhook verification, refund or chargeback
  reconciliation is integrated.

## Required before production
1. Owner-approved and reviewed migration with immutable issued-ID audit,
   verified backup, rollback and dry-run on separate staging infrastructure.
2. Dedicated staging API service and database, isolated credentials and
   environment, and real HTTP endpoint integration tests (current tests
   invoke the FastAPI handler function directly).
3. Production-grade transactional VIP reservation and normal registration
   under a shared lock, with account creation and payment state invariants.
4. Verified payment provider integration, server-side webhook signature
   checks, idempotency, dispute handling and an explicit commercial policy.
5. Security review: auth, session revocation, account recovery, rate limits,
   abuse prevention, logging, privacy and operational alerting.
6. Regression tests for login, mail, profile, contacts, concurrency and
   migrations; disaster recovery drill; deployment/rollback runbook.
7. Explicit owner approval before production schema or code changes.

## Current recommendation
Continue staging and security work only. Do not advertise VIP ID 2 as
available, sell IDs or modify live ID allocation until the gates above pass.
