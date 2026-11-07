# RKU ONE — VIP reservation migration design (NOT EXECUTED)

Status: proposal only. Do not execute on production or local restored backup.

## Verified offline snapshot
The owner restored an encrypted PostgreSQL backup on a separate Termux test database.
It showed one user with ID 1, a profile, and sequence last_value=1/is_called=true.
This is a historical snapshot, **not** an audit of current live Render data.

## Requirements before enabling sales
1. Read-only live inventory: issued IDs, identity sequence, existing constraints.
2. Owner approves an explicit VIP candidate range and free-number allocation policy.
3. Preserve all issued IDs, including ID 1. Never reset sequence or renumber.
4. Enforce reservation and free allocation in the *same* database transaction.
5. Record reservation owner, expiry, payment confirmation, and immutable audit events.
6. Never treat an offline candidate as available or sellable.
7. Use a payment provider's verified webhook, not client claims, before activation.
8. Test concurrency, retries, expiry, rollback, duplicate requests and ownership.
9. Backup and rehearse restore before any migration. Free Render PostgreSQL expiry
   is currently scheduled for 2026-12-01; recheck the dashboard.

## Proposed schema (review only, do not apply)
```sql
CREATE TABLE vip_number_reservations (
  rku_id BIGINT PRIMARY KEY CHECK (rku_id > 0),
  state TEXT NOT NULL CHECK (state IN ('reserved', 'allocated', 'cancelled')),
  reservation_key UUID NOT NULL UNIQUE,
  reserved_for BIGINT REFERENCES users(rku_id),
  reserved_until TIMESTAMPTZ,
  payment_reference TEXT UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

This table alone does NOT protect VIP numbers. Current registration inserts
straight into the users identity sequence. Deploying this schema without
changing registration atomically could allocate a purported VIP number to a
free registrant. Do not enable reservations until the allocator and DB
constraints are implemented and concurrency-tested together.

## Proposed safe rollout
- Stage 1: approve policy, read-only live audit, review proposed schema.
- Stage 2: implement transactional allocator behind disabled feature flag,
  with database-level safeguards and isolated PostgreSQL integration tests.
- Stage 3: rehearse on a copy of the backup; verify existing ID 1 unchanged.
- Stage 4: only after owner approval, production migration with rollback plan.
- Stage 5: payment integration, fraud controls and owner-approved launch.

No VIP IDs reserved or sold; no database changes made by this document.
