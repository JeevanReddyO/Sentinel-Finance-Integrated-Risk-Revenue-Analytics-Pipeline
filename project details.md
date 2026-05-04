# Project Details

This document is written from my side, as if I worked with you step-by-step on the Sentinel Finance pipeline project.

## What we built

We built a complete banking risk and revenue analytics pipeline with:
- PostgreSQL as the data store
- Python ETL pipeline to generate synthetic transactions, enrich data, and load it into the database
- Streamlit dashboard for operational analytics and customer lookup
- Power BI integration guidance for enterprise reporting
- GitHub Actions workflow scaffolding for daily ETL automation

## Step-by-step journey

### 1. Initial project setup

We created the project structure and added the main folders:
- `config/` for settings and database connection logic
- `database/` for schema SQL and seed data
- `src/` for the ETL and dashboard code
- `.github/workflows/` for automation

I helped you set up the environment with `requirements.txt` and `venv`.

### 2. Database configuration

We used PostgreSQL as our database engine.

Key pieces:
- `.env` stores secrets like `DATABASE_URL`, `DB_USER`, `DB_PASSWORD`, and `DB_NAME`
- `config/settings.py` reads environment variables and builds the SQLAlchemy connection string
- `config/database.py` creates a SQLAlchemy engine and manages safe connections

Example:
- `DATABASE_URL=postgresql://postgres:Jeevan@localhost:5432/bank_db`

This allowed the dashboard and ETL code to connect to the same database.

### 3. Schema design

In `database/schema.sql` we created:
- `customers` table for customer profile data
- `raw_transactions` table for transaction data
- `daily_kpis` view for daily aggregated metrics
- `customer_daily_metrics` view for customer-level metrics

We also added a `UNIQUE` constraint on `raw_transactions` so the UPSERT logic would work correctly.

### 4. Seed data and database initialization

I guided you to run:
- `psql -U postgres -d bank_db -f database/schema.sql`
- `psql -U postgres -d bank_db -f database/seed_data.sql`

Those commands created the schema and loaded the initial customer and transaction records.

### 5. ETL pipeline

The ETL pipeline is in `src/extract.py`.

It does:
- `TransactionGenerator` generates synthetic transactions with Faker
- `ExchangeRateFetcher` gets currency rates from Alpha Vantage
- `DataCleaner` removes invalid or duplicate rows
- `DataLoader` upserts transactions into PostgreSQL

We also added a database connection test before ETL proceeds.

### 6. Streamlit dashboard

The dashboard is in `src/app.py` and includes:
- Dashboard page with KPIs
- Customer lookup page
- Fraud alerts page
- Power BI integration page

I helped you remove the About page from the sidebar and add a Power BI page with instructions.

### 7. Power BI integration

Because Streamlit cannot directly launch desktop apps reliably, the Power BI page now:
- explains how to connect Power BI Desktop to PostgreSQL
- includes the connection settings
- adds a clickable link to Power BI Service

This makes the integration experience easier and more complete.

## Technical terms explained with examples

### PostgreSQL
PostgreSQL is the database engine we used to store customer and transaction data.

Example:
- We created `bank_db` and loaded tables into it.

### SQLAlchemy
SQLAlchemy is a Python library that talks to PostgreSQL.

Example:
- `create_engine(SQLALCHEMY_DATABASE_URL)` builds the connection

### ETL
ETL stands for Extract, Transform, Load.

Example:
- Extract: generate synthetic transactions
- Transform: clean the transactions and add currency data
- Load: insert them into the `raw_transactions` table

### UPSERT
UPSERT means update or insert.

Example:
- In `raw_transactions`, we used `ON CONFLICT ON CONSTRAINT uq_transactions_unique DO UPDATE...`
- That means if the same transaction appears twice, PostgreSQL updates it instead of inserting a duplicate.

### .env file
The `.env` file stores configuration values outside of the code.

Example:
- `DB_PASSWORD=Jeevan`
- The code reads it and builds the database URL automatically.

### Streamlit
Streamlit is a Python framework for building dashboards.

Example:
- `streamlit run src/app.py` starts the dashboard in your browser.

### Power BI DirectQuery
DirectQuery is a Power BI mode that queries the database live instead of importing data.

Example:
- Use Power BI Desktop with PostgreSQL and choose DirectQuery for real-time metrics.

## Prompts we used during the project

These were the important requests we worked from:
- "create a comprehensive Banking Risk & Revenue Analytics Pipeline"
- "create .env file properly to i have to included the api key that"
- "delete previous env example file"
- "pip install -r requirements.txt"
- "run the project getting errors while creaing dbs"
- "once check env"
- "updated env now run it"
- "i have installed postgreSQL and pg admin aslo running pathg of the psl folder"
- "createdb: error: database creation failed: ERROR: database 'bank_db' already exists"
- "remove about section from dashboard and correct the error in image customer lookup and aslso give power bi"
- "still that load issue and i also want power bi integration for the whole project if i click on power bi in side bar it should open the power bi app to show analytics"

## Challenges we faced and how we overcame them

### 1. PostgreSQL not accessible from terminal

Problem:
- `psql` was not found in PATH

Solution:
- used the full path `C:\Program Files\PostgreSQL\18\bin\psql.exe`
- verified the binaries exist

### 2. Password mismatch in `.env`

Problem:
- `DATABASE_URL` and `DB_PASSWORD` did not match

Solution:
- updated `.env` to use `postgresql://postgres:Jeevan@localhost:5432/bank_db`
- verified connection with `psql`

### 3. `.env` not loading in Python

Problem:
- Python was using defaults and not the updated `.env`

Solution:
- added `python-dotenv` loading in `config/settings.py`
- used `load_dotenv(DOTENV_PATH, override=True)`

### 4. UPSERT failure due to missing unique constraint

Problem:
- `ON CONFLICT (customer_id, transaction_date, transaction_time, merchant)` failed because there was no unique constraint

Solution:
- added `UNIQUE (customer_id, transaction_date, transaction_time, merchant)` to `raw_transactions`
- used `ON CONFLICT ON CONSTRAINT uq_transactions_unique`

### 5. Pandas SQL parameter syntax error

Problem:
- `pd.read_sql_query` failed on `:customer_id` syntax

Solution:
- switched to `%(customer_id)s` placeholders in the SQL queries
- kept `params={"customer_id": customer_id}` and `params={"limit": limit}` for safe query binding

### 6. Dashboard navigation and Power BI page

Problem:
- the Streamlit app still shown an About page and user wanted Power BI integration

Solution:
- removed the About page from the sidebar menu
- added a dedicated `📈 Power BI` page with PostgreSQL connection instructions
- included a link to Power BI Service and guidance for Power BI Desktop

## Final state of the project

After the fixes, the project now:
- connects successfully to PostgreSQL
- loads schema and seed data correctly
- runs the ETL pipeline without database errors
- displays the dashboard with customer lookup and fraud alerts
- provides Power BI integration guidance in the sidebar

This file is written in a human tone, from my perspective, describing everything we did together as one project.
