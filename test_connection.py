"""
Test Snowflake connection with different account formats
"""

import os
import snowflake.connector
from dotenv import load_dotenv

load_dotenv()

user = os.getenv('SNOWFLAKE_USER')
password = os.getenv('SNOWFLAKE_PASSWORD')
role = os.getenv('SNOWFLAKE_ROLE', 'ACCOUNTADMIN')

# Try different account identifier formats
account_formats = [
    'idqiiap-uqb65919',  # orgname-accountname format
    'uqb65919',          # just account name
    'UQB65919',          # uppercase account name
    'idqiiap.uqb65919',  # orgname.accountname format
    'uqb65919.us-east-1', # account.region format (common regions)
    'uqb65919.us-west-2',
    'uqb65919.us-central1.gcp',  # GCP format
    'uqb65919.east-us-2.azure',  # Azure format
]

print("\n" + "=" * 80)
print("TESTING SNOWFLAKE CONNECTION WITH DIFFERENT ACCOUNT FORMATS")
print("=" * 80)
print(f"\nUsername: {user}")
print(f"Role: {role}")
print()

for account in account_formats:
    print("-" * 80)
    print(f"Trying account format: {account}")
    print("-" * 80)

    try:
        conn = snowflake.connector.connect(
            account=account,
            user=user,
            password=password,
            role=role,
            login_timeout=10
        )

        cursor = conn.cursor()
        cursor.execute("SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_ACCOUNT()")
        result = cursor.fetchone()

        print(f"✓✓✓ SUCCESS! ✓✓✓")
        print(f"✓ Connected successfully!")
        print(f"✓ User: {result[0]}")
        print(f"✓ Role: {result[1]}")
        print(f"✓ Account: {result[2]}")
        print(f"\n>>> CORRECT ACCOUNT FORMAT: {account} <<<\n")

        cursor.close()
        conn.close()

        print("=" * 80)
        print(f"USE THIS IN YOUR .ENV FILE: SNOWFLAKE_ACCOUNT={account}")
        print("=" * 80)
        exit(0)

    except snowflake.connector.errors.DatabaseError as e:
        error_code = e.errno
        if error_code == 250001:
            print(f"✗ Authentication failed (wrong username/password)")
        elif error_code == 290404:
            print(f"✗ Account not found (wrong account identifier)")
        else:
            print(f"✗ Error {error_code}: {e}")
    except Exception as e:
        print(f"✗ Connection failed: {e}")

    print()

print("\n" + "=" * 80)
print("ALL FORMATS FAILED")
print("=" * 80)
print("\nPlease verify:")
print("1. Your Snowflake account URL is correct")
print("2. Your username and password are correct")
print("3. Your account is active and accessible")
print()
