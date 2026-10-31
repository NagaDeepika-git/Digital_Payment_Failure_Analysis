"""
Unit tests for KPI calculations and metric aggregations.
"""

import pytest
import pandas as pd
import numpy as np

from src.metrics import (
    calculate_overall_kpis,
    calculate_grouped_metrics,
    calculate_failure_reasons_breakdown,
    calculate_hourly_metrics,
    calculate_dow_metrics,
)


def test_overall_kpis_calculation(sample_cleaned_dataframe):
    """Test KPI calculations against known ground-truth values."""
    kpis = calculate_overall_kpis(sample_cleaned_dataframe)

    assert kpis["total_transactions"] == 20
    assert kpis["eligible_transactions"] == 20
    assert kpis["successful_transactions"] == 15
    assert kpis["failed_transactions"] == 5
    assert kpis["failure_rate_pct"] == 25.0  # (5 / 20) * 100
    assert kpis["success_rate_pct"] == 75.0  # (15 / 20) * 100
    assert kpis["total_tpv_inr"] > 0
    assert kpis["failed_tpv_inr"] > 0
    assert kpis["avg_latency_ms"] > 0


def test_zero_denominator_safeguard():
    """Test that empty or zero-eligible DataFrame returns safe zero metrics."""
    empty_df = pd.DataFrame(columns=[
        "transaction_id", "transaction_status", "transaction_amount", "latency_ms", "transaction_timestamp"
    ])
    kpis = calculate_overall_kpis(empty_df)

    assert kpis["total_transactions"] == 0
    assert kpis["eligible_transactions"] == 0
    assert kpis["failure_rate_pct"] == 0.0
    assert kpis["success_rate_pct"] == 0.0
    assert kpis["total_tpv_inr"] == 0.0


def test_grouped_metrics_weighted_rate(sample_cleaned_dataframe):
    """Test that group failure rate is properly weighted by transaction volume."""
    grouped = calculate_grouped_metrics(sample_cleaned_dataframe, "bank_switch")

    for _, row in grouped.iterrows():
        expected_rate = round((row["failed_transactions"] / row["total_transactions"]) * 100.0, 2)
        assert row["failure_rate_pct"] == expected_rate


def test_failure_reasons_breakdown(sample_cleaned_dataframe):
    """Test that failure reason breakdown covers 100% of failed transactions."""
    breakdown = calculate_failure_reasons_breakdown(sample_cleaned_dataframe)

    assert len(breakdown) > 0
    assert breakdown["failed_count"].sum() == 5  # Total failures in sample fixture
    assert abs(breakdown["share_of_failures_pct"].sum() - 100.0) < 0.1


def test_hourly_metrics_structure(sample_cleaned_dataframe):
    """Test hourly metrics calculation and ordering."""
    hourly = calculate_hourly_metrics(sample_cleaned_dataframe)
    assert "hour_of_day" in hourly.columns
    assert "failure_rate_pct" in hourly.columns
    assert len(hourly) > 0


def test_dow_metrics_structure(sample_cleaned_dataframe):
    """Test day of week metrics calculation."""
    dow = calculate_dow_metrics(sample_cleaned_dataframe)
    assert "day_of_week" in dow.columns
    assert "failure_rate_pct" in dow.columns
