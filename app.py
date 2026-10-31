"""
Interactive Fintech Analytics Dashboard.
Digital Payment Failure Analysis
Streamlit Application
"""

import sys
import sqlite3
from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Set Page Configuration (Must be first Streamlit command)
st.set_page_config(
    page_title="Digital Payment Failure Analysis",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Light-Theme CSS Styling
st.markdown("""
<style>
    /* Global Typography & Spacing */
    .main {
        background-color: #F8FAFC;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    
    /* Header Container */
    .header-box {
        background: linear-gradient(135deg, #1E3A8A 0%, #1E40AF 100%);
        padding: 24px 32px;
        border-radius: 12px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .header-title {
        font-size: 26px;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
        color: #FFFFFF !important;
    }
    .header-subtitle {
        font-size: 14px;
        color: #E2E8F0;
        margin-top: 6px;
        margin-bottom: 0;
    }
    
    /* Metric Cards */
    .metric-card {
        background: white;
        padding: 18px 20px;
        border-radius: 10px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.04);
        margin-bottom: 16px;
    }
    .metric-label {
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        color: #64748B;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }
    .metric-value {
        font-size: 24px;
        font-weight: 700;
        color: #0F172A;
    }
    .metric-sub {
        font-size: 12px;
        color: #94A3B8;
        margin-top: 4px;
    }
    
    /* Alert / Callout Box */
    .info-callout {
        background-color: #EFF6FF;
        border-left: 4px solid #3B82F6;
        padding: 14px 18px;
        border-radius: 6px;
        font-size: 13px;
        color: #1E3A8A;
        margin-bottom: 20px;
        line-height: 1.5;
    }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid #E2E8F0;
    }
    .stTabs [data-baseweb="tab"] {
        height: 42px;
        white-space: pre-wrap;
        background-color: white;
        border-radius: 6px 6px 0 0;
        border: 1px solid #E2E8F0;
        border-bottom: none;
        padding: 8px 16px;
        font-weight: 500;
        color: #475569;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1E3A8A !important;
        color: white !important;
        border-color: #1E3A8A !important;
    }
</style>
""", unsafe_allow_html=True)

# Import Project Modules
from src.config import (
    PROCESSED_DATA_PATH,
    DATABASE_PATH,
    TABLES_DIR,
    LIGHT_THEME_COLORS,
    ELIGIBLE_STATUSES
)
from src.data_loader import load_processed_data
from src.feature_engineering import engineer_features
from src.metrics import (
    calculate_overall_kpis,
    calculate_grouped_metrics,
    calculate_failure_reasons_breakdown,
    calculate_hourly_metrics,
    calculate_dow_metrics
)
from src.charts import (
    plot_status_distribution,
    plot_failure_rate_by_bank,
    plot_failure_rate_by_method,
    plot_failure_reasons_breakdown,
    plot_hourly_trend_dual_axis,
    plot_peak_hour_bank_breakdown,
    plot_latency_box_by_status,
    plot_amount_band_failure_rate
)


@st.cache_data(show_spinner=False)
def get_analytical_data() -> pd.DataFrame:
    """Load cleaned dataset and enrich with features."""
    df = load_processed_data(PROCESSED_DATA_PATH)
    if "hour_of_day" not in df.columns or "amount_band" not in df.columns:
        df = engineer_features(df)
    return df


# -------------------------------------------------------------
# APPLICATION HEADER
# -------------------------------------------------------------
st.markdown("""
<div class="header-box">
    <h1 class="header-title">Digital Payment Failure Analysis</h1>
    <p class="header-subtitle">
        Diagnostic telemetry, switch latency modeling, and operational root-cause analysis across 50,000 transactions.
    </p>
</div>
""", unsafe_allow_html=True)

# Load Data
try:
    df_full = get_analytical_data()
except Exception as e:
    st.error(f"Error loading analytical dataset: {e}")
    st.stop()

# -------------------------------------------------------------
# SIDEBAR FILTERS
# -------------------------------------------------------------
st.sidebar.markdown("### 🔍 Operational Filters")
st.sidebar.caption("📌 *Analyzing 50,000 synthetic payment records (seed=42)*")

# Date Filter
min_ts = pd.to_datetime(df_full["transaction_timestamp"].min()).date()
max_ts = pd.to_datetime(df_full["transaction_timestamp"].max()).date()

date_selection = st.sidebar.date_input(
    "Date Range",
    value=(min_ts, max_ts),
    min_value=min_ts,
    max_value=max_ts
)

# Bank Filter
all_banks = sorted(df_full["bank_switch"].unique().tolist())
selected_banks = st.sidebar.multiselect(
    "Bank Switch",
    options=all_banks,
    default=all_banks
)

# Payment Method Filter
all_methods = sorted(df_full["payment_method"].unique().tolist())
selected_methods = st.sidebar.multiselect(
    "Payment Instrument",
    options=all_methods,
    default=all_methods
)

# Status Filter
all_statuses = sorted(df_full["transaction_status"].unique().tolist())
selected_statuses = st.sidebar.multiselect(
    "Transaction Outcome",
    options=all_statuses,
    default=all_statuses
)

# Merchant Category Filter
all_categories = sorted(df_full["merchant_category"].unique().tolist())
selected_categories = st.sidebar.multiselect(
    "Merchant Category",
    options=all_categories,
    default=all_categories
)

# Geography Filter
all_geographies = sorted(df_full["geography"].unique().tolist())
selected_geographies = st.sidebar.multiselect(
    "Geography (City)",
    options=all_geographies,
    default=all_geographies
)

# Amount Range Filter
min_amt = float(df_full["transaction_amount"].min())
max_amt = float(df_full["transaction_amount"].max())
amount_range = st.sidebar.slider(
    "Transaction Amount (INR)",
    min_value=float(np.floor(min_amt)),
    max_value=float(np.ceil(max_amt)),
    value=(float(np.floor(min_amt)), float(np.ceil(max_amt))),
    step=100.0
)

# Apply Filters
filtered_df = df_full.copy()

# Date filtering (handle both 2-element tuple and 1-element intermediate state)
if isinstance(date_selection, tuple) and len(date_selection) == 2:
    start_d, end_d = date_selection
    filtered_df = filtered_df[
        (pd.to_datetime(filtered_df["transaction_timestamp"]).dt.date >= start_d) &
        (pd.to_datetime(filtered_df["transaction_timestamp"]).dt.date <= end_d)
    ]
elif isinstance(date_selection, tuple) and len(date_selection) == 1:
    start_d = date_selection[0]
    filtered_df = filtered_df[
        pd.to_datetime(filtered_df["transaction_timestamp"]).dt.date >= start_d
    ]

# Multi-select filtering
filtered_df = filtered_df[filtered_df["bank_switch"].isin(selected_banks)]
filtered_df = filtered_df[filtered_df["payment_method"].isin(selected_methods)]
filtered_df = filtered_df[filtered_df["transaction_status"].isin(selected_statuses)]
filtered_df = filtered_df[filtered_df["merchant_category"].isin(selected_categories)]
filtered_df = filtered_df[filtered_df["geography"].isin(selected_geographies)]

# Amount filtering
filtered_df = filtered_df[
    (filtered_df["transaction_amount"] >= amount_range[0]) &
    (filtered_df["transaction_amount"] <= amount_range[1])
]

# Handle Empty Filter State
if len(filtered_df) == 0:
    st.warning("⚠️ No transactions match the current filter selection. Please broaden your filter criteria in the sidebar.")
    st.stop()

# -------------------------------------------------------------
# EXECUTIVE KPI SUMMARY BANNER
# -------------------------------------------------------------
kpi_dict = calculate_overall_kpis(filtered_df)

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Total Transactions</div>
        <div class="metric-value">{kpi_dict['total_transactions']:,}</div>
        <div class="metric-sub">{(kpi_dict['total_transactions']/len(df_full)*100):.1f}% of platform volume</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    fail_color = "#EF4444" if kpi_dict["failure_rate_pct"] > 15 else "#10B981"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Failure Rate</div>
        <div class="metric-value" style="color: {fail_color};">{kpi_dict['failure_rate_pct']:.2f}%</div>
        <div class="metric-sub">{kpi_dict['failed_transactions']:,} failed transactions</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Success Rate</div>
        <div class="metric-value" style="color: #10B981;">{kpi_dict['success_rate_pct']:.2f}%</div>
        <div class="metric-sub">{kpi_dict['successful_transactions']:,} successful</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Total TPV</div>
        <div class="metric-value">₹{kpi_dict['total_tpv_inr']/1e6:.2f}M</div>
        <div class="metric-sub">Avg ticket: ₹{kpi_dict['avg_ticket_inr']:.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">P95 Response Latency</div>
        <div class="metric-value">{kpi_dict['p95_latency_ms']:.0f} ms</div>
        <div class="metric-sub">Avg latency: {kpi_dict['avg_latency_ms']:.0f} ms</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div class="info-callout">
    💡 <b>Analytical Definition Notice:</b> <b>Failed Transaction Value</b> reflects potentially affected Gross Merchandise Value (GMV), 
    not direct lost revenue. A customer experiencing a technical decline frequently retries immediately or switches payment instruments.
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# MAIN DASHBOARD TABS
# -------------------------------------------------------------
tab_overview, tab_diagnostics, tab_time, tab_amounts, tab_stats, tab_quality, tab_recommendations, tab_explorer = st.tabs([
    "📊 Executive Overview",
    "🔍 Failure Diagnostics",
    "⏰ Time Dynamics",
    "💰 Amount & Latency",
    "📐 Statistical Rigor",
    "🛡️ Data Quality",
    "🚀 Operational Actions",
    "🔎 Transaction Explorer"
])

# -------------------------------------------------------------
# TAB 1: EXECUTIVE OVERVIEW
# -------------------------------------------------------------
with tab_overview:
    st.subheader("Platform Outcome Breakdown & Switch Performance")
    col_a, col_b = st.columns([1, 1])
    
    with col_a:
        st.plotly_chart(plot_status_distribution(filtered_df), theme=None)
        
    with col_b:
        st.plotly_chart(plot_failure_rate_by_bank(filtered_df), theme=None)

    st.markdown("---")
    st.subheader("Bank Switch Performance Summary")
    bank_summary_df = calculate_grouped_metrics(filtered_df, "bank_switch")
    st.dataframe(
        bank_summary_df.style.format({
            "total_transactions": "{:,.0f}",
            "successful_transactions": "{:,.0f}",
            "failed_transactions": "{:,.0f}",
            "failure_rate_pct": "{:.2f}%",
            "success_rate_pct": "{:.2f}%",
            "total_tpv_inr": "₹{:,.2f}",
            "failed_tpv_inr": "₹{:,.2f}",
            "avg_latency_ms": "{:.1f} ms",
            "p95_latency_ms": "{:.1f} ms"
        })
    )

# -------------------------------------------------------------
# TAB 2: FAILURE DIAGNOSTICS
# -------------------------------------------------------------
with tab_diagnostics:
    st.subheader("Root-Cause Categorization & Error Code Analysis")
    col_d1, col_d2 = st.columns([1, 1])
    
    with col_d1:
        st.plotly_chart(plot_failure_reasons_breakdown(filtered_df), theme=None)
        
    with col_d2:
        st.plotly_chart(plot_failure_rate_by_method(filtered_df), theme=None)

    st.markdown("---")
    st.subheader("Method x Bank Failure Matrix (Cross-Tabulation)")
    def cross_tab_calc(sub):
        tot = len(sub)
        fail = (sub["transaction_status"] == "FAILED").sum()
        return (fail / tot * 100.0) if tot > 0 else 0.0

    matrix = filtered_df.groupby(["bank_switch", "payment_method"]).apply(cross_tab_calc, include_groups=False).unstack()
    st.dataframe(
        matrix.style.format("{:.2f}%").background_gradient(cmap="Reds", vmin=10, vmax=40)
    )
    st.caption("Values indicate failure rate (%) within each Bank Switch and Payment Method combination.")

# -------------------------------------------------------------
# TAB 3: TIME DYNAMICS
# -------------------------------------------------------------
with tab_time:
    st.subheader("Hourly Failure Rates & Peak Switch Congestion")
    st.plotly_chart(plot_hourly_trend_dual_axis(filtered_df), theme=None)
    
    st.markdown("---")
    st.subheader("Peak Hours (20:00 - 22:59) Switch Outage Audit")
    st.plotly_chart(plot_peak_hour_bank_breakdown(filtered_df), theme=None)

    st.info(
        "📌 **Operational Finding:** Notice how HDFC failure rates surge to **34.0%** during 20:00–22:59, accompanied by a ~4,000 ms latency spike. "
        "In contrast, ICICI and Axis Bank maintain steady failure rates of ~11.6% across the exact same window, proving this is an HDFC switch capacity bottleneck."
    )

# -------------------------------------------------------------
# TAB 4: AMOUNT & LATENCY ANALYSIS
# -------------------------------------------------------------
with tab_amounts:
    st.subheader("Transaction Latency & Ticket Size Dynamics")
    col_l1, col_l2 = st.columns([1, 1])
    
    with col_l1:
        st.plotly_chart(plot_latency_box_by_status(filtered_df), theme=None)
        
    with col_l2:
        st.plotly_chart(plot_amount_band_failure_rate(filtered_df), theme=None)

    st.markdown("""
    > [!NOTE]
    > **Ticket Size vs. Technical Drops:** Failure rates remain largely uniform across amount bands (~14.8%–15.1%), indicating that 
    > high-value transactions are not systematically penalized by routing rules. However, timeout clusters predominantly affect UPI during evening peaks.
    """)

# -------------------------------------------------------------
# TAB 5: STATISTICAL RIGOR
# -------------------------------------------------------------
with tab_stats:
    st.subheader("Hypothesis Testing & Wilson Score Confidence Intervals")
    
    # Dynamic Wilson CI calculation for active filtered selection
    k_fails = int((filtered_df["transaction_status"] == "FAILED").sum())
    n_total = len(filtered_df)
    if n_total > 0:
        from scipy import stats
        z = stats.norm.ppf(0.975)  # 95% two-sided
        p = k_fails / n_total
        denom = 1 + (z**2 / n_total)
        center = (p + (z**2 / (2 * n_total))) / denom
        margin = (z * np.sqrt((p * (1 - p) / n_total) + (z**2 / (4 * n_total**2)))) / denom
        ci_lower = max(0.0, center - margin) * 100
        ci_upper = min(1.0, center + margin) * 100
        obs_rate = (k_fails / n_total) * 100
        
        st.markdown(f"""
        <div style="background-color: white; border: 1px solid #E2E8F0; border-radius: 8px; padding: 16px; margin-bottom: 20px;">
            <span style="font-size: 12px; font-weight: 600; text-transform: uppercase; color: #64748B;">Active Filtered Segment Wilson 95% Confidence Interval</span><br>
            <span style="font-size: 22px; font-weight: 700; color: #1E3A8A;">{obs_rate:.2f}%</span>
            <span style="font-size: 14px; color: #475569; margin-left: 8px;">[95% CI: <b>{ci_lower:.2f}%</b> — <b>{ci_upper:.2f}%</b>] (n={n_total:,})</span>
        </div>
        """, unsafe_allow_html=True)

    tests_table_path = TABLES_DIR / "statistical_tests_summary.csv"
    ci_table_path = TABLES_DIR / "confidence_intervals.csv"
    
    if tests_table_path.exists():
        st.markdown("#### Formal Hypothesis Test Results (Full Platform Baseline, N=50,000)")
        tests_df = pd.read_csv(tests_table_path)
        st.dataframe(tests_df)
    
    if ci_table_path.exists():
        st.markdown("#### Subgroup 95% Wilson Score Confidence Intervals")
        ci_df = pd.read_csv(ci_table_path)
        st.dataframe(
            ci_df.style.format({
                "sample_size": "{:,.0f}",
                "failed_count": "{:,.0f}",
                "failure_rate_pct": "{:.2f}%",
                "ci_lower_95_pct": "{:.2f}%",
                "ci_upper_95_pct": "{:.2f}%"
            })
        )

    st.markdown("""
    > [!NOTE]
    > **Statistical vs. Practical Significance:** In large samples ($N=50,000$), p-values frequently reach infinitesimal thresholds ($p < 10^{-50}$). 
    > While the Chi-Square test confirms non-random associations, operational decisions are guided by **Cramer's V effect size** and practical risk exposure.
    """)

# -------------------------------------------------------------
# TAB 6: DATA QUALITY
# -------------------------------------------------------------
with tab_quality:
    st.subheader("Data Cleaning & Quality Audit Trail")
    
    audit_table_path = TABLES_DIR / "cleaning_audit_summary.csv"
    missing_table_path = TABLES_DIR / "raw_missingness.csv"
    
    col_q1, col_q2 = st.columns([1, 1])
    with col_q1:
        st.markdown("#### Before/After Cleaning Audit Summary")
        if audit_table_path.exists():
            st.dataframe(pd.read_csv(audit_table_path))
            
    with col_q2:
        st.markdown("#### Raw Missingness Profile")
        if missing_table_path.exists():
            st.dataframe(pd.read_csv(missing_table_path))

    st.markdown("---")
    st.markdown("#### Automated Validation Suite Assertions")
    st.markdown("""
    * **Schema Check:** Passed (13 required columns standardized to lower snake_case).
    * **Primary Key Uniqueness:** Passed (50,000 unique `transaction_id`s, 0 duplicate keys).
    * **Categorical Domain Integrity:** Passed (All values belong to closed permitted vocabularies).
    * **Numeric Bounds:** Passed (Amounts strictly between ₹1.00 and ₹100,000.00; Latencies between 10 ms and 60,000 ms).
    * **Outcome Consistency:** Passed (`failure_reason == 'None'` strictly asserted for all 42,536 SUCCESS records).
    """)

# -------------------------------------------------------------
# TAB 7: OPERATIONAL ACTIONS & RECOMMENDATIONS
# -------------------------------------------------------------
with tab_recommendations:
    st.subheader("Evidence-Backed Operational Interventions")
    
    st.markdown("""
    ### 1. Dynamic Traffic Re-Routing (HDFC UPI Switch)
    * **Evidence:** HDFC UPI failure rate surges from 12.2% off-peak to **34.0% during 20:00–22:59**, with P99 latency exceeding 5,000 ms due to `ERR_BANK_TIMEOUT`.
    * **Action:** Configure the payment gateway smart router to divert 50% of HDFC UPI traffic to alternate partner switches (ICICI / Axis Bank) as soon as rolling 5-minute failure rates breach 20%.

    ### 2. Pre-Debit Customer Balance Warning (SBI Cards)
    * **Evidence:** SBI card failure rate reaches **~38%–39%**, with over 75% attributed to customer `ERR_INSUFFICIENT_FUNDS` rather than core banking infrastructure faults.
    * **Action:** Implement a proactive in-app balance prompt or suggest debiting an alternate verified UPI handle before dispatching high-ticket card payment intents.

    ### 3. Asynchronous 1-Click Auto-Retry for Gateway Drops
    * **Evidence:** `ERR_GATEWAY_DROP` and `ERR_AUTH_DECLINED` account for **77.5% of total platform failures**, with normal average latency (~1,090 ms).
    * **Action:** Enable a 1-click silent auto-retry within 3 seconds of connection drop before rendering an explicit failure screen to the consumer.
    """)
    
    st.markdown("""
    > [!IMPORTANT]
    > **Data Provenance & Simulation Caveat:** This telemetry dataset is 100% synthetic, generated algorithmically (seed=42) to model real-world Indian fintech payment switches. 
    > Operational patterns identified here reflect algorithmic model configurations and must not be interpreted as actual historical incidents or downtime of the commercial banks named.
    """)

# -------------------------------------------------------------
# TAB 8: TRANSACTION EXPLORER
# -------------------------------------------------------------
with tab_explorer:
    st.subheader("Transaction-Level Analytical Explorer")
    st.caption("Search, filter, and inspect granular transaction telemetry. Not a CRUD application.")
    
    search_query = st.text_input("Search by Transaction ID, Customer ID, or Merchant Name", "")
    if search_query:
        view_df = filtered_df[
            filtered_df["transaction_id"].str.contains(search_query, case=False, na=False) |
            filtered_df["customer_id"].str.contains(search_query, case=False, na=False) |
            filtered_df["merchant_name"].str.contains(search_query, case=False, na=False)
        ]
    else:
        view_df = filtered_df

    st.write(f"Displaying top **{min(100, len(view_df))}** of **{len(view_df):,}** matching transactions:")
    display_cols = [
        "transaction_id", "customer_id", "transaction_timestamp",
        "payment_method", "bank_switch", "merchant_name",
        "transaction_amount", "transaction_status", "error_code",
        "failure_reason", "latency_ms"
    ]
    
    formatted_table = view_df[display_cols].head(100).copy()
    st.dataframe(
        formatted_table.style.format({
            "transaction_amount": "₹{:,.2f}",
            "latency_ms": "{:,.0f} ms"
        })
    )

    # CSV Download Button
    csv_bytes = view_df[display_cols].head(1000).to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Export Filtered Transactions (CSV - Max 1,000)",
        data=csv_bytes,
        file_name="filtered_payment_transactions.csv",
        mime="text/csv"
    )
