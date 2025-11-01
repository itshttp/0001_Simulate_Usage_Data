#!/usr/bin/env python3
"""
Phone Usage Data Generator - Quick Start Script

Customize the configuration section below and run:
    ./venv/bin/python generate_data.py

or:
    python3 generate_data.py
"""

from datetime import datetime
import function

# ============================================================================
# CONFIGURATION - CUSTOMIZE THESE VALUES
# ============================================================================

# Number of accounts to generate
NUM_ACCOUNTS = 100

# Churn rate (0.0 to 1.0)
# Examples: 0.05 = 5%, 0.10 = 10%, 0.20 = 20%
CHURN_RATE = 0.05

# Time period
MOST_RECENT_MONTH = datetime(2025, 10, 1)  # End date
NUM_MONTHS = 36  # Number of months of usage data (36 = 3 years)
USAGE_START_DATE = datetime(2023, 1, 1)  # Start date for usage data

# Companies - Add as many as you want
COMPANIES = [
    'Acme Corporation',
    'TechStart Innovations',
    'Global Solutions Ltd',
    'Enterprise Dynamics',
    'Digital Ventures'
]

# Brands (id, name) - Each account gets one brand
BRANDS = [
    (1, 'Premium Brand'),
    (2, 'Standard Brand'),
    (3, 'Economy Brand'),
    (4, 'Elite Brand')
]

# UBrands (id, description) - Unified brands
UBRANDS = [
    ('UA1', 'Unified Brand Alpha'),
    ('UA2', 'Unified Brand Beta'),
    ('UA3', 'Unified Brand Gamma')
]

# Packages (id, name, catalog_id, catalog_name)
# Note: 10% probability of package change every 24 months
PACKAGES = [
    (100, 'Starter Package', 'CAT-100', 'Catalog Starter'),
    (200, 'Business Package', 'CAT-200', 'Catalog Business'),
    (300, 'Professional Package', 'CAT-300', 'Catalog Professional'),
    (400, 'Enterprise Package', 'CAT-400', 'Catalog Enterprise'),
    (500, 'Ultimate Package', 'CAT-500', 'Catalog Ultimate')
]

# Tiers (id, name, edition) - Remains constant for each account
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
# DO NOT MODIFY BELOW THIS LINE (unless you know what you're doing)
# ============================================================================

def main():
    """Main function to generate data"""

    print("=" * 70)
    print("PHONE USAGE DATA GENERATOR")
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

    # Set configuration
    function.NUM_ENTERPRISE_ACCOUNTS = NUM_ACCOUNTS
    function.MOST_RECENT_MONTH = MOST_RECENT_MONTH
    function.COMPANIES = COMPANIES
    function.BRANDS = BRANDS
    function.UBRANDS = UBRANDS
    function.PACKAGES = PACKAGES
    function.TIERS = TIERS
    function.OPCOS = OPCOS

    print("Starting data generation...")
    print()

    # Generate all tables
    account_df, usage_df, churn_df = function.generate_all_tables(
        non_active_ratio=CHURN_RATE,
        num_months=NUM_MONTHS,
        usage_start_date=USAGE_START_DATE,
        save_to_csv=True
    )

    # Summary
    print()
    print("=" * 70)
    print("GENERATION COMPLETE!")
    print("=" * 70)
    print(f"\nOutput Files:")
    print(f"  ✓ account_attributes_monthly.csv ({len(account_df):,} records)")
    print(f"  ✓ phone_usage_data.csv ({len(usage_df):,} records)")
    print(f"  ✓ churn_records.csv ({len(churn_df):,} records)")
    print()
    print(f"Summary Statistics:")
    print(f"  Total Accounts: {account_df['SERVICE_ACCOUNT_ID'].nunique():,}")

    active_accounts = account_df[account_df['SA_ACCT_STATUS'] == 'Active']['SERVICE_ACCOUNT_ID'].nunique()
    print(f"  Active Accounts: {active_accounts:,}")
    print(f"  Churned Accounts: {len(churn_df):,}")

    actual_churn_rate = (len(churn_df) / account_df['SERVICE_ACCOUNT_ID'].nunique()) * 100
    print(f"  Actual Churn Rate: {actual_churn_rate:.2f}%")

    print(f"  Usage Records: {len(usage_df):,}")
    avg_usage = len(usage_df) / usage_df['USERID'].nunique()
    print(f"  Avg Usage Records per Account: {avg_usage:.1f}")
    print()

    # Package change statistics
    package_changes = 0
    for account_id in account_df['SERVICE_ACCOUNT_ID'].unique():
        account_data = account_df[account_df['SERVICE_ACCOUNT_ID'] == account_id]
        if account_data['PACKAGE_NAME'].nunique() > 1:
            package_changes += 1

    if package_changes > 0:
        print(f"Package Changes:")
        print(f"  Accounts with package changes: {package_changes}")
        print()

    print("Next Steps:")
    print("  1. Review the CSV files")
    print("  2. Load data into Snowflake (see snowflake_loader.py)")
    print("  3. View dashboard (see streamlit_app.py)")
    print()

if __name__ == "__main__":
    main()
