"""
Unit tests for statistical hypothesis tests and confidence intervals.
"""

import pytest
import numpy as np
import pandas as pd

from src.statistics_analysis import (
    calculate_proportion_confidence_interval,
    cramers_v,
    run_statistical_analysis,
)


def test_wilson_confidence_interval_bounds():
    """Verify Wilson Score CI behavior and mathematical bounds."""
    # Test typical case (50 successes out of 100)
    p, low, high = calculate_proportion_confidence_interval(50, 100, confidence=0.95)
    assert p == 50.0
    assert 0.0 <= low < p < high <= 100.0
    assert abs((high + low) / 2 - 50.0) < 1.0  # Symmetric near 0.5

    # Test edge case: 0 successes
    p_zero, low_zero, high_zero = calculate_proportion_confidence_interval(0, 100)
    assert p_zero == 0.0
    assert low_zero == 0.0
    assert high_zero > 0.0

    # Test edge case: 0 observations
    p_empty, low_empty, high_empty = calculate_proportion_confidence_interval(0, 0)
    assert p_empty == 0.0
    assert low_empty == 0.0
    assert high_empty == 0.0


def test_cramers_v_bounds():
    """Verify Cramer's V effect size calculation."""
    # Perfectly independent table
    indep_table = np.array([[50, 50], [50, 50]])
    v_indep = cramers_v(indep_table)
    assert v_indep == 0.0

    # Strong association table
    assoc_table = np.array([[100, 0], [0, 100]])
    v_assoc = cramers_v(assoc_table)
    assert 0.95 <= v_assoc <= 1.0


def test_statistical_analysis_pipeline(sample_cleaned_dataframe):
    """Verify execution of hypothesis testing engine."""
    results = run_statistical_analysis(sample_cleaned_dataframe)

    assert "confidence_intervals" in results
    assert "hypothesis_tests" in results

    ci_df = results["confidence_intervals"]
    tests_df = results["hypothesis_tests"]

    assert len(ci_df) > 0
    assert len(tests_df) > 0

    # Check that p-values are valid probabilities
    for p_val in tests_df["p_value"]:
        assert 0.0 <= p_val <= 1.0
