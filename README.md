# 🛡️ Sentinel Finance: Banking Risk & Revenue Analytics Pipeline

**An integrated banking risk and revenue analytics system built with PostgreSQL, Python, Streamlit, and Power BI-ready business intelligence.**

---

## 🚀 Why this project matters

This project is designed for real-world banking operations where data must be:
- captured daily,
- enriched with market signals,
- validated for quality,
- stored reliably,
- and surfaced quickly for actionable decisions.

Sentinel Finance is not just a dashboard — it is a complete analytical pipeline that turns raw transaction data into customer risk insight and executive reporting.

---

## ✅ What this repo delivers

- Automated ETL pipeline for transaction generation, enrichment, and PostgreSQL loading
- PostgreSQL schema for customer, transaction, and analytics views
- Streamlit dashboard for live operations and customer risk lookup
- Power BI integration guidance for executive analytics
- Diagnostics, logging, and engineering-grade error handling
- GitHub Actions workflow for scheduled daily ETL

---

## 🧩 High-level architecture

```
                          +---------------------+
                          |  GitHub Actions     |
                          |  (daily ETL run)    |
                          +----------+----------+
                                     |
                                     ▼
               +-----------------------------+
               |       ETL Pipeline          |
               |       (src/extract.py)      |
               | - Faker synthetic data      |
               | - Alpha Vantage exchange    |
               | - Data cleaning & validation|
               | - PostgreSQL UPSERT         |
               +---------------+-------------+
                               |
                               ▼
               +-----------------------------+
               |      PostgreSQL Database     |
               | - customers                 |
               | - raw_transactions          |
               | - daily_kpis view           |
               | - customer_daily_metrics    |
               +---------------+-------------+
                               |
               +---------------+-------------+
               |   Data Consumers            |
               | - Streamlit dashboard       |
               | - Power BI recommendations  |
               +-----------------------------+
```

---

## 📌 What you will learn from this project

- how to build a resilient ETL pipeline from raw source to analytics-ready data
- how to design PostgreSQL schema and analytics views for banking use cases
- how to implement idempotent UPSERT logic in PostgreSQL
- how to build an operational dashboard using Streamlit
- how to prepare a project for enterprise BI consumption with Power BI
- how to troubleshoot environment, connection, and SQL issues

---

## 🛠️ Core technologies used

- **Python 3.8+** — application language
- **PostgreSQL** — transactional and analytical storage
- **SQLAlchemy** — Python database API
- **Streamlit** — dashboard UI
- **Faker** — synthetic transaction generation
- **Alpha Vantage** — exchange rate enrichment
- **python-dotenv** — environment configuration
- **GitHub Actions** — scheduled automation
- **Power BI** — enterprise reporting strategy

---

## 🚀 Quick start

### 1. Clone the repository
```bash
git clone https://github.com/<organization>/sentinel-finance.git
cd "Sentinel Finance Integrated Risk and Revenue Analytics Pipeline"
```

### 2. Create and activate the environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Prepare `.env`
Copy `.env.example` to `.env` in the project root and update the values with your PostgreSQL credentials and API key.

Example:
```ini
DATABASE_URL=postgresql://postgres:<your_password>@localhost:5432/bank_db
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=<your_password>
DB_NAME=bank_db
ALPHA_VANTAGE_API_KEY=<your_alpha_vantage_api_key>
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### 4. Initialize the database
```bash
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d bank_db -f "database/schema.sql"
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d bank_db -f "database/seed_data.sql"
```

### 5. Run diagnostics
```bash
python src/run_diagnostics.py
```

### 6. Run ETL
```bash
python src/extract.py
```

### 7. Launch dashboard
```bash
streamlit run src/app.py
```

Open `http://localhost:8501` in your browser.

---

## 🔧 Project structure explained

- `config/` — configuration and database connection management
- `database/` — schema and seed SQL files
- `src/` — ETL logic, dashboard UI, diagnostics
- `.github/workflows/` — scheduled ETL automation
- `requirements.txt` — package dependencies
- `.env` — local configuration values
- `project details.md` — narrative summary of work and engineering decisions

---

## 📘 What each module does

### `config/settings.py`
Loads environment variables, builds the SQLAlchemy URL, and centralizes constants.

### `config/database.py`
Creates the database engine and manages connection lifecycles.

### `database/schema.sql`
Defines the PostgreSQL tables, indexes, unique constraints, and analytics views.

### `database/seed_data.sql`
Populates the database with initial customers and transaction samples.

### `src/extract.py`
Executes the ETL process:
- generates synthetic transactions
- enriches records with exchange rates
- cleans and validates data
- loads data using UPSERT

### `src/app.py`
Delivers the operational dashboard and Power BI integration guidance.

### `src/run_diagnostics.py`
Verifies configuration, connectivity, dependencies, and API availability.

---

## 💡 Why this is a strong design

### 1. Resilience
- the ETL pipeline is idempotent through PostgreSQL UPSERT
- duplicate ingestion does not create duplicate rows

### 2. Observability
- diagnostics script validates environment and connectivity
- logging captures data pipeline behavior and errors

### 3. Modularity
- configuration, database, ETL, and UI are separated clearly
- each component can be extended independently

### 4. Business focus
- dashboard surfaces risk, fraud, and revenue metrics
- Power BI guidance bridges operational analytics to executive reporting

---

## 📈 Power BI integration

The project includes a dedicated Power BI page in the dashboard with:
- PostgreSQL connection settings
- recommended tables and views
- best practice for DirectQuery vs Import

Recommended sources:
- `customers`
- `raw_transactions`
- `daily_kpis`
- `customer_daily_metrics`

Since local desktop apps cannot be launched reliably from a browser, the page provides a service link and instructions instead.

---

## 🧪 Common challenges we overcame

### PostgreSQL connection issues
- resolved missing `psql` path by using the full PostgreSQL bin path
- fixed password mismatches in the `.env` file

### `.env` loading
- ensured `python-dotenv` loads configuration with `override=True`

### UPSERT syntax
- added the unique constraint required by `ON CONFLICT`
- switched to `ON CONFLICT ON CONSTRAINT uq_transactions_unique`

### SQL parameter style
- corrected `pd.read_sql_query` binding to use `%(param)s` syntax

---

## 🧠 Senior engineer notes

This repository is built to demonstrate production-grade analytics engineering. It is designed for business context, data reliability, and extensibility.

If you want, I can also add:
- a `Power BI` `pbix` starter template,
- a deployment checklist for cloud or containerized hosting,
- automated reporting email notifications,
- or a separate customer-facing analytics microservice.

---

## 📄 License
MIT License
