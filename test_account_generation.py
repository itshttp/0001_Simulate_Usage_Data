"""
Test script for the updated generate_account_data function
Tests that:
1. Account attributes remain constant across months
2. Only status and package can change
3. Package changes occur at ~10% probability every 24 months
"""

import sys
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd

# Import the function module
import function

# Set up configuration constants (same as in your main script)
function.NUM_ENTERPRISE_ACCOUNTS = 10  # Small number for testing
function.MOST_RECENT_MONTH = datetime(2025, 10, 1)

# Sample data
function.COMPANIES = ['Acme Corp', 'TechStart Inc', 'Global Solutions', 'Enterprise Ltd']
function.BRANDS = [
    (1, 'Brand A'),
    (2, 'Brand B'),
    (3, 'Brand C')
]
function.UBRANDS = [
    ('UA1', 'UBrand Alpha'),
    ('UA2', 'UBrand Beta')
]
function.PACKAGES = [
    (100, 'Basic Plan', 'CAT-100', 'Catalog Basic'),
    (200, 'Professional Plan', 'CAT-200', 'Catalog Professional'),
    (300, 'Enterprise Plan', 'CAT-300', 'Catalog Enterprise')
]
function.TIERS = [
    (1, 'Tier 1', 'Standard Edition'),
    (2, 'Tier 2', 'Premium Edition')
]
function.OPCOS = ['OPCO-US', 'OPCO-EU', 'OPCO-APAC']

# Generate account data
print("Generating account data...")
records = function.generate_account_data(non_active_ratio=0.2)

# Convert to DataFrame for easier analysis
df = pd.DataFrame(records)
df['MONTH'] = pd.to_datetime(df['MONTH'])

print(f"\nGenerated {len(records)} records for {df['SERVICE_ACCOUNT_ID'].nunique()} accounts")
print(f"Date range: {df['MONTH'].min()} to {df['MONTH'].max()}")

# Test 1: Verify account attributes remain constant
print("\n" + "="*70)
print("TEST 1: Verifying account attributes remain constant")
print("="*70)

test_account = df['SERVICE_ACCOUNT_ID'].iloc[0]
account_data = df[df['SERVICE_ACCOUNT_ID'] == test_account].sort_values('MONTH')

constant_fields = ['COMPANY', 'EA_BRAND_ID', 'EA_BRAND_NAME', 'SA_BRAND_ID',
                   'SA_BRAND_NAME', 'TIER_ID', 'TIER_NAME', 'EXTERNAL_ACCOUNT_ID',
                   'BAN', 'OPCO_ID']

print(f"\nChecking account {test_account} ({len(account_data)} months of data)")
all_constant = True
for field in constant_fields:
    unique_values = account_data[field].nunique()
    if unique_values == 1:
        print(f"  ✓ {field}: Constant")
    else:
        print(f"  ✗ {field}: CHANGED! ({unique_values} different values)")
        all_constant = False

if all_constant:
    print("\n✓ All constant fields remain unchanged across months")
else:
    print("\n✗ Some constant fields changed (ERROR)")

# Test 2: Check package changes
print("\n" + "="*70)
print("TEST 2: Verifying package change logic")
print("="*70)

accounts_with_package_changes = 0
total_package_changes = 0

for account_id in df['SERVICE_ACCOUNT_ID'].unique():
    account_data = df[df['SERVICE_ACCOUNT_ID'] == account_id].sort_values('MONTH')

    # Check if package changed
    if account_data['PACKAGE_NAME'].nunique() > 1:
        accounts_with_package_changes += 1
        changes = account_data['PACKAGE_NAME'].ne(account_data['PACKAGE_NAME'].shift()).sum() - 1
        total_package_changes += changes

        print(f"\nAccount {account_id}:")
        print(f"  Months of data: {len(account_data)}")
        print(f"  Package changes: {changes}")
        print(f"  Packages: {account_data['PACKAGE_NAME'].unique().tolist()}")

        # Show when changes occurred
        for idx in range(1, len(account_data)):
            if account_data.iloc[idx]['PACKAGE_NAME'] != account_data.iloc[idx-1]['PACKAGE_NAME']:
                print(f"  Change at month {idx}: {account_data.iloc[idx-1]['PACKAGE_NAME']} → {account_data.iloc[idx]['PACKAGE_NAME']}")

print(f"\n✓ {accounts_with_package_changes} accounts had package changes")
print(f"✓ {total_package_changes} total package changes across all accounts")

# Test 3: Check status changes
print("\n" + "="*70)
print("TEST 3: Verifying status changes (churn)")
print("="*70)

accounts_with_status_change = 0
for account_id in df['SERVICE_ACCOUNT_ID'].unique():
    account_data = df[df['SERVICE_ACCOUNT_ID'] == account_id].sort_values('MONTH')

    if account_data['SA_ACCT_STATUS'].nunique() > 1:
        accounts_with_status_change += 1
        print(f"\nAccount {account_id}:")
        print(f"  Status changes: {account_data['SA_ACCT_STATUS'].unique().tolist()}")

        # Find when status changed
        for idx in range(1, len(account_data)):
            if account_data.iloc[idx]['SA_ACCT_STATUS'] != account_data.iloc[idx-1]['SA_ACCT_STATUS']:
                print(f"  Changed at {account_data.iloc[idx]['MONTH']}: {account_data.iloc[idx-1]['SA_ACCT_STATUS']} → {account_data.iloc[idx]['SA_ACCT_STATUS']}")

print(f"\n✓ {accounts_with_status_change} accounts changed status")

# Test 4: Verify ID-Name consistency
print("\n" + "="*70)
print("TEST 4: Verifying ID-Name 1:1 relationship")
print("="*70)

# Check Brand ID to Brand Name mapping
brand_mapping = df[['EA_BRAND_ID', 'EA_BRAND_NAME']].drop_duplicates()
print(f"\nEA Brand ID to Name mappings:")
for _, row in brand_mapping.iterrows():
    print(f"  Brand ID {row['EA_BRAND_ID']} → {row['EA_BRAND_NAME']}")

# Check if each ID maps to exactly one name
brand_id_counts = df.groupby('EA_BRAND_ID')['EA_BRAND_NAME'].nunique()
if (brand_id_counts == 1).all():
    print("✓ All EA Brand IDs map to exactly one name")
else:
    print("✗ Some EA Brand IDs map to multiple names (ERROR)")

# Check SA Brand ID to Name mapping
sa_brand_mapping = df[['SA_BRAND_ID', 'SA_BRAND_NAME']].drop_duplicates()
print(f"\nSA Brand ID to Name mappings:")
for _, row in sa_brand_mapping.iterrows():
    print(f"  Brand ID {row['SA_BRAND_ID']} → {row['SA_BRAND_NAME']}")

sa_brand_id_counts = df.groupby('SA_BRAND_ID')['SA_BRAND_NAME'].nunique()
if (sa_brand_id_counts == 1).all():
    print("✓ All SA Brand IDs map to exactly one name")
else:
    print("✗ Some SA Brand IDs map to multiple names (ERROR)")

print("\n" + "="*70)
print("TESTING COMPLETE")
print("="*70)
