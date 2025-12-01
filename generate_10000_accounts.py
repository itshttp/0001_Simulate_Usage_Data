#!/usr/bin/env python3
"""
Generate 10,000 accounts with 8% churn rate
"""

import sys
from datetime import datetime
import function

# Configure encoding for Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# ============================================================================
# CONFIGURATION
# ============================================================================

# Number of accounts
NUM_ACCOUNTS = 10000

# Churn rate (8%)
CHURN_RATE = 0.08

# Time period
MOST_RECENT_MONTH = datetime(2025, 10, 1)
NUM_MONTHS = 36  # 36 months = 3 years
USAGE_START_DATE = datetime(2023, 1, 1)

# Companies
COMPANIES = [
    'Acme Corporation',
    'TechStart Innovations',
    'Global Solutions Ltd',
    'Enterprise Dynamics',
    'Digital Ventures',
    'Cloud Systems Inc',
    'Data Analytics Corp',
    'Network Solutions',
    'Business Intelligence LLC',
    'Innovation Partners'
]

# Brands (id, name)
BRANDS = [
    (1, 'Premium Brand'),
    (2, 'Standard Brand'),
    (3, 'Economy Brand'),
    (4, 'Elite Brand')
]

# UBrands (id, description)
UBRANDS = [
    ('UA1', 'Unified Brand Alpha'),
    ('UA2', 'Unified Brand Beta'),
    ('UA3', 'Unified Brand Gamma')
]

# Packages (id, name, catalog_id, catalog_name)
PACKAGES = [
    (100, 'Starter Package', 'CAT-100', 'Catalog Starter'),
    (200, 'Business Package', 'CAT-200', 'Catalog Business'),
    (300, 'Professional Package', 'CAT-300', 'Catalog Professional'),
    (400, 'Enterprise Package', 'CAT-400', 'Catalog Enterprise'),
    (500, 'Ultimate Package', 'CAT-500', 'Catalog Ultimate')
]

# Tiers (id, name, edition)
TIERS = [
    (1, 'Bronze Tier', 'Standard Edition'),
    (2, 'Silver Tier', 'Professional Edition'),
    (3, 'Gold Tier', 'Premium Edition'),
    (4, 'Platinum Tier', 'Enterprise Edition')
]

# Operating Companies
OPCOS = [
    'OPCO-NORTH-AMERICA',
    'OPCO-EUROPE',
    'OPCO-ASIA-PACIFIC',
    'OPCO-LATIN-AMERICA',
    'OPCO-MIDDLE-EAST'
]

# ============================================================================
# SET CONFIGURATION IN FUNCTION MODULE
# ============================================================================

function.NUM_ENTERPRISE_ACCOUNTS = NUM_ACCOUNTS
function.MOST_RECENT_MONTH = MOST_RECENT_MONTH
function.COMPANIES = COMPANIES
function.BRANDS = BRANDS
function.UBRANDS = UBRANDS
function.PACKAGES = PACKAGES
function.TIERS = TIERS
function.OPCOS = OPCOS

# ============================================================================
# GENERATE DATA
# ============================================================================

print("=" * 70)
print("PHONE USAGE DATA GENERATOR - 10,000 ACCOUNTS")
print("=" * 70)
print(f"\nConfiguration:")
print(f"  Number of Accounts: {NUM_ACCOUNTS:,}")
print(f"  Churn Rate: {CHURN_RATE * 100:.1f}%")
print(f"  Usage Period: {NUM_MONTHS} months")
print(f"  Most Recent Month: {MOST_RECENT_MONTH.strftime('%Y-%m-%d')}")
print(f"  Usage Start Date: {USAGE_START_DATE.strftime('%Y-%m-%d')}")
print(f"  Companies: {len(COMPANIES)}")
print(f"  Brands: {len(BRANDS)}")
print(f"  Packages: {len(PACKAGES)}")
print(f"  Tiers: {len(TIERS)}")
print(f"  OPCOs: {len(OPCOS)}")
print()
print("Starting data generation...")
print("This may take several minutes for 10,000 accounts...")
print()

# Generate all tables
account_df, usage_df, churn_df = function.generate_all_tables(
    non_active_ratio=CHURN_RATE,
    num_months=NUM_MONTHS,
    usage_start_date=USAGE_START_DATE,
    save_to_csv=True
)

# ============================================================================
# SUMMARY STATISTICS
# ============================================================================

print()
print("=" * 70)
print("GENERATION COMPLETE!")
print("=" * 70)

total_accounts = account_df['SERVICE_ACCOUNT_ID'].nunique()
active_accounts = account_df[account_df['SA_ACCT_STATUS'] == 'Active']['SERVICE_ACCOUNT_ID'].nunique()
churned_accounts = len(churn_df)
actual_churn_rate = (churned_accounts / total_accounts * 100) if total_accounts > 0 else 0

print(f"\nOutput Files:")
print(f"  - account_attributes_monthly.csv ({len(account_df):,} records)")
print(f"  - phone_usage_data.csv ({len(usage_df):,} records)")
print(f"  - churn_records.csv ({len(churn_df):,} records)")

print(f"\nSummary Statistics:")
print(f"  Total Accounts: {total_accounts:,}")
print(f"  Active Accounts: {active_accounts:,}")
print(f"  Churned Accounts: {churned_accounts:,}")
print(f"  Actual Churn Rate: {actual_churn_rate:.2f}%")

print(f"\n  Usage Records: {len(usage_df):,}")
if usage_df['USERID'].nunique() > 0:
    avg_usage = len(usage_df) / usage_df['USERID'].nunique()
    print(f"  Avg Usage Records per Account: {avg_usage:.1f}")

# Package distribution
print(f"\nPackage Distribution:")
package_dist = account_df.groupby('PACKAGE_NAME')['SERVICE_ACCOUNT_ID'].nunique().sort_values(ascending=False)
for package, count in package_dist.items():
    pct = (count / total_accounts * 100) if total_accounts > 0 else 0
    print(f"  {package}: {count:,} accounts ({pct:.1f}%)")

print()
print("=" * 70)
print("Data generation completed successfully!")
print("=" * 70)

