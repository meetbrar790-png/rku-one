# RKU ONE — Account Recovery implementation plan

Status: **Design only — NOT enabled for users**.

## Security requirements
- Ownership proof: send a single-use password reset link to the account's previously verified email address. Never reset a password based only on a public RKU ID, name, or digital card.
- Prerequisite: configure a transactional email provider, a verified sending domain, and an application base URL. Do not embed provider credentials in GitHub or browser code.
- Add email verification before making email-based recovery available. Existing accounts need a verified-email migration flow.
- Reset tokens: generate at least 32 cryptographically random bytes, encode as URL-safe tokens, store only a SHA-256 digest server-side, expire after 15 minutes, and consume atomically on use.
- Reset requests must always show the same response whether an email exists or not. Rate-limit by account and network source without exposing account existence.
- On successful reset: enforce password policy, rotate authentication/session signing design to support revocation, revoke all active sessions, and send a security notification to the verified email.
- Never log reset tokens, passwords, or complete reset links. Avoid including tokens in analytics or referrers. Set no-store on reset pages.
- Test replay, expiration, concurrency, token leakage, account enumeration, and malicious reset links before enabling.

## Deployment prerequisites
1. Verify transactional email provider and domain (deferred until the user approves domain work).
2. Implement verified-email status and confirmation flow.
3. Add token table and endpoints with automated tests.
4. Implement session revocation and notification email.
5. Run integration and security tests in a non-production environment.
6. Enable recovery only after successful end-to-end delivery testing.

## Important
Do not present account recovery as working before these requirements are met. Current free Render Postgres expires on 2026-12-01 according to the account's Render metadata; protect user data and arrange a durable database and verified backups before public launch.
