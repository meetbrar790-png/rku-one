# RKU ONE VIP allocator — staged migration and rollback checklist

**Status: design/review only; NOT approved for execution.**
The existing live registration path still inserts into the identity sequence
without consulting VIP reservations. Do not activate VIP sales.

## Preconditions
1. Obtain owner approval for a maintenance window and backup/migration plan.
2. Check current Render PostgreSQL expiry (previously reported 2026-12-01).
3. Make a new encrypted backup and independently verify restore.
4. Run a read-only **live** audit of issued IDs and sequence state; the
   owner's November 8 restored snapshot showing ID 1 is not live inventory.
5. Decide which unissued IDs may become VIP. Existing IDs are immutable.
6. Document payment provider, reservation TTL, expiration, refund, audit and
   abuse policies. No payment integration is implemented.

## Stage 1 — disposable PostgreSQL only
- Rehearse migration on a *copy* in a dedicated test database.
- Add reservation table and durable allocation constraints.
- Ensure the future registration and VIP checkout code both acquire the same
  transaction-scoped lock and validate issued/reserved status atomically.
- Do not deploy the reservation schema alone and assume IDs are protected.
- Verify uniqueness under concurrency, transaction rollback, retry, expired
  holds, and a restart. Ensure registration is safe during rollout.
- Test ID 1 and every previously issued ID remain unchanged.

## Stage 2 — reviewed deployment (owner approval required)
- Stop new registration or use a verified coordinated cutover while migrating.
- Apply reviewed migration; deploy both paths together behind a disabled
  feature flag; verify existing accounts still authenticate.
- Check real sequence values without resetting them.
- Enable free allocation first only after safe staging and rollback review.
- Enable VIP reservations and later payment checkout only after separate
  owner approval and verified payment confirmation.

## Rollback
- Disable VIP checkout and registration changes first; prevent allocations
  while versions or schema are inconsistent.
- Roll back application code to last verified version only if compatible with
  the migrated schema. Never blindly drop reservation data or reset sequence.
- Reconcile all allocations and holds made since cutover; do not overwrite
  IDs, refund obligations, or paid entitlements.
- Restore backup only as an explicitly approved disaster-recovery operation,
  accounting for post-backup writes and potential data loss.
- Verify user 1, other existing IDs, login, mail, contacts, and profiles.
- Keep audit trail of incident and owner decision.

## Current limits
- Isolated PostgreSQL integration tests passed on GitHub; these do not
  establish that live registration and VIP checkout are safe.
- Prototype allocator is NOT wired into production.
- No real VIP number has been reserved or sold.
- No production DB change is authorized by this document.
