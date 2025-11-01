# Snowflake Integration Setup Guide

This guide will help you connect the phone usage data simulator to your Snowflake account and load data.

## Prerequisites

- Active Snowflake account
- Snowflake warehouse, database, and schema created
- Snowflake user with permissions to create tables and insert data

## Step 1: Install Dependencies

Install the required Snowflake packages:

```bash
# If using the virtual environment
./venv/bin/pip install snowflake-connector-python python-dotenv

# Or if pip is in your PATH
pip install snowflake-connector-python python-dotenv
```

## Step 2: Get Your Snowflake Connection Information

From your Snowflake URL: `https://app.snowflake.com/gcmbyoq/ehb83410/#/...`

Extract the following:
- **Account**: `gcmbyoq-ehb83410` (the part after `snowflake.com/` and before `/#/`)
- **User**: Your Snowflake username
- **Password**: Your Snowflake password
- **Warehouse**: Name of your compute warehouse (e.g., `COMPUTE_WH`)
- **Database**: Name of your database (e.g., `MY_DATABASE`)
- **Schema**: Name of your schema (e.g., `PUBLIC`)

## Step 3: Configure Credentials

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and fill in your credentials:
```bash
# Example .env file
SNOWFLAKE_ACCOUNT=gcmbyoq-ehb83410
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=MY_DATABASE
SNOWFLAKE_SCHEMA=PUBLIC
```

**Important**: Never commit the `.env` file to version control! It's already in `.gitignore`.

## Step 4: Test Connection

Test that you can connect to Snowflake:

### From Command Line
```bash
python snowflake_loader.py --test
```

### From Python
```python
from snowflake_loader import test_connection

test_connection()
```

You should see output like:
```
============================================================
Snowflake Connection Test - SUCCESS
============================================================
User:      YOUR_USERNAME
Role:      YOUR_ROLE
Database:  MY_DATABASE
Schema:    PUBLIC
Warehouse: COMPUTE_WH
============================================================
```

## Step 5: Generate Data

If you haven't already, generate the sample data:

```python
from function import generate_all_tables
from datetime import datetime

account_df, usage_df, churn_df = generate_all_tables(
    non_active_ratio=0.05,
    num_months=36,
    usage_start_date=datetime(2023, 1, 1),
    save_to_csv=True
)
```

## Step 6: Load Data to Snowflake

### Option A: Load from DataFrames (Recommended)

If you just generated data in Python/Jupyter:

```python
from snowflake_loader import load_all_data

load_all_data(
    from_dataframes=True,
    account_df=account_df,
    usage_df=usage_df,
    churn_df=churn_df,
    truncate=False
)
```

### Option B: Load from CSV Files

If you have CSV files saved:

```python
from snowflake_loader import load_all_data

load_all_data(from_dataframes=False)
```

### Command Line

```bash
# Load from CSV files
python snowflake_loader.py

# Replace existing data
python snowflake_loader.py --truncate
```

## Step 7: Verify Data

Check that data was loaded successfully:

### From Python
```python
from snowflake_loader import show_table_summary

show_table_summary()
```

### From Command Line
```bash
python snowflake_loader.py --summary
```

### From Snowflake UI

Log into Snowflake and run:
```sql
SELECT COUNT(*) FROM ACCOUNT_ATTRIBUTES_MONTHLY;
SELECT COUNT(*) FROM PHONE_USAGE_DATA;
SELECT COUNT(*) FROM CHURN_RECORDS;
```

## Tables Created

The loader creates three tables:

### 1. ACCOUNT_ATTRIBUTES_MONTHLY
- 25 columns including account details, brands, packages, tiers
- Primary key: (SERVICE_ACCOUNT_ID, MONTH)

### 2. PHONE_USAGE_DATA
- 27 columns with detailed phone usage metrics
- Primary key: (USERID, MONTH)

### 3. CHURN_RECORDS
- 3 columns: USERID, CHURN_DATE, CHURNED
- Primary key: USERID

## Troubleshooting

### Connection Failed

**Error**: `NameError: name 'account_records' is not defined`
- **Solution**: Make sure you've installed all dependencies: `pip install snowflake-connector-python python-dotenv`

**Error**: `Missing required environment variables`
- **Solution**: Check that `.env` file exists and has all required fields filled in

**Error**: `Authentication failed`
- **Solution**: Verify your username and password in `.env` are correct

**Error**: `Database/Schema does not exist`
- **Solution**: Create the database and schema in Snowflake first, or use existing ones

### Permission Denied

**Error**: `SQL access control error`
- **Solution**: Your Snowflake user needs permissions to:
  - CREATE TABLE
  - INSERT data
  - Access the specified warehouse, database, and schema

Contact your Snowflake administrator to grant appropriate permissions.

### Network Issues

**Error**: `Unable to connect to Snowflake`
- **Solution**: Check your network connection and firewall settings
- Ensure you can access `https://app.snowflake.com` from your browser

## Advanced Usage

### Custom Table Names

Edit `snowflake_loader.py` to customize table names if needed.

### Different Warehouse for Loading

You can switch warehouses in your `.env` file to use a larger warehouse for data loading.

### Incremental Loads

By default, data is appended. To replace data:
```python
load_all_data(truncate=True, ...)
```

### Drop and Recreate Tables

```python
from snowflake_loader import get_snowflake_connection, drop_all_tables

conn = get_snowflake_connection()
drop_all_tables(conn)  # ⚠️ WARNING: Deletes all data!
conn.close()
```

## Security Best Practices

1. ✅ **Never commit `.env` file** - It's in `.gitignore`
2. ✅ **Use strong passwords** - Follow Snowflake security guidelines
3. ✅ **Rotate credentials** - Change passwords periodically
4. ✅ **Use appropriate roles** - Don't use ACCOUNTADMIN for loading data
5. ✅ **Monitor usage** - Check Snowflake warehouse usage and costs

## Next Steps

Once data is loaded, you can:
- Query the data in Snowflake for analysis
- Build dashboards in Tableau, Power BI, etc.
- Create views and aggregations
- Schedule regular data refreshes
- Train ML models using Snowflake ML features

## Support

For issues with:
- **Snowflake connection**: Check Snowflake documentation or contact your admin
- **Data generation**: See main README.md and test_functions.ipynb
- **Python code**: Check the code comments in snowflake_loader.py
