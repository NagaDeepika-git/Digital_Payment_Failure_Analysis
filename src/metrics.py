"""
KPI and Operational Metric Calculation Engine.
Digital Payment Failure Analysis
"""

import logging
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

from src.config import ELIGIBLE_STATUSES

logger = logging.getLogger(__name__)


def calculate_overall_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute platform-wide executive KPIs with strict zero-denominator safeguards.
    """
    if df is None or len(df) == 0:
        return {
            "total_transactions": 0,
            "eligible_transactions": 0,
            "successful_transactions": 0,
            "failed_transactions": 0,
            "failure_rate_pct": 0.0,
            "success_rate_pct": 0.0,
            "total_tpv_inr": 0.0,
            "failed_tpv_inr": 0.0,
            "successful_tpv_inr": 0.0,
            "avg_ticket_inr": 0.0,
            "median_ticket_inr": 0.0,
            "avg_latency_ms": 0.0,
            "median_latency_ms": 0.0,
            "p90_latency_ms": 0.0,
            "p95_latency_ms": 0.0,
            "p99_latency_ms": 0.0,
            "date_start": None,
            "date_end": None,
        }

    total_count = len(df)
    
    # Filter for eligible terminal statuses
    status_series = df["transaction_status"].astype(str).str.upper()
    eligible_df = df[status_series.isin(ELIGIBLE_STATUSES)]
    eligible_count = len(eligible_df)

    success_df = df[status_series == "SUCCESS"]
    failed_df = df[status_series == "FAILED"]

    success_count = len(success_df)
    failed_count = len(failed_df)

    failure_rate = (failed_count / eligible_count * 100.0) if eligible_count > 0 else 0.0
    success_rate = (success_count / eligible_count * 100.0) if eligible_count > 0 else 0.0

    total_tpv = float(df["transaction_amount"].sum())
    failed_tpv = float(failed_df["transaction_amount"].sum())
    success_tpv = float(success_df["transaction_amount"].sum())

    avg_ticket = float(df["transaction_amount"].mean())
    median_ticket = float(df["transaction_amount"].median())

    latencies = df["latency_ms"].dropna()
    avg_latency = float(latencies.mean()) if len(latencies) > 0 else 0.0
    median_latency = float(latencies.median()) if len(latencies) > 0 else 0.0
    p90_lat = float(latencies.quantile(0.90)) if len(latencies) > 0 else 0.0
    p95_lat = float(latencies.quantile(0.95)) if len(latencies) > 0 else 0.0
    p99_lat = float(latencies.quantile(0.99)) if len(latencies) > 0 else 0.0

    ts_col = df["transaction_timestamp"]
    date_start = str(ts_col.min()) if len(df) > 0 else None
    date_end = str(ts_col.max()) if len(df) > 0 else None

    return {
        "total_transactions": int(total_count),
        "eligible_transactions": int(eligible_count),
        "successful_transactions": int(success_count),
        "failed_transactions": int(failed_count),
        "failure_rate_pct": float(np.round(failure_rate, 2)),
        "success_rate_pct": float(np.round(success_rate, 2)),
        "total_tpv_inr": float(np.round(total_tpv, 2)),
        "failed_tpv_inr": float(np.round(failed_tpv, 2)),
        "successful_tpv_inr": float(np.round(success_tpv, 2)),
        "avg_ticket_inr": float(np.round(avg_ticket, 2)),
        "median_ticket_inr": float(np.round(median_ticket, 2)),
        "avg_latency_ms": float(np.round(avg_latency, 2)),
        "median_latency_ms": float(np.round(median_latency, 2)),
        "p90_latency_ms": float(np.round(p90_lat, 2)),
        "p95_latency_ms": float(np.round(p95_lat, 2)),
        "p99_latency_ms": float(np.round(p99_lat, 2)),
        "date_start": date_start,
        "date_end": date_end,
    }


def calculate_grouped_metrics(
    df: pd.DataFrame,
    group_col: str,
    min_volume: int = 1
) -> pd.DataFrame:
    """
    Calculate weighted group failure rates and volume breakdowns.
    Ensures group failure rate = sum(failures) / sum(total), not an unweighted mean.
    """
    if df is None or len(df) == 0:
        return pd.DataFrame(columns=[
            group_col, "total_transactions", "successful_transactions",
            "failed_transactions", "failure_rate_pct", "success_rate_pct",
            "total_tpv_inr", "failed_tpv_inr", "avg_latency_ms", "p95_latency_ms"
        ])

    def agg_fn(sub_df):
        total = len(sub_df)
        success = (sub_df["transaction_status"] == "SUCCESS").sum()
        failed = (sub_df["transaction_status"] == "FAILED").sum()
        fail_rate = (failed / total * 100.0) if total > 0 else 0.0
        succ_rate = (success / total * 100.0) if total > 0 else 0.0
        tot_tpv = sub_df["transaction_amount"].sum()
        fail_tpv = sub_df.loc[sub_df["transaction_status"] == "FAILED", "transaction_amount"].sum()
        avg_lat = sub_df["latency_ms"].mean()
        p95_lat = sub_df["latency_ms"].quantile(0.95)

        return pd.Series({
            "total_transactions": total,
            "successful_transactions": success,
            "failed_transactions": failed,
            "failure_rate_pct": np.round(fail_rate, 2),
            "success_rate_pct": np.round(succ_rate, 2),
            "total_tpv_inr": np.round(tot_tpv, 2),
            "failed_tpv_inr": np.round(fail_tpv, 2),
            "avg_latency_ms": np.round(avg_lat, 2),
            "p95_latency_ms": np.round(p95_lat, 2),
        })

    grouped = df.groupby(group_col, as_index=False).apply(agg_fn, include_groups=False)
    
    # Filter min volume if requested
    if min_volume > 1:
        grouped = grouped[grouped["total_transactions"] >= min_volume]

    return grouped.sort_values(by="failed_transactions", ascending=False).reset_index(drop=True)


def calculate_failure_reasons_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """
    Produce a ranked breakdown of failure reasons and error codes among failed transactions.
    """
    if df is None or len(df) == 0:
        return pd.DataFrame(columns=[
            "failure_reason", "error_code", "failed_count",
            "failed_tpv_inr", "share_of_failures_pct", "share_of_platform_pct"
        ])

    total_platform_txns = len(df)
    failed_df = df[df["transaction_status"] == "FAILED"]
    total_failures = len(failed_df)

    if total_failures == 0:
        return pd.DataFrame(columns=[
            "failure_reason", "error_code", "failed_count",
            "failed_tpv_inr", "share_of_failures_pct", "share_of_platform_pct"
        ])

    breakdown = (
        failed_df.groupby(["failure_reason", "error_code"], as_index=False)
        .agg(
            failed_count=("transaction_id", "count"),
            failed_tpv_inr=("transaction_amount", lambda x: np.round(x.sum(), 2)),
            avg_latency_ms=("latency_ms", lambda x: np.round(x.mean(), 2)),
            p95_latency_ms=("latency_ms", lambda x: np.round(x.quantile(0.95), 2))
        )
    )

    breakdown["share_of_failures_pct"] = np.round((breakdown["failed_count"] / total_failures) * 100.0, 2)
    breakdown["share_of_platform_pct"] = np.round((breakdown["failed_count"] / total_platform_txns) * 100.0, 2)

    return breakdown.sort_values(by="failed_count", ascending=False).reset_index(drop=True)


def calculate_hourly_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate hour-by-hour transaction volumes, failure rates, and latencies."""
    if "hour_of_day" not in df.columns:
        ts = pd.to_datetime(df["transaction_timestamp"])
        df = df.copy()
        df["hour_of_day"] = ts.dt.hour

    return calculate_grouped_metrics(df, "hour_of_day").sort_values(by="hour_of_day").reset_index(drop=True)


def calculate_dow_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate day-of-week transaction volumes, failure rates, and latencies."""
    if "day_of_week" not in df.columns:
        ts = pd.to_datetime(df["transaction_timestamp"])
        df = df.copy()
        df["day_of_week"] = ts.dt.day_name()
        df["day_of_week_num"] = ts.dt.day_of_week

    dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    metrics = calculate_grouped_metrics(df, "day_of_week")
    metrics["dow_cat"] = pd.Categorical(metrics["day_of_week"], categories=dow_order, ordered=True)
    return metrics.sort_values(by="dow_cat").drop(columns=["dow_cat"]).reset_index(drop=True)
