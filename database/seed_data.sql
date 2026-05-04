-- ====================================================================
-- SENTINEL FINANCE: Seed Data for Testing
-- ====================================================================
-- This script populates the database with realistic sample data for
-- development and testing purposes.
-- ====================================================================

-- ====================================================================
-- 1. SEED CUSTOMERS TABLE
-- ====================================================================
INSERT INTO customers (name, age, annual_income, region, credit_limit, status)
VALUES
    ('John Anderson', 35, 75000.00, 'North America', 15000.00, 'ACTIVE'),
    ('Sarah Martinez', 42, 125000.00, 'North America', 25000.00, 'ACTIVE'),
    ('Michael Chen', 38, 95000.00, 'Asia Pacific', 20000.00, 'ACTIVE'),
    ('Emma Williams', 28, 55000.00, 'Europe', 10000.00, 'ACTIVE'),
    ('David Kumar', 45, 150000.00, 'Asia Pacific', 30000.00, 'ACTIVE'),
    ('Lisa Johnson', 32, 85000.00, 'North America', 18000.00, 'ACTIVE'),
    ('Robert Brown', 50, 210000.00, 'Europe', 40000.00, 'ACTIVE'),
    ('Amanda Davis', 26, 45000.00, 'North America', 8000.00, 'ACTIVE'),
    ('James Wilson', 55, 180000.00, 'Europe', 35000.00, 'ACTIVE'),
    ('Patricia Garcia', 31, 70000.00, 'Latin America', 14000.00, 'ACTIVE'),
    ('Christopher Lee', 44, 165000.00, 'Asia Pacific', 32000.00, 'ACTIVE'),
    ('Jennifer Taylor', 29, 60000.00, 'North America', 12000.00, 'ACTIVE'),
    ('Daniel Thomas', 39, 100000.00, 'Europe', 22000.00, 'ACTIVE'),
    ('Barbara Jackson', 48, 140000.00, 'Africa', 28000.00, 'ACTIVE'),
    ('Joseph White', 36, 80000.00, 'North America', 16000.00, 'ACTIVE');

-- ====================================================================
-- 2. SEED RAW_TRANSACTIONS TABLE
-- ====================================================================
-- Sample transactions for the last 7 days with realistic data
-- ====================================================================
INSERT INTO raw_transactions (
    customer_id, amount, category, transaction_date, transaction_time,
    merchant, is_fraud, mcc_code, currency_code, exchange_rate
)
VALUES
    (1, 125.50, 'Groceries', '2026-04-30', '2026-04-30 10:15:00', 'Whole Foods Market', FALSE, '5411', 'USD', 1.0000),
    (1, 89.99, 'Restaurants', '2026-04-30', '2026-04-30 19:45:00', 'Pizza Hut', FALSE, '5812', 'USD', 1.0000),
    (2, 450.00, 'Shopping', '2026-04-30', '2026-04-30 14:30:00', 'Amazon', FALSE, '5961', 'USD', 1.0000),
    (2, 75.00, 'Entertainment', '2026-04-29', '2026-04-29 20:00:00', 'Netflix Subscription', FALSE, '4899', 'USD', 1.0000),
    (3, 200.00, 'Travel', '2026-04-30', '2026-04-30 08:00:00', 'Uber', FALSE, '4121', 'USD', 1.0000),
    (3, 150.00, 'Utilities', '2026-04-28', '2026-04-28 09:00:00', 'Electric Company', FALSE, '4900', 'USD', 1.0000),
    (4, 45.99, 'Groceries', '2026-04-30', '2026-04-30 13:20:00', 'Trader Joe''s', FALSE, '5411', 'USD', 1.0000),
    (4, 120.00, 'Shopping', '2026-04-29', '2026-04-29 15:00:00', 'Target', FALSE, '5310', 'USD', 1.0000),
    (5, 1200.00, 'Business', '2026-04-30', '2026-04-30 11:00:00', 'IBM Software Services', FALSE, '7372', 'USD', 1.0000),
    (5, 350.00, 'Travel', '2026-04-27', '2026-04-27 12:00:00', 'Delta Airlines', FALSE, '4511', 'USD', 1.0000),
    (6, 65.00, 'Dining', '2026-04-30', '2026-04-30 18:30:00', 'Chipotle', FALSE, '5814', 'USD', 1.0000),
    (6, 200.00, 'Health', '2026-04-26', '2026-04-26 10:00:00', 'CVS Pharmacy', FALSE, '5912', 'USD', 1.0000),
    (7, 2500.00, 'Shopping', '2026-04-30', '2026-04-30 16:00:00', 'Gucci Store', FALSE, '5921', 'USD', 1.0000),
    (7, 800.00, 'Restaurants', '2026-04-25', '2026-04-25 20:00:00', 'Michelin Restaurant', FALSE, '5812', 'USD', 1.0000),
    (8, 35.50, 'Groceries', '2026-04-30', '2026-04-30 09:30:00', 'Walmart', FALSE, '5411', 'USD', 1.0000),
    (8, 15.00, 'Entertainment', '2026-04-28', '2026-04-28 19:00:00', 'Movie Ticket', FALSE, '7832', 'USD', 1.0000),
    (9, 600.00, 'Business', '2026-04-30', '2026-04-30 14:00:00', 'Microsoft Azure SaaS', FALSE, '7379', 'USD', 1.0000),
    (9, 250.00, 'Travel', '2026-04-24', '2026-04-24 10:00:00', 'British Airways', FALSE, '4511', 'USD', 1.0000),
    (10, 89.99, 'Shopping', '2026-04-30', '2026-04-30 15:45:00', 'H&M', FALSE, '5651', 'USD', 1.0000),
    (10, 45.00, 'Utilities', '2026-04-23', '2026-04-23 08:00:00', 'Water Company', FALSE, '4900', 'USD', 1.0000),
    (11, 750.00, 'Business', '2026-04-30', '2026-04-30 09:00:00', 'Google Cloud Platform', FALSE, '7374', 'USD', 1.0000),
    (11, 180.00, 'Dining', '2026-04-22', '2026-04-22 19:30:00', 'Fine Dining Restaurant', FALSE, '5812', 'USD', 1.0000),
    (12, 56.00, 'Groceries', '2026-04-30', '2026-04-30 10:00:00', 'Whole Foods Market', FALSE, '5411', 'USD', 1.0000),
    (12, 99.99, 'Shopping', '2026-04-29', '2026-04-29 14:00:00', 'Zara', FALSE, '5651', 'USD', 1.0000),
    (13, 500.00, 'Business', '2026-04-30', '2026-04-30 13:30:00', 'Salesforce CRM Package', FALSE, '7372', 'USD', 1.0000),
    (13, 120.00, 'Entertainment', '2026-04-21', '2026-04-21 20:00:00', 'Concert Tickets', FALSE, '7922', 'USD', 1.0000),
    (14, 310.00, 'Shopping', '2026-04-30', '2026-04-30 12:00:00', 'Hermès Store', FALSE, '5921', 'USD', 1.0000),
    (14, 200.00, 'Health', '2026-04-20', '2026-04-20 10:00:00', 'Private Hospital', FALSE, '8062', 'USD', 1.0000),
    (15, 78.00, 'Dining', '2026-04-30', '2026-04-30 19:00:00', 'Irish Pub', FALSE, '5813', 'USD', 1.0000),
    (15, 130.00, 'Shopping', '2026-04-19', '2026-04-19 16:00:00', 'Nike Store', FALSE, '5651', 'USD', 1.0000);

-- ====================================================================
-- VERIFY SEED DATA
-- ====================================================================
SELECT COUNT(*) as total_customers FROM customers;
SELECT COUNT(*) as total_transactions FROM raw_transactions;
SELECT * FROM daily_kpis ORDER BY date DESC LIMIT 5;

-- ====================================================================
-- END OF SEED DATA
-- ====================================================================
