-- ==========================================================
-- DIGITAL PAYMENT FAILURE ANALYSIS
-- SQL DATABASE SCHEMA (SQLite 3)
-- ==========================================================

DROP TABLE IF EXISTS transactions;

CREATE TABLE transactions (
    transaction_id          VARCHAR(50) PRIMARY KEY,
    customer_id             VARCHAR(50) NOT NULL,
    transaction_timestamp   DATETIME NOT NULL,
    payment_method          VARCHAR(30) NOT NULL,
    bank_switch             VARCHAR(50) NOT NULL,
    merchant_name           VARCHAR(50) NOT NULL,
    merchant_category       VARCHAR(50) NOT NULL,
    geography               VARCHAR(50) NOT NULL,
    transaction_amount      DECIMAL(12, 2) NOT NULL CHECK(transaction_amount > 0),
    transaction_status      VARCHAR(20) NOT NULL CHECK(transaction_status IN ('SUCCESS', 'FAILED')),
    error_code              VARCHAR(50) NOT NULL,
    failure_reason          VARCHAR(100) NOT NULL,
    latency_ms              INTEGER NOT NULL CHECK(latency_ms >= 0),
    transaction_date        DATE,
    hour_of_day             INTEGER CHECK(hour_of_day BETWEEN 0 AND 23),
    day_of_week             VARCHAR(15),
    day_of_week_num         INTEGER CHECK(day_of_week_num BETWEEN 0 AND 6),
    is_weekend              INTEGER CHECK(is_weekend IN (0, 1)),
    time_of_day_bucket      VARCHAR(30),
    is_peak_window          INTEGER CHECK(is_peak_window IN (0, 1)),
    amount_band             VARCHAR(30),
    latency_band            VARCHAR(30),
    is_failed               INTEGER CHECK(is_failed IN (0, 1)),
    failure_mode            VARCHAR(50)
);

-- B-Tree Performance Indexes for Analytics Queries
CREATE INDEX idx_txn_timestamp ON transactions(transaction_timestamp);
CREATE INDEX idx_txn_status ON transactions(transaction_status);
CREATE INDEX idx_txn_bank_method ON transactions(bank_switch, payment_method);
CREATE INDEX idx_txn_hour ON transactions(hour_of_day);
CREATE INDEX idx_txn_customer ON transactions(customer_id);
CREATE INDEX idx_txn_error ON transactions(error_code);
