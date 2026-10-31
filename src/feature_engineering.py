"""
Feature Engineering and Operational Telemetry Enrichment.
Digital Payment Failure Analysis
"""

import logging
from typing import Tuple
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate derived analytical features from cleaned payment transactions.
    Supports temporal analysis, ticket size segmentation, and latency categorization.
    """
    logger.info("Engineering features for payment transactions...")
    df = df.copy()

    # 1. Temporal Features
    ts = pd.to_datetime(df["transaction_timestamp"])
    df["transaction_date"] = ts.dt.date.astype(str)
    df["hour_of_day"] = ts.dt.hour
    df["day_of_week"] = ts.dt.day_name()
    df["day_of_week_num"] = ts.dt.day_of_week  # 0=Monday, 6=Sunday
    df["is_weekend"] = df["day_of_week_num"].isin([5, 6]).astype(int)

    # Time of Day Buckets
    def categorize_time_of_day(hour: int) -> str:
        if 6 <= hour < 12:
            return "Morning (06-12)"
        elif 12 <= hour < 17:
            return "Afternoon (12-17)"
        elif 17 <= hour < 23:
            return "Evening (17-23)"
        else:
            return "Night (23-06)"

    df["time_of_day_bucket"] = df["hour_of_day"].apply(categorize_time_of_day)

    # Peak Switch Window Flag (Known high congestion window: 20:00 to 22:59)
    df["is_peak_window"] = df["hour_of_day"].isin([20, 21, 22]).astype(int)

    # 2. Amount Bands (Defensible retail payment tiers)
    amount_bins = [-np.inf, 500, 1500, 5000, np.inf]
    amount_labels = ["Micro (< 500 INR)", "Low (500-1500 INR)", "Medium (1.5K-5K INR)", "High (> 5K INR)"]
    df["amount_band"] = pd.cut(
        df["transaction_amount"],
        bins=amount_bins,
        labels=amount_labels,
        right=True
    ).astype(str)

    # 3. Latency Operational Bands (SLA Thresholds)
    # Fast (< 800ms), Normal (800 - 1500ms), Degraded (1500 - 3000ms), Critical (> 3000ms)
    latency_bins = [-np.inf, 800, 1500, 3000, np.inf]
    latency_labels = ["Fast (<800ms)", "Normal (800-1500ms)", "Degraded (1500-3000ms)", "Critical (>3000ms)"]
    df["latency_band"] = pd.cut(
        df["latency_ms"],
        bins=latency_bins,
        labels=latency_labels,
        right=True
    ).astype(str)

    # 4. Binary Failure Indicator
    df["is_failed"] = (df["transaction_status"] == "FAILED").astype(int)

    # 5. Failure Mode High-Level Category
    def categorize_failure_mode(row) -> str:
        status = row["transaction_status"]
        reason = str(row["failure_reason"])
        if status == "SUCCESS":
            return "None (Success)"
        elif "Low Balance" in reason or "Insufficient" in str(row.get("error_code", "")):
            return "Business / Customer Decline"
        elif "Unresponsive" in reason or "Timeout" in str(row.get("error_code", "")):
            return "Technical / Switch Timeout"
        else:
            return "Technical / Network & Auth Drop"

    df["failure_mode"] = df.apply(categorize_failure_mode, axis=1)

    logger.info(f"Engineered features successfully. Total columns now: {df.shape[1]}.")
    return df


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    from src.data_loader import load_processed_data
    df = load_processed_data()
    featured_df = engineer_features(df)
    print("=" * 60)
    print("FEATURE ENGINEERING COMPLETE")
    print("=" * 60)
    print(f"Features: {featured_df.columns.tolist()}")
    print("\nAmount Bands Distribution:")
    print(featured_df["amount_band"].value_counts())
    print("\nLatency Bands Distribution:")
    print(featured_df["latency_band"].value_counts())
    print("\nFailure Modes Distribution:")
    print(featured_df["failure_mode"].value_counts())
