# Data Cleaning & Preprocessing Log

## 1. Executive Summary

The raw dataset `fintech_payment_transactions.csv` underwent a systematic, reproducible data-quality audit and cleaning pipeline (`src/cleaning.py`). Because the source data was generated using a controlled algorithmic script, structural defects (such as corrupted rows, missing customer IDs, or impossible negative values) were not present. 

The primary objectives of the cleaning stage were:
1. Standardizing schema nomenclature to canonical lower `snake_case`.
2. Safe datetime casting of `transaction_timestamp` with format validation.
3. Explicitly distinguishing semantic `None` (representing normal successful transactions with zero failures) from missing values.
4. Performing non-destructive bounds validation on monetary amounts and latency telemetry.

---

## 2. Before & After Reconciliation Audit

| Cleaning Metric | Raw Dataset | Cleaned Dataset | Variance / Delta | Operational Interpretation |
| :--- | :--- | :--- | :--- | :--- |
| **Total Rows** | 50,000 | 50,000 | 0 (100% retention) | No records were arbitrarily dropped. |
| **Total Columns** | 13 | 13 | 0 | Schema structure preserved. |
| **Exact Duplicate Rows** | 0 | 0 | 0 | Verified 0 full-row duplicate records. |
| **Duplicate Transaction IDs** | 0 | 0 | 0 | Primary key integrity confirmed. |
| **Invalid Timestamps** | 0 | 0 | 0 | All 50,000 dates parsed cleanly to ISO format. |
| **Negative Amounts / Latencies**| 0 | 0 | 0 | All values adhere to physical bounds. |
| **Missing Values (`failure_reason`)**| 42,536 (85.07%) | 0 (Explicit 'None') | -42,536 | Replaced empty values with literal `'None'` string. |
| **Successful Transactions** | 42,536 (85.07%) | 42,536 (85.07%) | 0 | Success volume perfectly conserved. |
| **Failed Transactions** | 7,464 (14.93%) | 7,464 (14.93%) | 0 | Failure volume perfectly conserved. |

---

## 3. Step-by-Step Cleaning Audit Trail

### Step 1: Column Standardization
- **Raw Headers:** `Transaction_id`, `Customer_ID`, `Transaction_Timestamp`, `Payment_Method`, `Bank_Switch`, `Merchant_Name`, `Merchant_Category`, `Geography`, `Transaction_Amount`, `Transaction_Status`, `Error_Code`, `Failure_Reason`, `Latency_ms`.
- **Transformation:** Stripped whitespace, lowered case, and replaced spaces with underscores.
- **Resulting Headers:** `transaction_id`, `customer_id`, `transaction_timestamp`, `payment_method`, `bank_switch`, `merchant_name`, `merchant_category`, `geography`, `transaction_amount`, `transaction_status`, `error_code`, `failure_reason`, `latency_ms`.

### Step 2: Duplicate Inspection & Integrity Verification
- Ran full-row duplicate detection: 0 matches found.
- Checked primary key uniqueness on `transaction_id`: 50,000 unique keys (`TXN_100000` to `TXN_149999`). No deduplication dropping was required.

### Step 3: Text Normalization
- Applied `.str.strip()` across all categorical string dimensions to prevent leading/trailing whitespace anomalies from skewing SQL `GROUP BY` aggregations.

### Step 4: Timestamp Casting
- Converted `transaction_timestamp` using `pd.to_datetime(..., errors="coerce", format="%Y-%m-%d %H:%M:%S")`.
- Validated date boundary: Earliest timestamp `2026-07-04 16:11:44`, Latest timestamp `2026-09-02 16:09:54`. Exactly 0 parsing errors occurred.

### Step 5: Semantic Imputation for Failure Reasons
- In the raw CSV, successful transactions have an empty value for `Failure_Reason`.
- In SQL engines and Pandas operations, bare `NULL` values in categorical fields can cause inadvertent exclusions during filtering or grouping.
- **Decision:** For all rows where `transaction_status == 'SUCCESS'`, `failure_reason` was assigned the explicit string literal `'None'`, and `error_code` was confirmed as `'SUCCESS_00'`.
- For failed transactions, all 7,464 records already possessed valid non-null failure reason strings.

### Step 6: Numeric Bounds Verification
- `transaction_amount`: Checked for negative values, zero tickets, and extreme outliers. Minimum ticket is ₹100.00, maximum is ₹15,196.92. Distribution is exponential as expected in digital retail payments.
- `latency_ms`: Checked for negative durations. Minimum latency is 250 ms, maximum is 6,173 ms (spike during bank switch timeouts). All 50,000 records fall within physically valid system parameters.
