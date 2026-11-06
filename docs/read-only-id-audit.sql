-- RKU ONE: READ-ONLY numeric ID inventory.
-- Run only through an authorized database administrator connection.
-- Does not expose email addresses, passwords, or session tokens.
-- Does not change any ID, sequence, table, or reservation.
SELECT COUNT(*) AS allocated_accounts,
       MIN(rku_id) AS lowest_allocated_id,
       MAX(rku_id) AS highest_allocated_id,
       COUNT(DISTINCT rku_id) AS distinct_allocated_ids
FROM users;

-- Count allocated IDs in the first 100 positions without identifying owners.
-- These counts are NOT a VIP reservation ledger.
SELECT COUNT(*) FILTER (WHERE rku_id BETWEEN 1 AND 10) AS allocated_1_to_10,
       COUNT(*) FILTER (WHERE rku_id BETWEEN 11 AND 100) AS allocated_11_to_100
FROM users;

-- The sequence and reservation inventory require a separate reviewed
-- migration; never run setval, ALTER SEQUENCE, TRUNCATE, or DELETE.
