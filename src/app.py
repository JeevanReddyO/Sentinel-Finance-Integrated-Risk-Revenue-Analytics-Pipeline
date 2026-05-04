"""
SENTINEL FINANCE: Operational Dashboard (Streamlit)
==================================================
Real-time banking risk and revenue analytics dashboard for bank managers.
Features:
- Customer risk lookup and profiling
- Real-time KPI metrics
- Fraud detection alerts
- 7-day spending trends
- Credit limit utilization analysis
"""

import sys
import logging
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy import text

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import (
    STREAMLIT_PAGE_CONFIG,
    STREAMLIT_CACHE_TTL,
    STREAMLIT_CHART_HEIGHT,
    CREDIT_UTILIZATION_HIGH_RISK,
    CREDIT_UTILIZATION_MEDIUM_RISK,
)
from config.database import get_db_connection, test_database_connection

# ====================================================================
# PAGE CONFIGURATION
# ====================================================================
st.set_page_config(**STREAMLIT_PAGE_CONFIG)

# ====================================================================
# LOGGING SETUP
# ====================================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ====================================================================
# CACHED DATABASE OPERATIONS
# ====================================================================
@st.cache_data(ttl=STREAMLIT_CACHE_TTL)
def get_database_status():
    """Get database connectivity status."""
    try:
        status = test_database_connection()
        return status["status"] == "connected"
    except:
        return False

@st.cache_data(ttl=STREAMLIT_CACHE_TTL)
def fetch_daily_kpis():
    """Fetch aggregate daily KPIs from database."""
    query = """
    SELECT
        date,
        active_customers,
        total_transactions,
        total_spend,
        avg_transaction_amount,
        fraud_transactions_flagged,
        fraud_rate_percent,
        high_risk_customer_percent
    FROM daily_kpis
    ORDER BY date DESC
    LIMIT 1;
    """
    
    try:
        with get_db_connection() as conn:
            result = conn.execute(text(query))
            row = result.fetchone()
            if row:
                return {
                    "date": row[0],
                    "active_customers": row[1],
                    "total_transactions": row[2],
                    "total_spend": row[3],
                    "avg_transaction_amount": row[4],
                    "fraud_transactions_flagged": row[5],
                    "fraud_rate_percent": row[6],
                    "high_risk_customer_percent": row[7],
                }
            return None
    except Exception as e:
        logger.error(f"❌ Error fetching KPIs: {str(e)}")
        return None

@st.cache_data(ttl=STREAMLIT_CACHE_TTL)
def fetch_all_customers():
    """Fetch all customers for lookup."""
    query = """
    SELECT customer_id, name, risk_score, credit_limit, region, status
    FROM customers
    ORDER BY name;
    """
    
    try:
        with get_db_connection() as conn:
            df = pd.read_sql_query(query, conn)
            return df
    except Exception as e:
        logger.error(f"❌ Error fetching customers: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=STREAMLIT_CACHE_TTL)
def fetch_customer_profile(customer_id: int):
    """Fetch detailed customer profile."""
    query = """
    SELECT
        customer_id, name, age, annual_income, region, risk_score,
        credit_limit, status, created_at
    FROM customers
    WHERE customer_id = :customer_id;
    """
    
    try:
        with get_db_connection() as conn:
            result = conn.execute(text(query), {"customer_id": customer_id})
            row = result.fetchone()
            if row:
                return {
                    "customer_id": row[0],
                    "name": row[1],
                    "age": row[2],
                    "annual_income": row[3],
                    "region": row[4],
                    "risk_score": row[5],
                    "credit_limit": row[6],
                    "status": row[7],
                    "created_at": row[8],
                }
            return None
    except Exception as e:
        logger.error(f"❌ Error fetching customer profile: {str(e)}")
        return None

@st.cache_data(ttl=STREAMLIT_CACHE_TTL)
def fetch_customer_daily_metrics(customer_id: int, days: int = 7):
    """Fetch customer's daily spending metrics."""
    query = f"""
    SELECT
        date, transaction_count, daily_spend, utilization_ratio_percent,
        fraud_flags, highest_transaction, risk_category
    FROM customer_daily_metrics
    WHERE customer_id = %(customer_id)s
        AND date >= CURRENT_DATE - INTERVAL '{days} days'
    ORDER BY date DESC;
    """
    
    try:
        with get_db_connection() as conn:
            df = pd.read_sql_query(
                query,
                conn,
                params={"customer_id": customer_id}
            )
            return df
    except Exception as e:
        logger.error(f"❌ Error fetching customer metrics: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=STREAMLIT_CACHE_TTL)
def fetch_customer_transactions(customer_id: int, days: int = 7):
    """Fetch recent transactions for a customer."""
    query = f"""
    SELECT
        transaction_id, transaction_date, transaction_time, merchant,
        amount, category, is_fraud, currency_code
    FROM raw_transactions
    WHERE customer_id = %(customer_id)s
        AND transaction_date >= CURRENT_DATE - INTERVAL '{days} days'
    ORDER BY transaction_time DESC
    LIMIT 50;
    """
    
    try:
        with get_db_connection() as conn:
            df = pd.read_sql_query(
                query,
                conn,
                params={"customer_id": customer_id}
            )
            return df
    except Exception as e:
        logger.error(f"❌ Error fetching transactions: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=STREAMLIT_CACHE_TTL)
def fetch_fraud_alerts(limit: int = 20):
    """Fetch recent fraud alerts."""
    query = """
    SELECT
        customer_id, name, transaction_date, merchant, amount,
        risk_score, fraud_flags, risk_category
    FROM customer_daily_metrics
    WHERE fraud_flags > 0 OR risk_category = 'HIGH RISK'
    ORDER BY transaction_date DESC
    LIMIT %(limit)s;
    """
    
    try:
        with get_db_connection() as conn:
            df = pd.read_sql_query(
                query,
                conn,
                params={"limit": limit}
            )
            return df
    except Exception as e:
        logger.error(f"❌ Error fetching fraud alerts: {str(e)}")
        return pd.DataFrame()

# ====================================================================
# UI COMPONENTS
# ====================================================================
def render_metric_card(title: str, value, subtitle: str = "", color: str = "blue"):
    """Render a metric card."""
    col_metric = st.container()
    
    with col_metric:
        if isinstance(value, float):
            st.metric(label=title, value=f"{value:,.2f}", label_visibility="collapsed")
        else:
            st.metric(label=title, value=f"{value:,.0f}", label_visibility="collapsed")
    
    return col_metric

def get_risk_level_color(risk_score: float):
    """Return color based on risk score."""
    if risk_score >= 70:
        return "🔴"  # High risk
    elif risk_score >= 50:
        return "🟡"  # Medium risk
    else:
        return "🟢"  # Low risk

def get_utilization_color(utilization_ratio: float):
    """Return color based on credit utilization ratio."""
    if utilization_ratio >= CREDIT_UTILIZATION_HIGH_RISK:
        return "🔴"  # High risk
    elif utilization_ratio >= CREDIT_UTILIZATION_MEDIUM_RISK:
        return "🟡"  # Medium risk
    else:
        return "🟢"  # Low risk

# ====================================================================
# PAGE: DASHBOARD
# ====================================================================
def page_dashboard():
    """Main dashboard page with KPIs."""
    st.title("🛡️ Sentinel Finance - Risk & Revenue Dashboard")
    st.markdown("---")
    
    # Check database connection
    if not get_database_status():
        st.error("❌ Database connection failed. Please check your database configuration.")
        return
    
    # Fetch KPIs
    kpis = fetch_daily_kpis()
    
    if not kpis:
        st.warning("⚠️ No data available. Please run the ETL pipeline first.")
        return
    
    st.markdown("### 📊 24-Hour Key Performance Indicators")
    
    # Create metric columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Revenue (24h)",
            f"${kpis['total_spend']:,.2f}",
            delta=f"{kpis['active_customers']:.0f} customers"
        )
    
    with col2:
        st.metric(
            "Transactions Processed",
            f"{kpis['total_transactions']:.0f}",
            delta=f"Avg: ${kpis['avg_transaction_amount']:.2f}"
        )
    
    with col3:
        st.metric(
            "Fraud Alerts",
            f"{kpis['fraud_transactions_flagged']:.0f}",
            delta=f"{kpis['fraud_rate_percent']:.2f}%"
        )
    
    with col4:
        st.metric(
            "High Risk Customers",
            f"{kpis['high_risk_customer_percent']:.1f}%",
            delta="Of active base"
        )
    
    st.markdown("---")
    
    # KPI Details
    st.markdown("### 📈 Detailed Metrics")
    kpi_df = pd.DataFrame([
        {"Metric": "Date", "Value": str(kpis['date'])},
        {"Metric": "Active Customers", "Value": f"{kpis['active_customers']:.0f}"},
        {"Metric": "Total Transactions", "Value": f"{kpis['total_transactions']:.0f}"},
        {"Metric": "Total Spend", "Value": f"${kpis['total_spend']:,.2f}"},
        {"Metric": "Average Transaction", "Value": f"${kpis['avg_transaction_amount']:,.2f}"},
        {"Metric": "Fraud Transactions", "Value": f"{kpis['fraud_transactions_flagged']:.0f}"},
        {"Metric": "Fraud Rate", "Value": f"{kpis['fraud_rate_percent']:.2f}%"},
    ])
    
    st.dataframe(kpi_df, use_container_width=True, hide_index=True)

# ====================================================================
# PAGE: CUSTOMER RISK LOOKUP
# ====================================================================
def page_customer_lookup():
    """Customer lookup and risk profiling page."""
    st.title("🔍 Customer Risk Lookup")
    st.markdown("---")
    
    # Get all customers
    customers_df = fetch_all_customers()
    
    if customers_df.empty:
        st.error("❌ No customers found in database.")
        return
    
    # Create search interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        customer_name = st.selectbox(
            "Search by Customer Name:",
            customers_df['name'].tolist(),
            key="customer_select"
        )
    
    # Get selected customer ID
    selected_customer = customers_df[customers_df['name'] == customer_name].iloc[0]
    customer_id = selected_customer['customer_id']
    
    # Fetch customer profile
    profile = fetch_customer_profile(customer_id)
    
    if not profile:
        st.error("❌ Could not load customer profile.")
        return
    
    st.markdown("---")
    st.markdown("### 👤 Customer Profile")
    
    # Profile cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Name", profile['name'])
    
    with col2:
        st.metric("Age", f"{profile['age']} years")
    
    with col3:
        st.metric("Region", profile['region'])
    
    with col4:
        status_emoji = "✅" if profile['status'] == "ACTIVE" else "❌"
        st.metric("Status", f"{status_emoji} {profile['status']}")
    
    st.markdown("---")
    
    # Risk Analysis
    st.markdown("### ⚠️ Risk Assessment")
    
    col1, col2, col3 = st.columns(3)
    
    risk_icon = get_risk_level_color(profile['risk_score'])
    with col1:
        st.metric(
            f"{risk_icon} Risk Score",
            f"{profile['risk_score']:.1f}/100"
        )
    
    with col2:
        st.metric("Annual Income", f"${profile['annual_income']:,.2f}")
    
    with col3:
        st.metric("Credit Limit", f"${profile['credit_limit']:,.2f}")
    
    st.markdown("---")
    
    # Daily Metrics & Spending Trend
    st.markdown("### 📊 7-Day Spending Analysis")
    
    daily_metrics = fetch_customer_daily_metrics(customer_id)
    
    if not daily_metrics.empty:
        # Sort by date ascending for chart
        daily_metrics_sorted = daily_metrics.sort_values('date', ascending=True)
        
        # Create spending trend chart
        fig_trend = go.Figure()
        
        fig_trend.add_trace(go.Scatter(
            x=daily_metrics_sorted['date'],
            y=daily_metrics_sorted['daily_spend'],
            mode='lines+markers',
            name='Daily Spend',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=8)
        ))
        
        fig_trend.update_layout(
            title="7-Day Spending Trend",
            xaxis_title="Date",
            yaxis_title="Daily Spend ($)",
            height=STREAMLIT_CHART_HEIGHT,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_trend, use_container_width=True)
        
        # Utilization metrics
        st.markdown("### 💳 Credit Utilization Analysis")
        
        current_utilization = daily_metrics_sorted.iloc[-1]['utilization_ratio_percent'] if not daily_metrics_sorted.empty else 0
        util_icon = get_utilization_color(current_utilization)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                f"{util_icon} Current Utilization",
                f"{current_utilization:.1f}%"
            )
        
        with col2:
            latest_spend = daily_metrics_sorted.iloc[-1]['daily_spend'] if not daily_metrics_sorted.empty else 0
            st.metric("Latest Daily Spend", f"${latest_spend:,.2f}")
        
        with col3:
            avg_spend = daily_metrics_sorted['daily_spend'].mean()
            st.metric("7-Day Avg Spend", f"${avg_spend:,.2f}")
        
        # Risk indicator
        if current_utilization >= CREDIT_UTILIZATION_HIGH_RISK:
            st.error(f"🚨 **HIGH RISK**: Customer has used {current_utilization:.1f}% of credit limit")
        elif current_utilization >= CREDIT_UTILIZATION_MEDIUM_RISK:
            st.warning(f"⚠️ **MEDIUM RISK**: Customer has used {current_utilization:.1f}% of credit limit")
        else:
            st.success(f"✅  **LOW RISK**: Customer has used {current_utilization:.1f}% of credit limit")
        
        # Daily metrics table
        st.markdown("---")
        st.markdown("### 📋 Daily Metrics Table")
        
        display_df = daily_metrics_sorted[[
            'date', 'transaction_count', 'daily_spend',
            'utilization_ratio_percent', 'fraud_flags', 'risk_category'
        ]].copy()
        
        display_df = display_df.rename(columns={
            'date': 'Date',
            'transaction_count': 'Transactions',
            'daily_spend': 'Daily Spend',
            'utilization_ratio_percent': 'Util %',
            'fraud_flags': 'Fraud Flags',
            'risk_category': 'Risk'
        })
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Transactions table
        st.markdown("---")
        st.markdown("### 💰 Recent Transactions (Last 7 Days)")
        
        transactions = fetch_customer_transactions(customer_id)
        
        if not transactions.empty:
            display_txn = transactions[[
                'transaction_date', 'transaction_time', 'merchant',
                'amount', 'category', 'is_fraud'
            ]].copy()
            
            display_txn['is_fraud'] = display_txn['is_fraud'].apply(
                lambda x: "🚨 FRAUD" if x else "✅ OK"
            )
            
            display_txn = display_txn.rename(columns={
                'transaction_date': 'Date',
                'transaction_time': 'Time',
                'merchant': 'Merchant',
                'amount': 'Amount ($)',
                'category': 'Category',
                'is_fraud': 'Status'
            })
            
            st.dataframe(display_txn, use_container_width=True, hide_index=True)
        else:
            st.info("No transactions found for this period.")
    else:
        st.info("No spending data available for this customer yet.")

# ====================================================================
# PAGE: FRAUD ALERTS
# ====================================================================
def page_fraud_alerts():
    """Fraud alerts and high-risk customers page."""
    st.title("🚨 Active Fraud & Risk Alerts")
    st.markdown("---")
    
    alerts = fetch_fraud_alerts()
    
    if alerts.empty:
        st.success("✅ No fraud alerts detected in the last 24 hours.")
        return
    
    st.warning(f"⚠️ **{len(alerts)}** High-Risk Customers or Fraudulent Transactions Detected")
    
    # Create visualization
    alert_by_risk = alerts['risk_category'].value_counts()
    
    fig = px.pie(
        values=alert_by_risk.values,
        names=alert_by_risk.index,
        title="Alert Distribution by Risk Category",
        color_discrete_sequence=['#d62728', '#ff7f0e', '#2ca02c']
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    st.markdown("### 📋 Detailed Alerts Table")
    
    display_alerts = alerts[[
        'customer_id', 'name', 'transaction_date', 'risk_score',
        'fraud_flags', 'risk_category'
    ]].copy()
    
    display_alerts = display_alerts.rename(columns={
        'customer_id': 'Customer ID',
        'name': 'Name',
        'transaction_date': 'Latest Date',
        'risk_score': 'Risk Score',
        'fraud_flags': 'Fraud Count',
        'risk_category': 'Risk Level'
    })
    
    st.dataframe(display_alerts, use_container_width=True, hide_index=True)

# ====================================================================
# PAGE: POWER BI
# ====================================================================
def page_power_bi():
    """Power BI integration instructions and data source guidance."""
    st.title("📈 Power BI Integration")
    st.markdown("---")
    st.markdown(
        """
        ## Connect Power BI to Sentinel Finance

        Use Power BI Desktop to connect directly to the PostgreSQL database.

        **Connection settings**:
        - **Server**: `localhost`
        - **Database**: `bank_db`
        - **Username**: `postgres`
        - **Password**: `Jeevan`

        **Recommended workflow**:
        1. Open **Power BI Desktop**.
        2. Select **Get Data** → **PostgreSQL database**.
        3. Enter the connection settings above.
        4. Choose **DirectQuery** for live analytics, or **Import** for offline reporting.
        5. Select the views and tables:
           - `daily_kpis`
           - `customer_daily_metrics`
           - `raw_transactions`
           - `customers`

        **Power BI tips**:
        - Use `daily_kpis` for executive KPI cards.
        - Use `customer_daily_metrics` for customer risk analysis.
        - Use `raw_transactions` for transaction-level reporting.
        - Use `customers` to join customer demographic and risk data.

        ### Optional custom SQL
        Use this query in Power BI to seed your report with active customers and spend:

        ```sql
        SELECT d.date,
               d.active_customers,
               d.total_transactions,
               d.total_spend,
               c.region,
               c.risk_score
        FROM daily_kpis d
        LEFT JOIN customers c ON c.customer_id = (
           SELECT customer_id FROM raw_transactions r
           WHERE r.transaction_date = d.date
           LIMIT 1
        );
        ```

        For best performance, model the data in Power BI using the views as star schema sources.
        """
    )
    st.markdown(
        "<p><a href='https://app.powerbi.com/' target='_blank' style='font-size:16px;font-weight:bold;color:#ffffff;background-color:#0078d7;padding:10px 16px;border-radius:6px;text-decoration:none;'>Open Power BI Service</a></p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p>If you have Power BI Desktop installed, open the app and connect to the PostgreSQL database using the details above.</p>",
        unsafe_allow_html=True,
    )

# ====================================================================
# PAGE: ABOUT
# ====================================================================
def page_about():
    """About page with project information."""
    st.title("ℹ️ About Sentinel Finance")
    st.markdown("---")
    
    st.markdown("""
    ## 🛡️ Sentinel Finance: Banking Risk & Revenue Intelligence
    
    **Subtitle:** Automated ETL pipeline and Operational Dashboard for banking risk mitigation
    
    ### Project Overview
    Sentinel Finance is an end-to-end automated data pipeline designed for modern banking operations.
    It extracts transaction data, enriches it with real-time market context, and provides intelligent
    risk assessments to help bank managers make faster, data-driven decisions.
    
    ### Key Features
    - **Real-Time Risk Scoring**: Automatic customer risk assessment based on spending patterns
    - **Fraud Detection**: Automated flagging of suspicious transactions
    - **KPI Dashboards**: Live metrics for bank revenue and customer activity
    - **7-Day Insights**: Customer spending trends and credit utilization analysis
    - **Automated ETL**: Daily data refresh via GitHub Actions
    - **Power BI Integration**: Executive dashboards via direct query
    
    ### Technology Stack
    - **Data Layer**: PostgreSQL with upsert logic for idempotent updates
    - **ETL Pipeline**: Python with Pandas, SQLAlchemy, Faker, and requests
    - **Analytics API**: Alpha Vantage for real-time currency exchange rates
    - **Operational Dashboard**: Streamlit with Plotly visualizations
    - **BI Platform**: Power BI with DirectQuery connectivity
    - **Orchestration**: GitHub Actions for automated scheduling
    
    ### Schema Components
    - **customers**: Master dimension table with risk scores and credit limits
    - **raw_transactions**: Fact table with UPSERT-capable daily ingestion
    - **daily_kpis**: Aggregated daily metrics view
    - **customer_daily_metrics**: Per-customer daily risk assessment view
    
    ### Key Metrics
    - **Fraud Detection Rate**: Percentage of flagged transactions
    - **Customer Utilization Ratio**: Spend as percentage of credit limit
    - **Risk Score**: 0-100 scale based on spending behavior and defaults
    - **Daily Revenue**: Sum of transaction amounts processed
    
    ### Risk Logic
    - 🟢 **Low Risk**: Utilization < 50%, Risk Score < 50
    - 🟡 **Medium Risk**: Utilization 50-80%, Risk Score 50-70
    - 🔴 **High Risk**: Utilization > 80%, Risk Score > 70
    
    ### Version
    **v1.0.0** - Production Ready
    
    ---
    
    **Developed by:** Senior Data Engineer & Financial Analyst  
    **Date:** April 2026  
    **License:** MIT
    """)

# ====================================================================
# MAIN APP
# ====================================================================
def main():
    """Main Streamlit application."""
    # Sidebar navigation
    st.sidebar.title("🛡️ Sentinel Finance")
    
    page_options = {
        "📊 Dashboard": page_dashboard,
        "🔍 Customer Lookup": page_customer_lookup,
        "🚨 Fraud Alerts": page_fraud_alerts,
        "📈 Power BI": page_power_bi,
    }
    
    selected_page = st.sidebar.radio("Navigation", page_options.keys())
    
    # Display selected page
    page_options[selected_page]()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    **Sentinel Finance v1.0.0**  
    Banking Risk & Revenue Intelligence  
    Updated: April 30, 2026
    """)

if __name__ == "__main__":
    main()
