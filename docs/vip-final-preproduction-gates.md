# RKU ONE VIP integration — final pre-production gate review

**Status: HOLD. Production VIP activation is NOT approved.**
Review date: 2026-11-08. Based on current source and successful isolated CI
tests, not a production database audit or security certification.

## Evidence completed
- Disposable PostgreSQL tests cover reserved-ID skipping, full user inserts,
  concurrent registrations, duplicate email, rollback/sequence gaps, expiry,
  payment-state simulations, duplicate notifications, and two-buyer races.
- Test-only full registration service refuses non-`*_vip_test` databases.
- Existing `registration.py` and `api.py` remain unchanged; no VIP
  reservation checkout is enabled.

## Remaining blockers (must close before launch)
1. **Production registration integration**: actual `register_user` still
   relies on PostgreSQL identity without checking VIP holds. Need a reviewed
   transaction-safe full-user allocation implementation and migration.
2. **Durable reservation schema and invariant enforcement**: ensure no issued
   ID can be reserved; ensure free signups cannot take a held ID; review
   transactional constraints and consistent lock ordering across all paths.
3. **Real payments**: select provider; validate signed webhook/API response,
   amount, currency, transaction ID, buyer and reserved ID; implement
   idempotency, expiry, refunds, chargebacks and reconciliation.
4. **Authentication/authorization**: VIP reservation and purchase must
   require authenticated account ownership; avoid trusting buyer IDs or
   payment status supplied by the browser.
5. **End-to-end staging**: run the real API with a disposable migrated DB,
   including existing login/mail/contacts/profile regression checks and
   concurrent cross-path requests. Current tests use simulated flows.
6. **Backup/recovery**: obtain fresh encrypted backup, verify restore and
   sequence, audit issued IDs from live DB read-only, rehearse rollback
   without resetting sequences or overwriting post-backup users.
7. **Operations**: monitor Render PostgreSQL expiration (previously
   reported 2026-12-01, must recheck), deployment availability, alerts,
   privacy/security logging and customer support.
8. **Owner decisions**: approve VIP inventory, payment provider, pricing,
   migration window and production cutover separately.

## Go/no-go criteria
**GO** only after all blockers are resolved, staging passes, backup and
rollback are verified, and the owner explicitly approves production changes.
Until then, **NO GO**: keep VIP sales and schema migration disabled.

## Next implementation milestone
Build a **test-only reservation service** that shares the allocator's
transaction lock and supports reserving an unissued ID, rejecting duplicate
buyers and committing a reservation. Integrate it with the existing
disposable full registration service, then test their race end-to-end.
Do not deploy to Render or change live `users` tables.
