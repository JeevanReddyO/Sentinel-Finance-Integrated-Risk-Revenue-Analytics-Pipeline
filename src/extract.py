"""
SENTINEL FINANCE: Data Extraction & ETL Module
==============================================
Automated daily data pipeline that:
- Generates synthetic banking transactions (Faker)
- Fetches real currency exchange rates (Alpha Vantage API)
- Cleans and validates transaction data
- Inserts data into PostgreSQL (with UPSERT logic)
- Logs all operations and handles errors gracefully
"""

import os
import sys
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple
import traceback

# Third-party imports
import pandas as pd
import requests
from faker import Faker
from sqlalchemy import text

# Import project modules
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import (
    FAKER_LOCALE,
    FAKER_SEED,
    DAILY_TRANSACTION_COUNT,
    ALPHA_VANTAGE_API_KEY,
    ALPHA_VANTAGE_BASE_URL,
    ALPHA_VANTAGE_TIMEOUT,
    MIN_TRANSACTION_AMOUNT,
    MAX_TRANSACTION_AMOUNT,
    BATCH_INSERT_SIZE,
    DEFAULT_CURRENCY,
    TARGET_CURRENCIES,
    LOGS_DIR,
)
from config.database import get_db_connection, get_db_session, test_database_connection

# ====================================================================
# LOGGING SETUP
# ====================================================================
log_file = LOGS_DIR / f"extract_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ====================================================================
# SYNTHETIC DATA GENERATION
# ====================================================================
class TransactionGenerator:
    """Generates realistic synthetic banking transactions using Faker."""
    
    TRANSACTION_CATEGORIES = [
        "Groceries", "Restaurants", "Shopping", "Utilities", "Travel",
        "Entertainment", "Health", "Dining", "Business", "Gas"
    ]
    
    MERCHANTS = {
        "Groceries": ["Whole Foods Market", "Walmart", "Trader Joe's", "Amazon Fresh", "Safeway"],
        "Restaurants": ["Pizza Hut", "Chipotle", "McDonald's", "Starbucks", "Dunkin'"],
        "Shopping": ["Amazon", "Target", "H&M", "Zara", "Gucci Store"],
        "Utilities": ["Electric Company", "Water Company", "Gas Company", "Internet Provider", "Phone Company"],
        "Travel": ["Uber", "Lyft", "Delta Airlines", "British Airways", "Hotel Booking"],
        "Entertainment": ["Netflix", "Disney+", "Spotify", "Movie Theater", "Concert Tickets"],
        "Health": ["CVS Pharmacy", "Walgreens", "Private Hospital", "Doctor Office", "Dental Clinic"],
        "Dining": ["Irish Pub", "Michelin Restaurant", "Fine Dining Restaurant", "Sushi Bar", "Steakhouse"],
        "Business": ["IBM Software Services", "Microsoft Azure", "Salesforce CRM", "Google Cloud Platform", "AWS Services"],
        "Gas": ["Shell Gas Station", "BP Gas", "Chevron", "Exxon", "Mobil"],
    }
    
    MCC_CODES = {
        "Groceries": "5411",
        "Restaurants": "5812",
        "Shopping": "5310",
        "Utilities": "4900",
        "Travel": "4121",
        "Entertainment": "7832",
        "Health": "8062",
        "Dining": "5813",
        "Business": "7372",
        "Gas": "5541",
    }
    
    def __init__(self):
        """Initialize Faker with optional seed for reproducible data."""
        self.fake = Faker(FAKER_LOCALE)
        if FAKER_SEED is not None:
            Faker.seed(FAKER_SEED)
    
    def generate_transaction(self, customer_id: int) -> Dict:
        """
        Generates a single synthetic transaction.
        
        Args:
            customer_id (int): Customer ID for the transaction
            
        Returns:
            dict: Transaction data with validation
        """
        category = self.fake.random.choice(self.TRANSACTION_CATEGORIES)
        merchant = self.fake.random.choice(self.MERCHANTS[category])
        
        # Generate realistic amount based on category
        amount_ranges = {
            "Groceries": (20, 150),
            "Restaurants": (15, 100),
            "Shopping": (50, 1000),
            "Utilities": (50, 300),
            "Travel": (50, 2000),
            "Entertainment": (10, 50),
            "Health": (30, 500),
            "Dining": (30, 200),
            "Business": (100, 3000),
            "Gas": (40, 80),
        }
        
        min_amt, max_amt = amount_ranges.get(category, (10, 500))
        amount = round(self.fake.random.uniform(min_amt, max_amt), 2)
        
        # Generate timestamp (past 7 days)
        days_ago = self.fake.random.randint(0, 6)
        hours_offset = self.fake.random.randint(0, 23)
        min_offset = self.fake.random.randint(0, 59)
        
        transaction_date = datetime.now() - timedelta(days=days_ago)
        transaction_time = transaction_date.replace(hour=hours_offset, minute=min_offset, second=0)
        
        return {
            "customer_id": customer_id,
            "amount": amount,
            "category": category,
            "transaction_date": transaction_date.date(),
            "transaction_time": transaction_time,
            "merchant": merchant,
            "mcc_code": self.MCC_CODES.get(category, "0000"),
            "currency_code": DEFAULT_CURRENCY,
            "exchange_rate": 1.0,
            "is_fraud": False,
        }
    
    def generate_batch(self, num_transactions: int, customer_ids: List[int]) -> List[Dict]:
        """
        Generates a batch of synthetic transactions.
        
        Args:
            num_transactions (int): Number of transactions to generate
            customer_ids (list): Available customer IDs
            
        Returns:
            list: List of transaction dictionaries
        """
        logger.info(f"🔄 Generating {num_transactions} synthetic transactions...")
        transactions = []
        
        for _ in range(num_transactions):
            customer_id = self.fake.random.choice(customer_ids)
            transaction = self.generate_transaction(customer_id)
            transactions.append(transaction)
        
        logger.info(f"✅ Generated {len(transactions)} transactions")
        return transactions

# ====================================================================
# API DATA FETCHING
# ====================================================================
class ExchangeRateFetcher:
    """Fetches currency exchange rates from Alpha Vantage API."""
    
    def __init__(self, api_key: str):
        """Initialize with Alpha Vantage API key."""
        self.api_key = api_key
        self.cache = {}
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Implements rate limiting (max 5 requests/minute for free tier)."""
        elapsed = time.time() - self.last_request_time
        if elapsed < 12:  # 60 seconds / 5 requests = 12 seconds per request
            time.sleep(12 - elapsed)
        self.last_request_time = time.time()
    
    def fetch_exchange_rate(self, from_currency: str, to_currency: str) -> float:
        """
        Fetches exchange rate from Alpha Vantage API.
        
        Args:
            from_currency (str): Source currency code (e.g., 'USD')
            to_currency (str): Target currency code (e.g., 'EUR')
            
        Returns:
            float: Exchange rate (default 1.0 if fetch fails)
        """
        # Check cache first
        cache_key = f"{from_currency}_{to_currency}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        if from_currency == to_currency:
            return 1.0
        
        try:
            self._rate_limit()
            
            params = {
                "function": "CURRENCY_EXCHANGE_RATE",
                "from_currency": from_currency,
                "to_currency": to_currency,
                "apikey": self.api_key,
            }
            
            response = requests.get(
                ALPHA_VANTAGE_BASE_URL,
                params=params,
                timeout=ALPHA_VANTAGE_TIMEOUT
            )
            response.raise_for_status()
            
            data = response.json()
            
            if "Realtime Currency Exchange Rate" in data:
                rate = float(data["Realtime Currency Exchange Rate"]["5. Exchange Rate"])
                self.cache[cache_key] = rate
                logger.info(f"✅ Fetched rate {from_currency}/{to_currency}: {rate}")
                return rate
            else:
                logger.warning(f"⚠️ No exchange rate data for {from_currency}/{to_currency}")
                return 1.0
        
        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠️ API fetch failed: {str(e)}. Using default rate 1.0")
            return 1.0
    
    def fetch_all_rates(self) -> Dict[str, float]:
        """Fetches all available exchange rates."""
        rates = {}
        logger.info("📡 Fetching exchange rates...")
        
        for currency in TARGET_CURRENCIES:
            rate = self.fetch_exchange_rate(DEFAULT_CURRENCY, currency)
            rates[currency] = rate
        
        return rates

# ====================================================================
# DATA CLEANING & VALIDATION
# ====================================================================
class DataCleaner:
    """Cleans and validates transaction data."""
    
    @staticmethod
    def clean_transactions(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """
        Cleans transaction dataframe by removing invalid records.
        
        Args:
            df (pd.DataFrame): Raw transaction data
            
        Returns:
            tuple: (cleaned_df, cleaning_stats)
        """
        stats = {
            "total_records": len(df),
            "removed_negative": 0,
            "removed_null_customer": 0,
            "removed_amount_outliers": 0,
            "final_records": 0,
        }
        
        logger.info(f"🧹 Cleaning {len(df)} transaction records...")
        
        # Remove negative amounts
        null_amount = df[df['amount'] < 0]
        stats["removed_negative"] = len(null_amount)
        df = df[df['amount'] >= MIN_TRANSACTION_AMOUNT]
        
        # Remove null customer IDs
        null_customer = df[df['customer_id'].isna()]
        stats["removed_null_customer"] = len(null_customer)
        df = df[df['customer_id'].notna()]
        
        # Remove amount outliers (>MAX_TRANSACTION_AMOUNT)
        outliers = df[df['amount'] > MAX_TRANSACTION_AMOUNT]
        stats["removed_amount_outliers"] = len(outliers)
        df = df[df['amount'] <= MAX_TRANSACTION_AMOUNT]
        
        # Remove duplicates based on key columns
        df = df.drop_duplicates(
            subset=['customer_id', 'transaction_date', 'transaction_time', 'merchant'],
            keep='first'
        )
        
        stats["final_records"] = len(df)
        
        logger.info(
            f"✅ Cleaning complete: "
            f"Removed {stats['removed_negative']} negative, "
            f"{stats['removed_null_customer']} null customer, "
            f"{stats['removed_amount_outliers']} outliers. "
            f"Final: {stats['final_records']} records"
        )
        
        return df, stats

# ====================================================================
# DATABASE INSERTION WITH UPSERT LOGIC
# ====================================================================
class DataLoader:
    """Loads cleaned data into PostgreSQL."""
    
    @staticmethod
    def upsert_transactions(transactions: List[Dict]) -> Dict:
        """
        Inserts transactions with UPSERT logic (ON CONFLICT handling).
        
        Args:
            transactions (list): List of transaction dictionaries
            
        Returns:
            dict: Insertion statistics
        """
        stats = {
            "total": len(transactions),
            "inserted": 0,
            "updated": 0,
            "failed": 0,
            "errors": []
        }
        
        if not transactions:
            logger.warning("⚠️ No transactions to insert")
            return stats
        
        logger.info(f"📥 Upserting {len(transactions)} transactions...")
        
        try:
            with get_db_connection() as conn:
                for i, txn in enumerate(transactions, 1):
                    try:
                        # Build UPSERT query
                        insert_sql = """
                        INSERT INTO raw_transactions (
                            customer_id, amount, category, transaction_date,
                            transaction_time, merchant, is_fraud, mcc_code,
                            currency_code, exchange_rate
                        ) VALUES (
                            :customer_id, :amount, :category, :transaction_date,
                            :transaction_time, :merchant, :is_fraud, :mcc_code,
                            :currency_code, :exchange_rate
                        )
                        ON CONFLICT ON CONSTRAINT uq_transactions_unique
                        DO UPDATE SET
                            amount = EXCLUDED.amount,
                            exchange_rate = EXCLUDED.exchange_rate,
                            updated_at = CURRENT_TIMESTAMP
                        RETURNING transaction_id;
                        """
                        
                        result = conn.execute(text(insert_sql), txn)
                        txn_id = result.scalar()
                        
                        if txn_id:
                            stats["inserted"] += 1
                        else:
                            stats["updated"] += 1
                        
                        # Commit every batch
                        if i % BATCH_INSERT_SIZE == 0:
                            conn.commit()
                            logger.info(f"✅ Batch {i//BATCH_INSERT_SIZE} committed")
                    
                    except Exception as e:
                        stats["failed"] += 1
                        error_msg = f"Txn {i}: {str(e)}"
                        stats["errors"].append(error_msg)
                        logger.warning(f"⚠️ {error_msg}")
                
                # Final commit
                conn.commit()
        
        except Exception as e:
            logger.error(f"❌ Upsert operation failed: {str(e)}")
            stats["errors"].append(str(e))
        
        logger.info(
            f"✅ Upsert complete: {stats['inserted']} inserted, "
            f"{stats['updated']} updated, {stats['failed']} failed"
        )
        
        return stats

# ====================================================================
# MAIN ETL ORCHESTRATION
# ====================================================================
def run_daily_sync():
    """
    Main ETL orchestration function.
    Executes the complete data pipeline daily.
    """
    start_time = time.time()
    execution_log = {
        "timestamp": datetime.now().isoformat(),
        "status": "RUNNING",
        "stages": {},
        "total_time_seconds": 0
    }
    
    try:
        logger.info("\n" + "="*60)
        logger.info("🚀 STARTING SENTINEL FINANCE DAILY ETL PIPELINE")
        logger.info("="*60)
        
        # Stage 1: Database Connectivity Check
        logger.info("\n📊 Stage 1: Testing Database Connection...")
        execution_log["stages"]["database_check"] = {}
        
        db_status = test_database_connection()
        execution_log["stages"]["database_check"]["status"] = db_status["status"]
        execution_log["stages"]["database_check"]["tables_found"] = db_status.get("tables_found", 0)
        
        if db_status["status"] != "connected":
            raise Exception(f"Database connection failed: {db_status['message']}")
        
        # Get customer IDs from database
        with get_db_connection() as conn:
            result = conn.execute(text("SELECT customer_id FROM customers LIMIT 100;"))
            customer_ids = [row[0] for row in result.fetchall()]
        
        if not customer_ids:
            logger.error("❌ No customers found in database. Run seed_data.sql first.")
            raise Exception("No customer records available")
        
        logger.info(f"✅ Found {len(customer_ids)} customers")
        
        # Stage 2: Synthetic Data Generation
        logger.info("\n🤖 Stage 2: Generating Synthetic Transactions...")
        execution_log["stages"]["data_generation"] = {}
        
        generator = TransactionGenerator()
        transactions = generator.generate_batch(DAILY_TRANSACTION_COUNT, customer_ids)
        execution_log["stages"]["data_generation"]["transactions_generated"] = len(transactions)
        
        # Stage 3: Exchange Rate Fetching
        logger.info("\n💱 Stage 3: Fetching Exchange Rates...")
        execution_log["stages"]["exchange_rates"] = {}
        
        try:
            fetcher = ExchangeRateFetcher(ALPHA_VANTAGE_API_KEY)
            rates = fetcher.fetch_all_rates()
            execution_log["stages"]["exchange_rates"]["rates"] = rates
            logger.info(f"✅ Fetched {len(rates)} exchange rates")
        except Exception as e:
            logger.warning(f"⚠️ Exchange rate fetch failed: {str(e)}. Using default rates.")
            execution_log["stages"]["exchange_rates"]["warning"] = str(e)
        
        # Stage 4: Data Cleaning
        logger.info("\n🧹 Stage 4: Cleaning & Validation...")
        execution_log["stages"]["data_cleaning"] = {}
        
        df = pd.DataFrame(transactions)
        df_clean, cleaning_stats = DataCleaner.clean_transactions(df)
        execution_log["stages"]["data_cleaning"]["stats"] = cleaning_stats
        
        # Convert cleaned dataframe back to list of dicts
        transactions_clean = df_clean.to_dict('records')
        
        # Stage 5: Database Insertion
        logger.info("\n📥 Stage 5: Upserting to PostgreSQL...")
        execution_log["stages"]["database_insertion"] = {}
        
        # Convert datetime objects to strings for SQL
        for txn in transactions_clean:
            if isinstance(txn['transaction_date'], pd.Timestamp):
                txn['transaction_date'] = txn['transaction_date'].date()
            if isinstance(txn['transaction_time'], pd.Timestamp):
                txn['transaction_time'] = txn['transaction_time'].isoformat()
        
        loader = DataLoader()
        insert_stats = loader.upsert_transactions(transactions_clean)
        execution_log["stages"]["database_insertion"]["stats"] = insert_stats
        
        # Stage 6: Verification
        logger.info("\n✅ Stage 6: Verification...")
        execution_log["stages"]["verification"] = {}
        
        with get_db_connection() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM raw_transactions;"))
            total_transactions = result.scalar()
            
            result = conn.execute(text("SELECT COUNT(*) FROM daily_kpis;"))
            daily_records = result.scalar()
        
        execution_log["stages"]["verification"]["total_transactions"] = total_transactions
        execution_log["stages"]["verification"]["daily_kpi_records"] = daily_records
        
        # Success!
        execution_log["status"] = "SUCCESS"
        execution_log["total_time_seconds"] = time.time() - start_time
        
        logger.info("\n" + "="*60)
        logger.info("✅ SENTINEL FINANCE ETL PIPELINE COMPLETED SUCCESSFULLY!")
        logger.info(f"⏱️  Total Execution Time: {execution_log['total_time_seconds']:.2f} seconds")
        logger.info("="*60 + "\n")
        
    except Exception as e:
        execution_log["status"] = "FAILED"
        execution_log["error"] = str(e)
        execution_log["total_time_seconds"] = time.time() - start_time
        
        logger.error("\n" + "="*60)
        logger.error("❌ SENTINEL FINANCE ETL PIPELINE FAILED!")
        logger.error(f"Error: {str(e)}")
        logger.error("="*60 + "\n")
        logger.error(traceback.format_exc())
    
    finally:
        # Save execution log
        log_path = LOGS_DIR / "execution_log.json"
        with open(log_path, 'a') as f:
            f.write(json.dumps(execution_log) + "\n")
        
        return execution_log

# ====================================================================
# CLI ENTRY POINT
# ====================================================================
if __name__ == "__main__":
    result = run_daily_sync()
    sys.exit(0 if result["status"] == "SUCCESS" else 1)
