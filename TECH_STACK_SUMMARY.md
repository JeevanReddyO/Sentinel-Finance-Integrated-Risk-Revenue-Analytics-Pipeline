# Tech Stack Summary


## Project Summary

Built a banking analytics pipeline that processes synthetic transaction data, enriches it with live currency rates, stores it in PostgreSQL, and surfaces operational insights through a Streamlit dashboard.

## Skills Applied

- Data engineering with Python and SQL
- Database schema design and analytics modeling
- ETL pipeline implementation and data validation
- Interactive dashboard development
- Automation with scheduled workflows

## Technologies Used

- **Python** for ETL, data processing, and dashboard logic
- **PostgreSQL** for transactional and analytical storage
- **SQLAlchemy** for database connectivity and query execution
- **Faker** for generating synthetic banking transactions
- **Alpha Vantage** for currency exchange enrichment
- **Streamlit** for the operational dashboard UI
- **Power BI** for executive reporting with DirectQuery live connections
- **Plotly** for interactive data visualizations
- **python-dotenv** for environment configuration management
- **GitHub Actions** for scheduled pipeline automation

## What I Delivered

- A clean PostgreSQL schema with `customers`, `raw_transactions`, and analytics views
- An idempotent ETL process with UPSERT support
- A Streamlit dashboard for KPIs, customer lookup, and fraud alerts with real-time updates
- Power BI integration with DirectQuery support for executive reporting and decision-making
- Production-oriented engineering practices like `.env` management, `.gitignore`, and diagnostic checks

## Business Value

This project enables real-time monitoring of revenue, transaction volume, and customer risk. It also provides a clear path for executive reporting through Power BI, making the data ready for decision-makers.
