#!/usr/bin/env python3
"""
Generate Large Dataset: 10,000 accounts with 8% churn rate
"""

from datetime import datetime
import function

print("=" * 70)
print("GENERATING LARGE DATASET")
print("=" * 70)
print(f"\nConfiguration:")
print(f"  Accounts: 10,000")
print(f"  Churn Rate: 8%")
print(f"  Time Period: 36 months (3 years)")
print()

# ============================================================================
# CONFIGURATION
# ============================================================================

# Number of accounts
function.NUM_ENTERPRISE_ACCOUNTS = 10000

# Time settings
function.MOST_RECENT_MONTH = datetime(2025, 10, 1)

# Companies
function.COMPANIES = [
    'Global Telecom Inc',
    'Enterprise Communications Ltd',
    'Business Phone Solutions',
    'Corporate Networks LLC',
    'Digital Voice Systems',
    'United Communications',
    'Metro Business Services',
    'Pacific Telecom Group'
]

# Brands (id, name)
function.BRANDS = [
    (1, 'Premium Voice'),
    (2, 'Business Plus'),
    (3, 'Standard Connect'),
    (4, 'Enterprise Link'),
    (5, 'Global Voice')
]

# UBrands (id, description)
function.UBRANDS = [
    ('UC1', 'Unified Communications Alpha'),
    ('UC2', 'Unified Communications Beta'),
    ('UC3', 'Unified Communications Gamma')
]

# Packages (id, name, catalog_id, catalog_name)
function.PACKAGES = [
    (100, 'Small Business', 'CAT-100', 'Small Business Catalog'),
    (200, 'Medium Business', 'CAT-200', 'Medium Business Catalog'),
    (300, 'Large Business', 'CAT-300', 'Large Business Catalog'),
    (400, 'Enterprise', 'CAT-400', 'Enterprise Catalog'),
    (500, 'Enterprise Plus', 'CAT-500', 'Enterprise Plus Catalog')
]

# Tiers (id, name, edition)
function.TIERS = [
    (1, 'Basic Tier', 'Standard Edition'),
    (2, 'Professional Tier', 'Professional Edition'),
    (3, 'Premium Tier', 'Premium Edition'),
    (4, 'Enterprise Tier', 'Enterprise Edition')
]

# Operating Companies
function.OPCOS = [
    'OPCO-NORTH-AMERICA',
    'OPCO-EUROPE',
    'OPCO-ASIA-PACIFIC',
    'OPCO-LATIN-AMERICA'
]

# ============================================================================
# GENERATE DATA
# ============================================================================

print("Starting data generation...")
print("This may take several minutes for 10,000 accounts...")
print()

# Generate all tables with 8% churn rate
account_df, usage_df, churn_df = function.generate_all_tables(
    non_active_ratio=0.08,  # 8% churn rate
    num_months=36,          # 3 years of data
    usage_start_date=datetime(2022, 10, 1),
    save_to_csv=True
)

# ============================================================================
# SUMMARY
# ============================================================================

print()
print("=" * 70)
print("GENERATION COMPLETE!")
print("=" * 70)
print(f"\nOutput Files:")
print(f"  ✓ account_attributes_monthly.csv ({len(account_df):,} records)")
print(f"  ✓ phone_usage_data.csv ({len(usage_df):,} records)")
print(f"  ✓ churn_records.csv ({len(churn_df):,} records)")
print()

# Calculate statistics
total_accounts = account_df['SERVICE_ACCOUNT_ID'].nunique()
active_accounts = account_df[account_df['SA_ACCT_STATUS'] == 'Active']['SERVICE_ACCOUNT_ID'].nunique()
churned_accounts = len(churn_df)
actual_churn_rate = (churned_accounts / total_accounts) * 100

print(f"Summary Statistics:")
print(f"  Total Accounts: {total_accounts:,}")
print(f"  Active Accounts: {active_accounts:,}")
print(f"  Churned Accounts: {churned_accounts:,}")
print(f"  Actual Churn Rate: {actual_churn_rate:.2f}%")
print()

print(f"  Usage Records: {len(usage_df):,}")
avg_usage = len(usage_df) / usage_df['USERID'].nunique()
print(f"  Avg Usage Records per Account: {avg_usage:.1f}")
print()

# Package statistics
package_dist = account_df.groupby('PACKAGE_NAME')['SERVICE_ACCOUNT_ID'].nunique()
print(f"Package Distribution:")
for package, count in package_dist.items():
    print(f"  {package}: {count:,} accounts ({count/total_accounts*100:.1f}%)")
print()

# Company statistics
company_dist = account_df.groupby('COMPANY')['SERVICE_ACCOUNT_ID'].nunique()
print(f"Company Distribution:")
for company, count in company_dist.items():
    print(f"  {company}: {count:,} accounts ({count/total_accounts*100:.1f}%)")
print()

print("Next Steps:")
print("  1. ✓ Data files generated")
print("  2. Clean Snowflake tables (run snowflake_cleanup.py)")
print("  3. Load data to Snowflake (run snowflake_loader.py)")
print("  4. Verify data consistency")
print()
