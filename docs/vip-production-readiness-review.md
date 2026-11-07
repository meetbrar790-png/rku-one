# VIP production-readiness review — 2026-11-08

**Decision: NOT READY for live VIP sales or registration cutover.**
This is a source-code review, not a live security audit. No production
database or Render configuration was changed.

## Confirmed from current source
- `registration.py`: free signup inserts into `users` using its identity
  sequence, without the VIP reservation ledger or shared advisory lock.
- `api.py`: `/register` calls that existing signup function.
- `vip_allocator_prototype.py`: explicitly refuses non-`*_vip_test`
  databases and requires matching disposable test object names. It inserts
  only an ID into a test users table, not a complete real account.
- The GitHub VIP workflow runs isolated PostgreSQL 18 tests for reservation
  conflicts, registration concurrency, expiry, simulated payment allocation,
  duplicate notifications and buyer races.
- Payment test flags are simulated; no actual provider signature, API
  verification, settlement, refunds or webhook endpoint is present.

## Blocking work before any live rollout
1. **Real allocation integration:** implement an atomic full-user registration
   path sharing the same transaction lock and reservation checks as VIP
   checkout. Keep existing IDs immutable and enforce DB constraints.
2. **Schema migration:** design and rehearse reservation/payment ledgers,
   state transitions, unique idempotency keys and foreign-key relationships
   on a separate restored test database. Never migrate live automatically.
3. **Provider trust:** select a payment processor, verify signatures and
   transaction status server-side, bind amount/currency/ID/buyer, handle
   duplicate/out-of-order webhooks, refunds and disputes.
4. **Expiry race:** expiration must never override a verified payment or
   allocated number; lock/recheck and audit every state change.
5. **Ownership:** require authenticated, authorized buyer and prevent ID
   reassignment, takeover or free registration into held inventory.
6. **Operations:** fresh encrypted backup, tested restore, read-only issued-ID
   and sequence audit, alerting, support/reconciliation, disaster recovery.
7. **Deployment:** owner-approved VIP inventory, explicit migration approval,
   disabled-by-default flags, rehearsed rollback and coordinated cutover.
8. **Infrastructure:** verify Render free Postgres expiry before launch;
   previously observed expiry was 2026-12-01, subject to recheck.

## Testing limitations
- Passing disposable DB tests do not prove production code is integrated.
- Simulated `payment_verified=True` is not proof of a real payment.
- A test showing one winning buyer does not cover a malicious provider
  payload, stale hold, delayed settlement, chargeback or service crash.
- Real signup and existing account/mail/profile/contact regression tests
  must pass against a staged schema before deployment.

## Next safe milestone
Build a complete **test-only registration-and-reservation service** using
the disposable database, with real user fields and transactional constraints,
then add concurrent registration/reservation and crash-retry tests. Request
separate owner approval before changing production registration or schema.
