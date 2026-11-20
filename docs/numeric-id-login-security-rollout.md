# RKU ONE numeric-ID login: security rollout gate

Status: DESIGN ONLY. No production login endpoint or database migration is authorized by this document.

## Current verified code behavior
- `registration.verify_login` handles existing email/password login and stores per-email failures in PostgreSQL.
- `numeric_id_login_prototype.verify_numeric_id_password` only checks a stored hash and does **not** enforce lockout, IP throttling, or generic response timing.
- The prototype must **not** be connected to a public FastAPI route until the gates below are met.

## Required controls before enabling a public numeric-ID login
1. Reuse a PostgreSQL-backed, transactional per-ID failed-login counter with a 15-minute rolling window and a temporary lockout after five failures; use advisory transaction locks per numeric ID to avoid multi-worker races. Do not modify existing email login behavior.
2. Apply separate IP-based rate limits **before** expensive password hashing. Use trusted proxy configuration; never trust arbitrary user-provided forwarded headers. Consider shared NAT/mobile networks to avoid overly aggressive blocking.
3. Use one generic authentication error for unknown ID, wrong password, or blocked ID; avoid account enumeration and assess timing differences.
4. Use existing session token issuance only after successful verification; verify expiry, revocation strategy, secret handling, and secure storage on mobile.
5. Keep all SQL parameterized. Preserve existing user IDs, reserved VIP IDs, and free-ID allocation. Never reset identity sequences.
6. Add tests for valid login, bad password, nonexistent ID, lockout threshold, lockout expiry, concurrent attempts, IP limit, and generic errors.
7. Run CI with disposable PostgreSQL. Review migration and rollback on staging with backup/restore validation; do not test by modifying production data.
8. Obtain explicit approval before merging to main or enabling a public endpoint; verify Render deploy health after approval.

## Additional security review
- Do not treat login lockout as full account protection: MFA/OTP, recovery abuse controls, audit logs without secrets, alerting, dependency scanning, and incident response are separate launch requirements.
- No OTP provider, phone-number verification, or live numeric-ID registration is implemented by this document.
