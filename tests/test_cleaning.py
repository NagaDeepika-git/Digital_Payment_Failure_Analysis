"""
Unit tests for data cleaning and validation pipeline.
"""

import pytest
import pandas as pd
import numpy as np

from src.cleaning import clean_payment_data
from src.validation import (
    validate_schema,
    validate_primary_keys,
    validate_categorical_domains,
    validate_numeric_ranges,
    validate_status_consistency,
    run_all_validations,
    DataValidationError,
)


def test_column_standardization(sample_raw_dataframe):
    """Verify that column names are converted to lower snake_case."""
    cleaned_df, _ = clean_payment_data(sample_raw_dataframe, output_path=None)
    for col in cleaned_df.columns:
        assert col == col.lower()
        assert " " not in col


def test_status_and_reason_imputation(sample_raw_dataframe):
    """Verify that SUCCESS rows receive failure_reason='None'."""
    cleaned_df, _ = clean_payment_data(sample_raw_dataframe, output_path=None)
    success_rows = cleaned_df[cleaned_df["transaction_status"] == "SUCCESS"]
    assert (success_rows["failure_reason"] == "None").all()
    assert (success_rows["error_code"] == "SUCCESS_00").all()

    failed_rows = cleaned_df[cleaned_df["transaction_status"] == "FAILED"]
    assert (failed_rows["failure_reason"] != "None").all()
    assert (failed_rows["error_code"] != "SUCCESS_00").all()


def test_duplicate_removal():
    """Verify that exact duplicate rows are removed."""
    df_with_dups = pd.DataFrame({
        "Transaction_id": ["TXN_1", "TXN_1", "TXN_2"],
        "Customer_ID": ["CUST_1", "CUST_1", "CUST_2"],
        "Transaction_Timestamp": ["2026-08-01 12:00:00"] * 3,
        "Payment_Method": ["UPI"] * 3,
        "Bank_Switch": ["HDFC"] * 3,
        "Merchant_Name": ["Amazon"] * 3,
        "Merchant_Category": ["E-Commerce"] * 3,
        "Geography": ["Mumbai"] * 3,
        "Transaction_Amount": [500.0] * 3,
        "Transaction_Status": ["SUCCESS"] * 3,
        "Error_Code": ["SUCCESS_00"] * 3,
        "Failure_Reason": [None] * 3,
        "Latency_ms": [1000] * 3
    })
    cleaned_df, log = clean_payment_data(df_with_dups, output_path=None)
    assert len(cleaned_df) == 2
    assert cleaned_df["transaction_id"].nunique() == 2


def test_numeric_bounds_validation():
    """Verify that negative amounts or latencies are flagged."""
    invalid_df = pd.DataFrame({
        "Transaction_id": ["TXN_1", "TXN_2"],
        "Customer_ID": ["CUST_1", "CUST_2"],
        "Transaction_Timestamp": ["2026-08-01 12:00:00"] * 2,
        "Payment_Method": ["UPI"] * 2,
        "Bank_Switch": ["HDFC"] * 2,
        "Merchant_Name": ["Amazon"] * 2,
        "Merchant_Category": ["E-Commerce"] * 2,
        "Geography": ["Mumbai"] * 2,
        "Transaction_Amount": [-100.0, 500.0],
        "Transaction_Status": ["SUCCESS"] * 2,
        "Error_Code": ["SUCCESS_00"] * 2,
        "Failure_Reason": [None] * 2,
        "Latency_ms": [1000, -50]
    })
    cleaned_df, _ = clean_payment_data(invalid_df, output_path=None)
    # The negative amount and negative latency rows must be filtered out
    assert len(cleaned_df) == 0


def test_validation_engine_pass(sample_cleaned_dataframe):
    """Verify that valid cleaned DataFrame passes all assertions."""
    passed, errors = run_all_validations(sample_cleaned_dataframe)
    assert passed is True
    assert len(errors) == 0


def test_validation_engine_missing_columns():
    """Verify that missing schema columns raise DataValidationError."""
    incomplete_df = pd.DataFrame({"transaction_id": ["TXN_1"]})
    with pytest.raises(DataValidationError):
        validate_schema(incomplete_df)


def test_validation_engine_status_inconsistency(sample_cleaned_dataframe):
    """Verify that corrupted error codes trigger DataValidationError."""
    corrupted_df = sample_cleaned_dataframe.copy()
    corrupted_df.loc[0, "transaction_status"] = "SUCCESS"
    corrupted_df.loc[0, "error_code"] = "ERR_BANK_TIMEOUT"
    with pytest.raises(DataValidationError):
        validate_status_consistency(corrupted_df)
