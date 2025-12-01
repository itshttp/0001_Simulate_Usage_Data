"""
Test Snowflake connection with SSL workarounds
"""

import os
import sys
import snowflake.connector
from dotenv import load_dotenv

# Fix encoding for Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

load_dotenv()

print("=" * 70)
print("SNOWFLAKE CONNECTION TEST (with SSL workarounds)")
print("=" * 70)
print()

# Get credentials
account = os.getenv('SNOWFLAKE_ACCOUNT')
user = os.getenv('SNOWFLAKE_USER')
password = os.getenv('SNOWFLAKE_PASSWORD')
warehouse = os.getenv('SNOWFLAKE_WAREHOUSE')
database = os.getenv('SNOWFLAKE_DATABASE')
schema = os.getenv('SNOWFLAKE_SCHEMA')
role = os.getenv('SNOWFLAKE_ROLE')

if not all([account, user, password, warehouse, database, schema]):
    print("ERROR: Missing required environment variables in .env file")
    print("Required: SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD,")
    print("          SNOWFLAKE_WAREHOUSE, SNOWFLAKE_DATABASE, SNOWFLAKE_SCHEMA")
    sys.exit(1)

print(f"Account: {account}")
print(f"User: {user}")
print(f"Warehouse: {warehouse}")
print(f"Database: {database}")
print(f"Schema: {schema}")
print()

# Try different connection methods
connection_methods = [
    {
        'name': 'Standard connection',
        'params': {
            'account': account,
            'user': user,
            'password': password,
            'warehouse': warehouse,
            'database': database,
            'schema': schema,
        }
    },
    {
        'name': 'Connection with SSL disabled (for testing only)',
        'params': {
            'account': account,
            'user': user,
            'password': password,
            'warehouse': warehouse,
            'database': database,
            'schema': schema,
            'insecure_mode': True,  # Disables SSL verification
        }
    },
    {
        'name': 'Connection with role',
        'params': {
            'account': account,
            'user': user,
            'password': password,
            'warehouse': warehouse,
            'database': database,
            'schema': schema,
            'role': role if role else 'ACCOUNTADMIN',
        }
    },
]

if role:
    connection_methods[0]['params']['role'] = role

for i, method in enumerate(connection_methods, 1):
    print(f"Method {i}: {method['name']}")
    print("-" * 70)
    
    try:
        conn = snowflake.connector.connect(**method['params'])
        cursor = conn.cursor()
        
        # Get session info
        cursor.execute("SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_DATABASE(), CURRENT_SCHEMA(), CURRENT_WAREHOUSE()")
        result = cursor.fetchone()
        
        print("SUCCESS! Connection established.")
        print()
        print("Session Information:")
        print(f"  User:      {result[0]}")
        print(f"  Role:      {result[1]}")
        print(f"  Database:  {result[2]}")
        print(f"  Schema:    {result[3]}")
        print(f"  Warehouse: {result[4]}")
        print()
        
        # Test a simple query
        cursor.execute("SELECT 1 as test")
        test_result = cursor.fetchone()
        print(f"Query test: SELECT 1 = {test_result[0]}")
        print()
        
        cursor.close()
        conn.close()
        
        print("=" * 70)
        print("CONNECTION TEST PASSED!")
        print("=" * 70)
        
        if method['name'].startswith('Connection with SSL disabled'):
            print()
            print("WARNING: SSL verification was disabled for this connection.")
            print("This is not recommended for production use.")
            print("Consider fixing SSL certificate issues instead.")
        
        sys.exit(0)
        
    except snowflake.connector.errors.OperationalError as e:
        error_msg = str(e)
        if 'SSL' in error_msg or 'certificate' in error_msg.lower():
            print(f"SSL Error: {error_msg[:200]}...")
        elif '250001' in error_msg:
            print("Authentication failed - check username/password")
        elif '250003' in error_msg:
            print("SSL certificate verification failed")
        else:
            print(f"Connection error: {error_msg[:200]}...")
    except Exception as e:
        print(f"Error: {str(e)[:200]}...")
    
    print()

print("=" * 70)
print("ALL CONNECTION METHODS FAILED")
print("=" * 70)
print()
print("Possible solutions:")
print("1. Check your .env file has correct credentials")
print("2. Verify network/firewall allows connections to Snowflake")
print("3. Check if you're behind a corporate proxy")
print("4. Try connecting from a different network")
print("5. Contact your IT department about SSL certificate issues")
print()
print("For more help, see: https://docs.snowflake.com/en/user-guide/client-connectivity-troubleshooting/overview")
print()

