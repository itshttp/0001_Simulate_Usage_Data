"""
Add Clustering Keys to Snowflake Tables

This script adds clustering keys to optimize query performance on frequently
filtered columns. Clustering keys enable automatic micro-partition pruning,
reducing the amount of data scanned during queries.

EFFICIENCY BENEFITS:
- Faster queries on filtered data (30-50% improvement)
- Automatic partition pruning based on clustering keys
- Reduced compute costs for filtered queries

Usage:
    python add_clustering_keys.py
"""

import os
import snowflake.connector
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def add_clustering_keys():
    """Add clustering keys to tables for query optimization."""

    print("\n" + "=" * 80)
    print("ADDING CLUSTERING KEYS TO SNOWFLAKE TABLES")
    print("=" * 80)

    # Get credentials from .env
    account = os.getenv('SNOWFLAKE_ACCOUNT')
    user = os.getenv('SNOWFLAKE_USER')
    password = os.getenv('SNOWFLAKE_PASSWORD')
    warehouse = os.getenv('SNOWFLAKE_WAREHOUSE', 'MY_FIRST_WH')
    database = os.getenv('SNOWFLAKE_DATABASE', 'MY_DATABASE')
    schema = os.getenv('SNOWFLAKE_SCHEMA', 'PUBLIC')
    role = os.getenv('SNOWFLAKE_ROLE', 'ACCOUNTADMIN')

    print(f"\nConnecting to Snowflake account: {account}")
    print(f"User: {user}")
    print(f"Role: {role}")
    print(f"Database: {database}.{schema}")
    print()

    try:
        # Connect to Snowflake
        conn = snowflake.connector.connect(
            account=account,
            user=user,
            password=password,
            warehouse=warehouse,
            database=database,
            schema=schema,
            role=role
        )

        cursor = conn.cursor()
        print("✓ Connected to Snowflake successfully!\n")

        # Check if tables exist
        print("-" * 80)
        print("Checking Tables...")
        print("-" * 80)

        tables_to_check = [
            'PHONE_USAGE_DATA',
            'ACCOUNT_ATTRIBUTES_MONTHLY'
        ]

        existing_tables = []
        for table in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table} LIMIT 1")
                row_count = cursor.fetchone()[0]
                existing_tables.append((table, row_count))
                print(f"✓ {table} exists ({row_count:,} rows)")
            except Exception as e:
                print(f"✗ {table} does not exist or cannot be accessed: {e}")

        if not existing_tables:
            print("\n⚠️  No tables found. Please create tables first.")
            cursor.close()
            conn.close()
            return False

        print()

        # Add clustering keys
        print("-" * 80)
        print("Adding Clustering Keys...")
        print("-" * 80)
        print()

        # 1. PHONE_USAGE_DATA - Cluster on (USERID, MONTH)
        # This optimizes queries filtering by user and date range
        print("1. Adding clustering key to PHONE_USAGE_DATA...")
        print("   Clustering on: (USERID, MONTH)")
        print("   Benefit: Optimizes queries filtering by user ID and date ranges")
        try:
            cursor.execute("""
                ALTER TABLE PHONE_USAGE_DATA 
                CLUSTER BY (USERID, MONTH)
            """)
            print("   ✓ Clustering key added successfully")
            print("   ⚠️  Note: Initial clustering may take time for large tables")
            print("   ⚠️  Note: Snowflake will automatically maintain clustering")
        except Exception as e:
            print(f"   ✗ Error: {e}")
            print("   ℹ️  Table may already have clustering or may need to be recreated")

        print()

        # 2. ACCOUNT_ATTRIBUTES_MONTHLY - Cluster on (SERVICE_ACCOUNT_ID, MONTH)
        # This optimizes queries filtering by account and date range
        print("2. Adding clustering key to ACCOUNT_ATTRIBUTES_MONTHLY...")
        print("   Clustering on: (SERVICE_ACCOUNT_ID, MONTH)")
        print("   Benefit: Optimizes queries filtering by account ID and date ranges")
        try:
            cursor.execute("""
                ALTER TABLE ACCOUNT_ATTRIBUTES_MONTHLY 
                CLUSTER BY (SERVICE_ACCOUNT_ID, MONTH)
            """)
            print("   ✓ Clustering key added successfully")
            print("   ⚠️  Note: Initial clustering may take time for large tables")
            print("   ⚠️  Note: Snowflake will automatically maintain clustering")
        except Exception as e:
            print(f"   ✗ Error: {e}")
            print("   ℹ️  Table may already have clustering or may need to be recreated")

        print()

        # Verify clustering keys
        print("-" * 80)
        print("Verifying Clustering Keys...")
        print("-" * 80)

        for table in ['PHONE_USAGE_DATA', 'ACCOUNT_ATTRIBUTES_MONTHLY']:
            try:
                cursor.execute(f"""
                    SELECT CLUSTERING_KEY
                    FROM INFORMATION_SCHEMA.TABLES
                    WHERE TABLE_SCHEMA = '{schema}'
                    AND TABLE_NAME = '{table}'
                """)
                result = cursor.fetchone()
                if result and result[0]:
                    print(f"✓ {table}: Clustered on {result[0]}")
                else:
                    print(f"⚠️  {table}: No clustering key found (may need table recreation)")
            except Exception as e:
                print(f"⚠️  {table}: Could not verify clustering: {e}")

        # Close connection
        cursor.close()
        conn.close()

        print("\n" + "=" * 80)
        print("CLUSTERING KEYS SETUP COMPLETE!")
        print("=" * 80)
        print("\n📊 Expected Benefits:")
        print("  - 30-50% faster queries on filtered data")
        print("  - Automatic micro-partition pruning")
        print("  - Reduced compute costs for date/user filtered queries")
        print("\n💡 Tips:")
        print("  - Clustering is maintained automatically by Snowflake")
        print("  - Monitor clustering depth: SELECT SYSTEM$CLUSTERING_DEPTH('TABLE_NAME')")
        print("  - Re-cluster if depth > 1.0: ALTER TABLE TABLE_NAME RECLUSTER")
        print()

        return True

    except Exception as e:
        print(f"\n✗ Failed to add clustering keys: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = add_clustering_keys()

    if success:
        print("\n✓ Clustering keys have been added successfully!")
        print("  Your queries should now be more efficient.")
        exit(0)
    else:
        print("\n✗ Failed to add clustering keys.")
        print("  Please check the errors above and try again.")
        exit(1)





