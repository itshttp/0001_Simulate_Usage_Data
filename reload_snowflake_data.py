"""
Reload Snowflake Data

This script:
1. Truncates existing Snowflake tables
2. Loads newly generated CSV data
3. Verifies the data load

Usage:
    python reload_snowflake_data.py
"""

import sys
from snowflake_loader import (
    get_snowflake_connection,
    create_all_tables,
    load_csv_to_snowflake,
    get_table_counts
)


def truncate_all_tables(conn):
    """
    Truncate all existing data from tables.

    Args:
        conn: Active Snowflake connection
    """
    cursor = conn.cursor()

    print("\n" + "=" * 80)
    print("TRUNCATING EXISTING DATA")
    print("=" * 80)

    tables = ['ACCOUNT_ATTRIBUTES_MONTHLY', 'PHONE_USAGE_DATA', 'CHURN_RECORDS']

    for table in tables:
        try:
            print(f"\nTruncating {table}...")
            cursor.execute(f"TRUNCATE TABLE IF EXISTS {table}")
            print(f"✓ {table} truncated")
        except Exception as e:
            print(f"⚠️  Warning: Could not truncate {table}: {e}")

    cursor.close()
    print("\n" + "=" * 80)


def verify_data_load(conn):
    """
    Verify data was loaded correctly.

    Args:
        conn: Active Snowflake connection
    """
    print("\n" + "=" * 80)
    print("VERIFYING DATA LOAD")
    print("=" * 80)

    counts = get_table_counts(conn)

    print("\nTable Counts:")
    for table, count in counts.items():
        print(f"  {table}: {count:,} rows")

    # Additional verification queries
    cursor = conn.cursor()

    # Check date range
    print("\nData Period Verification:")
    try:
        cursor.execute("""
            SELECT
                MIN(MONTH) as min_month,
                MAX(MONTH) as max_month,
                COUNT(DISTINCT MONTH) as unique_months
            FROM PHONE_USAGE_DATA
        """)
        result = cursor.fetchone()
        print(f"  Usage Data Period: {result[0]} to {result[1]}")
        print(f"  Unique Months: {result[2]}")
    except Exception as e:
        print(f"  Error checking period: {e}")

    # Check churn statistics
    print("\nChurn Statistics:")
    try:
        cursor.execute("""
            SELECT
                SUM(CHURNED) as churned_count,
                COUNT(*) as total_count,
                ROUND(SUM(CHURNED) * 100.0 / COUNT(*), 2) as churn_rate
            FROM CHURN_RECORDS
        """)
        result = cursor.fetchone()
        print(f"  Churned Accounts: {result[0]:,}")
        print(f"  Total Accounts: {result[1]:,}")
        print(f"  Churn Rate: {result[2]}%")
    except Exception as e:
        print(f"  Error checking churn: {e}")

    # Check account distribution
    print("\nAccount Distribution:")
    try:
        cursor.execute("""
            SELECT
                COUNT(DISTINCT SERVICE_ACCOUNT_ID) as unique_accounts
            FROM ACCOUNT_ATTRIBUTES_MONTHLY
        """)
        result = cursor.fetchone()
        print(f"  Unique Accounts: {result[0]:,}")
    except Exception as e:
        print(f"  Error checking accounts: {e}")

    cursor.close()
    print("\n" + "=" * 80)


def main():
    """Main reload function."""
    print("\n" + "=" * 80)
    print("SNOWFLAKE DATA RELOAD")
    print("=" * 80)
    print("\nThis script will:")
    print("  1. Truncate all existing data")
    print("  2. Load new CSV data")
    print("  3. Verify the data load")
    print("\n⚠️  WARNING: This will DELETE all existing data in Snowflake!")
    print("=" * 80)

    # Confirm
    response = input("\nDo you want to proceed? (yes/no): ")
    if response.lower() != 'yes':
        print("\n❌ Operation cancelled.")
        sys.exit(0)

    try:
        # Connect to Snowflake
        print("\nConnecting to Snowflake...")
        conn = get_snowflake_connection()

        # Truncate existing data
        truncate_all_tables(conn)

        # Create tables (if they don't exist)
        print("\n" + "=" * 80)
        print("ENSURING TABLES EXIST")
        print("=" * 80)
        create_all_tables(conn)

        # Load new data
        print("\n" + "=" * 80)
        print("LOADING NEW DATA")
        print("=" * 80)

        print("\nLoading account attributes...")
        load_csv_to_snowflake(conn, 'account_attributes_monthly.csv',
                              'ACCOUNT_ATTRIBUTES_MONTHLY', truncate=False)

        print("\nLoading phone usage data...")
        load_csv_to_snowflake(conn, 'phone_usage_data.csv',
                              'PHONE_USAGE_DATA', truncate=False)

        print("\nLoading churn records...")
        load_csv_to_snowflake(conn, 'churn_records.csv',
                              'CHURN_RECORDS', truncate=False)

        # Verify data
        verify_data_load(conn)

        # Close connection
        conn.close()

        print("\n" + "=" * 80)
        print("✓ DATA RELOAD COMPLETE!")
        print("=" * 80)
        print("\nYour Snowflake database now contains the new realistic data.")
        print("You can now use the Account Usage Dashboard to analyze the data.")
        print()

    except Exception as e:
        print(f"\n❌ Error during reload: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
