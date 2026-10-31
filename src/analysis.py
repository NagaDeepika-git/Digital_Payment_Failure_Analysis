"""
Comprehensive Exploratory Data Analysis & Business Intelligence Aggregations.
Digital Payment Failure Analysis
"""

import logging
from pathlib import Path
from typing import Dict, Any
import numpy as np
import pandas as pd

from src.config import TABLES_DIR
from src.data_loader import load_processed_data
from src.feature_engineering import engineer_features
from src.metrics import (
    calculate_overall_kpis,
    calculate_grouped_metrics,
    calculate_failure_reasons_breakdown,
    calculate_hourly_metrics,
    calculate_dow_metrics,
)

logger = logging.getLogger(__name__)


def run_full_exploratory_analysis(df: pd.DataFrame = None) -> Dict[str, Any]:
    """
    Run complete exploratory analysis across all dimensions.
    Exports key analytical tables to reports/tables/ and returns structured results.
    """
    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    if df is None:
        df = load_processed_data()

    if "hour_of_day" not in df.columns:
        df = engineer_features(df)

    results = {}

    # 1. Overall KPIs
    kpis = calculate_overall_kpis(df)
    kpis_df = pd.DataFrame([{"Metric": k, "Value": str(v)} for k, v in kpis.items()])
    kpis_df.to_csv(TABLES_DIR / "kpi_summary.csv", index=False)
    results["overall_kpis"] = kpis

    # 2. Payment Method Analysis
    pm_df = calculate_grouped_metrics(df, "payment_method")
    pm_df.to_csv(TABLES_DIR / "payment_method_summary.csv", index=False)
    results["payment_method"] = pm_df

    # 3. Bank Switch Analysis
    bank_df = calculate_grouped_metrics(df, "bank_switch")
    bank_df.to_csv(TABLES_DIR / "bank_switch_summary.csv", index=False)
    results["bank_switch"] = bank_df

    # 4. Bank x Payment Method Matrix (Cross-tab)
    def cross_tab_agg(sub):
        tot = len(sub)
        fail = (sub["transaction_status"] == "FAILED").sum()
        rate = (fail / tot * 100.0) if tot > 0 else 0.0
        return pd.Series({
            "total": tot,
            "failed": fail,
            "failure_rate_pct": np.round(rate, 2),
            "avg_latency": np.round(sub["latency_ms"].mean(), 2)
        })

    matrix_raw = df.groupby(["bank_switch", "payment_method"]).apply(cross_tab_agg, include_groups=False).reset_index()
    matrix_pivoted = matrix_raw.pivot(index="bank_switch", columns="payment_method", values="failure_rate_pct")
    matrix_pivoted.to_csv(TABLES_DIR / "bank_payment_method_matrix.csv")
    results["bank_method_matrix"] = matrix_pivoted

    # 5. Failure Reasons Breakdown
    reasons_df = calculate_failure_reasons_breakdown(df)
    reasons_df.to_csv(TABLES_DIR / "failure_reasons_summary.csv", index=False)
    results["failure_reasons"] = reasons_df

    # 6. Hourly Patterns
    hourly_df = calculate_hourly_metrics(df)
    hourly_df.to_csv(TABLES_DIR / "hourly_summary.csv", index=False)
    results["hourly"] = hourly_df

    # 7. Day of Week Patterns
    dow_df = calculate_dow_metrics(df)
    dow_df.to_csv(TABLES_DIR / "dow_summary.csv", index=False)
    results["dow"] = dow_df

    # 8. Amount Band Analysis
    amt_df = calculate_grouped_metrics(df, "amount_band")
    amt_df.to_csv(TABLES_DIR / "amount_band_summary.csv", index=False)
    results["amount_band"] = amt_df

    # 9. Latency Band Analysis
    lat_df = calculate_grouped_metrics(df, "latency_band")
    lat_df.to_csv(TABLES_DIR / "latency_band_summary.csv", index=False)
    results["latency_band"] = lat_df

    # 10. Merchant Category Analysis
    cat_df = calculate_grouped_metrics(df, "merchant_category")
    cat_df.to_csv(TABLES_DIR / "merchant_category_summary.csv", index=False)
    results["merchant_category"] = cat_df

    # 11. Geography Analysis
    geo_df = calculate_grouped_metrics(df, "geography")
    geo_df.to_csv(TABLES_DIR / "geography_summary.csv", index=False)
    results["geography"] = geo_df

    # 12. Peak Hour Deep Dive (20:00 to 22:59 vs. Off-Peak by Bank)
    peak_df = df[df["is_peak_window"] == 1]
    offpeak_df = df[df["is_peak_window"] == 0]

    peak_bank = peak_df.groupby("bank_switch").agg(
        peak_total=("transaction_id", "count"),
        peak_failed=("is_failed", "sum"),
        peak_avg_latency=("latency_ms", "mean"),
        peak_p95_latency=("latency_ms", lambda x: x.quantile(0.95))
    )
    peak_bank["peak_failure_rate_pct"] = np.round((peak_bank["peak_failed"] / peak_bank["peak_total"]) * 100.0, 2)

    offpeak_bank = offpeak_df.groupby("bank_switch").agg(
        offpeak_total=("transaction_id", "count"),
        offpeak_failed=("is_failed", "sum"),
        offpeak_avg_latency=("latency_ms", "mean"),
        offpeak_p95_latency=("latency_ms", lambda x: x.quantile(0.95))
    )
    offpeak_bank["offpeak_failure_rate_pct"] = np.round((offpeak_bank["offpeak_failed"] / offpeak_bank["offpeak_total"]) * 100.0, 2)

    peak_comparison = peak_bank.join(offpeak_bank)
    peak_comparison["failure_rate_delta_pct"] = np.round(
        peak_comparison["peak_failure_rate_pct"] - peak_comparison["offpeak_failure_rate_pct"], 2
    )
    peak_comparison["latency_delta_ms"] = np.round(
        peak_comparison["peak_avg_latency"] - peak_comparison["offpeak_avg_latency"], 2
    )
    peak_comparison.to_csv(TABLES_DIR / "peak_hour_comparison.csv")
    results["peak_hour_comparison"] = peak_comparison

    logger.info("Exploratory analysis complete. All summary tables exported to reports/tables/.")
    return results


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    res = run_full_exploratory_analysis()
    print("=" * 60)
    print("EDA COMPLETE: KEY OBSERVATIONS")
    print("=" * 60)
    print("\nOverall KPIs:")
    for k, v in res["overall_kpis"].items():
        print(f"  {k}: {v}")
    print("\nBank Switch Performance:")
    print(res["bank_switch"][["bank_switch", "total_transactions", "failed_transactions", "failure_rate_pct", "avg_latency_ms"]])
    print("\nPeak Hour Comparison (Peak 20-22 vs Offpeak):")
    print(res["peak_hour_comparison"][["peak_failure_rate_pct", "offpeak_failure_rate_pct", "failure_rate_delta_pct", "latency_delta_ms"]])
