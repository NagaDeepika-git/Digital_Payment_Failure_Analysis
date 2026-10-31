"""
Pytest Test Fixtures and Synthetic Telemetry Data.
Digital Payment Failure Analysis
"""

import pytest
import pandas as pd
import numpy as np


@pytest.fixture
def sample_raw_dataframe():
    """Deterministic 20-row raw DataFrame reflecting the raw schema."""
    return pd.DataFrame({
        "Transaction_id": [f"TXN_{100 + i}" for i in range(20)],
        "Customer_ID": [f"CUST_{10 + (i % 5)}" for i in range(20)],
        "Transaction_Timestamp": [
            f"2026-08-01 {10 + (i % 12):02d}:{i * 2:02d}:00" for i in range(20)
        ],
        "Payment_Method": (["UPI"] * 10) + (["Credit Card"] * 5) + (["Debit Card"] * 3) + (["NetBanking"] * 2),
        "Bank_Switch": (["HDFC"] * 8) + (["SBI"] * 6) + (["ICICI"] * 4) + (["Axis Bank"] * 2),
        "Merchant_Name": ["Amazon", "Flipkart", "Swiggy", "Zomato"] * 5,
        "Merchant_Category": ["E-Commerce", "E-Commerce", "Food & Grocery", "Food & Grocery"] * 5,
        "Geography": ["Mumbai", "Bengaluru", "Delhi", "Pune"] * 5,
        "Transaction_Amount": [500.0 + (i * 100.0) for i in range(20)],
        "Transaction_Status": (["SUCCESS"] * 15) + (["FAILED"] * 5),
        "Error_Code": (["SUCCESS_00"] * 15) + ["ERR_BANK_TIMEOUT", "ERR_INSUFFICIENT_FUNDS", "ERR_AUTH_DECLINED", "ERR_INVALID_PIN", "ERR_GATEWAY_DROP"],
        "Failure_Reason": ([None] * 15) + ["Bank Switch Unresponsive", "Customer Account Low Balance", "Authentication / Network Failure", "Authentication / Network Failure", "Authentication / Network Failure"],
        "Latency_ms": [800 + (i * 50) for i in range(15)] + [5200, 1100, 1050, 1120, 1080]
    })


@pytest.fixture
def sample_cleaned_dataframe(sample_raw_dataframe):
    """Processed and feature-engineered version of the test fixture."""
    from src.cleaning import clean_payment_data
    from src.feature_engineering import engineer_features

    cleaned_df, _ = clean_payment_data(sample_raw_dataframe, output_path=None)
    featured_df = engineer_features(cleaned_df)
    return featured_df
