# Quick Start Guide

Get up and running in 5 minutes!

## 1. Setup Virtual Environment ✅

```bash
# Already done! Your venv is set up with all dependencies
source venv/bin/activate
```

## 2. Your Snowflake Connection ✅

Your `.env` file is configured with:
- Account: FOB96555
- User: ITSHTTP
- Warehouse: MY_FIRST_WH
- Database: MY_DATABASE
- Schema: PUBLIC

**Connection tested:** ✅ Working!

## 3. Data in Snowflake ✅

Currently loaded:
- **ACCOUNT_ATTRIBUTES_MONTHLY**: 1,218 rows
- **PHONE_USAGE_DATA**: 3,528 rows
- **CHURN_RECORDS**: 10 rows

## 4. Launch the Dashboard 🚀

### Option A: Use the Launch Script (Easiest)

```bash
./start_dashboard.sh
```

### Option B: Run Directly

```bash
streamlit run streamlit_app.py
```

Dashboard opens at: **http://localhost:8501**

## 5. Explore the Dashboard

Navigate using the sidebar:

1. **🏠 Overview** - Start here for KPIs and high-level trends
2. **👥 Account Analytics** - Account distribution and growth
3. **📈 Usage Trends** - Time series and usage patterns
4. **⚠️ Churn Analysis** - Churn prediction and patterns
5. **🎯 User Segmentation** - Heavy/medium/light user analysis

### Interactive Filters

- **Date Range**: Filter by time period
- **Company**: Filter by specific company

## Common Tasks

### Refresh Data from Snowflake

```bash
# The dashboard auto-caches for 5 minutes
# To force refresh, press 'C' in the browser
# Or restart the dashboard
```

### Generate New Data

```bash
# Run in Python or Jupyter
from function import generate_all_tables

account_df, usage_df, churn_df = generate_all_tables(
    non_active_ratio=0.05,
    num_months=36,
    save_to_csv=True
)

# Load to Snowflake
from snowflake_loader import load_all_data

load_all_data(
    from_dataframes=True,
    account_df=account_df,
    usage_df=usage_df,
    churn_df=churn_df,
    truncate=True  # Replace existing data
)
```

### Query Snowflake Directly

```sql
-- In Snowflake UI
SELECT COUNT(*) FROM ACCOUNT_ATTRIBUTES_MONTHLY;
SELECT COUNT(*) FROM PHONE_USAGE_DATA;
SELECT COUNT(*) FROM CHURN_RECORDS;
```

## Troubleshooting

### Dashboard won't start

```bash
# Check if Streamlit is installed
pip list | grep streamlit

# Reinstall if needed
pip install streamlit plotly
```

### No data showing

```bash
# Verify Snowflake connection
python snowflake_loader.py --test

# Check data exists
python snowflake_loader.py --summary
```

### Connection errors

```bash
# Check .env file exists
cat .env

# Test connection
python snowflake_loader.py --test
```

## Next Steps

1. ✅ Dashboard is running
2. 📊 Explore the visualizations
3. 🎯 Filter data by date/company
4. 📈 Analyze churn patterns
5. 💡 Share insights with team

## Need Help?

- **Dashboard Guide**: [STREAMLIT_DASHBOARD.md](STREAMLIT_DASHBOARD.md)
- **Snowflake Setup**: [SNOWFLAKE_SETUP.md](SNOWFLAKE_SETUP.md)
- **Full README**: [README.md](README.md)

## Quick Commands Reference

```bash
# Start dashboard
./start_dashboard.sh

# Test Snowflake connection
python snowflake_loader.py --test

# Show table summary
python snowflake_loader.py --summary

# Load data to Snowflake
python snowflake_loader.py

# Run Jupyter notebook
jupyter notebook test_functions.ipynb
```

Happy analyzing! 📊✨
