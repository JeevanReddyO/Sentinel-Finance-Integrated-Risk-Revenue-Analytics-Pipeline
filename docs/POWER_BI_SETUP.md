# 📊 Power BI Integration Guide for Sentinel Finance

**Executive Dashboard Setup Using DirectQuery**

---

## 📑 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Step-by-Step Setup](#step-by-step-setup)
4. [Dashboard Components](#dashboard-components)
5. [DAX Formulas](#dax-formulas)
6. [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

Power BI provides an executive dashboard for real-time banking analytics. By connecting directly to PostgreSQL via DirectQuery, your Power BI reports are always in sync with the latest data.

### Benefits
- ✅ Real-time data (no import lag)
- ✅ Live KPIs updated instantly
- ✅ Executive-ready visualizations
- ✅ Drill-down capabilities
- ✅ Mobile-friendly dashboards

### Architecture
```
PostgreSQL Database
      ↓
  DirectQuery
      ↓
Power BI Desktop
      ↓
Power BI Service (Online)
      ↓
Executive Dashboard
```

---

## 📦 Prerequisites

### Software
- **Power BI Desktop** (Free) - [Download](https://powerbi.microsoft.com/desktop/)
- **Power BI Service** (Optional for sharing)
  - Pro License: $9.99/month per user
  - Premium Capacity: $4,995/month

### Database Access
- PostgreSQL host: `your-postgres-host.com`
- Database: `bank_db`
- Username: `postgres`
- Password: (secure)
- Port: `5432`

### Network
- Power BI must be able to reach PostgreSQL
- Standard port 5432 should be open
- Consider using SSL for security

---

## 🔧 Step-by-Step Setup

### Phase 1: Power BI Desktop Installation

1. **Download Power BI Desktop**
   - Go to [powerbi.microsoft.com/desktop](https://powerbi.microsoft.com/desktop/)
   - Click "Download Free"
   - Run installer

2. **Launch Power BI Desktop**
   - Click Start
   - Search for "Power BI Desktop"
   - Open application

3. **Create Workspace**
   - File > New
   - Name: "Sentinel Finance Banking Analytics"
   - Set as default workspace

### Phase 2: Connect to PostgreSQL

1. **Get Data**
   - Home tab > Get data > More...
   - Search for "PostgreSQL"
   - Click "Connect"

2. **PostgreSQL Connection Dialog**
   - **Server:** your-db-host.com (or localhost)
   - **Database:** bank_db
   - Click "OK"

3. **Authentication**
   - Click "Database"
   - **User name:** postgres
   - **Password:** [your password]
   - Click "Connect"

4. **Navigator Window**
   - Expand "bank_db"
   - Select tables/views:
     - ✅ customers
     - ✅ raw_transactions
     - ✅ daily_kpis
     - ✅ customer_daily_metrics
   - Click "Load"

### Phase 3: Data Modeling

Once data is loaded, you'll see three tabs:
- **Report** - Create visualizations
- **Data** - View tables
- **Model** - Configure relationships

**No additional modeling needed!** PostgreSQL relationships auto-import.

### Phase 4: Create Executive Dashboard

#### 1. KPI Cards (Top Section)

**Card 1: Today's Revenue**
- Field: `daily_kpis[total_spend]`
- Filter: date = TODAY()
- Number format: Currency ($)
- Target: $50,000

**Card 2: Transaction Count**
- Field: `daily_kpis[total_transactions]`
- Filter: date = TODAY()
- Number format: Number
- Target: 5,000

**Card 3: Fraud Alert Count**
- Field: `daily_kpis[fraud_transactions_flagged]`
- Filter: date = TODAY()
- Number format: Number (red for >50)

**Card 4: Active Customers**
- Field: `daily_kpis[active_customers]`
- Filter: date = TODAY()
- Filter: status = 'ACTIVE'

#### 2. Line Chart: 30-Day Revenue Trend

**Visualization:** Line Chart
```
X-Axis: daily_kpis[date]
Y-Axis: SUM(daily_kpis[total_spend])
Filter: date >= TODAY()-30
```

**Formatting:**
- Title: "Revenue Trend (30 Days)"
- X-axis label: "Date"
- Y-axis label: "Revenue ($)"
- Trend line: ✅ Enabled

#### 3. Clustered Column Chart: Daily KPI Metrics

**Visualization:** Clustered Column Chart
```
X-Axis: daily_kpis[date]
Y-Axis1: SUM(daily_kpis[total_transactions])
Y-Axis2: DIVIDE(SUM(daily_kpis[fraud_transactions_flagged]), SUM(daily_kpis[total_transactions]), 0) * 100
```

**Legend:** Two series (blue for txns, red for fraud %)

#### 4. Scatter Plot: Risk vs. Spend

**Visualization:** Scatter Chart
```
X-Axis: customer_daily_metrics[utilization_ratio_percent]
Y-Axis: customers[risk_score]
Size: customer_daily_metrics[daily_spend]
Color: customer_daily_metrics[risk_category]
```

**Interpretation:**
- Top-right = High spend, high risk (red)
- Bottom-left = Low spend, low risk (green)
- Bubble size = Amount spent

#### 5. Map: Fraud by Region

**Visualization:** Map (if using regional data)
```
Location: customers[region]
Size: COUNT(raw_transactions[is_fraud=TRUE])
```

#### 6. Data Table: Top 10 At-Risk Customers

**Visualization:** Table
```
Columns:
- customers[name]
- customers[risk_score]
- customer_daily_metrics[utilization_ratio_percent]
- customer_daily_metrics[daily_spend]
- customer_daily_metrics[risk_category]

Sort by: risk_score DESC
Top N: 10
```

#### 7. Donut Chart: Transaction Category Distribution

**Visualization:** Donut Chart
```
Legend (Category): raw_transactions[category]
Values: COUNT(raw_transactions[transaction_id])
Filter: transaction_date = TODAY()
```

---

## 📐 DAX Formulas

### High-Risk Customers Count
```dax
High Risk Customers = 
CALCULATE(
    COUNTDISTINCT(customers[customer_id]),
    customers[risk_score] > 70
)
```

### Credit Utilization Rate (Average)
```dax
Avg Utilization % = 
AVERAGE(customer_daily_metrics[utilization_ratio_percent])
```

### Fraud Rate
```dax
Fraud Rate % = 
DIVIDE(
    CALCULATE(
        COUNT(raw_transactions[transaction_id]),
        raw_transactions[is_fraud] = TRUE()
    ),
    COUNT(raw_transactions[transaction_id]),
    0
) * 100
```

### 7-Day Revenue Change
```dax
Revenue vs Last Week % = 
VAR Current7Day = 
    CALCULATE(
        SUM(daily_kpis[total_spend]),
        DatesBetween(daily_kpis[date], TODAY()-7, TODAY())
    )
VAR Previous7Day = 
    CALCULATE(
        SUM(daily_kpis[total_spend]),
        DatesBetween(daily_kpis[date], TODAY()-14, TODAY()-7)
    )
RETURN
    DIVIDE(Current7Day - Previous7Day, Previous7Day, 0) * 100
```

### Total Customers
```dax
Total Customers = COUNTDISTINCT(customers[customer_id])
```

### Active Customers Today
```dax
Active Today = 
CALCULATE(
    DISTINCTCOUNT(raw_transactions[customer_id]),
    raw_transactions[transaction_date] = TODAY()
)
```

---

## 👁️ Dashboard Layout

### Typical Executive Dashboard
```
┌─────────────────────────────────────────────────────────┐
│         SENTINEL FINANCE - BANKING ANALYTICS DASHBOARD  │
├─────────────────────────────────────────────────────────┤
│  $258.5M    │  12,450    │    47 Alerts  │  4,820       │
│  Revenue    │ Transactions│   Fraud Flags  │  Customers   │
├─────────────────────────────────────────────────────────┤
│                    30-Day Revenue Trend                  │
│  [Line Chart showing upward trend with $50M-$60M range] │
├─────────────────────────────────────────────────────────┤
│  Daily KPI Metrics         │  Risk vs Spend Analysis    │
│  [Column Chart]            │  [Scatter Plot]            │
├─────────────────────────────────────────────────────────┤
│  Top 10 At-Risk Customers  │  Transaction Categories    │
│  [Data Table]              │  [Donut Chart]             │
├─────────────────────────────────────────────────────────┤
│  Fraud by Region           │  Utilization Heatmap       │
│  [Map Visualization]       │  [Heat Map]                │
└─────────────────────────────────────────────────────────┘
```

---

## 🔐 Security Considerations

### DirectQuery Security
- ✅ Queries execute on PostgreSQL server (not locally)
- ✅ Credentials stored securely in Power BI Service
- ✅ Row-level security (RLS) can be implemented
- ✅ Audit logs available in Power BI Premium

### SSL/TLS Connection
```
Database connection string with SSL:
Server=your-host;
Database=bank_db;
Port=5432;
SSL Mode=require;
```

### Row-Level Security (RLS)
For multi-department scenarios:

```dax
// DAX Security Rule
[Region] = USERNAME()
// Only shows data for user's region
```

---

## 📱 Publishing to Power BI Service

### Step 1: Create Power BI Account
1. Go to [powerbi.microsoft.com](https://powerbi.microsoft.com/)
2. Sign up with work account
3. Create workspace: "Sentinel Finance"

### Step 2: Publish from Desktop
1. Power BI Desktop > Publish
2. Select workspace: Sentinel Finance
3. Click "Select"

### Step 3: Configure Gateway (If Needed)
For on-premise PostgreSQL:
1. Install On-Premises Data Gateway
2. Configure PostgreSQL datasource
3. Enable in dataset settings
4. Schedule refresh: Daily at 01:00 UTC

### Step 4: Share Dashboard
1. Power BI Service > Sentinel Finance workspace
2. Click dashboard
3. Share > Enter email addresses
4. Role: Viewer (read-only)

---

## 🔄 Refresh Strategy

### DirectQuery (Recommended)
- Data updated in real-time
- Queries run on database
- Better for operational dashboards
- Slower for complex queries

**Set data refresh permissions:**
- Settings > Dataset settings
- Allow users to use DirectQuery
- No scheduled refresh needed

### Import Mode (Alternative)
- Scheduled refresh: Daily at 01:00 UTC
- Faster interactive experience
- Data lag up to 24 hours
- Better for large analytical queries

### Recommended Refresh Schedule
```
Daily Refresh:
  Trigger: 01:30 UTC (30 min after ETL completes)
  Frequency: Every day
  Retry policy: 2 retries if failed
```

---

## 📧 Email Subscriptions

Set up automated report emails:

1. **Create Subscription**
   - Dashboard > ... > Subscribe
   - Email address: executive@bank.com
   - Frequency: Daily
   - Time: 08:00 AM

2. **Email Content**
   - KPI summary cards
   - Key charts
   - Drill-down links

---

## 📞 Troubleshooting

### "Unable to connect to PostgreSQL"
```
✓ Verify PostgreSQL is running
✓ Check firewall allows port 5432
✓ Verify username/password
✓ Test with: psql -U postgres -h your-host -d bank_db
✓ For cloud (Supabase), use SSL Mode = require
```

### "Query timeout"
```
✓ Reduce data volume with filters
✓ Use Import mode instead of DirectQuery
✓ Create aggregated view instead of raw tables
✓ Increase Power BI query timeout: Settings > Options
```

### "Credentials have expired"
```
✓ Power BI Service > Settings > Datasources
✓ Edit credentials
✓ Re-enter PostgreSQL password
✓ Test connection
```

### "Row-level security (RLS) not working"
```
✓ Verify RLS rule syntax using DAX debugger
✓ Test with "View as" feature
✓ Check username values match database
✓ Publish RLS role to Power BI Service
```

---

## 📚 Additional Resources

### Official Microsoft Documentation
- [Power BI Documentation](https://learn.microsoft.com/en-us/power-bi/)
- [PostgreSQL Connector](https://learn.microsoft.com/en-us/power-query/connectors/postgresql)
- [DirectQuery Best Practices](https://learn.microsoft.com/en-us/power-bi/connect-data/desktop-directquery-about)

### DAX Learning
- [DAX Function Reference](https://learn.microsoft.com/en-us/dax/dax-function-reference)
- [DAX Patterns Website](https://daxpatterns.com/)

### Design Best Practices
- [Choose the right visualization](https://learn.microsoft.com/en-us/power-bi/visuals/power-bi-visualization-types-for-reports-and-q-and-a)
- [Dashboard design tips](https://learn.microsoft.com/en-us/power-bi/create-reports/service-dashboards)

---

## 🎬 Next Steps

1. ✅ Install Power BI Desktop
2. ✅ Connect to PostgreSQL
3. ✅ Load Sentinel Finance tables
4. ✅ Create executive dashboard
5. ✅ Publish to Power BI Service
6. ✅ Share with stakeholders
7. ✅ Set up email subscriptions

---

**Last Updated:** April 30, 2026  
**Power BI Version:** 2.110+  
**PostgreSQL:** 12+

**Ready to create your executive dashboard? Start with Step-by-Step Setup above!**
