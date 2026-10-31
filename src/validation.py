"""
Data Validation and Assertion Engine.
Digital Payment Failure Analysis
"""

import logging
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np

from src.config import (
    PAYMENT_METHODS,
    BANKS,
    MERCHANTS,
    GEOGRAPHIES,
    ELIGIBLE_STATUSES,
)

logger = logging.getLogger(__name__)


class DataValidationError(Exception):
    """Raised when data validation assertions fail."""
    pass


REQUIRED_COLUMNS = [
    "transaction_id",
    "customer_id",
    "transaction_timestamp",
    "payment_method",
    "bank_switch",
    "merchant_name",
    "merchant_category",
    "geography",
    "transaction_amount",
    "transaction_status",
    "error_code",
    "failure_reason",
    "latency_ms"
]

ALLOWED_ERROR_CODES = {
    "SUCCESS_00",
    "ERR_BANK_TIMEOUT",
    "ERR_INSUFFICIENT_FUNDS",
    "ERR_AUTH_DECLINED",
    "ERR_INVALID_PIN",
    "ERR_GATEWAY_DROP"
}

ALLOWED_FAILURE_REASONS = {
    "None",
    "Bank Switch Unresponsive",
    "Customer Account Low Balance",
    "Authentication / Network Failure"
}


def validate_schema(df: pd.DataFrame) -> bool:
    """Validate that all required columns exist in the DataFrame."""
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise DataValidationError(f"Missing required columns: {missing}")
    return True


def validate_primary_keys(df: pd.DataFrame) -> bool:
    """Validate uniqueness and non-null status of transaction_id."""
    if df["transaction_id"].isnull().any():
        raise DataValidationError("Found null values in transaction_id primary key.")
    if df["transaction_id"].duplicated().any():
        dup_count = df["transaction_id"].duplicated().sum()
        raise DataValidationError(f"Found {dup_count} duplicate transaction_id values.")
    return True


def validate_categorical_domains(df: pd.DataFrame) -> Dict[str, List[str]]:
    """Validate categorical columns against allowed domain lists."""
    unexpected = {}
    # Fill NA for failure_reason with 'None' if standard read_csv coerced string 'None' to NaN
    reasons = df["failure_reason"].fillna("None")

    def check_col(col_name, series, allowed_set):
        actual_set = set(series.dropna().unique())
        diff = actual_set - set(allowed_set)
        if diff:
            unexpected[col_name] = list(diff)

    check_col("payment_method", df["payment_method"], PAYMENT_METHODS)
    check_col("bank_switch", df["bank_switch"], BANKS)
    check_col("merchant_name", df["merchant_name"], MERCHANTS)
    check_col("geography", df["geography"], GEOGRAPHIES)
    check_col("transaction_status", df["transaction_status"], ELIGIBLE_STATUSES)
    check_col("error_code", df["error_code"], ALLOWED_ERROR_CODES)
    check_col("failure_reason", reasons, ALLOWED_FAILURE_REASONS)

    if unexpected:
        raise DataValidationError(f"Unexpected categorical values detected: {unexpected}")
    return unexpected


def validate_numeric_ranges(df: pd.DataFrame) -> bool:
    """Validate that numeric columns fall within realistic physical bounds."""
    # Amount must be strictly positive
    invalid_amounts = (df["transaction_amount"] <= 0) | df["transaction_amount"].isnull()
    if invalid_amounts.any():
        raise DataValidationError(f"Found {invalid_amounts.sum()} records with non-positive transaction amounts.")

    # Latency must be non-negative
    invalid_latencies = (df["latency_ms"] < 0) | df["latency_ms"].isnull()
    if invalid_latencies.any():
        raise DataValidationError(f"Found {invalid_latencies.sum()} records with negative latency values.")
    return True


def validate_status_consistency(df: pd.DataFrame) -> bool:
    """Validate logical consistency between status, error code, and failure reason."""
    # Ensure failure_reason handles default pandas NA coercion
    failure_reasons = df["failure_reason"].fillna("None")

    # Rule 1: SUCCESS must have SUCCESS_00 and None
    success_mask = df["transaction_status"] == "SUCCESS"
    success_err_violations = (success_mask & (df["error_code"] != "SUCCESS_00")).sum()
    success_reason_violations = (success_mask & (failure_reasons != "None")).sum()

    if success_err_violations > 0 or success_reason_violations > 0:
        raise DataValidationError(
            f"Status consistency violation on SUCCESS: {success_err_violations} error code violations, "
            f"{success_reason_violations} failure reason violations."
        )

    # Rule 2: FAILED must NOT have SUCCESS_00 or None
    failed_mask = df["transaction_status"] == "FAILED"
    failed_err_violations = (failed_mask & (df["error_code"] == "SUCCESS_00")).sum()
    failed_reason_violations = (failed_mask & (failure_reasons == "None")).sum()

    if failed_err_violations > 0 or failed_reason_violations > 0:
        raise DataValidationError(
            f"Status consistency violation on FAILED: {failed_err_violations} error code violations, "
            f"{failed_reason_violations} failure reason violations."
        )

    return True


def run_all_validations(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Run complete validation suite.
    Returns (True, []) if all pass, or raises DataValidationError.
    """
    logger.info("Running data validation suite...")
    validate_schema(df)
    validate_primary_keys(df)
    validate_categorical_domains(df)
    validate_numeric_ranges(df)
    validate_status_consistency(df)
    logger.info("All data validation checks passed successfully!")
    return True, []


if __name__ == "__main__":
    from src.config import PROCESSED_DATA_PATH
    df = pd.read_csv(PROCESSED_DATA_PATH)
    success, errors = run_all_validations(df)
    print("=" * 60)
    print("VALIDATION STATUS: PASSED (100% Consistent)")
    print("=" * 60)
