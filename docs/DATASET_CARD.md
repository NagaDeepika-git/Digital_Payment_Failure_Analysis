# Dataset Card: Digital Payment Transaction Health

## 1. Dataset Overview

* **Dataset Title:** Digital Payment Transaction Health Analytics Dataset
* **Source Repository:** [ManojMaliDev/Digital-Payment-Transaction-Health-Analytics](https://github.com/ManojMaliDev/Digital-Payment-Transaction-Health-Analytics)
* **Original Author/Publisher:** Manoj Mali
* **Date Obtained:** October 29, 2026
* **Acquisition Method:** Direct programmatic download of `Raw_fintech_payment_transactions.csv` via HTTPS from the author's public repository, backed by a deterministic generator (`generate_fintech_data.py`).
* **License & Permitted Use:** Public open-source repository on GitHub (no explicit custom license file specified; standard open GitHub attribution guidelines applied). Used strictly for non-commercial educational portfolio and research purposes.

---

## 2. Provenance & Authenticity Disclosure

> [!IMPORTANT]
> **Synthetic Nature Disclosure:** This dataset is **100% synthetic**. It was generated programmatically using Python (NumPy and Pandas) with a fixed seed (`seed=42`) to simulate real-world Indian fintech transaction telemetry.
> 
> Under no circumstances should the patterns, bank failure rates, or latencies observed in this dataset be interpreted as actual historical performance of the National Payments Corporation of India (NPCI) or commercial banks (e.g., HDFC, SBI, ICICI, Axis Bank, Kotak).

### Verified Generation Logic
The synthetic generator was intentionally engineered by the author to encode three distinct operational scenarios:
1. **HDFC UPI Peak-Hour Switch Outages:** Between 20:00 and 22:59, HDFC UPI transactions experience a 45% conditional failure rate with an injected latency penalty of +4,000 ms (`ERR_BANK_TIMEOUT` / `Bank Switch Unresponsive`).
2. **SBI Card Balance Declines:** SBI card transactions experience a 28% decline rate due to customer low account balances (`ERR_INSUFFICIENT_FUNDS` / `Customer Account Low Balance`), without latency penalties.
3. **Baseline Platform Noise:** All remaining transactions follow an ~88% baseline success rate, with residual failures assigned to network drops or authentication declines (`ERR_AUTH_DECLINED`, `ERR_INVALID_PIN`, `ERR_GATEWAY_DROP`).

---

## 3. Dataset Characteristics

* **Record Count:** 50,000 transaction rows (+ 1 header row = 50,001 lines).
* **Column Count:** 13 attributes.
* **File Size:** ~6.11 MB (6,110,248 bytes).
* **Time Span:** 60-day window (~June 15, 2026 to August 14, 2026).
* **Missing Values in Raw Data:** `Failure_Reason` has missing values (empty string / NULL) exclusively for `SUCCESS` transactions. All other 12 columns have 0 missing values.
* **Exact Duplicate Rows:** 0 duplicate rows.
* **Unique Transaction IDs:** 50,000 unique keys (`TXN_100000` to `TXN_149999`).

---

## 4. Column Schema & Data Dictionary

| Column Name | Data Type | Non-Null Count | Sample Values | Description |
| :--- | :--- | :--- | :--- | :--- |
| `Transaction_id` | String | 50,000 | `TXN_100000`, `TXN_100001` | Unique alphanumeric transaction attempt identifier. |
| `Customer_ID` | String | 50,000 | `CUST_8270`, `CUST_1860` | Anonymized customer account identifier. |
| `Transaction_Timestamp` | String (Datetime) | 50,000 | `2026-08-14 18:36:08` | ISO format timestamp of payment initiation. |
| `Payment_Method` | String (Categorical) | 50,000 | `UPI`, `Credit Card`, `Debit Card`, `NetBanking` | Rail used to route the payment. |
| `Bank_Switch` | String (Categorical) | 50,000 | `HDFC`, `SBI`, `ICICI`, `Axis Bank`, `Kotak` | Remitter/acquirer core banking switch partner. |
| `Merchant_Name` | String (Categorical) | 50,000 | `Amazon`, `Flipkart`, `Swiggy`, `Uber` | Partner merchant entity receiving payment. |
| `Merchant_Category` | String (Categorical) | 50,000 | `E-Commerce`, `Food & Grocery`, `Travel & Mobility` | Commercial sector of the merchant. |
| `Geography` | String (Categorical) | 50,000 | `Mumbai`, `Bengaluru`, `Delhi`, `Pune`, `Chennai`, `Hyderabad` | Metropolitan area of origin. |
| `Transaction_Amount` | Float | 50,000 | `2140.05`, `887.95`, `509.51` | Transaction ticket size in Indian Rupees (INR). |
| `Transaction_Status` | String (Categorical) | 50,000 | `SUCCESS`, `FAILED` | Final outcome state of the payment attempt. |
| `Error_Code` | String (Categorical) | 50,000 | `SUCCESS_00`, `ERR_BANK_TIMEOUT`, `ERR_INSUFFICIENT_FUNDS` | Technical error code returned by switch/gateway. |
| `Failure_Reason` | String (Categorical) | 7,464 (non-null) | `Bank Switch Unresponsive`, `Customer Account Low Balance` | Human-readable categorization of the root cause. Null for successful transactions. |
| `Latency_ms` | Integer | 50,000 | `1588`, `1232`, `1182`, `5120` | End-to-end round trip processing duration (ms). |

---

## 5. Limitations & Caveats

1. **Synthetic Generation Artifacts:** Because timestamps were generated via uniform random seconds, day-of-week and month-level variations exhibit near-uniform baseline volume rather than real-world weekend surges or holiday spikes.
2. **Absence of Pending/Reversal States:** The raw dataset models transactions strictly as binary (`SUCCESS` vs `FAILED`). No asynchronous `PENDING`, `REVERSED`, or `DISPUTED` intermediate statuses exist.
3. **No Financial Loss Equivalence:** Failed transaction value cannot be treated as permanent lost revenue, as customers often retry or use alternate instruments.

---

## 6. Reproducibility

The raw dataset can be downloaded or deterministically regenerated at any time using:
```powershell
python -m src.data_loader
```
