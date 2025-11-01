"""
Snowflake Data Loader

This module provides functions to connect to Snowflake and load the generated
account, usage, and churn data into Snowflake tables.

Setup:
1. Install dependencies: pip install snowflake-connector-python python-dotenv
2. Copy .env.example to .env
3. Fill in your Snowflake credentials in .env
4. Run load_all_data() to create tables and load data

Example:
    from snowflake_loader import load_all_data, test_connection

    # Test connection first
    test_connection()

    # Load all data
    load_all_data()
"""

import os
import pandas as pd
import snowflake.connector
from dotenv import load_dotenv
from typing import Optional, Dict, Any

# Load environment variables from .env file
load_dotenv()


def get_snowflake_connection():
    """
    Create and return a Snowflake connection using credentials from environment variables.

    Returns:
        snowflake.connector.connection.SnowflakeConnection: Active Snowflake connection

    Raises:
        ValueError: If required environment variables are missing
        Exception: If connection fails
    """
    # Required environment variables
    required_vars = [
        'SNOWFLAKE_ACCOUNT',
        'SNOWFLAKE_USER',
        'SNOWFLAKE_PASSWORD',
        'SNOWFLAKE_WAREHOUSE',
        'SNOWFLAKE_DATABASE',
        'SNOWFLAKE_SCHEMA'
    ]

    # Check for missing variables
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}\n"
            f"Please create a .env file based on .env.example and fill in your credentials."
        )

    # Connection parameters
    conn_params = {
        'account': os.getenv('SNOWFLAKE_ACCOUNT'),
        'user': os.getenv('SNOWFLAKE_USER'),
        'password': os.getenv('SNOWFLAKE_PASSWORD'),
        'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE'),
        'database': os.getenv('SNOWFLAKE_DATABASE'),
        'schema': os.getenv('SNOWFLAKE_SCHEMA'),
    }

    # Optional role parameter
    if os.getenv('SNOWFLAKE_ROLE'):
        conn_params['role'] = os.getenv('SNOWFLAKE_ROLE')

    try:
        conn = snowflake.connector.connect(**conn_params)
        print(f"✓ Connected to Snowflake: {conn_params['database']}.{conn_params['schema']}")
        return conn
    except Exception as e:
        print(f"✗ Failed to connect to Snowflake: {e}")
        raise


def test_connection():
    """Test the Snowflake connection and display current session info."""
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()

        # Get current session info
        cursor.execute("SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_DATABASE(), CURRENT_SCHEMA(), CURRENT_WAREHOUSE()")
        result = cursor.fetchone()

        print("\n" + "=" * 60)
        print("Snowflake Connection Test - SUCCESS")
        print("=" * 60)
        print(f"User:      {result[0]}")
        print(f"Role:      {result[1]}")
        print(f"Database:  {result[2]}")
        print(f"Schema:    {result[3]}")
        print(f"Warehouse: {result[4]}")
        print("=" * 60 + "\n")

        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"\n✗ Connection test failed: {e}\n")
        return False


def create_account_table(conn):
    """
    Create the ACCOUNT_ATTRIBUTES_MONTHLY table in Snowflake.

    Args:
        conn: Active Snowflake connection
    """
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS ACCOUNT_ATTRIBUTES_MONTHLY (
        MONTH DATE,
        ENTERPRISE_ACCOUNT_ID INTEGER,
        COMPANY VARCHAR(255),
        EA_BRAND_ID INTEGER,
        EA_BRAND_NAME VARCHAR(255),
        EA_UBRAND_ID VARCHAR(50),
        EA_UBRAND_DESCRIPTION VARCHAR(255),
        EA_ACCT_STATUS VARCHAR(50),
        SERVICE_ACCOUNT_ID INTEGER,
        SA_BRAND_ID INTEGER,
        SA_BRAND_NAME VARCHAR(255),
        SA_UBRAND_ID VARCHAR(50),
        SA_UBRAND_DESCRIPTION VARCHAR(255),
        SA_ACCT_STATUS VARCHAR(50),
        PACKAGE_ID INTEGER,
        PACKAGE_NAME VARCHAR(255),
        CATALOG_PACKAGE_ID VARCHAR(50),
        CATALOG_PACKAGE_NAME VARCHAR(255),
        IS_TESTER BOOLEAN,
        TIER_ID INTEGER,
        TIER_NAME VARCHAR(255),
        EDITION_NAME VARCHAR(255),
        EXTERNAL_ACCOUNT_ID VARCHAR(50),
        BAN VARCHAR(50),
        OPCO_ID VARCHAR(50),
        PRIMARY KEY (SERVICE_ACCOUNT_ID, MONTH)
    );
    """

    cursor = conn.cursor()
    cursor.execute(create_table_sql)
    print("✓ Table ACCOUNT_ATTRIBUTES_MONTHLY created/verified")
    cursor.close()


def create_usage_table(conn):
    """
    Create the PHONE_USAGE_DATA table in Snowflake.

    Args:
        conn: Active Snowflake connection
    """
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS PHONE_USAGE_DATA (
        USERID INTEGER,
        MONTH DATE,
        PHONE_TOTAL_CALLS INTEGER,
        PHONE_TOTAL_MINUTES_OF_USE FLOAT,
        VOICE_CALLS INTEGER,
        VOICE_MINS FLOAT,
        FAX_CALLS INTEGER,
        FAX_MINS FLOAT,
        PHONE_TOTAL_NUM_INBOUND_CALLS INTEGER,
        PHONE_TOTAL_NUM_OUTBOUND_CALLS INTEGER,
        PHONE_TOTAL_INBOUND_MIN FLOAT,
        PHONE_TOTAL_OUTBOUND_MIN FLOAT,
        OUT_VOICE_CALLS INTEGER,
        IN_VOICE_CALLS INTEGER,
        OUT_VOICE_MINS FLOAT,
        IN_VOICE_MINS FLOAT,
        OUT_FAX_CALLS INTEGER,
        IN_FAX_CALLS INTEGER,
        OUT_FAX_MINS FLOAT,
        IN_FAX_MINS FLOAT,
        PHONE_MAU INTEGER,
        CALL_MAU INTEGER,
        FAX_MAU INTEGER,
        HARDPHONE_CALLS INTEGER,
        SOFTPHONE_CALLS INTEGER,
        MOBILE_CALLS INTEGER,
        MOBILE_ANDROID_CALLS INTEGER,
        PRIMARY KEY (USERID, MONTH)
    );
    """

    cursor = conn.cursor()
    cursor.execute(create_table_sql)
    print("✓ Table PHONE_USAGE_DATA created/verified")
    cursor.close()


def create_churn_table(conn):
    """
    Create the CHURN_RECORDS table in Snowflake.

    Args:
        conn: Active Snowflake connection
    """
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS CHURN_RECORDS (
        USERID INTEGER PRIMARY KEY,
        CHURN_DATE DATE,
        CHURNED INTEGER
    );
    """

    cursor = conn.cursor()
    cursor.execute(create_table_sql)
    print("✓ Table CHURN_RECORDS created/verified")
    cursor.close()


def load_dataframe_to_snowflake(conn, df: pd.DataFrame, table_name: str,
                                  truncate: bool = False):
    """
    Load a pandas DataFrame into a Snowflake table using write_pandas.

    Args:
        conn: Active Snowflake connection
        df: pandas DataFrame to load
        table_name: Target table name in Snowflake
        truncate: If True, truncate table before loading (default: False)

    Returns:
        Tuple of (success: bool, nchunks: int, nrows: int, output: list)
    """
    try:
        # Make a copy to avoid modifying the original DataFrame
        df = df.copy()

        # Convert datetime columns to date format (DATE type, not TIMESTAMP)
        # Convert to string format YYYY-MM-DD which Snowflake can properly cast to DATE
        if 'MONTH' in df.columns and pd.api.types.is_datetime64_any_dtype(df['MONTH']):
            df['MONTH'] = pd.to_datetime(df['MONTH']).dt.strftime('%Y-%m-%d')
        if 'CHURN_DATE' in df.columns and pd.api.types.is_datetime64_any_dtype(df['CHURN_DATE']):
            df['CHURN_DATE'] = pd.to_datetime(df['CHURN_DATE']).dt.strftime('%Y-%m-%d')

        # Truncate table if requested
        if truncate:
            cursor = conn.cursor()
            cursor.execute(f"TRUNCATE TABLE IF EXISTS {table_name}")
            print(f"  Truncated table {table_name}")
            cursor.close()

        # Use write_pandas for efficient bulk loading
        from snowflake.connector.pandas_tools import write_pandas

        success, nchunks, nrows, output = write_pandas(
            conn=conn,
            df=df,
            table_name=table_name,
            auto_create_table=False,  # We create tables explicitly
            overwrite=False  # We handle truncate separately
        )

        if success:
            print(f"✓ Loaded {nrows:,} rows into {table_name}")
        else:
            print(f"✗ Failed to load data into {table_name}")

        return success, nchunks, nrows, output

    except Exception as e:
        print(f"✗ Error loading {table_name}: {e}")
        return False, 0, 0, []


def load_csv_to_snowflake(conn, csv_file: str, table_name: str,
                           truncate: bool = False):
    """
    Load a CSV file into a Snowflake table.

    Args:
        conn: Active Snowflake connection
        csv_file: Path to CSV file
        table_name: Target table name in Snowflake
        truncate: If True, truncate table before loading (default: False)

    Returns:
        Tuple of (success: bool, nchunks: int, nrows: int, output: list)
    """
    try:
        # Read CSV into DataFrame
        df = pd.read_csv(csv_file)

        # Convert date columns to proper date format (DATE type, not TIMESTAMP)
        # Convert to string format YYYY-MM-DD which Snowflake can properly cast to DATE
        if 'MONTH' in df.columns:
            df['MONTH'] = pd.to_datetime(df['MONTH']).dt.strftime('%Y-%m-%d')
        if 'CHURN_DATE' in df.columns:
            df['CHURN_DATE'] = pd.to_datetime(df['CHURN_DATE']).dt.strftime('%Y-%m-%d')

        print(f"  Loaded {len(df):,} rows from {csv_file}")

        # Load DataFrame to Snowflake
        return load_dataframe_to_snowflake(conn, df, table_name, truncate)

    except Exception as e:
        print(f"✗ Error loading CSV {csv_file}: {e}")
        return False, 0, 0, []


def create_all_tables(conn):
    """
    Create all required Snowflake tables.

    Args:
        conn: Active Snowflake connection
    """
    print("\nCreating Snowflake tables...")
    print("-" * 60)
    create_account_table(conn)
    create_usage_table(conn)
    create_churn_table(conn)
    print("-" * 60 + "\n")


def load_all_data(truncate: bool = False, from_dataframes: bool = False,
                  account_df: Optional[pd.DataFrame] = None,
                  usage_df: Optional[pd.DataFrame] = None,
                  churn_df: Optional[pd.DataFrame] = None):
    """
    Complete workflow: Create tables and load all data into Snowflake.

    Args:
        truncate: If True, truncate tables before loading (default: False)
        from_dataframes: If True, load from provided DataFrames instead of CSV files
        account_df: pandas DataFrame with account data (required if from_dataframes=True)
        usage_df: pandas DataFrame with usage data (required if from_dataframes=True)
        churn_df: pandas DataFrame with churn data (required if from_dataframes=True)

    Returns:
        bool: True if all operations successful, False otherwise
    """
    try:
        print("\n" + "=" * 60)
        print("Snowflake Data Loading - Starting")
        print("=" * 60 + "\n")

        # Connect to Snowflake
        conn = get_snowflake_connection()

        # Create tables
        create_all_tables(conn)

        # Load data
        print("Loading data into Snowflake...")
        print("-" * 60)

        if from_dataframes:
            # Load from DataFrames (useful when running from Jupyter)
            if account_df is None or usage_df is None or churn_df is None:
                raise ValueError("DataFrames must be provided when from_dataframes=True")

            load_dataframe_to_snowflake(conn, account_df, 'ACCOUNT_ATTRIBUTES_MONTHLY', truncate)
            load_dataframe_to_snowflake(conn, usage_df, 'PHONE_USAGE_DATA', truncate)
            load_dataframe_to_snowflake(conn, churn_df, 'CHURN_RECORDS', truncate)
        else:
            # Load from CSV files
            load_csv_to_snowflake(conn, 'account_attributes_monthly.csv',
                                 'ACCOUNT_ATTRIBUTES_MONTHLY', truncate)
            load_csv_to_snowflake(conn, 'phone_usage_data.csv',
                                 'PHONE_USAGE_DATA', truncate)
            load_csv_to_snowflake(conn, 'churn_records.csv',
                                 'CHURN_RECORDS', truncate)

        print("-" * 60)

        # Close connection
        conn.close()

        print("\n" + "=" * 60)
        print("Snowflake Data Loading - COMPLETE ✓")
        print("=" * 60 + "\n")

        return True

    except Exception as e:
        print(f"\n✗ Error during data loading: {e}\n")
        return False


def drop_all_tables(conn):
    """
    Drop all tables (useful for resetting).
    WARNING: This will delete all data!

    Args:
        conn: Active Snowflake connection
    """
    cursor = conn.cursor()

    print("\n⚠️  Dropping all tables...")
    cursor.execute("DROP TABLE IF EXISTS ACCOUNT_ATTRIBUTES_MONTHLY")
    print("  Dropped ACCOUNT_ATTRIBUTES_MONTHLY")

    cursor.execute("DROP TABLE IF EXISTS PHONE_USAGE_DATA")
    print("  Dropped PHONE_USAGE_DATA")

    cursor.execute("DROP TABLE IF EXISTS CHURN_RECORDS")
    print("  Dropped CHURN_RECORDS")

    cursor.close()
    print("✓ All tables dropped\n")


def get_table_counts(conn) -> Dict[str, int]:
    """
    Get row counts for all tables.

    Args:
        conn: Active Snowflake connection

    Returns:
        Dictionary with table names as keys and row counts as values
    """
    cursor = conn.cursor()
    counts = {}

    tables = ['ACCOUNT_ATTRIBUTES_MONTHLY', 'PHONE_USAGE_DATA', 'CHURN_RECORDS']

    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            counts[table] = count
        except:
            counts[table] = 0

    cursor.close()
    return counts


def show_table_summary():
    """Display summary statistics for all Snowflake tables."""
    try:
        conn = get_snowflake_connection()
        counts = get_table_counts(conn)

        print("\n" + "=" * 60)
        print("Snowflake Table Summary")
        print("=" * 60)
        for table, count in counts.items():
            print(f"  {table}: {count:,} rows")
        print("=" * 60 + "\n")

        conn.close()
    except Exception as e:
        print(f"✗ Error getting table summary: {e}")


if __name__ == "__main__":
    # Example usage when run as a script
    import argparse

    parser = argparse.ArgumentParser(description='Load data into Snowflake')
    parser.add_argument('--test', action='store_true', help='Test connection only')
    parser.add_argument('--truncate', action='store_true', help='Truncate tables before loading')
    parser.add_argument('--summary', action='store_true', help='Show table summary')

    args = parser.parse_args()

    if args.test:
        test_connection()
    elif args.summary:
        show_table_summary()
    else:
        load_all_data(truncate=args.truncate)
