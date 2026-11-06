# RKU ONE — A → B → C → D implementation order

## A. Numeric ID protection and VIP inventory (first)
- Existing IDs are permanent. Never renumber, recycle, overwrite, or reset the users identity sequence.
- Current authentication uses password hashes and signed sessions; password reset, MFA, account recovery, and session revocation are NOT implemented.
- Before activating VIP sales: conduct a **read-only** inventory audit of existing IDs and next sequence value. Record who already owns each ID; do not assume IDs 1–5 are unassigned.
- Design a reservation ledger with statuses (available/reserved/allocated), transaction-safe checkout, payment verification and an audit trail. Never claim a number is reserved until database enforcement is implemented and tested.
- Normal free ID allocation must skip genuinely reserved VIP IDs; migration and concurrency tests are required before enabling this.
- Never expose user email addresses in public ID lookup.

## B. RKU Cloud (after A)
- Implement private object storage and authenticated per-owner metadata.
- Validate quota, content size, checksum, ownership, and download authorization.
- Manual upload first; mobile background backup requires separate native-app support and user consent.
- See docs/rku-cloud-security-plan.md. No production upload is enabled.

## C. RKU ID-to-ID sharing (after B)
- Sender grants a recipient ID access to a specific file; recipient can accept/decline.
- No permanent public URLs. Use short-lived download grants, expiration and revocation.
- Test that unrelated IDs cannot read files and revoked access stops working.

## D. RKU Family Cloud (after C)
- Separate family workspace from personal files; invitation requires acceptance.
- Roles: owner, adult member, child-safe limited member. No implicit access to personal vaults.
- Per-file and per-album sharing permissions, removal and recovery tests.

## Launch safety
- Remain on free hosting during development; no domain launch or paid plan without owner approval.
- Tests use mocks and cannot prove live backup, production security or end-to-end recovery.
- Verify Render Postgres free-tier expiration and prepare an export/migration before it expires.
