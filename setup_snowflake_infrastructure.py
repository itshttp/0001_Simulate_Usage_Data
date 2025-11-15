"""
Setup Snowflake Infrastructure

This script creates the necessary Snowflake infrastructure:
- Warehouse
- Database
- Schema

It uses the admin credentials from .env to create these resources.
"""

import os
import snowflake.connector
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def create_snowflake_infrastructure():
    """Create warehouse, database, and schema in Snowflake."""

    print("\n" + "=" * 80)
    print("SNOWFLAKE INFRASTRUCTURE SETUP")
    print("=" * 80)

    # Get credentials from .env
    account = os.getenv('SNOWFLAKE_ACCOUNT')
    user = os.getenv('SNOWFLAKE_USER')
    password = os.getenv('SNOWFLAKE_PASSWORD')
    role = os.getenv('SNOWFLAKE_ROLE', 'ACCOUNTADMIN')

    # Define resource names
    warehouse_name = 'MY_FIRST_WH'
    database_name = 'MY_DATABASE'
    schema_name = 'PUBLIC'

    print(f"\nConnecting to Snowflake account: {account}")
    print(f"User: {user}")
    print(f"Role: {role}")
    print()

    try:
        # Connect to Snowflake without specifying warehouse/database/schema
        # since they don't exist yet
        conn = snowflake.connector.connect(
            account=account,
            user=user,
            password=password,
            role=role
        )

        cursor = conn.cursor()
        print("✓ Connected to Snowflake successfully!\n")

        # Create Warehouse
        print("-" * 80)
        print("Creating Warehouse...")
        print("-" * 80)
        try:
            cursor.execute(f"""
                CREATE WAREHOUSE IF NOT EXISTS {warehouse_name}
                WITH WAREHOUSE_SIZE = 'XSMALL'
                AUTO_SUSPEND = 300
                AUTO_RESUME = TRUE
                INITIALLY_SUSPENDED = FALSE
            """)
            print(f"✓ Warehouse '{warehouse_name}' created successfully")
            print(f"  - Size: XSMALL")
            print(f"  - Auto-suspend: 300 seconds")
            print(f"  - Auto-resume: Enabled")
        except Exception as e:
            print(f"✗ Error creating warehouse: {e}")
            raise

        # Use the warehouse
        cursor.execute(f"USE WAREHOUSE {warehouse_name}")
        print(f"✓ Using warehouse: {warehouse_name}\n")

        # Create Database
        print("-" * 80)
        print("Creating Database...")
        print("-" * 80)
        try:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_name}")
            print(f"✓ Database '{database_name}' created successfully")
        except Exception as e:
            print(f"✗ Error creating database: {e}")
            raise

        # Use the database
        cursor.execute(f"USE DATABASE {database_name}")
        print(f"✓ Using database: {database_name}\n")

        # Create Schema (PUBLIC schema is created by default, but we'll ensure it exists)
        print("-" * 80)
        print("Creating Schema...")
        print("-" * 80)
        try:
            cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
            print(f"✓ Schema '{schema_name}' created successfully")
        except Exception as e:
            print(f"✗ Error creating schema: {e}")
            raise

        # Use the schema
        cursor.execute(f"USE SCHEMA {schema_name}")
        print(f"✓ Using schema: {schema_name}\n")

        # Verify the setup
        print("-" * 80)
        print("Verifying Setup...")
        print("-" * 80)
        cursor.execute("SELECT CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_SCHEMA(), CURRENT_ROLE()")
        result = cursor.fetchone()
        print(f"✓ Current warehouse: {result[0]}")
        print(f"✓ Current database: {result[1]}")
        print(f"✓ Current schema: {result[2]}")
        print(f"✓ Current role: {result[3]}")

        # Close connection
        cursor.close()
        conn.close()

        print("\n" + "=" * 80)
        print("INFRASTRUCTURE SETUP COMPLETE!")
        print("=" * 80)
        print(f"\nCreated resources:")
        print(f"  - Warehouse: {warehouse_name}")
        print(f"  - Database: {database_name}")
        print(f"  - Schema: {schema_name}")
        print()

        return {
            'warehouse': warehouse_name,
            'database': database_name,
            'schema': schema_name,
            'success': True
        }

    except Exception as e:
        print(f"\n✗ Failed to setup infrastructure: {e}")
        print("\nPlease check your credentials in the .env file.")
        return {
            'warehouse': None,
            'database': None,
            'schema': None,
            'success': False,
            'error': str(e)
        }


if __name__ == "__main__":
    result = create_snowflake_infrastructure()

    if result['success']:
        print("\n✓ You can now proceed with loading data into Snowflake!")
        exit(0)
    else:
        print(f"\n✗ Setup failed: {result.get('error', 'Unknown error')}")
        exit(1)
