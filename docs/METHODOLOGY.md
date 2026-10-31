# Analytical & Statistical Methodology

## 1. Metric Formulations & KPI Definitions

To ensure analytical correctness, every KPI in this project is defined with an explicit mathematical formulation, numerator, and denominator.

### 1.1 Platform Failure Rate ($FR$)
$$\text{Failure Rate} = \frac{\sum_{i=1}^{N} \mathbb{I}(\text{status}_i = \text{FAILED})}{\sum_{i=1}^{N} \mathbb{I}(\text{status}_i \in \{\text{SUCCESS}, \text{FAILED}\})} \times 100$$
* **Numerator:** Total count of transactions that terminated in a failed state.
* **Denominator:** Total count of eligible completed transactions. Transactions with non-terminal states (pending, reversed, or unknown, if any) are excluded from the denominator to avoid deflating the rate.

### 1.2 Weighted Group Failure Rate
For any partition $g \in G$ (e.g., bank switch or payment method):
$$\text{Failure Rate}_g = \frac{N_{\text{failed}, g}}{N_{\text{total}, g}} \times 100$$
* **Analytical Rule:** Group failure rates are **never** calculated as an unweighted average of subgroups. The pooled rate correctly weights by the transaction volume of each cell.

### 1.3 Total Payment Volume (TPV) & Failed Value
$$\text{TPV} = \sum_{i=1}^{N} \text{Amount}_i \quad ; \quad \text{Failed TPV} = \sum_{i \in \text{Failed}} \text{Amount}_i$$
* **Business Interpretation:** Failed TPV represents **potentially affected Gross Merchandise Value (GMV)**, not permanent lost revenue. Users frequently retry successful transactions or switch instruments.

---

## 2. Statistical Analysis & Hypothesis Testing

### 2.1 Proportion Confidence Intervals (Wilson Score Interval)
Given observed successes/failures in large samples, the Wilson Score interval provides superior coverage probability without the asymmetry flaws of the normal approximation near boundaries:
$$CI = \frac{p + \frac{z^2}{2n} \pm z \sqrt{\frac{p(1-p)}{n} + \frac{z^2}{4n^2}}}{1 + \frac{z^2}{n}}$$
Where:
- $p = \frac{x}{n}$ (sample failure proportion)
- $z = 1.96$ for a 95% two-sided confidence level ($\alpha = 0.05$)
- $n = \text{sample size}$

### 2.2 Chi-Square Test of Independence ($\chi^2$)
Used to test whether categorical attributes (e.g., Bank Switch, Payment Method, Peak Window) are statistically independent of transaction outcome (`SUCCESS` vs `FAILED`):
$$\chi^2 = \sum_{i=1}^{r} \sum_{j=1}^{c} \frac{(O_{ij} - E_{ij})^2}{E_{ij}}$$
Where:
- $O_{ij}$ is the observed transaction count in cell $(i, j)$
- $E_{ij} = \frac{(\sum \text{row } i)(\sum \text{col } j)}{N}$ is the expected count under $H_0$
- **Assumption Verification:** All expected cell frequencies $E_{ij} \gg 5$ (minimum cell count in our data exceeds 500, easily satisfying asymptotic requirements).

### 2.3 Effect Size: Cramer's V ($V$)
Because large sample sizes ($N=50,000$) routinely produce infinitesimal p-values ($p < 10^{-50}$), effect sizes are mandatory to measure practical business relevance:
$$V = \sqrt{\frac{\phi^2}{\min(r-1, c-1)}} \quad \text{where} \quad \phi^2 = \frac{\chi^2}{N}$$
* **Thresholds:** $V \approx 0.10$ (small effect), $V \approx 0.30$ (moderate effect), $V \ge 0.50$ (large effect).

### 2.4 Non-Parametric Latency Comparison (Mann-Whitney U Test)
Transaction latency distributions exhibit heavy right-skew and multi-modal peaks during timeout events, violating the normality assumptions required for Student's t-test. The non-parametric Mann-Whitney U test evaluates whether random latency draws from failed transactions are stochastically greater than successful transactions:
$$U = R_1 - \frac{n_1(n_1 + 1)}{2}$$
Effect size is reported via the Rank-Biserial correlation coefficient ($r$).

### 2.5 Multiple Comparisons & Family-Wise Error Rate (Bonferroni Adjustment)
When performing $k = 5$ pairwise bank comparisons against the platform baseline:
$$\alpha_{\text{adjusted}} = \frac{\alpha}{k} = \frac{0.05}{5} = 0.010$$
A bank comparison is only considered statistically significant if $p < 0.010$, controlling family-wise type I error inflation.

---

## 3. SQL Analytics Methodology

Analytical data is persisted in a relational SQLite database (`data/payment_analytics.db`) using the documented schema in `sql/schema.sql`.
- **Primary Key:** `transaction_id` (`VARCHAR(50)`).
- **Secondary B-Tree Indexes:** Created on `(bank_switch, payment_method)`, `(transaction_timestamp)`, and `(transaction_status)` to accelerate range filters and multi-dimensional joins.
- **Aggregations:** Written in standardized ANSI SQL using CTEs (`WITH` clauses) and window functions (`ROW_NUMBER()`, `RANK()`, `SUM() OVER ()`) to guarantee identical metric output between Python and SQL pipelines.
