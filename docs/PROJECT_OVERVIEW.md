# Project Overview: Digital Payment Failure Analysis

## 1. Business Context & Motivation

In the modern digital economy, real-time payment processing (via UPI, credit cards, debit cards, and net banking) has become mission-critical infrastructure. A payment failure does not simply represent a dropped transaction; it represents:
- **Direct Conversion Dropoff:** Customers abandon checkouts when payments fail.
- **Support Overhead:** Escalated tickets, customer inquiries, and dispute investigations.
- **Brand Erosion:** Frustration when funds are deducted or transactions repeatedly time out.
- **Operational Blind Spots:** Lack of visibility into whether a spike in failures is caused by bank core banking systems (CBS), gateway network timeouts, or user-side insufficient funds.

The **Digital Payment Failure Analysis** project is an end-to-end analytics platform designed to ingest payment telemetry, isolate technical from business failure modes, perform rigorous statistical validation, and present actionable operational insights via interactive dashboards and automated reports.

---

## 2. Problem Statement

Payment operations teams are frequently flooded with raw transaction logs without clear categorization between:
1. **Technical Declines:** Server timeouts, gateway drops, switch unresponsiveness (infrastructure-driven).
2. **Business/Customer Declines:** Insufficient balances, invalid credentials, customer-side limits.
3. **Volume vs. Rate Distortions:** Larger payment switches process higher transaction counts and naturally log more raw failures, creating an illusion of poor performance when their underlying failure rate may actually be stable.

Without rigorous analytics, operations teams misallocate engineering resources trying to fix bank switch connections when the true culprit is customer balance exhaustion, or fail to catch severe peak-hour latency degradations in specific bank routing switches.

---

## 3. Project Objectives

- **Data Integrity & Profiling:** Establish an automated quality profiling and cleaning pipeline to sanitize raw payment telemetry.
- **Diagnostic Root-Cause Analysis:** Quantify the exact impact of payment methods, bank switches, peak hours, and ticket amounts on failure rates.
- **Statistical Rigor:** Apply hypothesis testing (Chi-square test of independence, Mann-Whitney U test, proportion confidence intervals) to separate genuine systemic signals from random variance.
- **Relational SQL Modeling:** Persist validated data in an indexed SQLite analytical database and query it using CTEs, window functions, and multi-dimensional aggregations.
- **Interactive Executive & Ops Tooling:** Deploy a clean, light-themed Streamlit dashboard for payment operations managers and site reliability engineers.
- **Actionable Operational Guidance:** Translate statistical findings into concrete SLAs, dynamic routing rules, and auto-retry policies.

---

## 4. Key Business Definitions & Metric Precision

To prevent misinterpreting financial telemetry, this project enforces strict operational definitions:

| Metric | Definition | Formula / Denominator | Business Meaning |
| :--- | :--- | :--- | :--- |
| **Total Transaction Volume** | Total number of payment attempts initiated. | $N = \sum \text{all attempts}$ | Overall platform traffic. |
| **Eligible Population** | Transactions with verified final outcomes (`SUCCESS`, `FAILED`). | $N_{\text{eligible}} = N_{\text{success}} + N_{\text{failed}}$ | Baseline for rate calculations. |
| **Failure Rate (%)** | Proportion of eligible transactions that terminated in failure. | $\frac{N_{\text{failed}}}{N_{\text{eligible}}} \times 100$ | Primary operational reliability KPI. |
| **Success Rate (%)** | Proportion of eligible transactions that succeeded. | $\frac{N_{\text{success}}}{N_{\text{eligible}}} \times 100$ | Primary commercial health KPI. |
| **Total Payment Volume (TPV)**| Gross monetary value of all initiated payment attempts. | $\sum \text{Transaction\_Amount}$ | Total economic throughput. |
| **Failed Transaction Value** | Total value of transactions that resulted in failure. | $\sum_{\text{failed}} \text{Transaction\_Amount}$ | **Potentially affected GMV** (not direct loss). |
| **P90 / P99 Latency** | 90th and 99th percentile round-trip processing duration. | Quantile($0.90$), Quantile($0.99$) | Tail latency experienced by end-users. |

> [!CAUTION]
> **Failed Transaction Value vs. Lost Revenue:** Failed transaction value is **not** direct financial loss. In digital payments, users frequently retry the payment immediately, switch to another payment method, or use Cash-on-Delivery. Treating all failed transaction amounts as lost revenue grossly inflates commercial risk.

---

## 5. Core Research Questions

This project is built to answer 10 concrete operational questions supported by the data:
1. What is the baseline platform failure rate across all transactions?
2. Which payment methods (UPI, Cards, NetBanking) exhibit elevated failure rates?
3. Which bank switches account for the highest volume of failures vs. the highest failure rate?
4. What are the dominant error codes and root-cause failure categories?
5. How does network response latency correlate with failure outcomes?
6. Are failures concentrated during specific peak operating hours or days?
7. Do transaction ticket sizes (amount bands) influence success probabilities?
8. Are merchant categories or metropolitan regions disproportionately impacted?
9. Is the association between bank switch and failure outcome statistically significant?
10. What specific technical interventions (routing rules, retry logic) should operations teams implement?

---

## 6. Target Audience

- **Head of Payment Operations:** Monitoring overall switch health, provider SLAs, and conversion metrics.
- **Fintech Site Reliability Engineers (SREs):** Tracking P95/P99 latency spikes and gateway switch timeouts.
- **Product Managers (Checkout & Conversion):** Designing user-side retry prompts, payment method suggestions, and error messaging.
- **Data Analysts & Scientists:** Auditing data quality, validating statistical hypotheses, and building SQL analytics models.
