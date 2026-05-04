-- ====================================================================
-- SENTINEL FINANCE: Banking Risk & Revenue Analytics
-- Database Schema Definition
-- ====================================================================
-- This schema defines the core tables for customer management and 
-- transaction tracking, with built-in support for automatic data
-- updates using PostgreSQL's UPSERT (ON CONFLICT) mechanism.
-- ====================================================================

-- Drop existing objects if needed (for fresh deployment)
DROP VIEW IF EXISTS daily_kpis CASCADE;
DROP TABLE IF EXISTS raw_transactions CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

-- ====================================================================
-- 1. CUSTOMERS TABLE
-- ====================================================================
-- Stores customer profiles with risk metrics and credit information.
-- This is the master dimension table for all banking operations.
-- ====================================================================
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    age INTEGER CHECK (age >= 18 AND age <= 120),
    annual_income NUMERIC(15, 2) CHECK (annual_income >= 0),
    region VARCHAR(50) NOT NULL,
    risk_score DECIMAL(5, 2) DEFAULT 0.00 CHECK (risk_score >= 0 AND risk_score <= 100),
    credit_limit NUMERIC(15, 2) NOT NULL CHECK (credit_limit > 0),
    status VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE', 'SUSPENDED')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_name CHECK (LENGTH(TRIM(name)) > 0),
    CONSTRAINT valid_region CHECK (LENGTH(TRIM(region)) > 0)
);

-- Create indexes for fast lookups
CREATE INDEX idx_customers_region ON customers(region);
CREATE INDEX idx_customers_risk_score ON customers(risk_score DESC);
CREATE INDEX idx_customers_status ON customers(status);

-- ====================================================================
-- 2. RAW_TRANSACTIONS TABLE
-- ====================================================================
-- Stores all transaction records with full audit trail.
-- Uses UPSERT logic to handle duplicate daily data ingestion.
-- ====================================================================
CREATE TABLE raw_transactions (
    transaction_id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    amount NUMERIC(15, 2) NOT NULL CHECK (amount > 0),
    category VARCHAR(50) NOT NULL,
    transaction_date DATE NOT NULL,
    transaction_time TIMESTAMP NOT NULL,
    merchant VARCHAR(100) NOT NULL,
    is_fraud BOOLEAN DEFAULT FALSE,
    mcc_code VARCHAR(10),
    currency_code VARCHAR(3) DEFAULT 'USD',
    exchange_rate NUMERIC(10, 4) DEFAULT 1.0000,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_merchant CHECK (LENGTH(TRIM(merchant)) > 0),
    CONSTRAINT valid_category CHECK (LENGTH(TRIM(category)) > 0),
    CONSTRAINT uq_transactions_unique UNIQUE (customer_id, transaction_date, transaction_time, merchant)
);

-- Create indexes for query performance
CREATE INDEX idx_transactions_customer ON raw_transactions(customer_id);
CREATE INDEX idx_transactions_date ON raw_transactions(transaction_date DESC);
CREATE INDEX idx_transactions_fraud ON raw_transactions(is_fraud) WHERE is_fraud = TRUE;
CREATE INDEX idx_transactions_category ON raw_transactions(category);

-- ====================================================================
-- 3. DAILY_KPIS VIEW
-- ====================================================================
-- Aggregated metrics for daily risk and revenue analysis.
-- Automatically reflects the latest transaction and customer data.
-- ====================================================================
CREATE VIEW daily_kpis AS
SELECT
    DATE(rt.transaction_date) AS date,
    COUNT(DISTINCT rt.customer_id) AS active_customers,
    COUNT(rt.transaction_id) AS total_transactions,
    SUM(rt.amount) AS total_spend,
    AVG(rt.amount) AS avg_transaction_amount,
    MIN(rt.amount) AS min_transaction_amount,
    MAX(rt.amount) AS max_transaction_amount,
    COUNT(CASE WHEN rt.is_fraud = TRUE THEN 1 END) AS fraud_transactions_flagged,
    ROUND(
        100.0 * COUNT(CASE WHEN rt.is_fraud = TRUE THEN 1 END) / 
        NULLIF(COUNT(rt.transaction_id), 0), 
        2
    ) AS fraud_rate_percent,
    ROUND(
        100.0 * COUNT(CASE WHEN c.risk_score > 70 THEN 1 END) / 
        NULLIF(COUNT(DISTINCT rt.customer_id), 0), 
        2
    ) AS high_risk_customer_percent,
    COUNT(DISTINCT c.region) AS regions_active,
    ARRAY_AGG(DISTINCT c.region) AS regions_list
FROM raw_transactions rt
LEFT JOIN customers c ON rt.customer_id = c.customer_id
GROUP BY DATE(rt.transaction_date)
ORDER BY DATE(rt.transaction_date) DESC;

-- ====================================================================
-- 4. CUSTOMER_DAILY_METRICS VIEW
-- ====================================================================
-- Per-customer daily metrics for risk assessment and dashboard display.
-- ====================================================================
CREATE VIEW customer_daily_metrics AS
SELECT
    DATE(rt.transaction_date) AS date,
    rt.customer_id,
    c.name,
    c.credit_limit,
    c.risk_score,
    COUNT(rt.transaction_id) AS transaction_count,
    SUM(rt.amount) AS daily_spend,
    ROUND(
        (SUM(rt.amount) / c.credit_limit * 100)::NUMERIC, 
        2
    ) AS utilization_ratio_percent,
    COUNT(CASE WHEN rt.is_fraud = TRUE THEN 1 END) AS fraud_flags,
    MAX(rt.amount) AS highest_transaction,
    CASE 
        WHEN (SUM(rt.amount) / c.credit_limit) > 0.80 THEN 'HIGH RISK'
        WHEN (SUM(rt.amount) / c.credit_limit) > 0.50 THEN 'MEDIUM RISK'
        ELSE 'LOW RISK'
    END AS risk_category
FROM raw_transactions rt
JOIN customers c ON rt.customer_id = c.customer_id
GROUP BY DATE(rt.transaction_date), rt.customer_id, c.name, c.credit_limit, c.risk_score
ORDER BY DATE(rt.transaction_date) DESC, daily_spend DESC;

-- ====================================================================
-- 5. UPSERT FUNCTION (Optional: Helper for Application Logic)
-- ====================================================================
-- This function demonstrates idempotent insertion patterns.
-- Call from Python application for reliably handling duplicate ingestion.
-- ====================================================================
CREATE OR REPLACE FUNCTION upsert_transaction(
    p_customer_id INTEGER,
    p_amount NUMERIC,
    p_category VARCHAR,
    p_transaction_date DATE,
    p_transaction_time TIMESTAMP,
    p_merchant VARCHAR,
    p_currency_code VARCHAR DEFAULT 'USD',
    p_exchange_rate NUMERIC DEFAULT 1.0000
)
RETURNS TABLE(transaction_id INTEGER, status VARCHAR) AS $$
DECLARE
    v_transaction_id INTEGER;
    v_status VARCHAR;
BEGIN
    -- Verify customer exists
    IF NOT EXISTS (SELECT 1 FROM customers WHERE customer_id = p_customer_id) THEN
        RAISE EXCEPTION 'Customer ID % does not exist', p_customer_id;
    END IF;

    -- Validate amount
    IF p_amount <= 0 THEN
        RAISE EXCEPTION 'Transaction amount must be positive';
    END IF;

    -- Insert or update (UPSERT logic)
    INSERT INTO raw_transactions (
        customer_id, amount, category, transaction_date, transaction_time,
        merchant, currency_code, exchange_rate
    )
    VALUES (
        p_customer_id, p_amount, p_category, p_transaction_date, p_transaction_time,
        p_merchant, p_currency_code, p_exchange_rate
    )
    ON CONFLICT DO UPDATE
    SET
        amount = EXCLUDED.amount,
        merchant = EXCLUDED.merchant,
        updated_at = CURRENT_TIMESTAMP
    WHERE
        raw_transactions.customer_id = p_customer_id
        AND raw_transactions.transaction_date = p_transaction_date
        AND raw_transactions.transaction_time = p_transaction_time
    RETURNING raw_transactions.transaction_id, 'SUCCESS'::VARCHAR
    INTO v_transaction_id, v_status;

    IF v_transaction_id IS NULL THEN
        v_status := 'FAILED';
    END IF;

    RETURN QUERY SELECT v_transaction_id, v_status;
EXCEPTION WHEN OTHERS THEN
    RETURN QUERY SELECT NULL::INTEGER, 'ERROR: ' || SQLERRM;
END;
$$ LANGUAGE plpgsql;

-- ====================================================================
-- 6. GRANT PERMISSIONS (for application user)
-- ====================================================================
-- Uncomment and modify user name as needed for your deployment
-- ====================================================================
-- CREATE USER bank_app_user WITH PASSWORD 'secure_password';
-- GRANT USAGE ON SCHEMA public TO bank_app_user;
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO bank_app_user;
-- GRANT SELECT ON ALL VIEWS IN SCHEMA public TO bank_app_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO bank_app_user;

-- ====================================================================
-- END OF SCHEMA DEFINITION
-- ====================================================================
