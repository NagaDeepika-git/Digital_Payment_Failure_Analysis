"""
Project Configuration and Path Management.
Digital Payment Failure Analysis
"""

from pathlib import Path

# Base Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Data Directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
SAMPLE_DATA_DIR = DATA_DIR / "sample"

# Data File Paths
RAW_DATA_PATH = RAW_DATA_DIR / "fintech_payment_transactions.csv"
PROCESSED_DATA_PATH = PROCESSED_DATA_DIR / "payment_transactions_cleaned.csv"
SAMPLE_DATA_PATH = SAMPLE_DATA_DIR / "sample_transactions.csv"

# SQLite Database
DATABASE_DIR = PROJECT_ROOT / "data"
DATABASE_PATH = DATABASE_DIR / "payment_analytics.db"

# SQL Scripts
SQL_DIR = PROJECT_ROOT / "sql"
SCHEMA_SQL_PATH = SQL_DIR / "schema.sql"
ANALYSIS_SQL_PATH = SQL_DIR / "analysis_queries.sql"

# Reports & Outputs
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
TABLES_DIR = REPORTS_DIR / "tables"

# Documentation
DOCS_DIR = PROJECT_ROOT / "docs"

# Source Dataset Details
REMOTE_RAW_URL = (
    "https://raw.githubusercontent.com/ManojMaliDev/"
    "Digital-Payment-Transaction-Health-Analytics/main/"
    "Raw_fintech_payment_transactions.csv"
)

# Business Definitions & Categories
ELIGIBLE_STATUSES = ["SUCCESS", "FAILED"]

PAYMENT_METHODS = ["UPI", "Credit Card", "Debit Card", "NetBanking"]
BANKS = ["HDFC", "SBI", "ICICI", "Axis Bank", "Kotak"]
MERCHANTS = ["Amazon", "Flipkart", "Swiggy", "Zomato", "Uber", "MakeMyTrip", "JioMart", "Myntra"]
GEOGRAPHIES = ["Mumbai", "Bengaluru", "Pune", "Delhi", "Hyderabad", "Chennai"]

# Plotting Theme - Clean Modern Light Palette
LIGHT_THEME_COLORS = {
    "primary": "#1E3A8A",      # Deep Navy
    "secondary": "#3B82F6",    # Bright Blue
    "success": "#10B981",      # Emerald Green
    "failure": "#EF4444",      # Rose Red
    "warning": "#F59E0B",      # Amber
    "info": "#06B6D4",         # Cyan
    "neutral_dark": "#1F2937", # Slate Dark Gray
    "neutral_light": "#F9FAFB",# Off White
    "border": "#E5E7EB",       # Soft Gray
}
