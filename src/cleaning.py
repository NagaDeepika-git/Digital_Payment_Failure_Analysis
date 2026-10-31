"""
Reproducible Data Cleaning and Normalization Pipeline.
Digital Payment Failure Analysis
"""

import logging
from pathlib import Path
from typing import Tuple, Dict, Any
import numpy as np
import pandas as pd

from src.config import RAW_DATA_PATH, PROCESSED_DATA_PATH, TABLES_DIR
from src.data_loader import load_raw_data

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def clean_payment_data(
    raw_df: pd.DataFrame = None,
    output_path: Path = PROCESSED_DATA_PATH
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Execute end-to-end cleaning and standardization on the raw payment transactions dataset.
    Preserves raw data and writes validated output to output_path.
    """
    if raw_df is None:
        raw_df = load_raw_data(RAW_DATA_PATH)

    logger.info("Starting data cleaning pipeline...")
    df = raw_df.copy()
    initial_rows, initial_cols = df.shape
    audit_log = {
        "initial_rows": initial_rows,
        "initial_columns": initial_cols,
        "transformations": []
    }

    # Step 1: Standardize Column Names
    old_columns = df.columns.tolist()
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
    )
    new_columns = df.columns.tolist()
    audit_log["transformations"].append({
        "step": "column_standardization",
        "detail": f"Standardized {len(old_columns)} column names to lower snake_case."
    })

    # Step 2: Remove Complete Duplicate Rows
    dup_count = int(df.duplicated().sum())
    if dup_count > 0:
        df = df.drop_duplicates()
    audit_log["transformations"].append({
        "step": "duplicate_row_removal",
        "detail": f"Investigated duplicates. Removed {dup_count} exact duplicate rows."
    })

    # Step 3: Transaction ID Deduplication
    txn_id_col = "transaction_id"
    dup_txn_count = int(df[txn_id_col].duplicated().sum())
    if dup_txn_count > 0:
        df = df.drop_duplicates(subset=[txn_id_col], keep="first")
    audit_log["transformations"].append({
        "step": "transaction_id_deduplication",
        "detail": f"Investigated duplicate transaction IDs. Dropped {dup_txn_count} duplicates."
    })

    # Step 4: String Columns Trimming and Normalization
    string_cols = [
        "transaction_id", "customer_id", "payment_method",
        "bank_switch", "merchant_name", "merchant_category",
        "geography", "transaction_status", "error_code"
    ]
    for col in string_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # Step 5: Timestamp Parsing & Validation
    df["transaction_timestamp"] = pd.to_datetime(
        df["transaction_timestamp"],
        errors="coerce",
        format="%Y-%m-%d %H:%M:%S"
    )
    invalid_ts = int(df["transaction_timestamp"].isnull().sum())
    if invalid_ts > 0:
        logger.warning(f"Found {invalid_ts} invalid timestamps. Dropping unparseable records.")
        df = df.dropna(subset=["transaction_timestamp"])
    audit_log["transformations"].append({
        "step": "timestamp_parsing",
        "detail": f"Parsed transaction_timestamp to datetime64[ns]. Found {invalid_ts} invalid dates."
    })

    # Step 6: Normalizing Statuses and Handling Failure Reason
    df["transaction_status"] = df["transaction_status"].str.upper()
    
    # Clean failure_reason: For SUCCESS, explicitly assign string 'None' instead of NaN
    if "failure_reason" in df.columns:
        df["failure_reason"] = df["failure_reason"].fillna("None").astype(str).str.strip()
        # Ensure that if status is SUCCESS, failure_reason is guaranteed 'None'
        df.loc[df["transaction_status"] == "SUCCESS", "failure_reason"] = "None"
        df.loc[df["transaction_status"] == "SUCCESS", "error_code"] = "SUCCESS_00"

    audit_log["transformations"].append({
        "step": "status_and_reason_normalization",
        "detail": "Standardized status labels. Assigned 'None' string to failure_reason for SUCCESS transactions."
    })

    # Step 7: Numeric Validations (Non-destructive checking)
    df["transaction_amount"] = pd.to_numeric(df["transaction_amount"], errors="coerce")
    df["latency_ms"] = pd.to_numeric(df["latency_ms"], errors="coerce")

    invalid_amounts = int((df["transaction_amount"].isnull() | (df["transaction_amount"] <= 0)).sum())
    invalid_latencies = int((df["latency_ms"].isnull() | (df["latency_ms"] < 0)).sum())

    if invalid_amounts > 0:
        logger.warning(f"Filtering out {invalid_amounts} invalid transaction amounts.")
        df = df[df["transaction_amount"] > 0]
    if invalid_latencies > 0:
        logger.warning(f"Filtering out {invalid_latencies} invalid latencies.")
        df = df[df["latency_ms"] >= 0]

    audit_log["transformations"].append({
        "step": "numeric_validation",
        "detail": f"Validated amount and latency ranges. Invalid amounts: {invalid_amounts}, Invalid latencies: {invalid_latencies}."
    })

    # Final Record Count
    final_rows, final_cols = df.shape
    audit_log["final_rows"] = final_rows
    audit_log["final_columns"] = final_cols
    audit_log["rows_dropped"] = initial_rows - final_rows

    # Export Processed Dataset if requested
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info(f"Cleaned dataset saved to {output_path} ({final_rows} rows, {final_cols} columns).")

    # Save Cleaning Audit Summary
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    audit_summary_df = pd.DataFrame([
        {"Step": "Raw Input Records", "Metric": "Row Count", "Value": str(initial_rows)},
        {"Step": "Raw Input Attributes", "Metric": "Column Count", "Value": str(initial_cols)},
        {"Step": "Exact Duplicate Rows", "Metric": "Removed", "Value": str(dup_count)},
        {"Step": "Duplicate Transaction IDs", "Metric": "Removed", "Value": str(dup_txn_count)},
        {"Step": "Invalid Timestamps", "Metric": "Removed", "Value": str(invalid_ts)},
        {"Step": "Invalid Amounts (<=0)", "Metric": "Removed", "Value": str(invalid_amounts)},
        {"Step": "Invalid Latency (<0)", "Metric": "Removed", "Value": str(invalid_latencies)},
        {"Step": "Final Cleaned Records", "Metric": "Row Count", "Value": str(final_rows)},
        {"Step": "Data Retention Rate", "Metric": "Percentage", "Value": f"{(final_rows/initial_rows)*100:.2f}%"}
    ])
    audit_summary_df.to_csv(TABLES_DIR / "cleaning_audit_summary.csv", index=False)

    return df, audit_log


if __name__ == "__main__":
    df, log = clean_payment_data()
    print("=" * 60)
    print("DATA CLEANING COMPLETE")
    print("=" * 60)
    print(f"Initial Rows: {log['initial_rows']} -> Final Rows: {log['final_rows']}")
    print(f"Total Dropped: {log['rows_dropped']}")
    for t in log["transformations"]:
        print(f" - [{t['step']}]: {t['detail']}")
