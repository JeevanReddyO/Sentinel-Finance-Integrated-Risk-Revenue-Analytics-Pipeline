"""
SENTINEL FINANCE: Configuration Settings Module
================================================
Centralized configuration for the Banking Risk & Revenue Analytics Pipeline.
Manages database connectivity, API settings, and application constants.
"""

import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env at project root if present
BASE_DIR = Path(__file__).resolve().parent.parent
DOTENV_PATH = BASE_DIR / ".env"
if DOTENV_PATH.exists():
    load_dotenv(DOTENV_PATH, override=True)

# ====================================================================
# PROJECT METADATA
# ====================================================================
PROJECT_NAME = "Sentinel Finance"
PROJECT_VERSION = "1.0.0"
PROJECT_DESCRIPTION = "Automated ETL pipeline and Operational Dashboard for banking risk mitigation"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# ====================================================================
# PATHS & DIRECTORIES
# ====================================================================
SRC_DIR = BASE_DIR / "src"
DATABASE_DIR = BASE_DIR / "database"
DOCS_DIR = BASE_DIR / "docs"
LOGS_DIR = BASE_DIR / "logs"

# Create logs directory if it doesn't exist
LOGS_DIR.mkdir(exist_ok=True)

# ====================================================================
# DATABASE CONFIGURATION
# ====================================================================
# PostgreSQL connection parameters
# Use environment variables for secure credential management
DATABASE_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
    "database": os.getenv("DB_NAME", "bank_db"),
    "schema": "public",
}

# SQLAlchemy connection string
SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}"
    f"@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}"
)

# Connection pool settings for production
SQLALCHEMY_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", 5))
SQLALCHEMY_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", 10))
SQLALCHEMY_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", 3600))

# ====================================================================
# API CONFIGURATION
# ====================================================================
# Alpha Vantage for currency exchange rates
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "demo")
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"
ALPHA_VANTAGE_RATE_LIMIT = 5  # Max 5 requests per minute (free tier)
ALPHA_VANTAGE_TIMEOUT = 30  # seconds

# ====================================================================
# DATA EXTRACTION SETTINGS
# ====================================================================
# Faker library configuration for synthetic data generation
FAKER_LOCALE = "en_US"
FAKER_SEED = 42  # For reproducible test data (set to None for random)
DAILY_TRANSACTION_COUNT = 50  # Number of synthetic transactions to generate daily

# Currency conversion settings
DEFAULT_CURRENCY = "USD"
TARGET_CURRENCIES = ["EUR", "GBP", "JPY", "INR"]

# ====================================================================
# DATA VALIDATION & CLEANING
# ====================================================================
# Transaction validation thresholds
MIN_TRANSACTION_AMOUNT = 0.01
MAX_TRANSACTION_AMOUNT = 100000.00

# Risk scoring thresholds
CREDIT_UTILIZATION_HIGH_RISK = 0.80  # >80% of credit limit
CREDIT_UTILIZATION_MEDIUM_RISK = 0.50  # >50% of credit limit

# Fraud detection flags
FRAUD_AMOUNT_THRESHOLD = 5000.00  # High-value transaction flag
FRAUD_FREQUENCY_THRESHOLD = 10  # More than 10 txns in 1 hour

# ====================================================================
# STREAMLIT APP CONFIGURATION
# ====================================================================
STREAMLIT_PAGE_CONFIG = {
    "page_title": "Sentinel Finance | Risk Dashboard",
    "page_icon": "🛡️",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

# Cache settings for Streamlit app
STREAMLIT_CACHE_TTL = 600  # 10 minutes in seconds
STREAMLIT_CHART_HEIGHT = 400
STREAMLIT_MAX_SEARCH_RESULTS = 50

# ====================================================================
# LOGGING CONFIGURATION
# ====================================================================
LOG_FILE = LOGS_DIR / f"sentinel_finance_{datetime.now().strftime('%Y%m%d')}.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ====================================================================
# GITHUB ACTIONS & SCHEDULING
# ====================================================================
# Daily ETL execution schedule (cron syntax in GitHub Actions)
# Default: runs at 00:00 UTC daily
ETL_SCHEDULE = "0 0 * * *"
ETL_TIMEOUT_MINUTES = 30

# ====================================================================
# FEATURE FLAGS
# ====================================================================
# Enable/disable features for A/B testing or gradual rollout
FEATURES = {
    "enable_fraud_detection": True,
    "enable_risk_scoring": True,
    "enable_currency_conversion": True,
    "enable_email_alerts": False,  # Requires SMTP configuration
    "enable_power_bi_sync": False,  # Requires Power BI API key
}

# ====================================================================
# ALERT & NOTIFICATION SETTINGS
# ====================================================================
ALERT_HIGH_RISK_THRESHOLD = 70  # Customer risk score
ALERT_FRAUD_COUNT_THRESHOLD = 3  # Fraud flags in 24 hours
DEFAULT_EMAIL_TO = os.getenv("ALERT_EMAIL", "alerts@sentinelfinance.com")

# ====================================================================
# PERFORMANCE TUNING
# ====================================================================
# Batch processing size for large data loads
BATCH_INSERT_SIZE = 1000  # Insert 1000 records at a time
BATCH_QUERY_LIMIT = 10000  # Fetch max 10k records per query

# ====================================================================
# SECURITY SETTINGS
# ====================================================================
# Hash sensitive data
HASH_ALGORITHM = "sha256"
ENCRYPT_SENSITIVE_FIELDS = True

# API rate limiting
API_RATE_LIMIT_CALLS = 100
API_RATE_LIMIT_PERIOD = 3600  # seconds

print(f"✅ Configuration loaded for {ENVIRONMENT} environment")
