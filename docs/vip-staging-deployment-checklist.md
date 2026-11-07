# RKU ONE — isolated VIP staging deployment checklist

**Status: planning only. No staging infrastructure has been created and no production
database, Render environment variable, service, or DNS setting was changed.**

## Isolation and approval
- Obtain owner approval for a **separate** Render staging service and separate
  disposable PostgreSQL instance; confirm the cost before provisioning.
- Do not copy production `DATABASE_URL`, tokens, passwords or user records.
- Use staging-only credentials, a dedicated DB role, and nonproduction
  test accounts. No production personal data.
- The existing local CI PostgreSQL database ending `_vip_test` is **not**
  a substitute for a durable staging environment. The test-only services
  explicitly reject non-disposable DB names and should not be repurposed
  as production handlers.
- Protect staging with access control and nonindexing; never publish
  staging registration or VIP checkout as a customer-facing feature.

## Implementation and validation
1. Create a separate staging branch/release with reviewed VIP-aware
   registration integration and a staged reservation schema migration.
2. Prove existing issued IDs stay unchanged, ID 1 is never reassigned,
   and reserved VIP numbers are never allocated to free registrations.
3. Validate concurrent signups, concurrent reservations, duplicate
   normalized emails, transaction rollback and retry behavior.
4. Exercise **real network HTTP requests** to a running staging service
   with staging DB; current TestClient checks are in-process HTTP routing
   tests, not a deployed network server.
5. Add signed-webhook payment verification, idempotency, buyer ownership,
   refund and chargeback policy before accepting real payments.
6. Run auth, session, abuse and privacy security reviews, plus recovery
   and rollback rehearsals.
7. Require an explicit owner go/no-go before any live migration or
   production registration code rollout.

## Evidence already collected
- GitHub backend unit workflow and disposable PostgreSQL VIP workflow
  were green at review.
- In-process HTTP registration tests verified VIP skip, concurrency,
  duplicate normalized email and HTTP error responses.
- No live VIP sales, payment processing or production VIP allocation
  is implemented.

## Owner decision required
Approve the exact staging infrastructure plan and its costs **before**
creating new Render resources. Keep production unchanged.
