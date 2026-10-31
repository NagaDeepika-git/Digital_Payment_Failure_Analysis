"""
End-to-End Pipeline Orchestration & Artifact Generator.
Digital Payment Failure Analysis
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging
from typing import Dict, Any
import pandas as pd

from src.data_loader import load_raw_data, load_processed_data
from src.profiling import profile_raw_data
from src.cleaning import clean_payment_data
from src.validation import run_all_validations
from src.feature_engineering import engineer_features
from src.metrics import calculate_overall_kpis
from src.analysis import run_full_exploratory_analysis
from src.statistics_analysis import run_statistical_analysis
from src.database import load_data_to_sqlite, verify_python_sql_consistency, run_all_analysis_queries
from src.charts import export_all_report_figures

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def run_complete_pipeline() -> Dict[str, Any]:
    """
    Execute the entire analytical lifecycle from raw data loading to reporting.
    Guarantees that all artifacts, tables, database records, and figures are freshly computed.
    """
    logger.info("=" * 70)
    logger.info("STARTING COMPLETE END-TO-END ANALYTICS PIPELINE")
    logger.info("=" * 70)

    # 1. Load Raw Data
    logger.info("[Stage 1/8] Loading Raw Dataset...")
    raw_df = load_raw_data()

    # 2. Profile Raw Data
    logger.info("[Stage 2/8] Profiling Raw Dataset & Auditing Quality...")
    profiling_report = profile_raw_data(raw_df)

    # 3. Clean & Normalize Data
    logger.info("[Stage 3/8] Cleaning & Normalizing Data...")
    cleaned_df, cleaning_log = clean_payment_data(raw_df)

    # 4. Validate Cleaned Data
    logger.info("[Stage 4/8] Running Automated Validation Assertions...")
    run_all_validations(cleaned_df)

    # 5. Feature Engineering
    logger.info("[Stage 5/8] Engineering Temporal & Telemetry Features...")
    featured_df = engineer_features(cleaned_df)

    # 6. Exploratory Data Analysis & Table Exports
    logger.info("[Stage 6/8] Executing Multi-Dimensional Exploratory Analysis...")
    eda_results = run_full_exploratory_analysis(featured_df)

    # 7. Statistical Hypothesis Testing
    logger.info("[Stage 7/8] Executing Statistical Hypothesis Testing & Confidence Intervals...")
    stat_results = run_statistical_analysis(featured_df)

    # 8. SQLite Database Ingestion, SQL Queries & Verification
    logger.info("[Stage 8/8] Ingesting into SQLite & Verifying Metric Consistency...")
    load_data_to_sqlite(featured_df)
    consistency_audit = verify_python_sql_consistency(featured_df)
    sql_query_results = run_all_analysis_queries()

    # 9. Chart & Figure Asset Generation
    logger.info("Exporting High-Resolution Visualizations...")
    export_all_report_figures(featured_df)

    logger.info("=" * 70)
    logger.info("ANALYTICS PIPELINE COMPLETED SUCCESSFULLY")
    logger.info("=" * 70)

    return {
        "profiling": profiling_report,
        "cleaning": cleaning_log,
        "eda": eda_results,
        "statistics": stat_results,
        "consistency": consistency_audit,
        "sql_queries": sql_query_results,
    }


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    run_complete_pipeline()
