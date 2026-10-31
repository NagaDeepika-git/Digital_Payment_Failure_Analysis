"""
End-to-end integration tests for the full analytics pipeline.
"""

import pytest
import pandas as pd
from pathlib import Path

from src.cleaning import clean_payment_data
from src.validation import run_all_validations
from src.feature_engineering import engineer_features
from src.metrics import calculate_overall_kpis
from src.analysis import run_full_exploratory_analysis
from src.statistics_analysis import run_statistical_analysis
from src.database import load_data_to_sqlite, verify_python_sql_consistency


def test_full_pipeline_integration(sample_raw_dataframe, tmp_path):
    """Test full analytics lifecycle on test fixture."""
    # 1. Clean
    cleaned_df, clean_log = clean_payment_data(sample_raw_dataframe, output_path=None)
    assert len(cleaned_df) == 20
    assert clean_log["final_rows"] == 20

    # 2. Validate
    passed, errors = run_all_validations(cleaned_df)
    assert passed is True

    # 3. Engineer Features
    featured_df = engineer_features(cleaned_df)
    assert "hour_of_day" in featured_df.columns
    assert "amount_band" in featured_df.columns
    assert "latency_band" in featured_df.columns

    # 4. Overall KPIs
    kpis = calculate_overall_kpis(featured_df)
    assert kpis["total_transactions"] == 20
    assert kpis["failed_transactions"] == 5

    # 5. Exploratory Analysis
    eda_res = run_full_exploratory_analysis(featured_df)
    assert "payment_method" in eda_res
    assert "bank_switch" in eda_res
    assert "peak_hour_comparison" in eda_res

    # 6. Statistical Analysis
    stat_res = run_statistical_analysis(featured_df)
    assert len(stat_res["confidence_intervals"]) > 0
    assert len(stat_res["hypothesis_tests"]) > 0

    # 7. SQLite Load & Consistency
    test_db = tmp_path / "integration_test.db"
    load_data_to_sqlite(featured_df, db_path=test_db)
    consistency = verify_python_sql_consistency(featured_df, db_path=test_db)
    assert consistency["all_consistent"] is True
