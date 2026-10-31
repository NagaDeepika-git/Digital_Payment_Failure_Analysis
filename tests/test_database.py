"""
Unit tests for SQLite database operations and SQL analytics queries.
"""

import pytest
import sqlite3
import pandas as pd
from pathlib import Path

from src.database import (
    init_database,
    load_data_to_sqlite,
    execute_query,
    parse_named_queries,
    verify_python_sql_consistency,
)
from src.config import SCHEMA_SQL_PATH, ANALYSIS_SQL_PATH


@pytest.fixture
def temp_db_path(tmp_path):
    """Provide a path to an isolated temporary SQLite database."""
    return tmp_path / "test_analytics.db"


def test_database_initialization(temp_db_path):
    """Verify that schema.sql creates the transactions table and indexes."""
    init_database(db_path=temp_db_path, schema_path=SCHEMA_SQL_PATH)

    with sqlite3.connect(temp_db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='transactions';")
        assert cursor.fetchone() is not None

        # Verify indexes exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index';")
        indexes = [row[0] for row in cursor.fetchall()]
        assert "idx_txn_timestamp" in indexes
        assert "idx_txn_status" in indexes
        assert "idx_txn_bank_method" in indexes


def test_data_ingestion_and_querying(temp_db_path, sample_cleaned_dataframe):
    """Verify loading records into SQLite and querying them."""
    row_count = load_data_to_sqlite(
        df=sample_cleaned_dataframe,
        db_path=temp_db_path,
        table_name="transactions"
    )
    assert row_count == len(sample_cleaned_dataframe)

    # Query back
    result_df = execute_query("SELECT COUNT(*) AS total FROM transactions;", db_path=temp_db_path)
    assert result_df["total"].iloc[0] == 20


def test_named_queries_execution(temp_db_path, sample_cleaned_dataframe):
    """Verify that all queries in analysis_queries.sql parse and execute without syntax errors."""
    load_data_to_sqlite(df=sample_cleaned_dataframe, db_path=temp_db_path)
    queries = parse_named_queries(ANALYSIS_SQL_PATH)

    assert len(queries) >= 7

    for name, sql in queries.items():
        res = execute_query(sql, db_path=temp_db_path)
        assert isinstance(res, pd.DataFrame), f"Query '{name}' did not return a DataFrame."
        assert len(res) >= 0


def test_python_sql_consistency_assertion(temp_db_path, sample_cleaned_dataframe):
    """Verify that Python KPIs match SQL KPIs within tolerance."""
    load_data_to_sqlite(df=sample_cleaned_dataframe, db_path=temp_db_path)
    audit = verify_python_sql_consistency(df=sample_cleaned_dataframe, db_path=temp_db_path)

    assert audit["all_consistent"] is True
    for comp in audit["comparisons"]:
        assert comp["is_consistent"] is True
        assert comp["difference"] < 0.05
