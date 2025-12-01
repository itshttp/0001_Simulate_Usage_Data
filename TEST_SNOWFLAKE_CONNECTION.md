# How to Test Snowflake Access Using .env File

This guide shows you how to verify that your Snowflake credentials in the `.env` file are working correctly.

## Prerequisites

1. ✅ `.env` file exists in the project root directory
2. ✅ All required credentials are filled in
3. ✅ Python dependencies installed (`snowflake-connector-python`, `python-dotenv`)

## Method 1: Command Line Test (Easiest) ⭐

### Step 1: Ensure .env File Exists

Make sure you have a `.env` file in the project root with your credentials:

```bash
# .env file location: project_root/.env
SNOWFLAKE_ACCOUNT=your-account-org
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=MY_FIRST_WH
SNOWFLAKE_DATABASE=MY_DATABASE
SNOWFLAKE_SCHEMA=PUBLIC
```

### Step 2: Run the Test Command

Open terminal/PowerShell in the project directory and run:

```bash
python snowflake_loader.py --test
```

### Expected Success Output

If everything is configured correctly, you should see:

```
✓ Connected to Snowflake: MY_DATABASE.PUBLIC
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

### Common Error Messages

**Error: "Missing required environment variables"**
```
✗ Connection test failed: Missing required environment variables: SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER
Please create a .env file based on .env.example and fill in your credentials.
```

**Solution:**
- ✅ Check `.env` file exists in project root
- ✅ Verify all required variables are present (no empty values)
- ✅ Check file name is exactly `.env` (not `.env.txt` or `.env.example`)

**Error: "Authentication failed"**
```
✗ Failed to connect to Snowflake: 250001 (08004): Incorrect username or password
```

**Solution:**
- ✅ Verify username and password are correct
- ✅ Check for typos (especially account identifier format)
- ✅ Ensure account is not locked

**Error: "Database does not exist"**
```
✗ Failed to connect to Snowflake: 251005: Database 'MY_DATABASE' does not exist
```

**Solution:**
- ✅ Verify database name matches exactly (case-sensitive)
- ✅ Create database in Snowflake if it doesn't exist:
  ```sql
  CREATE DATABASE IF NOT EXISTS MY_DATABASE;
  ```

**Error: "Warehouse not found"**
```
✗ Failed to connect to Snowflake: 251001: Warehouse 'MY_FIRST_WH' does not exist
```

**Solution:**
- ✅ Verify warehouse name matches exactly
- ✅ Create warehouse in Snowflake:
  ```sql
  CREATE WAREHOUSE IF NOT EXISTS MY_FIRST_WH
      WITH WAREHOUSE_SIZE = 'X-SMALL';
  ```
- ✅ Resume warehouse if suspended:
  ```sql
  ALTER WAREHOUSE MY_FIRST_WH RESUME;
  ```

---

## Method 2: Python Script Test

### Step 1: Create a Test Script

Create a file named `test_connection.py`:

```python
from snowflake_loader import test_connection

if __name__ == "__main__":
    print("Testing Snowflake connection...")
    success = test_connection()
    
    if success:
        print("\n✅ Connection test PASSED!")
    else:
        print("\n❌ Connection test FAILED!")
        print("Please check your .env file and Snowflake credentials.")
```

### Step 2: Run the Script

```bash
python test_connection.py
```

---

## Method 3: Interactive Python Test

### Step 1: Open Python

```bash
python
```

### Step 2: Run Test Commands

```python
# Import the test function
from snowflake_loader import test_connection

# Run the test
test_connection()
```

### Expected Output

```
✓ Connected to Snowflake: MY_DATABASE.PUBLIC
============================================================
Snowflake Connection Test - SUCCESS
============================================================
User:      YOUR_USERNAME
Role:      YOUR_ROLE
Database:  MY_DATABASE
Schema:    PUBLIC
Warehouse: MY_FIRST_WH
============================================================

True
```

---

## Method 4: Detailed Connection Test

For more detailed testing, you can create a custom test script:

```python
import os
from dotenv import load_dotenv
import snowflake.connector

# Load environment variables
load_dotenv()

print("Checking environment variables...")
print(f"Account: {'✅' if os.getenv('SNOWFLAKE_ACCOUNT') else '❌'} {os.getenv('SNOWFLAKE_ACCOUNT', 'NOT SET')}")
print(f"User: {'✅' if os.getenv('SNOWFLAKE_USER') else '❌'} {os.getenv('SNOWFLAKE_USER', 'NOT SET')}")
print(f"Password: {'✅' if os.getenv('SNOWFLAKE_PASSWORD') else '❌'} {'***' if os.getenv('SNOWFLAKE_PASSWORD') else 'NOT SET'}")
print(f"Warehouse: {'✅' if os.getenv('SNOWFLAKE_WAREHOUSE') else '❌'} {os.getenv('SNOWFLAKE_WAREHOUSE', 'NOT SET')}")
print(f"Database: {'✅' if os.getenv('SNOWFLAKE_DATABASE') else '❌'} {os.getenv('SNOWFLAKE_DATABASE', 'NOT SET')}")
print(f"Schema: {'✅' if os.getenv('SNOWFLAKE_SCHEMA') else '❌'} {os.getenv('SNOWFLAKE_SCHEMA', 'NOT SET')}")

print("\nAttempting connection...")
try:
    conn = snowflake.connector.connect(
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
        database=os.getenv('SNOWFLAKE_DATABASE'),
        schema=os.getenv('SNOWFLAKE_SCHEMA')
    )
    
    cursor = conn.cursor()
    cursor.execute("SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_DATABASE(), CURRENT_SCHEMA(), CURRENT_WAREHOUSE()")
    result = cursor.fetchone()
    
    print("\n✅ Connection successful!")
    print(f"   User: {result[0]}")
    print(f"   Role: {result[1]}")
    print(f"   Database: {result[2]}")
    print(f"   Schema: {result[3]}")
    print(f"   Warehouse: {result[4]}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"\n❌ Connection failed: {e}")
```

Save this as `detailed_test.py` and run:
```bash
python detailed_test.py
```

---

## Verifying .env File Format

### Correct Format

```bash
# .env file (no quotes needed, no spaces around =)
SNOWFLAKE_ACCOUNT=gcmbyoq-ehb83410
SNOWFLAKE_USER=john.doe
SNOWFLAKE_PASSWORD=MySecurePassword123
SNOWFLAKE_WAREHOUSE=MY_FIRST_WH
SNOWFLAKE_DATABASE=MY_DATABASE
SNOWFLAKE_SCHEMA=PUBLIC
```

### Common Mistakes to Avoid

❌ **Wrong:** Quotes around values
```bash
SNOWFLAKE_ACCOUNT="gcmbyoq-ehb83410"  # Don't use quotes
```

✅ **Correct:** No quotes
```bash
SNOWFLAKE_ACCOUNT=gcmbyoq-ehb83410
```

❌ **Wrong:** Spaces around `=`
```bash
SNOWFLAKE_ACCOUNT = gcmbyoq-ehb83410  # Spaces cause issues
```

✅ **Correct:** No spaces
```bash
SNOWFLAKE_ACCOUNT=gcmbyoq-ehb83410
```

❌ **Wrong:** File named `.env.txt` or `.env.example`
```bash
# File must be named exactly: .env
```

✅ **Correct:** File named `.env` (no extension)

---

## Testing Specific Components

### Test 1: Verify .env File is Loaded

```python
from dotenv import load_dotenv
import os

load_dotenv()
print(f"Account: {os.getenv('SNOWFLAKE_ACCOUNT')}")
print(f"User: {os.getenv('SNOWFLAKE_USER')}")
```

If these print `None`, the `.env` file is not being loaded correctly.

### Test 2: Test Account Format

The account identifier should be in format: `ACCOUNT-ORG`

Example:
- URL: `https://app.snowflake.com/gcmbyoq/ehb83410/`
- Account: `gcmbyoq-ehb83410` (combine with hyphen)

### Test 3: Test Warehouse Access

```python
from snowflake_loader import get_snowflake_connection

conn = get_snowflake_connection()
cursor = conn.cursor()

# Test warehouse
cursor.execute("SELECT CURRENT_WAREHOUSE()")
warehouse = cursor.fetchone()[0]
print(f"Current warehouse: {warehouse}")

# Resume warehouse if needed
cursor.execute("ALTER WAREHOUSE IF EXISTS MY_FIRST_WH RESUME")

cursor.close()
conn.close()
```

### Test 4: Test Database/Schema Access

```python
from snowflake_loader import get_snowflake_connection

conn = get_snowflake_connection()
cursor = conn.cursor()

# Test database
cursor.execute("SELECT CURRENT_DATABASE()")
database = cursor.fetchone()[0]
print(f"Current database: {database}")

# Test schema
cursor.execute("SELECT CURRENT_SCHEMA()")
schema = cursor.fetchone()[0]
print(f"Current schema: {schema}")

# List tables (if any exist)
cursor.execute("SHOW TABLES")
tables = cursor.fetchall()
print(f"Tables in schema: {[t[1] for t in tables]}")

cursor.close()
conn.close()
```

---

## Quick Troubleshooting Checklist

If the test fails, check these in order:

1. ✅ `.env` file exists in project root directory
2. ✅ All required variables are set (no empty values)
3. ✅ File name is exactly `.env` (not `.env.txt`)
4. ✅ No quotes around values in `.env` file
5. ✅ No spaces around `=` in `.env` file
6. ✅ Account format is correct: `ACCOUNT-ORG` (with hyphen)
7. ✅ Username and password are correct
8. ✅ Warehouse exists in Snowflake
9. ✅ Database exists in Snowflake
10. ✅ Warehouse is resumed (not suspended)
11. ✅ User has permissions to access warehouse, database, schema
12. ✅ Python packages installed: `pip install snowflake-connector-python python-dotenv`

---

## Next Steps After Successful Test

Once your connection test passes:

1. ✅ **Generate data** - Use `generate_all_tables()` function
2. ✅ **Load data** - Use `load_all_data()` function
3. ✅ **Verify data** - Use `show_table_summary()` or query in Snowflake UI
4. ✅ **Deploy dashboard** - Set up Streamlit dashboard

---

## Summary

**Quickest way to test:**
```bash
python snowflake_loader.py --test
```

**Expected result:**
- ✅ Connection successful
- ✅ Session info displayed (user, role, database, schema, warehouse)

**If it fails:**
- Check the error message
- Verify `.env` file format
- Ensure all Snowflake resources exist
- Verify user permissions

---

**Need more help?** See [NEW_SNOWFLAKE_SETUP.md](NEW_SNOWFLAKE_SETUP.md) for complete setup guide.

