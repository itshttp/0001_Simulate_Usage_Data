"""
Monitor Snowflake Query Performance

This script analyzes query history to identify expensive queries, track
performance trends, and monitor warehouse usage for cost optimization.

EFFICIENCY BENEFITS:
- Identify expensive queries for optimization
- Track query performance trends
- Monitor warehouse usage and costs
- Detect inefficient query patterns

Usage:
    python monitor_query_performance.py [--days N] [--limit N] [--warehouse NAME]
"""

import os
import sys
import argparse
from datetime import datetime, timedelta
import pandas as pd
import snowflake.connector
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_snowflake_connection():
    """Create and return a Snowflake connection."""
    account = os.getenv('SNOWFLAKE_ACCOUNT')
    user = os.getenv('SNOWFLAKE_USER')
    password = os.getenv('SNOWFLAKE_PASSWORD')
    warehouse = os.getenv('SNOWFLAKE_WAREHOUSE', 'MY_FIRST_WH')
    database = os.getenv('SNOWFLAKE_DATABASE', 'MY_DATABASE')
    schema = os.getenv('SNOWFLAKE_SCHEMA', 'PUBLIC')
    role = os.getenv('SNOWFLAKE_ROLE', 'ACCOUNTADMIN')

    return snowflake.connector.connect(
        account=account,
        user=user,
        password=password,
        warehouse=warehouse,
        database=database,
        schema=schema,
        role=role
    )


def analyze_expensive_queries(conn, days=7, limit=20, warehouse=None):
    """Analyze the most expensive queries in the query history."""
    
    print("\n" + "=" * 80)
    print("EXPENSIVE QUERIES ANALYSIS")
    print("=" * 80)
    print(f"\nAnalyzing queries from the last {days} days...")
    if warehouse:
        print(f"Filtering by warehouse: {warehouse}")
    print()

    cursor = conn.cursor()

    # Build query
    warehouse_filter = f"AND WAREHOUSE_NAME = '{warehouse}'" if warehouse else ""
    
    query = f"""
    SELECT 
        QUERY_ID,
        QUERY_TEXT,
        WAREHOUSE_NAME,
        DATABASE_NAME,
        SCHEMA_NAME,
        USER_NAME,
        ROLE_NAME,
        START_TIME,
        END_TIME,
        TOTAL_ELAPSED_TIME / 1000 AS ELAPSED_TIME_SECONDS,
        BYTES_SCANNED,
        ROWS_PRODUCED,
        PARTITIONS_SCANNED,
        PARTITIONS_TOTAL,
        CREDITS_USED_CLOUD_SERVICES,
        CASE 
            WHEN WAREHOUSE_SIZE = 'XSMALL' THEN 1
            WHEN WAREHOUSE_SIZE = 'SMALL' THEN 2
            WHEN WAREHOUSE_SIZE = 'MEDIUM' THEN 4
            WHEN WAREHOUSE_SIZE = 'LARGE' THEN 8
            WHEN WAREHOUSE_SIZE = 'X-LARGE' THEN 16
            WHEN WAREHOUSE_SIZE = '2X-LARGE' THEN 32
            WHEN WAREHOUSE_SIZE = '3X-LARGE' THEN 64
            WHEN WAREHOUSE_SIZE = '4X-LARGE' THEN 128
            ELSE 1
        END * (TOTAL_ELAPSED_TIME / 3600000.0) AS ESTIMATED_CREDITS
    FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
    WHERE START_TIME >= DATEADD(DAY, -{days}, CURRENT_TIMESTAMP())
        AND QUERY_TYPE = 'SELECT'
        AND EXECUTION_STATUS = 'SUCCESS'
        {warehouse_filter}
    ORDER BY ESTIMATED_CREDITS DESC
    LIMIT {limit}
    """

    try:
        cursor.execute(query)
        results = cursor.fetchall()
        
        if not results:
            print("No queries found matching the criteria.")
            return None

        # Convert to DataFrame
        columns = [
            'QUERY_ID', 'QUERY_TEXT', 'WAREHOUSE_NAME', 'DATABASE_NAME', 
            'SCHEMA_NAME', 'USER_NAME', 'ROLE_NAME', 'START_TIME', 'END_TIME',
            'ELAPSED_TIME_SECONDS', 'BYTES_SCANNED', 'ROWS_PRODUCED',
            'PARTITIONS_SCANNED', 'PARTITIONS_TOTAL', 'CREDITS_USED_CLOUD_SERVICES',
            'ESTIMATED_CREDITS'
        ]
        
        df = pd.DataFrame(results, columns=columns)
        
        print(f"Found {len(df)} expensive queries:\n")
        print("-" * 80)
        
        for idx, row in df.iterrows():
            print(f"\n{idx + 1}. Query ID: {row['QUERY_ID']}")
            print(f"   Estimated Credits: {row['ESTIMATED_CREDITS']:.4f}")
            print(f"   Elapsed Time: {row['ELAPSED_TIME_SECONDS']:.2f} seconds")
            print(f"   Bytes Scanned: {row['BYTES_SCANNED']:,}" if row['BYTES_SCANNED'] else "   Bytes Scanned: N/A")
            print(f"   Partitions Scanned: {row['PARTITIONS_SCANNED']:,} / {row['PARTITIONS_TOTAL']:,}")
            print(f"   Warehouse: {row['WAREHOUSE_NAME']}")
            print(f"   User: {row['USER_NAME']}")
            print(f"   Time: {row['START_TIME']}")
            
            # Show first 200 chars of query
            query_preview = row['QUERY_TEXT'][:200].replace('\n', ' ')
            if len(row['QUERY_TEXT']) > 200:
                query_preview += "..."
            print(f"   Query: {query_preview}")
        
        print("\n" + "=" * 80)
        return df

    except Exception as e:
        print(f"Error analyzing queries: {e}")
        return None
    finally:
        cursor.close()


def analyze_query_patterns(conn, days=7):
    """Analyze query patterns to identify optimization opportunities."""
    
    print("\n" + "=" * 80)
    print("QUERY PATTERNS ANALYSIS")
    print("=" * 80)
    print(f"\nAnalyzing query patterns from the last {days} days...\n")

    cursor = conn.cursor()

    query = f"""
    SELECT 
        CASE 
            WHEN QUERY_TEXT ILIKE '%SELECT *%' THEN 'SELECT * (Full Column Scan)'
            WHEN QUERY_TEXT ILIKE '%WHERE%' THEN 'Has WHERE Clause'
            ELSE 'No WHERE Clause'
        END AS QUERY_PATTERN,
        COUNT(*) AS QUERY_COUNT,
        AVG(TOTAL_ELAPSED_TIME / 1000) AS AVG_ELAPSED_SECONDS,
        SUM(CASE 
            WHEN WAREHOUSE_SIZE = 'XSMALL' THEN 1
            WHEN WAREHOUSE_SIZE = 'SMALL' THEN 2
            WHEN WAREHOUSE_SIZE = 'MEDIUM' THEN 4
            WHEN WAREHOUSE_SIZE = 'LARGE' THEN 8
            WHEN WAREHOUSE_SIZE = 'X-LARGE' THEN 16
            WHEN WAREHOUSE_SIZE = '2X-LARGE' THEN 32
            WHEN WAREHOUSE_SIZE = '3X-LARGE' THEN 64
            WHEN WAREHOUSE_SIZE = '4X-LARGE' THEN 128
            ELSE 1
        END * (TOTAL_ELAPSED_TIME / 3600000.0)) AS TOTAL_ESTIMATED_CREDITS
    FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
    WHERE START_TIME >= DATEADD(DAY, -{days}, CURRENT_TIMESTAMP())
        AND QUERY_TYPE = 'SELECT'
        AND EXECUTION_STATUS = 'SUCCESS'
    GROUP BY QUERY_PATTERN
    ORDER BY TOTAL_ESTIMATED_CREDITS DESC
    """

    try:
        cursor.execute(query)
        results = cursor.fetchall()
        
        if not results:
            print("No query patterns found.")
            return None

        print("Query Pattern Analysis:")
        print("-" * 80)
        print(f"{'Pattern':<40} {'Count':<10} {'Avg Time (s)':<15} {'Est. Credits':<15}")
        print("-" * 80)
        
        for row in results:
            pattern, count, avg_time, credits = row
            print(f"{pattern:<40} {count:<10} {avg_time:<15.2f} {credits:<15.4f}")
        
        print("\n" + "=" * 80)
        return results

    except Exception as e:
        print(f"Error analyzing patterns: {e}")
        return None
    finally:
        cursor.close()


def analyze_warehouse_usage(conn, days=7):
    """Analyze warehouse usage and costs."""
    
    print("\n" + "=" * 80)
    print("WAREHOUSE USAGE ANALYSIS")
    print("=" * 80)
    print(f"\nAnalyzing warehouse usage from the last {days} days...\n")

    cursor = conn.cursor()

    query = f"""
    SELECT 
        WAREHOUSE_NAME,
        COUNT(DISTINCT QUERY_ID) AS QUERY_COUNT,
        SUM(TOTAL_ELAPSED_TIME / 1000) AS TOTAL_ELAPSED_SECONDS,
        AVG(TOTAL_ELAPSED_TIME / 1000) AS AVG_ELAPSED_SECONDS,
        SUM(CASE 
            WHEN WAREHOUSE_SIZE = 'XSMALL' THEN 1
            WHEN WAREHOUSE_SIZE = 'SMALL' THEN 2
            WHEN WAREHOUSE_SIZE = 'MEDIUM' THEN 4
            WHEN WAREHOUSE_SIZE = 'LARGE' THEN 8
            WHEN WAREHOUSE_SIZE = 'X-LARGE' THEN 16
            WHEN WAREHOUSE_SIZE = '2X-LARGE' THEN 32
            WHEN WAREHOUSE_SIZE = '3X-LARGE' THEN 64
            WHEN WAREHOUSE_SIZE = '4X-LARGE' THEN 128
            ELSE 1
        END * (TOTAL_ELAPSED_TIME / 3600000.0)) AS ESTIMATED_CREDITS
    FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
    WHERE START_TIME >= DATEADD(DAY, -{days}, CURRENT_TIMESTAMP())
        AND EXECUTION_STATUS = 'SUCCESS'
    GROUP BY WAREHOUSE_NAME
    ORDER BY ESTIMATED_CREDITS DESC
    """

    try:
        cursor.execute(query)
        results = cursor.fetchall()
        
        if not results:
            print("No warehouse usage data found.")
            return None

        print("Warehouse Usage Summary:")
        print("-" * 80)
        print(f"{'Warehouse':<30} {'Queries':<10} {'Total Time (s)':<15} {'Est. Credits':<15}")
        print("-" * 80)
        
        total_credits = 0
        for row in results:
            warehouse, query_count, total_time, avg_time, credits = row
            print(f"{warehouse:<30} {query_count:<10} {total_time:<15.0f} {credits:<15.4f}")
            total_credits += credits
        
        print("-" * 80)
        print(f"{'TOTAL':<30} {'':<10} {'':<15} {total_credits:<15.4f}")
        print("\n" + "=" * 80)
        return results

    except Exception as e:
        print(f"Error analyzing warehouse usage: {e}")
        return None
    finally:
        cursor.close()


def check_table_clustering(conn):
    """Check clustering status of tables."""
    
    print("\n" + "=" * 80)
    print("TABLE CLUSTERING STATUS")
    print("=" * 80)
    print()

    cursor = conn.cursor()

    query = """
    SELECT 
        TABLE_SCHEMA,
        TABLE_NAME,
        CLUSTERING_KEY,
        ROW_COUNT
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_SCHEMA = 'PUBLIC'
        AND TABLE_TYPE = 'BASE TABLE'
    ORDER BY TABLE_NAME
    """

    try:
        cursor.execute(query)
        results = cursor.fetchall()
        
        if not results:
            print("No tables found.")
            return None

        print("Table Clustering Status:")
        print("-" * 80)
        print(f"{'Table':<40} {'Clustering Key':<40} {'Row Count':<15}")
        print("-" * 80)
        
        for row in results:
            schema, table, clustering_key, row_count = row
            clustering = clustering_key if clustering_key else "❌ No clustering"
            row_count_str = f"{row_count:,}" if row_count else "N/A"
            print(f"{table:<40} {clustering:<40} {row_count_str:<15}")
        
        print("\n" + "=" * 80)
        return results

    except Exception as e:
        print(f"Error checking clustering: {e}")
        return None
    finally:
        cursor.close()


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Monitor Snowflake query performance')
    parser.add_argument('--days', type=int, default=7, help='Number of days to analyze (default: 7)')
    parser.add_argument('--limit', type=int, default=20, help='Number of expensive queries to show (default: 20)')
    parser.add_argument('--warehouse', type=str, default=None, help='Filter by warehouse name')
    parser.add_argument('--no-expensive', action='store_true', help='Skip expensive queries analysis')
    parser.add_argument('--no-patterns', action='store_true', help='Skip query patterns analysis')
    parser.add_argument('--no-warehouse', action='store_true', help='Skip warehouse usage analysis')
    parser.add_argument('--no-clustering', action='store_true', help='Skip clustering status check')

    args = parser.parse_args()

    print("\n" + "=" * 80)
    print("SNOWFLAKE QUERY PERFORMANCE MONITOR")
    print("=" * 80)

    try:
        conn = get_snowflake_connection()
        print("✓ Connected to Snowflake successfully!")

        # Run analyses
        if not args.no_expensive:
            analyze_expensive_queries(conn, days=args.days, limit=args.limit, warehouse=args.warehouse)

        if not args.no_patterns:
            analyze_query_patterns(conn, days=args.days)

        if not args.no_warehouse:
            analyze_warehouse_usage(conn, days=args.days)

        if not args.no_clustering:
            check_table_clustering(conn)

        conn.close()

        print("\n" + "=" * 80)
        print("ANALYSIS COMPLETE!")
        print("=" * 80)
        print("\n💡 Tips for optimization:")
        print("  - Look for queries with high bytes scanned (add WHERE clauses)")
        print("  - Check for SELECT * patterns (select specific columns)")
        print("  - Monitor queries without WHERE clauses (add filters)")
        print("  - Consider adding clustering keys to frequently filtered tables")
        print("  - Use materialized views for common aggregations")
        print()

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()








