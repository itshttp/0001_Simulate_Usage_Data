# Complete Setup Guide for New Snowflake Space

This comprehensive guide will walk you through setting up the entire project on a brand new Snowflake account/space from scratch.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Step 1: Set Up Snowflake Resources](#step-1-set-up-snowflake-resources)
3. [Step 2: Set Up Python Environment](#step-2-set-up-python-environment)
4. [Step 3: Configure Credentials](#step-3-configure-credentials)
5. [Step 4: Install Dependencies](#step-4-install-dependencies)
6. [Step 5: Configure Data Generation](#step-5-configure-data-generation)
7. [Step 6: Generate Data](#step-6-generate-data)
8. [Step 7: Load Data to Snowflake](#step-7-load-data-to-snowflake)
9. [Step 8: Verify Data](#step-8-verify-data)
10. [Step 9: Deploy Dashboard (Optional)](#step-9-deploy-dashboard-optional)
11. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before starting, you need:

- ✅ A Snowflake account with login access
- ✅ Permissions to create warehouses, databases, schemas, and tables
- ✅ Python 3.8+ installed on your machine
- ✅ Access to Snowflake UI (https://app.snowflake.com)

---

## Step 1: Set Up Snowflake Resources

### 1.1 Log Into Snowflake

1. Go to your Snowflake URL: `https://app.snowflake.com/[ACCOUNT]/[ORG]/`
2. Log in with your credentials

### 1.2 Extract Your Snowflake Account Identifier

From your Snowflake URL, extract the account identifier:

**Example URL:** `https://app.snowflake.com/gcmbyoq/ehb83410/#/...`

**Account format:** `gcmbyoq-ehb83410` (combine the parts before and after the first `/`)

### 1.3 Create a Warehouse

Run this SQL in the Snowflake worksheet:

```sql
-- Create a warehouse for compute resources
CREATE WAREHOUSE IF NOT EXISTS MY_FIRST_WH
    WITH WAREHOUSE_SIZE = 'X-SMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Warehouse for phone usage data project';
```

**Note:** Replace `MY_FIRST_WH` with your preferred warehouse name.

### 1.4 Create Database and Schema

```sql
-- Create database
CREATE DATABASE IF NOT EXISTS MY_DATABASE;

-- Use the database
USE DATABASE MY_DATABASE;

-- Create schema (or use existing PUBLIC schema)
CREATE SCHEMA IF NOT EXISTS PUBLIC;
USE SCHEMA PUBLIC;
```

**Note:** Replace `MY_DATABASE` with your preferred database name. The `PUBLIC` schema is standard, but you can use a custom schema name.

### 1.5 Verify Your Setup

Run these commands to verify:

```sql
-- Check warehouse exists
SHOW WAREHOUSES LIKE 'MY_FIRST_WH';

-- Check database and schema
SHOW DATABASES LIKE 'MY_DATABASE';
USE DATABASE MY_DATABASE;
USE SCHEMA PUBLIC;

-- Verify current context
SELECT CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_SCHEMA();
```

**Save these values - you'll need them for configuration:**
- Account identifier (from URL)
- Warehouse name
- Database name
- Schema name (usually `PUBLIC`)
- Your username
- Your password

---

## Step 2: Set Up Python Environment

### 2.1 Create Virtual Environment (Recommended)

**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2.2 Navigate to Project Directory

```bash
cd path/to/0001_Simulate_Usage_Data
```

---

## Step 3: Configure Credentials

### 3.1 Create .env File

Create a file named `.env` in the project root directory.

**Important:** The `.env` file is in `.gitignore` and will NOT be committed to version control.

### 3.2 Add Snowflake Credentials

Edit the `.env` file and add your Snowflake credentials:

```bash
# Snowflake Connection Configuration
# Get account from your Snowflake URL: https://app.snowflake.com/ACCOUNT/ORG/
# Format: ACCOUNT-ORG (e.g., gcmbyoq-ehb83410)

SNOWFLAKE_ACCOUNT=your-account-org
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=MY_FIRST_WH
SNOWFLAKE_DATABASE=MY_DATABASE
SNOWFLAKE_SCHEMA=PUBLIC

# Optional: Specify role if needed
# SNOWFLAKE_ROLE=YOUR_ROLE
```

**Example .env file:**
```bash
SNOWFLAKE_ACCOUNT=gcmbyoq-ehb83410
SNOWFLAKE_USER=john.doe
SNOWFLAKE_PASSWORD=MySecurePassword123
SNOWFLAKE_WAREHOUSE=MY_FIRST_WH
SNOWFLAKE_DATABASE=MY_DATABASE
SNOWFLAKE_SCHEMA=PUBLIC
```

**Security Notes:**
- ✅ Never commit `.env` to version control
- ✅ Use strong passwords
- ✅ Consider using key pair authentication for production

---

## Step 4: Install Dependencies

### 4.1 Install All Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- Core: pandas, numpy, python-dateutil
- Visualization: matplotlib, seaborn (for notebooks)
- Snowflake: snowflake-connector-python, python-dotenv
- Dashboard: streamlit, plotly (optional, for local dashboard)

### 4.2 Verify Installation

```bash
python -c "import snowflake.connector; print('Snowflake connector installed')"
python -c "from dotenv import load_dotenv; print('python-dotenv installed')"
```

---

## Step 5: Configure Data Generation

Before generating data, you need to configure the reference data that will be used.

### 5.1 Open Python or Jupyter Notebook

Create a script or open `test_functions.ipynb` and configure:

```python
from function import generate_all_tables
from datetime import datetime
import function

# Configure the number of enterprise accounts
function.NUM_ENTERPRISE_ACCOUNTS = 100

# Set the most recent month for data generation
function.MOST_RECENT_MONTH = datetime(2025, 1, 1)  # Adjust to your needs

# Define your reference data
function.COMPANIES = ['Company A', 'Company B', 'Company C']
function.BRANDS = [(1, 'Brand1'), (2, 'Brand2')]
function.UBRANDS = [('U1', 'UBrand1'), ('U2', 'UBrand2')]
function.PACKAGES = [
    (1, 'Basic', 101, 'Basic Package'),
    (2, 'Premium', 102, 'Premium Package')
]
function.TIERS = [
    (1, 'Tier1', 'Standard'),
    (2, 'Tier2', 'Enterprise')
]
function.OPCOS = ['OPCO1', 'OPCO2', 'OPCO3']
```

**Customize these values** based on your business requirements.

---

## Step 6: Generate Data

### 6.1 Generate All Tables

```python
from function import generate_all_tables
from datetime import datetime

# Generate all three tables
account_df, usage_df, churn_df = generate_all_tables(
    non_active_ratio=0.05,      # 5% of accounts will churn
    num_months=36,               # 36 months of historical data
    usage_start_date=datetime(2022, 1, 1),  # Start date for usage data
    save_to_csv=True             # Save to CSV files (optional)
)
```

This generates:
- `account_attributes_monthly.csv` - Account attributes by month
- `phone_usage_data.csv` - Phone usage metrics
- `churn_records.csv` - Churn events

### 6.2 Verify Generated Data

```python
print(f"Accounts: {len(account_df)} rows")
print(f"Usage: {len(usage_df)} rows")
print(f"Churn: {len(churn_df)} rows")
```

---

## Step 7: Load Data to Snowflake

### 7.1 Test Connection First

**From Command Line:**
```bash
python snowflake_loader.py --test
```

**From Python:**
```python
from snowflake_loader import test_connection
test_connection()
```

Expected output:
```
============================================================
Snowflake Connection Test - SUCCESS
============================================================
User:      YOUR_USERNAME
Role:      YOUR_ROLE
Database:  MY_DATABASE
Schema:    PUBLIC
Warehouse: MY_FIRST_WH
============================================================
```

### 7.2 Load Data from DataFrames (Recommended)

If you just generated data in Python:

```python
from snowflake_loader import load_all_data

load_all_data(
    from_dataframes=True,
    account_df=account_df,
    usage_df=usage_df,
    churn_df=churn_df,
    truncate=False  # Set True to replace existing data
)
```

### 7.3 Load Data from CSV Files

If you saved CSV files:

```python
from snowflake_loader import load_all_data

load_all_data(from_dataframes=False)
```

**Or from command line:**
```bash
# Load from CSV files
python snowflake_loader.py

# Replace existing data
python snowflake_loader.py --truncate
```

### 7.4 What Gets Created

The loader creates three tables:
- `ACCOUNT_ATTRIBUTES_MONTHLY` - Account attributes
- `PHONE_USAGE_DATA` - Phone usage metrics
- `CHURN_RECORDS` - Churn events

---

## Step 8: Verify Data

### 8.1 Check Data in Snowflake (Python)

```python
from snowflake_loader import show_table_summary
show_table_summary()
```

**Or from command line:**
```bash
python snowflake_loader.py --summary
```

### 8.2 Verify in Snowflake UI

Run these queries in Snowflake worksheet:

```sql
-- Check row counts
SELECT 'ACCOUNT_ATTRIBUTES_MONTHLY' as table_name, COUNT(*) as row_count 
FROM ACCOUNT_ATTRIBUTES_MONTHLY
UNION ALL
SELECT 'PHONE_USAGE_DATA', COUNT(*) FROM PHONE_USAGE_DATA
UNION ALL
SELECT 'CHURN_RECORDS', COUNT(*) FROM CHURN_RECORDS;

-- Sample data
SELECT * FROM ACCOUNT_ATTRIBUTES_MONTHLY LIMIT 5;
SELECT * FROM PHONE_USAGE_DATA LIMIT 5;
SELECT * FROM CHURN_RECORDS LIMIT 5;
```

---

## Step 9: Deploy Dashboard (Optional)

You have two options for the dashboard:

### Option A: Deploy in Snowflake Streamlit (Recommended) ⭐

**Benefits:**
- No local setup required
- Uses Snowflake's built-in authentication
- Easy to share with team
- Runs entirely in Snowflake

**Steps:**

1. **Log into Snowflake UI**
2. **Navigate to Streamlit** → Click **"+ Streamlit App"**
3. **Configure:**
   - Name: `Phone Usage Analytics`
   - Warehouse: `MY_FIRST_WH`
   - Database: `MY_DATABASE`
   - Schema: `PUBLIC`
   - **Click "Packages"** and add: `plotly`
4. **Copy code:**
   - Open `streamlit_app_snowflake.py`
   - Copy all code (Ctrl+A, Ctrl+C)
5. **Paste and run:**
   - Delete default code in Snowflake editor
   - Paste your code (Ctrl+V)
   - Click **Run**

📖 **See [SNOWFLAKE_STREAMLIT_DEPLOYMENT.md](SNOWFLAKE_STREAMLIT_DEPLOYMENT.md) for detailed guide.**

### Option B: Run Dashboard Locally

```bash
# Install Streamlit if not already installed
pip install streamlit plotly

# Run the dashboard
streamlit run streamlit_app.py
```

The dashboard opens at: **http://localhost:8501**

📖 **See [STREAMLIT_DASHBOARD.md](STREAMLIT_DASHBOARD.md) for local setup guide.**

---

## Troubleshooting

### Connection Issues

**Error: "Missing required environment variables"**
- ✅ Check `.env` file exists in project root
- ✅ Verify all required variables are set (no empty values)
- ✅ Check file name is exactly `.env` (not `.env.txt`)

**Error: "Authentication failed"**
- ✅ Verify username and password are correct
- ✅ Check account identifier format (should be `ACCOUNT-ORG`)
- ✅ Ensure account is not locked/suspended

**Error: "Database/Schema does not exist"**
- ✅ Verify database and schema names match exactly
- ✅ Ensure you have USAGE permission on database/schema
- ✅ Check database and schema names in `.env` match Snowflake

**Error: "Warehouse not found"**
- ✅ Verify warehouse name matches exactly
- ✅ Ensure warehouse exists: `SHOW WAREHOUSES;`
- ✅ Check you have USAGE permission on warehouse
- ✅ Resume warehouse if suspended: `ALTER WAREHOUSE MY_FIRST_WH RESUME;`

### Permission Issues

**Error: "SQL access control error"**

Your user needs these permissions:

```sql
-- Grant warehouse usage
GRANT USAGE ON WAREHOUSE MY_FIRST_WH TO ROLE YOUR_ROLE;

-- Grant database and schema usage
GRANT USAGE ON DATABASE MY_DATABASE TO ROLE YOUR_ROLE;
GRANT USAGE ON SCHEMA MY_DATABASE.PUBLIC TO ROLE YOUR_ROLE;

-- Grant table creation and modification
GRANT CREATE TABLE ON SCHEMA MY_DATABASE.PUBLIC TO ROLE YOUR_ROLE;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA MY_DATABASE.PUBLIC TO ROLE YOUR_ROLE;
```

Contact your Snowflake administrator to grant these permissions.

### Data Loading Issues

**Error: "Table already exists"**
- ✅ Drop existing tables if you want to recreate:
  ```python
  from snowflake_loader import get_snowflake_connection, drop_all_tables
  conn = get_snowflake_connection()
  drop_all_tables(conn)
  conn.close()
  ```
- ✅ Or use `truncate=True` to replace data:
  ```python
  load_all_data(truncate=True, ...)
  ```

**No data showing after load**
- ✅ Check if data was actually generated
- ✅ Verify CSV files exist (if loading from CSV)
- ✅ Check for errors in load output
- ✅ Query tables directly in Snowflake UI

### Python Environment Issues

**Error: "Module not found"**
- ✅ Activate virtual environment
- ✅ Install dependencies: `pip install -r requirements.txt`
- ✅ Check Python version: `python --version` (needs 3.8+)

**Error: "snowflake-connector-python" issues**
- ✅ Upgrade pip: `pip install --upgrade pip`
- ✅ Install specific version: `pip install snowflake-connector-python==3.0.0`

---

## Quick Reference Checklist

Use this checklist to ensure you've completed all steps:

### Snowflake Setup
- [ ] Logged into Snowflake
- [ ] Extracted account identifier from URL
- [ ] Created warehouse
- [ ] Created database
- [ ] Created/verified schema
- [ ] Saved all connection details

### Python Setup
- [ ] Python 3.8+ installed
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)

### Configuration
- [ ] `.env` file created in project root
- [ ] All Snowflake credentials added to `.env`
- [ ] Data generation parameters configured

### Data Generation
- [ ] Data generation script configured
- [ ] Data successfully generated
- [ ] Verified data row counts

### Data Loading
- [ ] Connection test successful
- [ ] Data loaded to Snowflake
- [ ] Verified data in Snowflake UI

### Dashboard (Optional)
- [ ] Dashboard deployed (Snowflake Streamlit or local)
- [ ] Dashboard loads data successfully

---

## Next Steps

After setup is complete:

1. **Explore the data** - Query tables in Snowflake
2. **Use the dashboard** - Analyze usage patterns and churn
3. **Generate more data** - Adjust parameters and regenerate
4. **Schedule refreshes** - Set up automated data generation/loading
5. **Share with team** - Deploy dashboard and share access

---

## Additional Resources

- **Snowflake Setup Details**: [SNOWFLAKE_SETUP.md](SNOWFLAKE_SETUP.md)
- **Quick Start Guide**: [QUICK_START.md](QUICK_START.md)
- **Streamlit Dashboard**: [STREAMLIT_DASHBOARD.md](STREAMLIT_DASHBOARD.md)
- **Snowflake Streamlit Deployment**: [SNOWFLAKE_STREAMLIT_DEPLOYMENT.md](SNOWFLAKE_STREAMLIT_DEPLOYMENT.md)
- **Main README**: [README.md](README.md)

---

## Getting Help

If you encounter issues:

1. Check the [Troubleshooting](#troubleshooting) section above
2. Review the specific documentation files
3. Verify all configuration matches exactly
4. Test connection first: `python snowflake_loader.py --test`

---

**🎉 You're all set! Your project is now running on your new Snowflake space!**

