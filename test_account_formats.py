"""
Test Snowflake connection with different account identifier formats
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

account = os.getenv('SNOWFLAKE_ACCOUNT')
user = os.getenv('SNOWFLAKE_USER')
password = os.getenv('SNOWFLAKE_PASSWORD')
warehouse = os.getenv('SNOWFLAKE_WAREHOUSE')
database = os.getenv('SNOWFLAKE_DATABASE')
schema = os.getenv('SNOWFLAKE_SCHEMA')

print("=" * 70)
print("TESTING DIFFERENT ACCOUNT FORMATS")
print("=" * 70)
print(f"\nCurrent account in .env: {account}")
print(f"User: {user}")
print(f"Warehouse: {warehouse}")
print(f"Database: {database}")
print(f"Schema: {schema}")
print()

# Generate different account format variations
account_formats = []
if account:
    account_formats = [
        account,                          # Original format
        account.lower(),                  # Lowercase
        account.upper(),                  # Uppercase
        account.replace('-', '.'),        # Replace - with .
        account.replace('.', '-'),        # Replace . with -
    ]
    
    # If account has format like "ORG-ACCOUNT", try just the account part
    if '-' in account:
        parts = account.split('-')
        account_formats.extend([
            parts[1],                     # Just account part (e.g., UQB65919)
            parts[1].lower(),             # Account part lowercase
            parts[0].lower() + '-' + parts[1].lower(),  # Both lowercase
        ])
    
    # Try with common regions
    if '-' in account:
        account_part = account.split('-')[1] if '-' in account else account
        account_formats.extend([
            f"{account_part}.us-east-1",
            f"{account_part}.us-west-2",
            f"{account.lower()}.us-east-1",
        ])

# Remove duplicates while preserving order
seen = set()
unique_formats = []
for fmt in account_formats:
    if fmt and fmt not in seen:
        seen.add(fmt)
        unique_formats.append(fmt)

print(f"Testing {len(unique_formats)} different account formats...")
print()

for i, fmt in enumerate(unique_formats, 1):
    print(f"Test {i}/{len(unique_formats)}: {fmt}")
    print("-" * 70)
    
    try:
        # Try with standard connection
        conn = snowflake.connector.connect(
            account=fmt,
            user=user,
            password=password,
            warehouse=warehouse,
            database=database,
            schema=schema,
            login_timeout=10
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_ACCOUNT(), CURRENT_DATABASE(), CURRENT_SCHEMA(), CURRENT_WAREHOUSE()")
        result = cursor.fetchone()
        
        print("✓✓✓ SUCCESS! ✓✓✓")
        print()
        print("Connection Details:")
        print(f"  User:      {result[0]}")
        print(f"  Role:      {result[1]}")
        print(f"  Account:   {result[2]}")
        print(f"  Database:  {result[3]}")
        print(f"  Schema:    {result[4]}")
        print(f"  Warehouse: {result[5]}")
        print()
        print("=" * 70)
        print(f"✓ CORRECT ACCOUNT FORMAT: {fmt}")
        print("=" * 70)
        print()
        print(f"Update your .env file with:")
        print(f"SNOWFLAKE_ACCOUNT={fmt}")
        print()
        
        cursor.close()
        conn.close()
        sys.exit(0)
        
    except snowflake.connector.errors.OperationalError as e:
        error_code = str(e).split(':')[0] if ':' in str(e) else ''
        if '250001' in str(e) or 'Authentication' in str(e):
            print("✗ Authentication failed (wrong username/password or account)")
        elif '250003' in str(e) or 'SSL' in str(e):
            print("✗ SSL error (trying with SSL disabled...)")
            # Try with SSL disabled
            try:
                conn = snowflake.connector.connect(
                    account=fmt,
                    user=user,
                    password=password,
                    warehouse=warehouse,
                    database=database,
                    schema=schema,
                    insecure_mode=True,
                    login_timeout=10
                )
                cursor = conn.cursor()
                cursor.execute("SELECT CURRENT_USER(), CURRENT_ACCOUNT()")
                result = cursor.fetchone()
                print("✓✓✓ SUCCESS (with SSL disabled)! ✓✓✓")
                print(f"  User: {result[0]}, Account: {result[1]}")
                print()
                print("=" * 70)
                print(f"✓ CORRECT ACCOUNT FORMAT: {fmt}")
                print("⚠ WARNING: SSL verification disabled (not recommended for production)")
                print("=" * 70)
                cursor.close()
                conn.close()
                sys.exit(0)
            except Exception as e2:
                print(f"✗ Still failed: {str(e2)[:100]}")
        elif '290404' in str(e) or 'does not exist' in str(e):
            print("✗ Account not found")
        else:
            print(f"✗ Error: {str(e)[:150]}")
    except Exception as e:
        print(f"✗ Connection failed: {str(e)[:150]}")
    
    print()

print()
print("=" * 70)
print("ALL ACCOUNT FORMATS FAILED")
print("=" * 70)
print()
print("Please verify:")
print("1. Your Snowflake account URL is correct")
print("2. Your username and password are correct")
print("3. Your account is active and accessible")
print("4. Network/firewall allows connections to Snowflake")
print()
print("To find your account identifier:")
print("- Log into Snowflake web UI")
print("- Check the URL: https://app.snowflake.com/{org}/{account}/")
print("- The account format is usually: {org}-{account} (lowercase)")
print()

