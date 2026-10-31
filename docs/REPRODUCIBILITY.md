# Reproducibility Guide: Digital Payment Failure Analysis

This document provides exact, step-by-step instructions to reproduce the entire data analytics pipeline, database generation, automated test suite, and interactive Streamlit dashboard on a clean machine.

---

## 1. System Requirements

* **Operating System:** Windows 10/11, macOS (12+), or Linux (Ubuntu 22.04+).
* **Python Version:** Python 3.10 to 3.13 (Verified on Python 3.13.2 64-bit).
* **Git:** Version 2.40+.
* **Disk Space:** ~50 MB for repository, dependencies, and SQLite database.

---

## 2. Environment Setup

### Windows (PowerShell)
```powershell
# 1. Clone repository
git clone https://github.com/NagaDeepika-git/Digital_Payment_Failure_Analysis.git
cd Digital_Payment_Failure_Analysis

# 2. Create virtual environment
python -m venv .venv

# 3. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 4. Upgrade pip and install pinned dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### macOS / Linux (Bash)
```bash
# 1. Clone repository
git clone https://github.com/NagaDeepika-git/Digital_Payment_Failure_Analysis.git
cd Digital_Payment_Failure_Analysis

# 2. Create virtual environment
python3 -m venv .venv

# 3. Activate virtual environment
source .venv/bin/activate

# 4. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 3. Dataset Acquisition & Ingestion

To acquire the raw 50,000-transaction dataset from the remote source or regenerate it deterministically offline:
```powershell
python -m src.data_loader
```
* **Output:** Creates `data/raw/fintech_payment_transactions.csv` (50,000 records) and `data/sample/sample_transactions.csv` (500 records).

---

## 4. Running the Complete Analytics Pipeline

To run data profiling, cleaning, validation assertions, feature engineering, exploratory analysis, statistical hypothesis testing, SQLite database generation, and visualization exports in a single command:
```powershell
python -m src.reporting
```
* **What this executes:**
  1. Profiles raw data and outputs `reports/tables/raw_profiling_overview.csv`.
  2. Cleans raw data and saves `data/processed/payment_transactions_cleaned.csv`.
  3. Executes assertions in `src/validation.py`.
  4. Generates 11 derived temporal and telemetry features in `src/feature_engineering.py`.
  5. Computes multi-dimensional KPI summaries in `reports/tables/`.
  6. Computes Wilson Score CIs and Chi-square tests in `reports/tables/`.
  7. Populates SQLite database `data/payment_analytics.db` and runs 8 analytical queries.
  8. Verifies 100% agreement between Python calculations and SQL database queries.
  9. Exports 7 interactive visualization HTML files to `reports/figures/`.

---

## 5. Individual Pipeline Stages (Modular Commands)

Each module can also be executed independently:

```powershell
# Profile Raw Data Quality
python -m src.profiling

# Execute Cleaning & Standardization
python -m src.cleaning

# Run Data Validation Assertions
python -m src.validation

# Feature Engineering
python -m src.feature_engineering

# Exploratory Analysis
python -m src.analysis

# Statistical Hypothesis Testing & Confidence Intervals
python -m src.statistics_analysis

# SQLite Database Ingest & Query Verification
python -m src.database

# Generate Interactive Figures
python -m src.charts
```

---

## 6. Running Automated Tests

Run the full pytest suite:
```powershell
pytest -v
```
* **Expected Output:**
  ```
  ============================= test session starts =============================
  collected 21 items

  tests/test_cleaning.py::test_column_standardization PASSED               [  4%]
  tests/test_cleaning.py::test_status_and_reason_imputation PASSED         [  9%]
  tests/test_cleaning.py::test_duplicate_removal PASSED                    [ 14%]
  tests/test_cleaning.py::test_numeric_bounds_validation PASSED            [ 19%]
  tests/test_cleaning.py::test_validation_engine_pass PASSED               [ 23%]
  tests/test_cleaning.py::test_validation_engine_missing_columns PASSED    [ 28%]
  tests/test_cleaning.py::test_validation_engine_status_inconsistency PASSED [ 33%]
  tests/test_database.py::test_database_initialization PASSED              [ 38%]
  tests/test_database.py::test_data_ingestion_and_querying PASSED          [ 42%]
  tests/test_database.py::test_named_queries_execution PASSED              [ 47%]
  tests/test_database.py::test_python_sql_consistency_assertion PASSED     [ 52%]
  tests/test_metrics.py::test_overall_kpis_calculation PASSED              [ 57%]
  tests/test_metrics.py::test_zero_denominator_safeguard PASSED            [ 61%]
  tests/test_metrics.py::test_grouped_metrics_weighted_rate PASSED         [ 66%]
  tests/test_metrics.py::test_failure_reasons_breakdown PASSED             [ 71%]
  tests/test_metrics.py::test_hourly_metrics_structure PASSED              [ 76%]
  tests/test_metrics.py::test_dow_metrics_structure PASSED                 [ 80%]
  tests/test_pipeline.py::test_full_pipeline_integration PASSED            [ 85%]
  tests/test_statistics.py::test_wilson_confidence_interval_bounds PASSED  [ 90%]
  tests/test_statistics.py::test_cramers_v_bounds PASSED                   [ 95%]
  tests/test_statistics.py::test_statistical_analysis_pipeline PASSED      [100%]

  ============================= 21 passed in 1.42s ==============================
  ```

---

## 7. Launching the Interactive Dashboard

Launch the Streamlit web application:
```powershell
streamlit run app.py
```
* **Local URL:** `http://localhost:8501`
* **Features:** Full executive KPI cards, 8 interactive tabs, dynamic multi-dimensional sidebar filters, interactive Plotly visualizations, and a transaction-level explorer with CSV export.
