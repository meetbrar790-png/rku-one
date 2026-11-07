# RKU ONE registration + VIP integration contract (design only)

**Not deployed. No live schema migration, VIP sales, or changes to registration.py.**

## Current production gap
`registration.register_user` inserts into `users(email,password_hash)`
using a PostgreSQL identity sequence. It does **not** inspect a VIP
reservation ledger or acquire the prototype allocation advisory lock.
The prototype allocator creates only `rku_id` in disposable test tables;
it cannot be directly substituted into the real users table.

## Required atomic transaction
1. Validate email and password and prepare password hash.
2. Open a single database transaction; acquire the shared allocation lock.
3. For a free registration, obtain the next sequence value and check issued
   IDs and active VIP reservations while holding that lock. Skip reserved IDs;
   never recycle or renumber issued IDs.
4. Insert the **full user record** (email, password_hash, rku_id) in that same
   transaction. The users primary key and email unique constraint are final
   backstops; handle conflicts without exposing credentials.
5. Commit once. On failure, roll back user insertion and reservation changes;
   sequence gaps are acceptable and should not be reused.
6. For VIP checkout, lock identically, verify ID is unissued and not
   reserved by another buyer, record an expiring hold with a unique idempotency
   key, and only allocate after independently verified payment confirmation.
7. Expired holds are *candidates* for transactional release, not automatic
   proof that payment or allocation has not happened. Recheck under lock.

## Safety invariants
- Existing user IDs, including ID 1, never change.
- No two users can own one numeric ID.
- No issued ID can be offered for VIP purchase.
- A paid, allocated, or still-active VIP hold is not released.
- A free registration cannot consume an active VIP reservation.
- All allocation paths share the lock and enforce database uniqueness.
- No client-selected ID without server authorization and payment verification.
- A rollback never resets the global sequence.

## Pre-deployment acceptance tests (disposable PostgreSQL)
- Realistic full-user inserts with email/password_hash and returned ID.
- Free vs VIP concurrent races and duplicate email submissions.
- Reservation hold, expiry, cancellation, verified payment, retries.
- Crash/rollback, connection restart, idempotent payment webhook.
- Migration rehearsal from a sanitized restored backup.
- Confirm old login, mail, profile, contacts still work.

## Deployment gates
1. Verify a fresh **read-only live** issued-ID and sequence audit.
2. Review live Postgres expiry, encrypted backup, and tested restore.
3. Obtain explicit owner approval of VIP number inventory and migration.
4. Stage application + schema together; use disabled-by-default feature flag.
5. Approve production cutover separately; do not assume this document grants it.

The earlier isolated tests demonstrate only components of this contract.
They are not proof that the existing production registration path is safe for
VIP sales.
