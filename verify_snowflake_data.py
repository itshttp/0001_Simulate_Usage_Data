"""
Verify Snowflake Data Quality

This script performs comprehensive data quality checks on the loaded Snowflake data.
"""

import os
from snowflake_loader import get_snowflake_connection

def verify_data_quality():
    """Run comprehensive data quality checks."""
    print("\n" + "=" * 80)
    print("SNOWFLAKE DATA QUALITY VERIFICATION")
    print("=" * 80)

    try:
        # Connect to Snowflake
        conn = get_snowflake_connection()
        cursor = conn.cursor()

        # 1. Table Row Counts
        print("\n" + "-" * 80)
        print("1. TABLE ROW COUNTS")
        print("-" * 80)

        tables = ['ACCOUNT_ATTRIBUTES_MONTHLY', 'PHONE_USAGE_DATA', 'CHURN_RECORDS']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table}: {count:,} rows")

        # 2. Date Ranges
        print("\n" + "-" * 80)
        print("2. DATE RANGES")
        print("-" * 80)

        cursor.execute("""
            SELECT
                MIN(MONTH) as min_date,
                MAX(MONTH) as max_date,
                COUNT(DISTINCT MONTH) as unique_months
            FROM PHONE_USAGE_DATA
        """)
        result = cursor.fetchone()
        print(f"  Usage Data:")
        print(f"    - Period: {result[0]} to {result[1]}")
        print(f"    - Unique Months: {result[2]}")

        cursor.execute("""
            SELECT
                MIN(MONTH) as min_date,
                MAX(MONTH) as max_date,
                COUNT(DISTINCT MONTH) as unique_months
            FROM ACCOUNT_ATTRIBUTES_MONTHLY
        """)
        result = cursor.fetchone()
        print(f"  Account Attributes:")
        print(f"    - Period: {result[0]} to {result[1]}")
        print(f"    - Unique Months: {result[2]}")

        # 3. Account Statistics
        print("\n" + "-" * 80)
        print("3. ACCOUNT STATISTICS")
        print("-" * 80)

        cursor.execute("""
            SELECT COUNT(DISTINCT SERVICE_ACCOUNT_ID)
            FROM ACCOUNT_ATTRIBUTES_MONTHLY
        """)
        unique_accounts = cursor.fetchone()[0]
        print(f"  Unique Accounts: {unique_accounts:,}")

        cursor.execute("""
            SELECT COUNT(DISTINCT USERID)
            FROM PHONE_USAGE_DATA
        """)
        unique_users = cursor.fetchone()[0]
        print(f"  Unique Users in Usage Data: {unique_users:,}")

        # 4. Churn Statistics
        print("\n" + "-" * 80)
        print("4. CHURN STATISTICS")
        print("-" * 80)

        cursor.execute("""
            SELECT
                COUNT(*) as churned_accounts,
                MIN(CHURN_DATE) as first_churn,
                MAX(CHURN_DATE) as last_churn
            FROM CHURN_RECORDS
            WHERE CHURNED = 1
        """)
        result = cursor.fetchone()
        churned_count = result[0]
        print(f"  Total Churned Accounts: {churned_count:,}")
        print(f"  First Churn Date: {result[1]}")
        print(f"  Last Churn Date: {result[2]}")
        print(f"  Active Accounts: {unique_accounts - churned_count:,}")
        print(f"  Churn Rate: {(churned_count / unique_accounts * 100):.2f}%")

        # 5. Usage Data Sample
        print("\n" + "-" * 80)
        print("5. USAGE DATA SAMPLE (First 3 records)")
        print("-" * 80)

        cursor.execute("""
            SELECT
                USERID,
                MONTH,
                PHONE_TOTAL_CALLS,
                PHONE_TOTAL_MINUTES_OF_USE,
                VOICE_CALLS,
                PHONE_MAU
            FROM PHONE_USAGE_DATA
            ORDER BY USERID, MONTH
            LIMIT 3
        """)
        results = cursor.fetchall()
        print(f"  {'USERID':<10} {'MONTH':<12} {'CALLS':<8} {'MINUTES':<10} {'VOICE':<8} {'MAU':<6}")
        print(f"  {'-'*10} {'-'*12} {'-'*8} {'-'*10} {'-'*8} {'-'*6}")
        for row in results:
            print(f"  {row[0]:<10} {str(row[1]):<12} {row[2]:<8} {row[3]:<10.2f} {row[4]:<8} {row[5]:<6}")

        # 6. Account Attributes Sample
        print("\n" + "-" * 80)
        print("6. ACCOUNT ATTRIBUTES SAMPLE (First 3 records)")
        print("-" * 80)

        cursor.execute("""
            SELECT
                SERVICE_ACCOUNT_ID,
                MONTH,
                COMPANY,
                PACKAGE_NAME,
                TIER_NAME,
                SA_ACCT_STATUS
            FROM ACCOUNT_ATTRIBUTES_MONTHLY
            ORDER BY SERVICE_ACCOUNT_ID, MONTH
            LIMIT 3
        """)
        results = cursor.fetchall()
        print(f"  {'ACCT_ID':<10} {'MONTH':<12} {'COMPANY':<25} {'PACKAGE':<15} {'TIER':<15} {'STATUS':<10}")
        print(f"  {'-'*10} {'-'*12} {'-'*25} {'-'*15} {'-'*15} {'-'*10}")
        for row in results:
            company = row[2][:23] if len(row[2]) > 23 else row[2]
            print(f"  {row[0]:<10} {str(row[1]):<12} {company:<25} {row[3]:<15} {row[4]:<15} {row[5]:<10}")

        # 7. Data Integrity Checks
        print("\n" + "-" * 80)
        print("7. DATA INTEGRITY CHECKS")
        print("-" * 80)

        # Check for orphaned records
        cursor.execute("""
            SELECT COUNT(*)
            FROM PHONE_USAGE_DATA u
            LEFT JOIN ACCOUNT_ATTRIBUTES_MONTHLY a
                ON u.USERID = a.SERVICE_ACCOUNT_ID
                AND u.MONTH = a.MONTH
            WHERE a.SERVICE_ACCOUNT_ID IS NULL
        """)
        orphaned_usage = cursor.fetchone()[0]
        print(f"  Orphaned Usage Records (no matching account): {orphaned_usage:,}")

        cursor.execute("""
            SELECT COUNT(*)
            FROM CHURN_RECORDS c
            LEFT JOIN ACCOUNT_ATTRIBUTES_MONTHLY a
                ON c.USERID = a.SERVICE_ACCOUNT_ID
            WHERE a.SERVICE_ACCOUNT_ID IS NULL
        """)
        orphaned_churn = cursor.fetchone()[0]
        print(f"  Orphaned Churn Records (no matching account): {orphaned_churn:,}")

        # 8. Access Verification
        print("\n" + "-" * 80)
        print("8. ACCESS VERIFICATION")
        print("-" * 80)

        cursor.execute("SHOW ROLES")
        roles = cursor.fetchall()
        role_names = [r[1] for r in roles]

        print(f"  Available Roles:")
        for role in ['READ_ONLY_ROLE', 'DATA_ANALYST_ROLE', 'ACCOUNTADMIN']:
            if role in role_names:
                print(f"    ✓ {role}")
            else:
                print(f"    ✗ {role} (not found)")

        cursor.close()
        conn.close()

        print("\n" + "=" * 80)
        print("VERIFICATION COMPLETE ✓")
        print("=" * 80)

        # Summary
        print("\n📊 SUMMARY:")
        print(f"  • Total Accounts: {unique_accounts:,}")
        print(f"  • Total Usage Records: {unique_users:,} users across {result[2]} months")
        print(f"  • Churned Accounts: {churned_count:,} ({(churned_count / unique_accounts * 100):.2f}%)")
        print(f"  • Active Accounts: {unique_accounts - churned_count:,}")
        print(f"  • Data Integrity: {'✓ PASSED' if orphaned_usage == 0 and orphaned_churn == 0 else '⚠ ISSUES FOUND'}")
        print()

        return True

    except Exception as e:
        print(f"\n✗ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = verify_data_quality()
    exit(0 if success else 1)
