"""
SQLite Analytical Database Management & Query Engine.
Digital Payment Failure Analysis
"""

import sqlite3
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

from src.config import DATABASE_PATH, SCHEMA_SQL_PATH, ANALYSIS_SQL_PATH
from src.data_loader import load_processed_data
from src.feature_engineering import engineer_features
from src.metrics import calculate_overall_kpis

logger = logging.getLogger(__name__)


def get_db_connection(db_path: Path = DATABASE_PATH) -> sqlite3.Connection:
    """Return an active connection to the SQLite analytics database."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_database(
    db_path: Path = DATABASE_PATH,
    schema_path: Path = SCHEMA_SQL_PATH
) -> None:
    """Initialize SQLite database using schema.sql script."""
    logger.info(f"Initializing database at {db_path} using {schema_path}...")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    with get_db_connection(db_path) as conn:
        conn.executescript(schema_sql)
    logger.info("Database schema and performance indexes initialized successfully.")


def load_data_to_sqlite(
    df: pd.DataFrame = None,
    db_path: Path = DATABASE_PATH,
    table_name: str = "transactions"
) -> int:
    """
    Ingest validated, feature-enriched dataset into the SQLite database.
    Returns the count of rows successfully inserted.
    """
    if df is None:
        df = load_processed_data()

    if "hour_of_day" not in df.columns:
        df = engineer_features(df)

    init_database(db_path)

    logger.info(f"Loading {len(df)} records into table '{table_name}' in {db_path}...")
    with get_db_connection(db_path) as conn:
        df.to_sql(table_name, conn, if_exists="append", index=False)
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        row_count = cursor.fetchone()[0]

    if row_count != len(df):
        raise ValueError(f"Row count mismatch after SQLite load: {len(df)} expected, {row_count} inserted.")

    logger.info(f"Successfully loaded and verified {row_count} records in SQLite.")
    return row_count


def execute_query(
    query: str,
    params: Optional[Tuple] = None,
    db_path: Path = DATABASE_PATH
) -> pd.DataFrame:
    """Execute arbitrary SQL query against SQLite database and return a DataFrame."""
    with get_db_connection(db_path) as conn:
        if params:
            df = pd.read_sql_query(query, conn, params=params)
        else:
            df = pd.read_sql_query(query, conn)
    return df


def parse_named_queries(sql_file_path: Path = ANALYSIS_SQL_PATH) -> Dict[str, str]:
    """Parse analysis_queries.sql to extract named queries prefixed with '-- NAME: <name>'."""
    with open(sql_file_path, "r", encoding="utf-8") as f:
        content = f.read()

    queries = {}
    current_name = None
    current_lines = []

    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("-- NAME:"):
            if current_name and current_lines:
                queries[current_name] = "\n".join(current_lines).strip()
                current_lines = []
            current_name = stripped.replace("-- NAME:", "").strip()
        elif current_name:
            if not stripped.startswith("-- ----------------------------------------------------------"):
                current_lines.append(line)

    if current_name and current_lines:
        queries[current_name] = "\n".join(current_lines).strip()

    return queries


def run_all_analysis_queries(
    db_path: Path = DATABASE_PATH,
    sql_file_path: Path = ANALYSIS_SQL_PATH
) -> Dict[str, pd.DataFrame]:
    """Execute all named analytical SQL queries from analysis_queries.sql."""
    named_queries = parse_named_queries(sql_file_path)
    logger.info(f"Executing {len(named_queries)} named SQL queries from {sql_file_path}...")
    results = {}
    for name, query in named_queries.items():
        results[name] = execute_query(query, db_path=db_path)
    return results


def verify_python_sql_consistency(
    df: pd.DataFrame = None,
    db_path: Path = DATABASE_PATH
) -> Dict[str, Any]:
    """
    Cross-check core KPIs calculated via Python vs. SQL to verify zero divergence.
    """
    if df is None:
        df = load_processed_data()

    py_kpis = calculate_overall_kpis(df)
    sql_df = execute_query(
        """
        SELECT
            COUNT(*) AS total_transactions,
            SUM(CASE WHEN transaction_status = 'FAILED' THEN 1 ELSE 0 END) AS failed_transactions,
            ROUND(SUM(CASE WHEN transaction_status = 'FAILED' THEN 1.0 ELSE 0.0 END) / COUNT(*) * 100.0, 2) AS failure_rate_pct,
            ROUND(SUM(transaction_amount), 2) AS total_tpv_inr,
            ROUND(SUM(CASE WHEN transaction_status = 'FAILED' THEN transaction_amount ELSE 0 END), 2) AS failed_tpv_inr
        FROM transactions;
        """,
        db_path=db_path
    )
    sql_row = sql_df.iloc[0].to_dict()

    comparisons = []
    keys_to_compare = [
        "total_transactions",
        "failed_transactions",
        "failure_rate_pct",
        "total_tpv_inr",
        "failed_tpv_inr"
    ]

    all_matched = True
    for key in keys_to_compare:
        py_val = py_kpis[key]
        sql_val = sql_row[key]
        diff = abs(py_val - sql_val)
        is_match = diff < 0.05
        if not is_match:
            all_matched = False
        comparisons.append({
            "metric": key,
            "python_value": py_val,
            "sql_value": sql_val,
            "difference": float(np.round(diff, 4)),
            "is_consistent": is_match
        })

    report = {
        "all_consistent": all_matched,
        "comparisons": comparisons
    }
    logger.info(f"Python vs. SQL consistency check completed. All matched: {all_matched}.")
    return report


if __name__ == "__main__":
    from src.data_loader import load_processed_data
    df = load_processed_data()
    load_data_to_sqlite(df)
    audit = verify_python_sql_consistency(df)
    print("=" * 60)
    print("PYTHON vs. SQL METRIC AUDIT")
    print("=" * 60)
    print(pd.DataFrame(audit["comparisons"]))
    print("\nConsistency Status: PASSED (100% Agreement)" if audit["all_consistent"] else "FAILED")
