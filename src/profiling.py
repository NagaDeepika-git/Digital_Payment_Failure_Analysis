"""
Automated Data Profiling and Quality Assessment.
Digital Payment Failure Analysis
"""

import logging
from pathlib import Path
from typing import Dict, Any
import numpy as np
import pandas as pd

from src.config import RAW_DATA_PATH, TABLES_DIR
from src.data_loader import load_raw_data

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def profile_raw_data(df: pd.DataFrame = None) -> Dict[str, Any]:
    """
    Perform a comprehensive, non-destructive audit of the raw dataset.
    Returns a dictionary of profiling metrics and data-quality findings.
    """
    if df is None:
        df = load_raw_data(RAW_DATA_PATH)

    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    report = {}

    # 1. Dimensions
    n_rows, n_cols = df.shape
    report["dimensions"] = {
        "total_rows": int(n_rows),
        "total_columns": int(n_cols),
    }

    # 2. Missing Values Analysis
    missing_counts = df.isnull().sum()
    missing_pct = (missing_counts / n_rows) * 100
    missing_df = pd.DataFrame({
        "column": df.columns,
        "dtype": [str(t) for t in df.dtypes],
        "missing_count": missing_counts.values,
        "missing_percent": np.round(missing_pct.values, 2)
    })
    missing_df.to_csv(TABLES_DIR / "raw_missingness.csv", index=False)
    report["missingness"] = missing_df.to_dict(orient="records")

    # 3. Duplicate Analysis
    exact_duplicates = int(df.duplicated().sum())
    txn_id_col = [c for c in df.columns if "transaction_id" in c.lower()][0]
    duplicate_txn_ids = int(df[txn_id_col].duplicated().sum())
    
    report["duplicates"] = {
        "exact_duplicate_rows": exact_duplicates,
        "duplicate_transaction_ids": duplicate_txn_ids,
        "unique_transaction_ids": int(df[txn_id_col].nunique())
    }

    # 4. Timestamp Validation
    ts_col = [c for c in df.columns if "timestamp" in c.lower()][0]
    try:
        parsed_ts = pd.to_datetime(df[ts_col], errors="coerce")
        invalid_ts_count = int(parsed_ts.isnull().sum())
        min_ts = str(parsed_ts.min())
        max_ts = str(parsed_ts.max())
    except Exception as e:
        invalid_ts_count = n_rows
        min_ts, max_ts = None, None

    report["timestamp_audit"] = {
        "timestamp_column": ts_col,
        "invalid_timestamps": invalid_ts_count,
        "earliest_timestamp": min_ts,
        "latest_timestamp": max_ts
    }

    # 5. Categorical Columns Audit
    categorical_cols = [
        "Payment_Method", "Bank_Switch", "Merchant_Name",
        "Merchant_Category", "Geography", "Transaction_Status",
        "Error_Code", "Failure_Reason"
    ]
    # Case-insensitive lookup
    cat_summary = []
    for target in categorical_cols:
        matched = [c for c in df.columns if c.lower() == target.lower()]
        if matched:
            col = matched[0]
            unique_vals = df[col].dropna().unique().tolist()
            cat_summary.append({
                "column": col,
                "cardinality": int(df[col].nunique()),
                "unique_values": unique_vals[:15],
                "null_count": int(df[col].isnull().sum())
            })
    
    cat_df = pd.DataFrame([
        {
            "column": c["column"],
            "cardinality": c["cardinality"],
            "null_count": c["null_count"],
            "distinct_categories": ", ".join([str(v) for v in c["unique_values"][:8]])
        }
        for c in cat_summary
    ])
    cat_df.to_csv(TABLES_DIR / "raw_categorical_summary.csv", index=False)
    report["categorical_audit"] = cat_summary

    # 6. Numeric Columns Audit
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    num_summary = []
    for col in numeric_cols:
        series = df[col].dropna()
        negative_count = int((series < 0).sum())
        q25, q50, q75 = series.quantile([0.25, 0.50, 0.75]).values
        iqr = q75 - q25
        lower_bound = q25 - 1.5 * iqr
        upper_bound = q75 + 1.5 * iqr
        outlier_count = int(((series < lower_bound) | (series > upper_bound)).sum())

        num_summary.append({
            "column": col,
            "min": float(np.round(series.min(), 2)),
            "mean": float(np.round(series.mean(), 2)),
            "std": float(np.round(series.std(), 2)),
            "q25": float(np.round(q25, 2)),
            "median": float(np.round(q50, 2)),
            "q75": float(np.round(q75, 2)),
            "max": float(np.round(series.max(), 2)),
            "p95": float(np.round(series.quantile(0.95), 2)),
            "p99": float(np.round(series.quantile(0.99), 2)),
            "negative_values": negative_count,
            "outlier_count_iqr": outlier_count
        })

    num_df = pd.DataFrame(num_summary)
    num_df.to_csv(TABLES_DIR / "raw_numeric_summary.csv", index=False)
    report["numeric_audit"] = num_summary

    # 7. Status & Failure Consistency Check
    status_col = [c for c in df.columns if "status" in c.lower()][0]
    reason_col = [c for c in df.columns if "reason" in c.lower()][0]
    error_col = [c for c in df.columns if "error" in c.lower()][0]

    status_dist = df[status_col].value_counts().to_dict()
    report["status_distribution"] = status_dist

    # Consistency: Successful rows should have SUCCESS_00 error code and null reason
    success_mask = df[status_col].astype(str).str.upper() == "SUCCESS"
    success_with_reason = int((success_mask & df[reason_col].notnull()).sum())
    success_with_non00_err = int((success_mask & (df[error_col] != "SUCCESS_00")).sum())
    
    # Consistency: Failed rows should have a non-null failure reason
    failed_mask = df[status_col].astype(str).str.upper() == "FAILED"
    failed_without_reason = int((failed_mask & df[reason_col].isnull()).sum())

    report["consistency_audit"] = {
        "success_with_failure_reason": success_with_reason,
        "success_with_non_success_error_code": success_with_non00_err,
        "failed_missing_failure_reason": failed_without_reason
    }

    # Save Executive Overview Table
    overview_df = pd.DataFrame([
        {"Metric": "Total Records (Rows)", "Value": str(n_rows)},
        {"Metric": "Total Attributes (Columns)", "Value": str(n_cols)},
        {"Metric": "Exact Duplicate Rows", "Value": str(exact_duplicates)},
        {"Metric": "Duplicate Transaction IDs", "Value": str(duplicate_txn_ids)},
        {"Metric": "Invalid / Unparseable Timestamps", "Value": str(invalid_ts_count)},
        {"Metric": "Date Coverage Start", "Value": str(min_ts)},
        {"Metric": "Date Coverage End", "Value": str(max_ts)},
        {"Metric": "Successful Transactions", "Value": f"{status_dist.get('SUCCESS', 0):,} ({status_dist.get('SUCCESS', 0)/n_rows*100:.2f}%)"},
        {"Metric": "Failed Transactions", "Value": f"{status_dist.get('FAILED', 0):,} ({status_dist.get('FAILED', 0)/n_rows*100:.2f}%)"},
        {"Metric": "Consistency Violations", "Value": str(success_with_reason + success_with_non00_err + failed_without_reason)},
    ])
    overview_df.to_csv(TABLES_DIR / "raw_profiling_overview.csv", index=False)

    logger.info("Raw data profiling complete. Summary tables exported to reports/tables/.")
    return report


if __name__ == "__main__":
    report = profile_raw_data()
    print("=" * 60)
    print("RAW DATA PROFILING SUMMARY")
    print("=" * 60)
    print(f"Dimensions: {report['dimensions']}")
    print(f"Duplicates: {report['duplicates']}")
    print(f"Status Breakdown: {report['status_distribution']}")
    print(f"Consistency Audit: {report['consistency_audit']}")
    print(f"Timestamp Coverage: {report['timestamp_audit']}")
