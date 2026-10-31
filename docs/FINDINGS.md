# Key Analytical Findings & Evidence-Backed Recommendations

This report presents the core diagnostic findings from auditing **50,000 digital payment transactions** representing **₹75.53M in Total Payment Volume (TPV)**. Every finding is ranked by operational impact, supported by exact empirical metrics, and paired with actionable engineering and business interventions.

---

## Executive Summary Matrix

| Rank | Finding / Focus Area | Sample Size ($n$) | Observed Metric | Statistical Evidence | Primary Driver | Recommended Action |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | **HDFC UPI Peak-Hour Switch Collapse** | 14,743 | Failure rate jumps from **12.23%** (off-peak) to **34.04%** (peak 20-23h) | $\chi^2 = 603.44$, $p = 2.99 \times 10^{-133}$, Cramer's $V = 0.202$ | Switch timeouts (`ERR_BANK_TIMEOUT`) with latency $+960$ ms | Dynamic routing to ICICI/Axis when peak failure rate breaches 20% |
| **2** | **SBI Elevated Card Declines** | 12,599 | **20.40%** overall failure rate vs. 13.08% for remainder of platform | $\chi^2 = 396.32$, $p = 3.48 \times 10^{-88}$, Odds Ratio = 1.70 | Insufficient balance (`ERR_INSUFFICIENT_FUNDS`), not switch faults | In-app low balance warning or alternate handle debit prompt |
| **3** | **Network & Credential Drops Dominance** | 50,000 | **77.52%** of all platform failures (5,786 of 7,464) | Spread across `ERR_AUTH_DECLINED`, `ERR_INVALID_PIN`, `ERR_GATEWAY_DROP` | Transient network disconnects & OTP input timeouts | 1-click instant silent retry (3s window) before rendering error screen |
| **4** | **Payment Method Divergence** | 50,000 | Cards (**18.34%**) fail more than UPI (**13.27%**) and NetBanking (**12.03%**) | $\chi^2 = 253.95$, $p = 9.14 \times 10^{-55}$, Cramer's $V = 0.071$ | Multi-hop 3DS authentication vs single-hop MPIN | Optimize card checkout SDK to reduce dropped auth sessions |
| **5** | **Ticket Size Invariance** | 50,000 | Failure rates remain stable across ticket sizes (~14.7% to 15.1%) | Amount band comparison: Micro (15.1%), High (14.7%) | Failures driven by rail & switch capacity, not ticket size | Deprioritize amount-based routing rules; focus on switch SLAs |

---

## Detailed Evidence & Diagnostic Analysis

### Finding 1: HDFC UPI Peak-Hour Switch Outage
* **Observation:** During the evening peak window (20:00 to 22:59), transactions routed through the HDFC switch experience severe degradation.
* **Empirical Evidence:**
  * Off-peak failure rate: **12.23%** [95% CI: 11.66% – 12.82%]
  * Peak-hour failure rate: **34.04%** [95% CI: 31.95% – 36.19%]
  * Absolute failure rate delta: **$+21.81\%$**
  * Average latency: **1,224.98 ms** overall, but spikes by **$+960.38\text{ ms}$** during peak hours, with P99 latency reaching **5,307 ms**.
  * Error code concentration: Exactly **449 transactions** failed with `ERR_BANK_TIMEOUT` (`Bank Switch Unresponsive`), and 100% of these timeouts occurred during the 20:00–22:59 window.
  * Contrast Group: ICICI (11.65%), Axis Bank (11.40%), and Kotak (11.62%) showed zero latency or failure rate spikes during the exact same peak hours.
* **Business Interpretation:** This is an infrastructure capacity bottleneck at HDFC's core banking switch rather than general internet congestion or client-side issues.
* **Caveat:** Synthetic data intentionally embedded this failure signature; however, it accurately reflects real-world Core Banking System (CBS) batch-processing and evening load spikes documented in NPCI root-cause reports.
* **Recommended Next Step:** Establish an automated SLA breach threshold. When HDFC switch rolling failure rate exceeds 20%, automatically re-route 50% of UPI volume to Axis Bank or ICICI.

---

### Finding 2: SBI High Failure Volume Driven by Customer Balance, Not Infrastructure
* **Observation:** SBI registers the highest failure rate of any bank switch (**20.40%**), accounting for **2,570 failed transactions** and **₹3.90M in affected GMV**.
* **Empirical Evidence:**
  * SBI failure rate: **20.40%** [95% CI: 19.70% – 21.11%]
  * Remainder of platform: **13.08%** [95% CI: 12.74% – 13.43%]
  * Pairwise Chi-Square test: $\chi^2 = 396.32$, $p = 3.48 \times 10^{-88}$, Odds Ratio = 1.70.
  * Latency comparison: SBI average latency is **1,096.30 ms** (virtually identical to the platform baseline of 1,100 ms).
  * Error code breakdown: Failures on SBI Card rails are dominated by `ERR_INSUFFICIENT_FUNDS` (1,229 transactions; 47.8% of SBI failures).
* **Business Interpretation:** SBI’s elevated failure rate is a **business/customer decline**, not a technical or switch reliability problem. Engineering teams should not spend SLA credits investigating SBI switch uptime.
* **Recommended Next Step:** Implement pre-debit client balance checks or prompt customers with low balances to switch to an alternate debit instrument before checkout submission.

---

### Finding 3: Technical Drops Account for 77.5% of All Platform Failures
* **Observation:** Over three-quarters of all transaction drops are caused by transient network disconnections, invalid PINs, and authentication timeouts.
* **Empirical Evidence:**
  * Total failures: **7,464**
  * `ERR_AUTH_DECLINED`: 1,932 failures (25.88% share, ₹2.92M affected GMV)
  * `ERR_INVALID_PIN`: 1,931 failures (25.87% share, ₹2.88M affected GMV)
  * `ERR_GATEWAY_DROP`: 1,923 failures (25.76% share, ₹3.00M affected GMV)
  * Cumulative share: **77.52%** of all platform dropoffs.
  * Latency profile: Latencies for these errors are normal (~1,090 ms), indicating immediate drops rather than timeout hangs.
* **Business Interpretation:** These drops represent high recovery potential because users who experience socket drops or mistype PINs intend to transact.
* **Recommended Next Step:** Implement a 1-click silent auto-retry mechanism for `ERR_GATEWAY_DROP` within a 3-second window, and allow quick PIN re-entry without restarting the checkout session.

---

### Finding 4: Payment Instrument Disparity (Cards vs. UPI & NetBanking)
* **Observation:** Debit Card (**18.64%**) and Credit Card (**18.12%**) exhibit significantly higher failure rates than UPI (**13.27%**) and NetBanking (**12.03%**).
* **Empirical Evidence:**
  * Chi-square test: $\chi^2 = 253.95$, $p = 9.14 \times 10^{-55}$, Cramer's $V = 0.071$.
  * UPI volume share: **55.18%** (27,588 txns), failure rate: **13.27%** [95% CI: 12.87% – 13.67%].
  * Card combined volume: **35.01%** (17,507 txns), combined failure rate: **18.35%**.
* **Business Interpretation:** Cards require multi-party redirection (merchant $\rightarrow$ gateway $\rightarrow$ card network $\rightarrow$ issuing bank ACS $\rightarrow$ OTP screen), compounding dropoff risk compared to UPI’s unified native protocol.
* **Recommended Next Step:** Encourage checkout defaults towards UPI and tokenized card flows to minimize friction.

---

### Finding 5: Failure Rate Invariance Across Transaction Amount Bands
* **Observation:** Ticket size has virtually no correlation with failure probability.
* **Empirical Evidence:**
  * Micro (< ₹500): 12,372 txns, failure rate = **15.11%**
  * Low (₹500 - ₹1.5K): 19,212 txns, failure rate = **14.80%**
  * Medium (₹1.5K - ₹5K): 16,803 txns, failure rate = **14.99%**
  * High (> ₹5K): 1,613 txns, failure rate = **14.69%**
* **Business Interpretation:** Payment failures on this platform are driven by switch health and authentication protocols rather than financial risk screening or fraud limits.
* **Recommended Next Step:** Avoid building complex amount-based routing rules; prioritize switch-health and time-of-day routing instead.
