-- ==========================================================
-- DIGITAL PAYMENT FAILURE ANALYSIS
-- ADVANCED ANALYTICAL SQL QUERIES (SQLite)
-- ==========================================================

-- ----------------------------------------------------------
-- Query 1: Platform-Wide Executive KPIs
-- Business Goal: Audits total transaction volume, success/failure counts, rates, and TPV.
-- ----------------------------------------------------------
-- NAME: platform_executive_kpis
SELECT
    COUNT(*) AS total_transactions,
    SUM(CASE WHEN transaction_status = 'SUCCESS' THEN 1 ELSE 0 END) AS successful_transactions,
    SUM(CASE WHEN transaction_status = 'FAILED' THEN 1 ELSE 0 END) AS failed_transactions,
    ROUND(SUM(CASE WHEN transaction_status = 'FAILED' THEN 1.0 ELSE 0.0 END) / COUNT(*) * 100.0, 2) AS failure_rate_pct,
    ROUND(SUM(CASE WHEN transaction_status = 'SUCCESS' THEN 1.0 ELSE 0.0 END) / COUNT(*) * 100.0, 2) AS success_rate_pct,
    ROUND(SUM(transaction_amount), 2) AS total_tpv_inr,
    ROUND(SUM(CASE WHEN transaction_status = 'FAILED' THEN transaction_amount ELSE 0 END), 2) AS failed_tpv_inr,
    ROUND(AVG(latency_ms), 2) AS avg_latency_ms
FROM transactions;


-- ----------------------------------------------------------
-- Query 2: Failure Rate & Volume by Payment Method
-- Business Goal: Identifies which payment rails suffer the highest failure rates vs. highest failure volume.
-- ----------------------------------------------------------
-- NAME: payment_method_breakdown
SELECT
    payment_method,
    COUNT(*) AS total_transactions,
    SUM(CASE WHEN transaction_status = 'FAILED' THEN 1 ELSE 0 END) AS failed_transactions,
    ROUND(SUM(CASE WHEN transaction_status = 'FAILED' THEN 1.0 ELSE 0.0 END) / COUNT(*) * 100.0, 2) AS failure_rate_pct,
    ROUND(SUM(transaction_amount), 2) AS total_tpv_inr,
    ROUND(SUM(CASE WHEN transaction_status = 'FAILED' THEN transaction_amount ELSE 0 END), 2) AS failed_tpv_inr,
    ROUND(AVG(latency_ms), 2) AS avg_latency_ms,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM transactions), 2) AS volume_share_pct
FROM transactions
GROUP BY payment_method
ORDER BY failure_rate_pct DESC;


-- ----------------------------------------------------------
-- Query 3: Bank Switch Reliability Ranking with Window Functions
-- Business Goal: Ranks bank switches by failure rate, failed volume, and latency.
-- ----------------------------------------------------------
-- NAME: bank_switch_ranking
WITH BankStats AS (
    SELECT
        bank_switch,
        COUNT(*) AS total_txns,
        SUM(CASE WHEN transaction_status = 'FAILED' THEN 1 ELSE 0 END) AS failed_txns,
        ROUND(SUM(CASE WHEN transaction_status = 'FAILED' THEN 1.0 ELSE 0.0 END) / COUNT(*) * 100.0, 2) AS failure_rate_pct,
        ROUND(SUM(transaction_amount), 2) AS total_tpv,
        ROUND(SUM(CASE WHEN transaction_status = 'FAILED' THEN transaction_amount ELSE 0 END), 2) AS failed_tpv,
        ROUND(AVG(latency_ms), 2) AS avg_latency_ms
    FROM transactions
    GROUP BY bank_switch
)
SELECT
    bank_switch,
    total_txns,
    failed_txns,
    failure_rate_pct,
    total_tpv,
    failed_tpv,
    avg_latency_ms,
    RANK() OVER (ORDER BY failure_rate_pct DESC) AS rank_by_failure_rate,
    RANK() OVER (ORDER BY failed_txns DESC) AS rank_by_failed_volume
FROM BankStats
ORDER BY failure_rate_pct DESC;


-- ----------------------------------------------------------
-- Query 4: Bank Switch x Payment Method Multi-Dimensional Matrix
-- Business Goal: Uncovers specific method-bank switch vulnerabilities (e.g., SBI Card vs HDFC UPI).
-- ----------------------------------------------------------
-- NAME: bank_method_matrix
SELECT
    bank_switch,
    payment_method,
    COUNT(*) AS total_transactions,
    SUM(CASE WHEN transaction_status = 'FAILED' THEN 1 ELSE 0 END) AS failed_transactions,
    ROUND(SUM(CASE WHEN transaction_status = 'FAILED' THEN 1.0 ELSE 0.0 END) / COUNT(*) * 100.0, 2) AS failure_rate_pct,
    ROUND(AVG(latency_ms), 2) AS avg_latency_ms
FROM transactions
GROUP BY bank_switch, payment_method
ORDER BY bank_switch, failure_rate_pct DESC;


-- ----------------------------------------------------------
-- Query 5: Root-Cause Failure Reasons & Error Code Pareto Analysis
-- Business Goal: Quantifies the contribution of each error code to total platform failures.
-- ----------------------------------------------------------
-- NAME: failure_reason_pareto
WITH ErrorStats AS (
    SELECT
        failure_reason,
        error_code,
        COUNT(*) AS failure_count,
        ROUND(SUM(transaction_amount), 2) AS failed_amount_inr,
        ROUND(AVG(latency_ms), 2) AS avg_latency_ms
    FROM transactions
    WHERE transaction_status = 'FAILED'
    GROUP BY failure_reason, error_code
),
PlatformFailures AS (
    SELECT COUNT(*) AS total_platform_failures FROM transactions WHERE transaction_status = 'FAILED'
)
SELECT
    e.failure_reason,
    e.error_code,
    e.failure_count,
    e.failed_amount_inr,
    e.avg_latency_ms,
    ROUND(e.failure_count * 100.0 / p.total_platform_failures, 2) AS share_of_failures_pct,
    ROUND(SUM(e.failure_count) OVER (ORDER BY e.failure_count DESC) * 100.0 / p.total_platform_failures, 2) AS cumulative_failure_pct
FROM ErrorStats e
CROSS JOIN PlatformFailures p
ORDER BY e.failure_count DESC;


-- ----------------------------------------------------------
-- Query 6: Peak Hour (20:00 - 22:59) Switch Stress Analysis
-- Business Goal: Compares switch performance between peak and off-peak hours using CTEs.
-- ----------------------------------------------------------
-- NAME: peak_hour_switch_comparison
WITH HourlyClassification AS (
    SELECT
        bank_switch,
        CASE WHEN hour_of_day IN (20, 21, 22) THEN 'Peak (20-23h)' ELSE 'Off-Peak' END AS time_window,
        COUNT(*) AS txns,
        SUM(CASE WHEN transaction_status = 'FAILED' THEN 1 ELSE 0 END) AS failures,
        AVG(latency_ms) AS avg_lat
    FROM transactions
    GROUP BY bank_switch, time_window
)
SELECT
    bank_switch,
    time_window,
    txns AS total_transactions,
    failures AS failed_transactions,
    ROUND(failures * 100.0 / txns, 2) AS failure_rate_pct,
    ROUND(avg_lat, 2) AS avg_latency_ms
FROM HourlyClassification
ORDER BY bank_switch, time_window DESC;


-- ----------------------------------------------------------
-- Query 7: Ticket Size Amount Band Performance
-- Business Goal: Analyzes if high-value transactions suffer disproportionate decline rates.
-- ----------------------------------------------------------
-- NAME: amount_band_performance
SELECT
    amount_band,
    COUNT(*) AS total_transactions,
    SUM(CASE WHEN transaction_status = 'FAILED' THEN 1 ELSE 0 END) AS failed_transactions,
    ROUND(SUM(CASE WHEN transaction_status = 'FAILED' THEN 1.0 ELSE 0.0 END) / COUNT(*) * 100.0, 2) AS failure_rate_pct,
    ROUND(SUM(transaction_amount), 2) AS total_tpv_inr,
    ROUND(SUM(CASE WHEN transaction_status = 'FAILED' THEN transaction_amount ELSE 0 END), 2) AS failed_tpv_inr,
    ROUND(AVG(latency_ms), 2) AS avg_latency_ms
FROM transactions
GROUP BY amount_band
ORDER BY total_transactions DESC;


-- ----------------------------------------------------------
-- Query 8: High-Risk Segments with Volume Safeguard (Min 100 Txns)
-- Business Goal: Identifies the worst-performing operational segments requiring immediate SLA intervention.
-- ----------------------------------------------------------
-- NAME: high_risk_segments
SELECT
    bank_switch,
    payment_method,
    merchant_category,
    COUNT(*) AS total_txns,
    SUM(CASE WHEN transaction_status = 'FAILED' THEN 1 ELSE 0 END) AS failed_txns,
    ROUND(SUM(CASE WHEN transaction_status = 'FAILED' THEN 1.0 ELSE 0.0 END) / COUNT(*) * 100.0, 2) AS failure_rate_pct,
    ROUND(AVG(latency_ms), 2) AS avg_latency_ms
FROM transactions
GROUP BY bank_switch, payment_method, merchant_category
HAVING COUNT(*) >= 100
ORDER BY failure_rate_pct DESC
LIMIT 10;
