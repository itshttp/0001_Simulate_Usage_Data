#!/usr/bin/env python3
"""
Full Data Refresh Script

This script performs the complete workflow:
1. Generate 10,000 accounts with 8% churn rate
2. Create CSV data files
3. Clean Snowflake tables
4. Load new data to Snowflake
5. Run consistency tests

Usage:
    ./venv/bin/python full_data_refresh.py
"""

from datetime import datetime
import pandas as pd
import function
import snowflake_loader

print("=" * 80)
print("FULL DATA REFRESH WORKFLOW")
print("=" * 80)
print()
print("This script will:")
print("  1. Generate 10,000 accounts with 8% churn rate")
print("  2. Create CSV data files")
print("  3. Clean Snowflake tables (TRUNCATE)")
print("  4. Load new data to Snowflake")
print("  5. Run consistency tests")
print()

input("Press ENTER to continue or CTRL+C to cancel...")
print()

# ============================================================================
# STEP 1: GENERATE DATA
# ============================================================================

print("=" * 80)
print("STEP 1: GENERATING DATA")
print("=" * 80)
print(f"\nConfiguration:")
print(f"  Accounts: 10,000")
print(f"  Churn Rate: 8%")
print(f"  Time Period: 36 months (3 years)")
print()

# Configuration
function.NUM_ENTERPRISE_ACCOUNTS = 10000
function.MOST_RECENT_MONTH = datetime(2025, 10, 1)

function.COMPANIES = [
    'Global Telecom Inc',
    'Enterprise Communications Ltd',
    'Business Phone Solutions',
    'Corporate Networks LLC',
    'Digital Voice Systems',
    'United Communications',
    'Metro Business Services',
    'Pacific Telecom Group'
]

function.BRANDS = [
    (1, 'Premium Voice'),
    (2, 'Business Plus'),
    (3, 'Standard Connect'),
    (4, 'Enterprise Link'),
    (5, 'Global Voice')
]

function.UBRANDS = [
    ('UC1', 'Unified Communications Alpha'),
    ('UC2', 'Unified Communications Beta'),
    ('UC3', 'Unified Communications Gamma')
]

function.PACKAGES = [
    (100, 'Small Business', 'CAT-100', 'Small Business Catalog'),
    (200, 'Medium Business', 'CAT-200', 'Medium Business Catalog'),
    (300, 'Large Business', 'CAT-300', 'Large Business Catalog'),
    (400, 'Enterprise', 'CAT-400', 'Enterprise Catalog'),
    (500, 'Enterprise Plus', 'CAT-500', 'Enterprise Plus Catalog')
]

function.TIERS = [
    (1, 'Basic Tier', 'Standard Edition'),
    (2, 'Professional Tier', 'Professional Edition'),
    (3, 'Premium Tier', 'Premium Edition'),
    (4, 'Enterprise Tier', 'Enterprise Edition')
]

function.OPCOS = [
    'OPCO-NORTH-AMERICA',
    'OPCO-EUROPE',
    'OPCO-ASIA-PACIFIC',
    'OPCO-LATIN-AMERICA'
]

print("Generating data (this may take several minutes)...")
print()

account_df, usage_df, churn_df = function.generate_all_tables(
    non_active_ratio=0.08,  # 8% churn rate
    num_months=36,          # 3 years of data
    usage_start_date=datetime(2022, 10, 1),
    save_to_csv=True
)

# Statistics
total_accounts = account_df['SERVICE_ACCOUNT_ID'].nunique()
active_accounts = account_df[account_df['SA_ACCT_STATUS'] == 'Active']['SERVICE_ACCOUNT_ID'].nunique()
churned_accounts = len(churn_df)
actual_churn_rate = (churned_accounts / total_accounts) * 100

print()
print("✓ Data generation complete!")
print(f"  - Account records: {len(account_df):,}")
print(f"  - Usage records: {len(usage_df):,}")
print(f"  - Churn records: {len(churn_df):,}")
print(f"  - Total accounts: {total_accounts:,}")
print(f"  - Churned accounts: {churned_accounts:,}")
print(f"  - Actual churn rate: {actual_churn_rate:.2f}%")
print()

# ============================================================================
# STEP 2: TEST SNOWFLAKE CONNECTION
# ============================================================================

print("=" * 80)
print("STEP 2: TESTING SNOWFLAKE CONNECTION")
print("=" * 80)
print()

if not snowflake_loader.test_connection():
    print("✗ Failed to connect to Snowflake. Please check your .env file.")
    exit(1)

print("✓ Connection successful!")
print()

# ============================================================================
# STEP 3: CLEAN SNOWFLAKE TABLES
# ============================================================================

print("=" * 80)
print("STEP 3: CLEANING SNOWFLAKE TABLES")
print("=" * 80)
print()
print("⚠️  WARNING: This will DELETE all data in the following tables:")
print("  - ACCOUNT_ATTRIBUTES_MONTHLY")
print("  - PHONE_USAGE_DATA")
print("  - CHURN_RECORDS")
print()

confirm = input("Type 'YES' to proceed with table cleanup: ")
if confirm != 'YES':
    print("✗ Cleanup cancelled. Exiting.")
    exit(1)

print()
print("Cleaning tables...")

try:
    conn = snowflake_loader.get_snowflake_connection()
    cursor = conn.cursor()

    # Truncate tables
    tables = ['ACCOUNT_ATTRIBUTES_MONTHLY', 'PHONE_USAGE_DATA', 'CHURN_RECORDS']
    for table in tables:
        cursor.execute(f"TRUNCATE TABLE IF EXISTS {table}")
        print(f"  ✓ Truncated {table}")

    cursor.close()
    conn.close()

    print()
    print("✓ All tables cleaned successfully!")
    print()

except Exception as e:
    print(f"✗ Error cleaning tables: {e}")
    exit(1)

# ============================================================================
# STEP 4: LOAD DATA TO SNOWFLAKE
# ============================================================================

print("=" * 80)
print("STEP 4: LOADING DATA TO SNOWFLAKE")
print("=" * 80)
print()
print("Loading data from DataFrames...")
print()

try:
    # Load data using the existing function
    snowflake_loader.load_all_data(
        truncate=False,  # Already truncated
        from_dataframes=True,
        account_df=account_df,
        usage_df=usage_df,
        churn_df=churn_df
    )

    print()
    print("✓ Data loaded successfully!")
    print()

except Exception as e:
    print(f"✗ Error loading data: {e}")
    exit(1)

# ============================================================================
# STEP 5: RUN CONSISTENCY TESTS
# ============================================================================

print("=" * 80)
print("STEP 5: RUNNING DATA CONSISTENCY TESTS")
print("=" * 80)
print()

try:
    conn = snowflake_loader.get_snowflake_connection()
    cursor = conn.cursor()

    tests_passed = 0
    tests_failed = 0

    # Test 1: Count accounts in Snowflake
    print("Test 1: Verifying account count...")
    cursor.execute("SELECT COUNT(DISTINCT SERVICE_ACCOUNT_ID) FROM ACCOUNT_ATTRIBUTES_MONTHLY")
    sf_account_count = cursor.fetchone()[0]

    if sf_account_count == total_accounts:
        print(f"  ✓ PASS: Account count matches ({sf_account_count:,} accounts)")
        tests_passed += 1
    else:
        print(f"  ✗ FAIL: Account count mismatch (Snowflake: {sf_account_count:,}, Expected: {total_accounts:,})")
        tests_failed += 1

    # Test 2: Count usage records
    print("\nTest 2: Verifying usage record count...")
    cursor.execute("SELECT COUNT(*) FROM PHONE_USAGE_DATA")
    sf_usage_count = cursor.fetchone()[0]

    if sf_usage_count == len(usage_df):
        print(f"  ✓ PASS: Usage record count matches ({sf_usage_count:,} records)")
        tests_passed += 1
    else:
        print(f"  ✗ FAIL: Usage record count mismatch (Snowflake: {sf_usage_count:,}, Expected: {len(usage_df):,})")
        tests_failed += 1

    # Test 3: Count churn records
    print("\nTest 3: Verifying churn record count...")
    cursor.execute("SELECT COUNT(*) FROM CHURN_RECORDS")
    sf_churn_count = cursor.fetchone()[0]

    if sf_churn_count == len(churn_df):
        print(f"  ✓ PASS: Churn record count matches ({sf_churn_count:,} records)")
        tests_passed += 1
    else:
        print(f"  ✗ FAIL: Churn record count mismatch (Snowflake: {sf_churn_count:,}, Expected: {len(churn_df):,})")
        tests_failed += 1

    # Test 4: Verify churn rate
    print("\nTest 4: Verifying churn rate...")
    cursor.execute("""
        SELECT
            COUNT(DISTINCT SERVICE_ACCOUNT_ID) as total_accounts,
            COUNT(DISTINCT CASE WHEN SA_ACCT_STATUS IN ('Suspended', 'Closed')
                  THEN SERVICE_ACCOUNT_ID END) as churned_accounts
        FROM ACCOUNT_ATTRIBUTES_MONTHLY
    """)
    result = cursor.fetchone()
    sf_total = result[0]
    sf_churned = result[1]
    sf_churn_rate = (sf_churned / sf_total * 100) if sf_total > 0 else 0

    # Allow 1% variance in churn rate
    if abs(sf_churn_rate - 8.0) <= 1.0:
        print(f"  ✓ PASS: Churn rate is {sf_churn_rate:.2f}% (expected ~8%)")
        tests_passed += 1
    else:
        print(f"  ✗ FAIL: Churn rate is {sf_churn_rate:.2f}% (expected ~8%)")
        tests_failed += 1

    # Test 5: Verify data integrity (no NULLs in key fields)
    print("\nTest 5: Verifying data integrity (no NULLs in key fields)...")
    cursor.execute("""
        SELECT COUNT(*)
        FROM ACCOUNT_ATTRIBUTES_MONTHLY
        WHERE SERVICE_ACCOUNT_ID IS NULL
           OR MONTH IS NULL
           OR COMPANY IS NULL
    """)
    null_count = cursor.fetchone()[0]

    if null_count == 0:
        print(f"  ✓ PASS: No NULL values in key fields")
        tests_passed += 1
    else:
        print(f"  ✗ FAIL: Found {null_count} NULL values in key fields")
        tests_failed += 1

    # Test 6: Verify usage data integrity
    print("\nTest 6: Verifying usage data has valid values...")
    cursor.execute("""
        SELECT COUNT(*)
        FROM PHONE_USAGE_DATA
        WHERE PHONE_TOTAL_CALLS < 0
           OR PHONE_TOTAL_MINUTES_OF_USE < 0
    """)
    invalid_count = cursor.fetchone()[0]

    if invalid_count == 0:
        print(f"  ✓ PASS: All usage values are valid (non-negative)")
        tests_passed += 1
    else:
        print(f"  ✗ FAIL: Found {invalid_count} records with invalid (negative) values")
        tests_failed += 1

    # Test 7: Verify package distribution
    print("\nTest 7: Verifying package distribution...")
    cursor.execute("""
        SELECT PACKAGE_NAME, COUNT(DISTINCT SERVICE_ACCOUNT_ID) as cnt
        FROM ACCOUNT_ATTRIBUTES_MONTHLY
        GROUP BY PACKAGE_NAME
        ORDER BY cnt DESC
    """)
    packages = cursor.fetchall()

    if len(packages) > 0:
        print(f"  ✓ PASS: Found {len(packages)} different packages")
        for pkg, cnt in packages:
            print(f"    - {pkg}: {cnt:,} accounts")
        tests_passed += 1
    else:
        print(f"  ✗ FAIL: No package distribution found")
        tests_failed += 1

    # Test 8: Verify account-usage relationship
    print("\nTest 8: Verifying all accounts have usage data...")
    cursor.execute("""
        SELECT COUNT(DISTINCT a.SERVICE_ACCOUNT_ID)
        FROM ACCOUNT_ATTRIBUTES_MONTHLY a
        LEFT JOIN PHONE_USAGE_DATA u ON a.SERVICE_ACCOUNT_ID = u.USERID
        WHERE u.USERID IS NULL
    """)
    orphan_accounts = cursor.fetchone()[0]

    if orphan_accounts == 0:
        print(f"  ✓ PASS: All accounts have usage data")
        tests_passed += 1
    else:
        print(f"  ✗ FAIL: Found {orphan_accounts} accounts without usage data")
        tests_failed += 1

    cursor.close()
    conn.close()

    # Summary
    print()
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"  Tests Passed: {tests_passed}")
    print(f"  Tests Failed: {tests_failed}")
    print(f"  Total Tests:  {tests_passed + tests_failed}")
    print()

    if tests_failed == 0:
        print("✓ ALL TESTS PASSED! Data is consistent and ready to use.")
    else:
        print("⚠️  SOME TESTS FAILED. Please review the results above.")
    print()

except Exception as e:
    print(f"✗ Error running tests: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# ============================================================================
# COMPLETION
# ============================================================================

print("=" * 80)
print("WORKFLOW COMPLETE!")
print("=" * 80)
print()
print("Summary:")
print(f"  ✓ Generated {total_accounts:,} accounts with {actual_churn_rate:.2f}% churn")
print(f"  ✓ Loaded {len(account_df):,} account records")
print(f"  ✓ Loaded {len(usage_df):,} usage records")
print(f"  ✓ Loaded {len(churn_df):,} churn records")
print(f"  ✓ Passed {tests_passed}/{tests_passed + tests_failed} consistency tests")
print()
print("Your Snowflake tables are now populated with fresh data!")
print()
