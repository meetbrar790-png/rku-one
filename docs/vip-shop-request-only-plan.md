# RKU ONE — VIP Shop / Choose Number (request-only implementation plan)

Status: DEVELOPMENT BRANCH ONLY. No payments, deployment, or production DB changes authorized.

## Customer experience
- VIP catalogue shows a proposed USD list price and category, never a false "available" label.
- Search accepts numeric IDs, rejects invalid or noncanonical input, and checks the server's authoritative inventory.
- Status values: available, issued, reserved, held, unavailable, unknown. Unknown is never treated as available.
- "Request to buy / reserve" sends an authenticated, rate-limited expression of interest, **not** a hold, sale, or allocation.
- A request acknowledgement explicitly states that the number is not guaranteed and no payment has been collected.
- IDs 1001+ follow the free-ID registration path; never show them as VIP products.

## Ownership and inventory rules
- Never reissue an allocated ID; preserve existing assignments.
- ID 1 (founder) and ID 11 (company) are not for sale.
- IDs 13 and 786 are specially designated; confirm owner authorization and live inventory before any listing as purchasable.
- VIP candidate range is 2–1000, subject to current reservations and issued IDs.
- Use existing vip_price_catalogue.py / vip_pricing_policy.py as proposed-price sources, but enforce pricing and availability on server.
- Never promise availability from the static demo.

## Request-only API contract (proposal, not yet implemented)
GET /api/vip/catalogue?limit=...
GET /api/vip/numbers/{id}/status
POST /api/vip/interest {number_id, request_id}
- POST requires authenticated user, CSRF protection where applicable, strict validation, rate limits and idempotency.
- Store minimum necessary request details; do not expose buyer identities or reservation ownership.
- Return request status; do not allocate or hold an ID or initiate payment.

## Before production
1. Review existing registration, VIP allocation and auth code and write tests for reserved, issued, race and unknown states.
2. Test in disposable PostgreSQL with no production credentials.
3. Confirm owner-approved list pricing, reservation inventory and UX.
4. Complete security review, then request separate authorization for live deployment.
5. Stripe and all checkout/payment routes remain disabled until separate explicit approval.
