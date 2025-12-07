#!/usr/bin/env python3
"""
Refresh Phone Usage Data with MRR

This script:
1. Drops the existing PHONE_USAGE_DATA table
2. Recreates it with PACKAGE_TIER and MRR columns
3. Loads the newly generated data with MRR

Usage:
    ./venv/bin/python refresh_phone_usage_with_mrr.py
"""

import sys
from snowflake_loader import (
    get_snowflake_connection,
    create_usage_table,
    create_churn_table,
    load_csv_to_snowflake
)


def drop_and_recreate_usage_table(conn):
    """
    Drop and recreate the PHONE_USAGE_DATA table with new schema.

    Args:
        conn: Active Snowflake connection
    """
    cursor = conn.cursor()

    print("\n" + "=" * 80)
    print("DROPPING AND RECREATING PHONE_USAGE_DATA TABLE")
    print("=" * 80)

    try:
        print("\nDropping existing PHONE_USAGE_DATA table...")
        cursor.execute("DROP TABLE IF EXISTS PHONE_USAGE_DATA")
        print("✓ Table dropped")

        print("\nCreating new PHONE_USAGE_DATA table with MRR columns...")
        cursor.close()
        create_usage_table(conn)

    except Exception as e:
        print(f"⚠️  Error: {e}")
        cursor.close()
        raise

    print("=" * 80)


def drop_and_recreate_churn_table(conn):
    """
    Drop and recreate the CHURN_RECORDS table.

    Args:
        conn: Active Snowflake connection
    """
    cursor = conn.cursor()

    print("\n" + "=" * 80)
    print("DROPPING AND RECREATING CHURN_RECORDS TABLE")
    print("=" * 80)

    try:
        print("\nDropping existing CHURN_RECORDS table...")
        cursor.execute("DROP TABLE IF EXISTS CHURN_RECORDS")
        print("✓ Table dropped")

        print("\nCreating new CHURN_RECORDS table...")
        cursor.close()
        create_churn_table(conn)

    except Exception as e:
        print(f"⚠️  Error: {e}")
        cursor.close()
        raise

    print("=" * 80)


def verify_data_load(conn):
    """
    Verify data was loaded correctly with MRR columns.

    Args:
        conn: Active Snowflake connection
    """
    print("\n" + "=" * 80)
    print("VERIFYING DATA LOAD")
    print("=" * 80)

    cursor = conn.cursor()

    # Check row count
    print("\nTable Counts:")
    cursor.execute("SELECT COUNT(*) FROM PHONE_USAGE_DATA")
    usage_count = cursor.fetchone()[0]
    print(f"  PHONE_USAGE_DATA: {usage_count:,} rows")

    cursor.execute("SELECT COUNT(*) FROM CHURN_RECORDS")
    churn_count = cursor.fetchone()[0]
    print(f"  CHURN_RECORDS: {churn_count:,} rows")

    # Check MRR statistics
    print("\nMRR Statistics:")
    try:
        cursor.execute("""
            SELECT
                PACKAGE_TIER,
                COUNT(*) as record_count,
                AVG(MRR) as avg_mrr,
                MIN(MRR) as min_mrr,
                MAX(MRR) as max_mrr
            FROM PHONE_USAGE_DATA
            WHERE MRR > 0
            GROUP BY PACKAGE_TIER
            ORDER BY avg_mrr DESC
        """)
        results = cursor.fetchall()
        print(f"\n  {'Package Tier':<15} {'Records':<12} {'Avg MRR':<12} {'Min MRR':<12} {'Max MRR':<12}")
        print("  " + "-" * 63)
        for row in results:
            tier, count, avg_mrr, min_mrr, max_mrr = row
            print(f"  {tier:<15} {count:<12,} ${avg_mrr:<11.2f} ${min_mrr:<11.2f} ${max_mrr:<11.2f}")
    except Exception as e:
        print(f"  Error checking MRR: {e}")

    # Check date range
    print("\nData Period:")
    try:
        cursor.execute("""
            SELECT
                MIN(MONTH) as min_month,
                MAX(MONTH) as max_month,
                COUNT(DISTINCT MONTH) as unique_months,
                COUNT(DISTINCT USERID) as unique_users
            FROM PHONE_USAGE_DATA
        """)
        result = cursor.fetchone()
        print(f"  Period: {result[0]} to {result[1]}")
        print(f"  Unique Months: {result[2]}")
        print(f"  Unique Users: {result[3]}")
    except Exception as e:
        print(f"  Error checking period: {e}")

    # Sample data with MRR
    print("\nSample Records (first 5 with MRR):")
    try:
        cursor.execute("""
            SELECT USERID, MONTH, PACKAGE_TIER, MRR
            FROM PHONE_USAGE_DATA
            WHERE MRR > 0
            LIMIT 5
        """)
        results = cursor.fetchall()
        print(f"\n  {'UserID':<10} {'Month':<12} {'Package':<15} {'MRR':<10}")
        print("  " + "-" * 47)
        for row in results:
            user_id, month, tier, mrr = row
            print(f"  {user_id:<10} {str(month):<12} {tier:<15} ${mrr:<9.2f}")
    except Exception as e:
        print(f"  Error fetching sample: {e}")

    cursor.close()
    print("\n" + "=" * 80)


def main():
    """Main refresh function."""
    print("\n" + "=" * 80)
    print("PHONE USAGE DATA REFRESH WITH MRR")
    print("=" * 80)
    print("\nThis script will:")
    print("  1. Drop existing PHONE_USAGE_DATA table")
    print("  2. Recreate table with PACKAGE_TIER and MRR columns")
    print("  3. Load new CSV data with MRR")
    print("  4. Drop and recreate CHURN_RECORDS table")
    print("  5. Load new churn data")
    print("  6. Verify the data load")
    print("\n⚠️  WARNING: This will DELETE existing phone usage data in Snowflake!")
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

        # Drop and recreate tables
        drop_and_recreate_usage_table(conn)
        drop_and_recreate_churn_table(conn)

        # Load new data
        print("\n" + "=" * 80)
        print("LOADING NEW DATA")
        print("=" * 80)

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
        print("✓ DATA REFRESH COMPLETE!")
        print("=" * 80)
        print("\nYour Snowflake PHONE_USAGE_DATA table now includes:")
        print("  - PACKAGE_TIER column (Basic, Standard, Premium, Enterprise)")
        print("  - MRR column (Monthly Recurring Revenue)")
        print("\nThe data reflects:")
        print("  - 10% annual price increases based on signup date")
        print("  - 5-15% discounts for larger accounts")
        print("  - Natural price variation (±5%)")
        print("  - MRR = $0 after churn date")
        print()

    except Exception as e:
        print(f"\n❌ Error during refresh: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
