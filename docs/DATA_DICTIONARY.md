# Data Dictionary: Digital Payment Failure Analysis

This document provides a comprehensive specification of every column present in the cleaned analytical dataset (`data/processed/payment_transactions_cleaned.csv`) and database (`data/payment_analytics.db`).

---

## Field Specifications

### 1. `transaction_id`
* **Data Type:** `VARCHAR(50)` / `string`
* **Description:** Unique system identifier assigned to each individual payment attempt.
* **Format:** `TXN_<6-digit-number>` (e.g., `TXN_100000`)
* **Constraints:** Primary Key, Unique, Not Null.
* **Business Rule:** Each record corresponds to exactly one payment authorization attempt.

### 2. `customer_id`
* **Data Type:** `VARCHAR(50)` / `string`
* **Description:** Anonymized client identifier representing the originating payer account.
* **Format:** `CUST_<4-digit-number>` (e.g., `CUST_8270`)
* **Constraints:** Not Null.
* **Business Rule:** A single customer may initiate multiple transactions across different payment methods and merchants.

### 3. `transaction_timestamp`
* **Data Type:** `DATETIME` / `datetime64[ns]`
* **Description:** Precise local timestamp when the payment request was logged at the switch gateway.
* **Format:** `YYYY-MM-DD HH:MM:SS` (e.g., `2026-08-14 18:36:08`)
* **Constraints:** Not Null, Range: `2026-07-04 16:11:44` to `2026-09-02 16:09:54`.
* **Business Rule:** Basis for all temporal feature engineering (hour of day, day of week, peak windows).

### 4. `payment_method`
* **Data Type:** `VARCHAR(30)` / `string`
* **Description:** The digital payment instrument or rail chosen by the user.
* **Allowed Values:**
  * `UPI` (Unified Payments Interface - Instant mobile payments)
  * `Credit Card` (Card network authorization rail)
  * `Debit Card` (Bank account debit authorization rail)
  * `NetBanking` (Direct bank portal redirect rail)
* **Constraints:** Not Null.

### 5. `bank_switch`
* **Data Type:** `VARCHAR(50)` / `string`
* **Description:** Core banking system switch responsible for routing and settling the transaction.
* **Allowed Values:**
  * `HDFC`
  * `SBI` (State Bank of India)
  * `ICICI`
  * `Axis Bank`
  * `Kotak`
* **Constraints:** Not Null.

### 6. `merchant_name`
* **Data Type:** `VARCHAR(50)` / `string`
* **Description:** The receiving merchant entity where the consumer checkout occurred.
* **Allowed Values:** `Amazon`, `Flipkart`, `Swiggy`, `Zomato`, `Uber`, `MakeMyTrip`, `JioMart`, `Myntra`.
* **Constraints:** Not Null.

### 7. `merchant_category`
* **Data Type:** `VARCHAR(50)` / `string`
* **Description:** Industry category of the merchant.
* **Allowed Values:**
  * `E-Commerce` (`Amazon`, `Flipkart`, `Myntra`)
  * `Food & Grocery` (`Swiggy`, `Zomato`, `JioMart`)
  * `Travel & Mobility` (`Uber`, `MakeMyTrip`)
* **Constraints:** Not Null.

### 8. `geography`
* **Data Type:** `VARCHAR(50)` / `string`
* **Description:** Metropolitan Indian city where the transaction originated.
* **Allowed Values:** `Mumbai`, `Bengaluru`, `Delhi`, `Pune`, `Chennai`, `Hyderabad`.
* **Constraints:** Not Null.

### 9. `transaction_amount`
* **Data Type:** `DECIMAL(12, 2)` / `float64`
* **Description:** Total monetary value of the payment request in Indian Rupees (INR, ₹).
* **Constraints:** Not Null, Value $> 0$, Min: `100.00`, Max: `15,196.92`.
* **Business Rule:** Used to compute Total Payment Volume (TPV) and potentially affected transaction value.

### 10. `transaction_status`
* **Data Type:** `VARCHAR(20)` / `string`
* **Description:** Final outcome state of the payment authorization.
* **Allowed Values:**
  * `SUCCESS` (Payment successfully authorized and confirmed)
  * `FAILED` (Payment declined, timed out, or dropped)
* **Constraints:** Not Null.
* **Business Rule:** Serves as the ground-truth binary label for failure rate calculations ($N_{\text{failed}} / N_{\text{eligible}}$).

### 11. `error_code`
* **Data Type:** `VARCHAR(50)` / `string`
* **Description:** Technical gateway error code returned by the payment processor.
* **Allowed Values:**
  * `SUCCESS_00`: Successful completion (0 errors).
  * `ERR_BANK_TIMEOUT`: Switch failed to acknowledge response within timeout threshold (typically associated with switch latency spikes).
  * `ERR_INSUFFICIENT_FUNDS`: Customer account has inadequate balance for the transaction amount.
  * `ERR_AUTH_DECLINED`: Authentication gateway rejected customer credentials or OTP.
  * `ERR_INVALID_PIN`: User entered incorrect payment PIN or security credentials.
  * `ERR_GATEWAY_DROP`: Upstream network packet loss or socket disconnection.
* **Constraints:** Not Null.

### 12. `failure_reason`
* **Data Type:** `VARCHAR(100)` / `string`
* **Description:** High-level operational classification of the failure root cause.
* **Allowed Values:**
  * `None`: Assigned to all successful transactions.
  * `Bank Switch Unresponsive`: Infrastructure-level technical decline (timeout).
  * `Customer Account Low Balance`: User-level business decline (insufficient funds).
  * `Authentication / Network Failure`: Gateway or credential error.
* **Constraints:** Not Null (explicitly normalized).

### 13. `latency_ms`
* **Data Type:** `INTEGER` / `int64`
* **Description:** End-to-end round-trip response duration from request initiation to terminal status confirmation in milliseconds.
* **Constraints:** Not Null, Value $\ge 0$, Min: `250 ms`, Max: `6,173 ms`.
* **Business Rule:** Telemetry for detecting switch degradation and setting SLA thresholds.
