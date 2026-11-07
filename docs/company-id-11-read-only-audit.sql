-- RKU ONE company ID 11: READ-ONLY availability preflight.
-- Authorized DBA only. No customer data, credentials, or secrets returned.
-- This checks existing account issuance, NOT a binding reservation.
-- IMPORTANT: current production registration still allocates sequential IDs.
-- Even if ID 11 is unissued now, it could be issued before a reservation
-- migration; do not advertise it as secured.

BEGIN READ ONLY;

SELECT CASE
         WHEN EXISTS (SELECT 1 FROM users WHERE rku_id = 11)
         THEN 'ISSUED_DO_NOT_REASSIGN'
         ELSE 'NOT_ISSUED_NOT_RESERVED'
       END AS company_id_11_status;

SELECT COUNT(*) AS issued_premium_range_2_to_1000
FROM users
WHERE rku_id BETWEEN 2 AND 1000;

SELECT COUNT(*) AS issued_company_id_11
FROM users
WHERE rku_id = 11;

COMMIT;

-- No INSERT, UPDATE, DELETE, ALTER, setval, reservation, or sequence reset.
-- This script cannot confirm any future availability or payment eligibility.
