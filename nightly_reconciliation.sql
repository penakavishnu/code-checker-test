-- nightly_reconciliation.sql
-- Reconciles daily transaction records against the customer master table.
-- Runs nightly after the Glue ETL job completes.

BEGIN TRANSACTION;

-- Remove reconciliation records past the 90-day retention window
DELETE FROM reconciliation_log
WHERE created_at < DATEADD(day, -90, GETDATE())
  AND status = 'PROCESSED';

-- Flag today's transactions that have no matching customer record
UPDATE transactions
SET reconciliation_status = 'ORPHANED'
WHERE customer_id NOT IN (SELECT customer_id FROM customers)
  AND transaction_date = CAST(GETDATE() AS DATE);

-- Insert today's summary into the daily reconciliation log
INSERT INTO reconciliation_log (run_date, total_transactions, orphaned_count, status)
SELECT
    CAST(GETDATE() AS DATE),
    COUNT(*),
    SUM(CASE WHEN reconciliation_status = 'ORPHANED' THEN 1 ELSE 0 END),
    'PROCESSED'
FROM transactions
WHERE transaction_date = CAST(GETDATE() AS DATE);

COMMIT;