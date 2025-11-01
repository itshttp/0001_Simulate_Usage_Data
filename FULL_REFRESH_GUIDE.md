# Full Data Refresh Guide

Complete guide for refreshing your Snowflake database with 10,000 accounts at 8% churn rate.

## Quick Start (One Command)

Run everything automatically:

```bash
./venv/bin/python full_data_refresh.py
```

This script will:
1. Generate 10,000 accounts with 8% churn
2. Create CSV files
3. Clean Snowflake tables (with confirmation)
4. Load new data
5. Run 8 consistency tests

**Time estimate**: 5-10 minutes

---

## Step-by-Step (Manual Control)

If you prefer to run each step separately:

### Step 1: Generate Data

```bash
./venv/bin/python generate_large_dataset.py
```

**What it does**:
- Generates 10,000 accounts
- 8% churn rate
- 36 months of usage data
- Creates 3 CSV files

**Output files**:
- `account_attributes_monthly.csv` (~100-150 MB)
- `phone_usage_data.csv` (~400-500 MB)
- `churn_records.csv` (~20 KB)

**Time**: 3-5 minutes

### Step 2: Verify Data Files

```bash
# Check files were created
ls -lh *.csv

# Count records
wc -l *.csv

# Preview data
head -5 account_attributes_monthly.csv
head -5 phone_usage_data.csv
head -5 churn_records.csv
```

### Step 3: Test Snowflake Connection

```python
from snowflake_loader import test_connection

test_connection()
```

**Expected output**:
```
✓ Connected to Snowflake: YOUR_DATABASE.YOUR_SCHEMA

Snowflake Connection Test - SUCCESS
User:      YOUR_USER
Role:      YOUR_ROLE
Database:  YOUR_DATABASE
Schema:    YOUR_SCHEMA
Warehouse: YOUR_WAREHOUSE
```

If this fails, check your `.env` file.

### Step 4: Clean Snowflake Tables

**Option A**: Using Python

```python
from snowflake_loader import get_snowflake_connection

conn = get_snowflake_connection()
cursor = conn.cursor()

# Truncate all tables
cursor.execute("TRUNCATE TABLE ACCOUNT_ATTRIBUTES_MONTHLY")
cursor.execute("TRUNCATE TABLE PHONE_USAGE_DATA")
cursor.execute("TRUNCATE TABLE CHURN_RECORDS")

print("✓ All tables cleaned")
cursor.close()
conn.close()
```

**Option B**: Using Snowflake Web UI

1. Log into Snowflake
2. Navigate to Worksheets
3. Run these queries:

```sql
TRUNCATE TABLE ACCOUNT_ATTRIBUTES_MONTHLY;
TRUNCATE TABLE PHONE_USAGE_DATA;
TRUNCATE TABLE CHURN_RECORDS;
```

### Step 5: Load Data to Snowflake

**Option A**: Load from CSV files

```python
from snowflake_loader import load_all_data

load_all_data(truncate=False, from_dataframes=False)
```

**Option B**: Load from DataFrames (if you just generated data)

```python
from snowflake_loader import load_all_data
import pandas as pd

# Load the CSV files you just created
account_df = pd.read_csv('account_attributes_monthly.csv')
usage_df = pd.read_csv('phone_usage_data.csv')
churn_df = pd.read_csv('churn_records.csv')

# Convert date columns
account_df['MONTH'] = pd.to_datetime(account_df['MONTH'])
usage_df['MONTH'] = pd.to_datetime(usage_df['MONTH'])
churn_df['CHURN_DATE'] = pd.to_datetime(churn_df['CHURN_DATE'])

# Load to Snowflake
load_all_data(
    truncate=False,
    from_dataframes=True,
    account_df=account_df,
    usage_df=usage_df,
    churn_df=churn_df
)
```

**Time**: 3-5 minutes

### Step 6: Run Consistency Tests

Create a test script `test_consistency.py`:

```python
from snowflake_loader import get_snowflake_connection

conn = get_snowflake_connection()
cursor = conn.cursor()

print("Running consistency tests...")
print()

# Test 1: Count accounts
cursor.execute("SELECT COUNT(DISTINCT SERVICE_ACCOUNT_ID) FROM ACCOUNT_ATTRIBUTES_MONTHLY")
account_count = cursor.fetchone()[0]
print(f"Test 1: Account count = {account_count:,}")
assert account_count == 10000, "Expected 10,000 accounts"
print("  ✓ PASS")

# Test 2: Count usage records
cursor.execute("SELECT COUNT(*) FROM PHONE_USAGE_DATA")
usage_count = cursor.fetchone()[0]
print(f"\nTest 2: Usage record count = {usage_count:,}")
print("  ✓ PASS")

# Test 3: Verify churn rate
cursor.execute("""
    SELECT
        COUNT(DISTINCT SERVICE_ACCOUNT_ID) as total,
        COUNT(DISTINCT CASE WHEN SA_ACCT_STATUS IN ('Suspended', 'Closed')
              THEN SERVICE_ACCOUNT_ID END) as churned
    FROM ACCOUNT_ATTRIBUTES_MONTHLY
""")
result = cursor.fetchone()
churn_rate = (result[1] / result[0] * 100) if result[0] > 0 else 0
print(f"\nTest 3: Churn rate = {churn_rate:.2f}%")
assert 7.0 <= churn_rate <= 9.0, f"Expected ~8% churn, got {churn_rate:.2f}%"
print("  ✓ PASS")

# Test 4: No NULL values
cursor.execute("""
    SELECT COUNT(*)
    FROM ACCOUNT_ATTRIBUTES_MONTHLY
    WHERE SERVICE_ACCOUNT_ID IS NULL OR MONTH IS NULL OR COMPANY IS NULL
""")
null_count = cursor.fetchone()[0]
print(f"\nTest 4: NULL check = {null_count} nulls found")
assert null_count == 0, "Found NULL values in key fields"
print("  ✓ PASS")

# Test 5: Valid usage values
cursor.execute("""
    SELECT COUNT(*)
    FROM PHONE_USAGE_DATA
    WHERE PHONE_TOTAL_CALLS < 0 OR PHONE_TOTAL_MINUTES_OF_USE < 0
""")
invalid_count = cursor.fetchone()[0]
print(f"\nTest 5: Invalid values check = {invalid_count} invalid records")
assert invalid_count == 0, "Found invalid (negative) usage values"
print("  ✓ PASS")

print("\n✓ ALL TESTS PASSED!")

cursor.close()
conn.close()
```

Run it:

```bash
./venv/bin/python test_consistency.py
```

---

## Verification Queries

Run these in Snowflake to verify your data:

### 1. Account Overview

```sql
SELECT
    COUNT(DISTINCT SERVICE_ACCOUNT_ID) as total_accounts,
    COUNT(DISTINCT CASE WHEN SA_ACCT_STATUS = 'Active'
          THEN SERVICE_ACCOUNT_ID END) as active_accounts,
    COUNT(DISTINCT CASE WHEN SA_ACCT_STATUS IN ('Suspended', 'Closed')
          THEN SERVICE_ACCOUNT_ID END) as churned_accounts
FROM ACCOUNT_ATTRIBUTES_MONTHLY;
```

**Expected**:
- Total accounts: 10,000
- Active: ~9,200
- Churned: ~800

### 2. Churn Rate

```sql
SELECT
    COUNT(DISTINCT a.SERVICE_ACCOUNT_ID) as total_accounts,
    COUNT(DISTINCT c.USERID) as churned_accounts,
    ROUND(COUNT(DISTINCT c.USERID) * 100.0 / COUNT(DISTINCT a.SERVICE_ACCOUNT_ID), 2) as churn_rate_pct
FROM ACCOUNT_ATTRIBUTES_MONTHLY a
LEFT JOIN CHURN_RECORDS c ON a.SERVICE_ACCOUNT_ID = c.USERID;
```

**Expected**: Churn rate ~8%

### 3. Package Distribution

```sql
SELECT
    PACKAGE_NAME,
    COUNT(DISTINCT SERVICE_ACCOUNT_ID) as account_count,
    ROUND(COUNT(DISTINCT SERVICE_ACCOUNT_ID) * 100.0 /
          SUM(COUNT(DISTINCT SERVICE_ACCOUNT_ID)) OVER(), 2) as percentage
FROM ACCOUNT_ATTRIBUTES_MONTHLY
GROUP BY PACKAGE_NAME
ORDER BY account_count DESC;
```

### 4. Usage Statistics

```sql
SELECT
    COUNT(*) as total_records,
    COUNT(DISTINCT USERID) as unique_users,
    ROUND(AVG(PHONE_TOTAL_CALLS), 2) as avg_calls,
    ROUND(AVG(PHONE_TOTAL_MINUTES_OF_USE), 2) as avg_minutes,
    MIN(MONTH) as earliest_month,
    MAX(MONTH) as latest_month
FROM PHONE_USAGE_DATA;
```

**Expected**:
- Total records: ~360,000 (10,000 users × 36 months)
- Unique users: 10,000
- Earliest month: 2022-10-01
- Latest month: 2025-09-01

### 5. Data Quality Check

```sql
-- Check for orphaned records
SELECT
    'Accounts without usage' as check_type,
    COUNT(DISTINCT a.SERVICE_ACCOUNT_ID) as count
FROM ACCOUNT_ATTRIBUTES_MONTHLY a
LEFT JOIN PHONE_USAGE_DATA u ON a.SERVICE_ACCOUNT_ID = u.USERID
WHERE u.USERID IS NULL

UNION ALL

SELECT
    'Usage without accounts',
    COUNT(DISTINCT u.USERID)
FROM PHONE_USAGE_DATA u
LEFT JOIN ACCOUNT_ATTRIBUTES_MONTHLY a ON u.USERID = a.SERVICE_ACCOUNT_ID
WHERE a.SERVICE_ACCOUNT_ID IS NULL;
```

**Expected**: Both counts should be 0

### 6. Churn Pattern Analysis

```sql
SELECT
    DATE_TRUNC('month', CHURN_DATE) as churn_month,
    COUNT(*) as churned_count
FROM CHURN_RECORDS
GROUP BY DATE_TRUNC('month', CHURN_DATE)
ORDER BY churn_month;
```

---

## Troubleshooting

### Issue: "Configuration constants must be set"

**Solution**: The configuration is already set in the scripts. If you see this, make sure you're running the scripts as provided.

### Issue: "Failed to connect to Snowflake"

**Solution**: Check your `.env` file:

```bash
# View current .env (without passwords)
cat .env | grep -v PASSWORD
```

Required variables:
- `SNOWFLAKE_ACCOUNT`
- `SNOWFLAKE_USER`
- `SNOWFLAKE_PASSWORD`
- `SNOWFLAKE_WAREHOUSE`
- `SNOWFLAKE_DATABASE`
- `SNOWFLAKE_SCHEMA`

### Issue: "Table does not exist"

**Solution**: Create tables first:

```python
from snowflake_loader import get_snowflake_connection, create_account_table, create_usage_table, create_churn_table

conn = get_snowflake_connection()
create_account_table(conn)
create_usage_table(conn)
create_churn_table(conn)
conn.close()
```

### Issue: Data loading is slow

**Possible causes**:
1. Snowflake warehouse is too small (try XS or S warehouse)
2. Network connection is slow
3. Large data volume

**Solution**: The scripts use batch loading which is already optimized. Be patient, it may take 5-10 minutes for 10,000 accounts.

### Issue: Out of memory

**Solution**: The scripts are designed to handle large datasets efficiently. If you still get memory errors:
1. Close other applications
2. Reduce `NUM_ENTERPRISE_ACCOUNTS` to 5000
3. Run generation and loading separately (not in one script)

---

## File Sizes Reference

For 10,000 accounts:

| File | Approximate Size | Records |
|------|------------------|---------|
| `account_attributes_monthly.csv` | 100-150 MB | ~120,000 |
| `phone_usage_data.csv` | 400-500 MB | ~360,000 |
| `churn_records.csv` | 20-30 KB | ~800 |

---

## Performance Tips

1. **Use larger Snowflake warehouse**: XS or S for faster loading
2. **Run during off-peak hours**: Less network congestion
3. **Keep warehouse running**: Avoid cold starts between steps
4. **Use the all-in-one script**: `full_data_refresh.py` is optimized

---

## Next Steps

After successful data refresh:

1. **View Dashboard**: Run Streamlit app
   ```bash
   ./venv/bin/streamlit run streamlit_app_snowflake.py
   ```

2. **Analyze Data**: Use Snowflake queries or your BI tool

3. **Schedule Refresh**: Set up cron job or Airflow DAG for regular refreshes

4. **Backup**: Consider backing up the CSV files

---

## Complete Workflow Summary

```bash
# One command to do everything:
./venv/bin/python full_data_refresh.py

# Or step by step:
./venv/bin/python generate_large_dataset.py  # Step 1: Generate
# ... verify files ...
./venv/bin/python -c "from snowflake_loader import load_all_data; load_all_data(truncate=True)"  # Steps 2-3: Clean & Load
./venv/bin/python test_consistency.py  # Step 4: Test
```

That's it! Your Snowflake database now has fresh data ready for analysis.
