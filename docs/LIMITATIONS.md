# Limitations, Assumptions & Ethical Considerations

## 1. Synthetic Data Constraints

> [!WARNING]
> **Synthetic Telemetry Disclosure:** The underlying dataset used in this project (`fintech_payment_transactions.csv`) was generated algorithmically with Python (`np.random.seed(42)`). 
> 
> The statistical patterns discovered in this project reflect the parameters and probability distributions embedded by the data generator. They must **never** be cited as official historical performance or SLA compliance metrics for real Indian commercial entities (such as HDFC Bank, State Bank of India, ICICI Bank, Axis Bank, Kotak Mahindra Bank, Amazon, or the National Payments Corporation of India).

### Specific Synthetic Artifacts
1. **Uniform Calendar Distribution:** Timestamp generation used a uniform distribution over 60 days. In real payment networks, weekend transaction volumes, salary-day surges (1st to 5th of the month), and festival shopping spikes create strong seasonality that is absent in this dataset.
2. **Simplified Independence in Baseline:** Outside of the explicitly programmed failure rules (HDFC peak-hour timeouts and SBI balance declines), baseline failure noise was sampled independently at random. As a result, cross-category interactions (such as Geography $\times$ Merchant Category) show no natural geographic clustering.
3. **No Retries Linkage:** Each record represents an independent attempt without a foreign session identifier linking repeated customer retries after an initial failure.

---

## 2. Observational & Statistical Boundaries

1. **Correlation vs. Causation:** Statistical tests (such as Chi-square and Mann-Whitney U) establish significant empirical associations between bank switches, payment methods, and failure states. However, observational data alone cannot prove mechanical causality without controlled A/B testing or server telemetry logs (e.g., CPU utilization, thread pool exhaustion, upstream switch response dumps).
2. **Infinitesimal P-Values ($p < 10^{-50}$):** With a large sample size ($N = 50,000$), standard hypothesis tests detect minute deviations from independence as statistically significant. Practitioners must evaluate **Cramer's V effect size** ($V \approx 0.07$ to $0.20$) and practical business cost rather than relying solely on p-values.

---

## 3. Financial & Business Interpretation Safeguards

1. **Failed TPV $\neq$ Lost Revenue:** 
   * The total failed transaction value on this platform is **₹11.32M** out of **₹75.53M TPV** (14.99% of total attempted value).
   * It is fundamentally inaccurate to report ₹11.32M as lost revenue. In consumer fintech, a user encountering an `ERR_GATEWAY_DROP` or `ERR_INVALID_PIN` typically re-enters their credentials within seconds or switches to an alternate payment method. 
   * True economic loss occurs only upon terminal checkout abandonment.
2. **Binary State Limitation:** Real payment systems possess intermediate, asynchronous transaction states (`PENDING`, `AUTHORIZED`, `SETTLED`, `REVERSED`, `DISPUTED`). This dataset models outcomes strictly as binary (`SUCCESS` vs `FAILED`), omitting settlement reconciliation windows.

---

## 4. Privacy, Security & Data Ethics

1. **No Personally Identifiable Information (PII):** The dataset contains zero genuine customer identifiers, PANs, CVVs, phone numbers, or residential addresses. Customer identifiers are hashed strings (`CUST_1000` to `CUST_9999`).
2. **Fair Representation:** Because this project uses synthetic data for educational portfolio demonstration, findings should not be used to disparage real financial institutions or influence vendor selection in commercial procurement without real internal benchmark telemetry.
