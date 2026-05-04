"""
SENTINEL FINANCE: Database Connection & Operations Module
========================================================
Manages PostgreSQL connections and provides utility functions
for database operations with error handling and logging.
"""

import logging
from contextlib import contextmanager
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.pool import NullPool, QueuePool
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from config.settings import (
    SQLALCHEMY_DATABASE_URL,
    SQLALCHEMY_POOL_SIZE,
    SQLALCHEMY_MAX_OVERFLOW,
    SQLALCHEMY_POOL_RECYCLE,
    ENVIRONMENT,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ====================================================================
# DATABASE ENGINE INITIALIZATION
# ====================================================================
def create_db_engine():
    """
    Creates and returns a SQLAlchemy engine with environment-specific
    configuration for optimal performance and reliability.
    
    Returns:
        Engine: SQLAlchemy engine instance
    """
    try:
        # Use NullPool for testing/development, QueuePool for production
        poolclass = NullPool if ENVIRONMENT == "development" else QueuePool
        
        # Base engine arguments
        engine_kwargs = {
            "poolclass": poolclass,
            "pool_recycle": SQLALCHEMY_POOL_RECYCLE,
            "echo": False,  # Set to True for SQL debugging
            "connect_args": {
                "connect_timeout": 10,
                "options": "-c statement_timeout=30000"  # 30 sec per query
            }
        }
        
        # Add pool size parameters only for QueuePool
        if poolclass == QueuePool:
            engine_kwargs.update({
                "pool_size": SQLALCHEMY_POOL_SIZE,
                "max_overflow": SQLALCHEMY_MAX_OVERFLOW,
            })
        
        engine = create_engine(SQLALCHEMY_DATABASE_URL, **engine_kwargs)
        
        logger.info(f"✅ Database engine created for {ENVIRONMENT} environment")
        return engine
        
    except SQLAlchemyError as e:
        logger.error(f"❌ Failed to create database engine: {str(e)}")
        raise

# Create global engine instance
db_engine = create_db_engine()

# ====================================================================
# CONNECTION CONTEXT MANAGER
# ====================================================================
@contextmanager
def get_db_connection():
    """
    Context manager for database connections with automatic cleanup.
    
    Yields:
        Connection: Active database connection
        
    Example:
        with get_db_connection() as conn:
            result = conn.execute(query)
    """
    connection = None
    try:
        connection = db_engine.connect()
        yield connection
        
    except SQLAlchemyError as e:
        logger.error(f"❌ Database connection error: {str(e)}")
        if connection:
            connection.rollback()
        raise
        
    finally:
        if connection:
            connection.close()

# ====================================================================
# DATABASE SESSION MANAGER
# ====================================================================
@contextmanager
def get_db_session():
    """
    Context manager for database sessions with transaction handling.
    
    Yields:
        Session: Active database session
    """
    from sqlalchemy.orm import sessionmaker
    
    Session = sessionmaker(bind=db_engine)
    session = Session()
    
    try:
        yield session
        session.commit()
        logger.debug("✅ Transaction committed successfully")
        
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Transaction rolled back: {str(e)}")
        raise
        
    finally:
        session.close()

# ====================================================================
# DATABASE HELPER FUNCTIONS
# ====================================================================
def test_database_connection():
    """
    Tests the database connection and returns detailed diagnostics.
    
    Returns:
        dict: Connection status and details
    """
    diagnostics = {
        "status": "unknown",
        "database_url": SQLALCHEMY_DATABASE_URL.replace(
            SQLALCHEMY_DATABASE_URL.split("@")[0], "***"
        ),  # Mask credentials
        "message": "",
    }
    
    try:
        with get_db_connection() as conn:
            result = conn.execute(text("SELECT version();"))
            db_version = result.fetchone()[0]
            
            # Get table count
            inspector = inspect(db_engine)
            tables = inspector.get_table_names()
            
            diagnostics["status"] = "connected"
            diagnostics["message"] = f"Connected successfully. Database version: {db_version}"
            diagnostics["tables_found"] = len(tables)
            diagnostics["tables"] = tables
            
            logger.info(f"✅ {diagnostics['message']}")
            
    except SQLAlchemyError as e:
        diagnostics["status"] = "connection_failed"
        diagnostics["message"] = str(e)
        logger.error(f"❌ Database connection test failed: {str(e)}")
    
    return diagnostics

def execute_query(query_string, fetch_type="all"):
    """
    Executes a SQL query and returns results.
    
    Args:
        query_string (str): SQL query to execute
        fetch_type (str): 'all', 'one', or 'none'
        
    Returns:
        Various: Query results or None
    """
    try:
        with get_db_connection() as conn:
            result = conn.execute(text(query_string))
            
            if fetch_type == "all":
                return result.fetchall()
            elif fetch_type == "one":
                return result.fetchone()
            elif fetch_type == "none":
                return None
                
    except SQLAlchemyError as e:
        logger.error(f"❌ Query execution failed: {str(e)}")
        raise

def bulk_insert(table_name, records):
    """
    Bulk inserts records into a table using batch operations.
    
    Args:
        table_name (str): Target table name
        records (list): List of dictionaries with column:value pairs
        
    Returns:
        dict: Insertion statistics
    """
    stats = {
        "total_records": len(records),
        "inserted": 0,
        "failed": 0,
        "errors": []
    }
    
    if not records:
        logger.warning("⚠️ No records provided for insertion")
        return stats
    
    try:
        with get_db_connection() as conn:
            for i, record in enumerate(records, 1):
                try:
                    # Build INSERT statement
                    columns = ", ".join(record.keys())
                    values = ", ".join([f"'{str(v).replace(chr(39), chr(39)*2)}'" for v in record.values()])
                    insert_sql = f"INSERT INTO {table_name} ({columns}) VALUES ({values})"
                    
                    conn.execute(text(insert_sql))
                    stats["inserted"] += 1
                    
                except IntegrityError as e:
                    stats["failed"] += 1
                    stats["errors"].append(f"Record {i}: Integrity violation - {str(e)}")
                    logger.warning(f"⚠️ Integrity error on record {i}: {str(e)}")
                    
            conn.commit()
            
    except SQLAlchemyError as e:
        logger.error(f"❌ Bulk insert failed: {str(e)}")
        stats["errors"].append(f"Bulk operation failed: {str(e)}")
    
    logger.info(f"✅ Bulk insert complete: {stats['inserted']} inserted, {stats['failed']} failed")
    return stats

def get_table_row_count(table_name):
    """
    Returns the row count for a given table.
    
    Args:
        table_name (str): Table name
        
    Returns:
        int: Row count
    """
    try:
        with get_db_connection() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name};"))
            count = result.scalar()
            return count
            
    except SQLAlchemyError as e:
        logger.error(f"❌ Failed to get row count for {table_name}: {str(e)}")
        return None

def close_db_engine():
    """Closes the database engine and any active connections."""
    try:
        db_engine.dispose()
        logger.info("✅ Database engine closed")
    except Exception as e:
        logger.error(f"❌ Error closing database engine: {str(e)}")

# ====================================================================
# INITIALIZATION CHECK
# ====================================================================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("SENTINEL FINANCE: Database Connectivity Test")
    print("="*60)
    
    diagnostics = test_database_connection()
    print(f"\n📊 Status: {diagnostics['status'].upper()}")
    print(f"📝 Message: {diagnostics['message']}")
    
    if diagnostics['status'] == 'connected':
        print(f"📋 Tables Found: {diagnostics['tables_found']}")
        for table in diagnostics.get('tables', []):
            print(f"   - {table}")
    
    print("\n" + "="*60)
