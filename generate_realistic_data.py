"""
Realistic Phone Usage Data Generator

Generates 20,000 accounts with realistic usage patterns from 2021-01 to 2025-12
Includes realistic churn patterns:
- Small accounts: 20% annual churn rate
- Medium/Large accounts: 10% annual churn rate
- New accounts: 30% churn within first 6 months

Features:
- 60 months of data per account (2021-01 to 2025-12)
- Realistic usage trends (growth, stability, decline)
- Seasonal patterns
- Pre-churn usage decline
- Account size variation
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import random

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

# Configuration
NUM_ACCOUNTS = 20000
START_DATE = datetime(2021, 1, 1)
END_DATE = datetime(2025, 12, 31)
MONTHS = 60  # 5 years

# Account size categories
SIZE_CATEGORIES = {
    'small': {'weight': 0.60, 'users': (1, 10), 'churn_rate': 0.20},      # 60% of accounts
    'medium': {'weight': 0.30, 'users': (11, 50), 'churn_rate': 0.10},    # 30% of accounts
    'large': {'weight': 0.10, 'users': (51, 200), 'churn_rate': 0.10}     # 10% of accounts
}

# Company names pool
COMPANY_PREFIXES = ['Global', 'Digital', 'Tech', 'Innovative', 'Smart', 'Cloud', 'Enterprise',
                    'Corporate', 'Advanced', 'Professional', 'Premier', 'Elite', 'Summit',
                    'Prime', 'Apex', 'Core', 'Alpha', 'Beta', 'Omega', 'Nexus']
COMPANY_SUFFIXES = ['Solutions', 'Systems', 'Technologies', 'Corp', 'Inc', 'Group', 'Networks',
                    'Communications', 'Telecom', 'Services', 'Enterprises', 'Industries',
                    'Partners', 'Ventures', 'Labs', 'Dynamics', 'Works', 'Hub']

# Brand names
BRANDS = ['RingCentral MVP', 'RingCentral Office', 'RingCentral Essentials',
          'AT&T Office@Hand', 'Avaya Cloud Office', 'BT Cloud Work',
          'Rainbow Office', 'Telus Business Connect', 'Unify Office']

# Package tiers
PACKAGES = {
    'Essentials': {'tier': 'Basic', 'edition': 'Standard'},
    'Standard': {'tier': 'Professional', 'edition': 'Professional'},
    'Premium': {'tier': 'Advanced', 'edition': 'Premium'},
    'Ultimate': {'tier': 'Enterprise', 'edition': 'Ultimate'}
}


def generate_company_name():
    """Generate a random company name."""
    return f"{random.choice(COMPANY_PREFIXES)} {random.choice(COMPANY_SUFFIXES)}"


def determine_account_size():
    """Randomly determine account size based on weights."""
    rand = random.random()
    cumulative = 0
    for size, config in SIZE_CATEGORIES.items():
        cumulative += config['weight']
        if rand <= cumulative:
            return size, config
    return 'small', SIZE_CATEGORIES['small']


def generate_onboarding_month():
    """Generate a random onboarding month between 2021-01 and 2025-06."""
    # Leave room for at least 6 months of data
    max_month = 54  # Leave 6 months before end
    month_offset = random.randint(0, max_month)
    return START_DATE + relativedelta(months=month_offset)


def calculate_churn_month(onboard_month, size_config, is_new_account_high_risk):
    """
    Calculate if and when an account churns.

    Returns:
        tuple: (churned: bool, churn_month: datetime or None)
    """
    # Calculate months since onboarding
    months_active = ((END_DATE.year - onboard_month.year) * 12 +
                    (END_DATE.month - onboard_month.month))

    # New account high risk (30% churn in first 6 months)
    if is_new_account_high_risk and months_active >= 6:
        if random.random() < 0.30:
            # Churn within first 6 months
            churn_offset = random.randint(1, min(6, months_active))
            return True, onboard_month + relativedelta(months=churn_offset)

    # Regular churn based on size
    annual_churn_rate = size_config['churn_rate']
    monthly_churn_rate = 1 - (1 - annual_churn_rate) ** (1/12)

    # Simulate each month
    current_month = onboard_month
    while current_month <= END_DATE:
        if random.random() < monthly_churn_rate:
            return True, current_month
        current_month += relativedelta(months=1)

    return False, None


def generate_usage_pattern(num_users, months_data, churn_month=None, onboard_month=None):
    """
    Generate realistic usage patterns with trends.

    Args:
        num_users: Number of users in account
        months_data: Number of months of data
        churn_month: Month when account churns (if applicable)
        onboard_month: Month when account onboarded

    Returns:
        dict: Dictionary with usage metrics for each month
    """
    # Base usage per user
    base_calls_per_user = random.randint(50, 150)
    base_minutes_per_user = random.randint(100, 400)

    usage_data = []

    # Determine overall trend
    trend_type = random.choice(['growth', 'stable', 'decline'])

    for month_idx in range(months_data):
        current_month = onboard_month + relativedelta(months=month_idx)

        # Calculate months until churn (if churning)
        if churn_month:
            months_to_churn = (churn_month.year - current_month.year) * 12 + (churn_month.month - current_month.month)
        else:
            months_to_churn = None

        # Seasonal factor (higher usage in Q4, lower in summer)
        month_num = current_month.month
        if month_num in [11, 12, 1, 2]:  # Winter/Holiday
            seasonal_factor = 1.15
        elif month_num in [6, 7, 8]:  # Summer
            seasonal_factor = 0.90
        else:
            seasonal_factor = 1.0

        # Trend factor
        if trend_type == 'growth':
            trend_factor = 1 + (month_idx * 0.02)  # 2% growth per month
        elif trend_type == 'decline':
            trend_factor = 1 - (month_idx * 0.01)  # 1% decline per month
        else:  # stable
            trend_factor = 1 + random.uniform(-0.05, 0.05)  # Small random variation

        # Pre-churn decline
        if months_to_churn is not None and months_to_churn <= 3:
            # Sharp decline in last 3 months before churn
            decline_factor = 0.5 - (3 - months_to_churn) * 0.15
        elif months_to_churn is not None and months_to_churn <= 6:
            # Gradual decline 6-3 months before churn
            decline_factor = 0.85 - (6 - months_to_churn) * 0.05
        else:
            decline_factor = 1.0

        # Calculate final usage
        total_factor = seasonal_factor * trend_factor * decline_factor
        total_calls = max(0, int(num_users * base_calls_per_user * total_factor * random.uniform(0.8, 1.2)))
        total_minutes = max(0, int(num_users * base_minutes_per_user * total_factor * random.uniform(0.8, 1.2)))

        # Voice calls (80-95% of total)
        voice_ratio = random.uniform(0.80, 0.95)
        voice_calls = int(total_calls * voice_ratio)
        voice_mins = total_minutes * voice_ratio

        # Fax calls (remaining)
        fax_calls = total_calls - voice_calls
        fax_mins = total_minutes - voice_mins

        # Inbound/Outbound split
        inbound_ratio = random.uniform(0.45, 0.55)
        inbound_calls = int(total_calls * inbound_ratio)
        outbound_calls = total_calls - inbound_calls
        inbound_mins = total_minutes * inbound_ratio
        outbound_mins = total_minutes - inbound_mins

        # MAU (Monthly Active Users)
        mau = min(num_users, max(1, int(num_users * total_factor * random.uniform(0.7, 1.0))))
        call_mau = mau
        fax_mau = max(1, int(mau * 0.3))  # 30% use fax

        # Device types
        hardphone_calls = int(total_calls * random.uniform(0.3, 0.5))
        softphone_calls = int(total_calls * random.uniform(0.3, 0.5))
        mobile_calls = total_calls - hardphone_calls - softphone_calls
        mobile_android = int(mobile_calls * 0.6)

        usage_data.append({
            'PHONE_TOTAL_CALLS': total_calls,
            'PHONE_TOTAL_MINUTES_OF_USE': round(total_minutes, 2),
            'VOICE_CALLS': voice_calls,
            'VOICE_MINS': round(voice_mins, 2),
            'FAX_CALLS': fax_calls,
            'FAX_MINS': round(fax_mins, 2),
            'PHONE_TOTAL_NUM_INBOUND_CALLS': inbound_calls,
            'PHONE_TOTAL_NUM_OUTBOUND_CALLS': outbound_calls,
            'PHONE_TOTAL_INBOUND_MIN': round(inbound_mins, 2),
            'PHONE_TOTAL_OUTBOUND_MIN': round(outbound_mins, 2),
            'OUT_VOICE_CALLS': int(voice_calls * (1 - inbound_ratio)),
            'IN_VOICE_CALLS': int(voice_calls * inbound_ratio),
            'OUT_VOICE_MINS': round(voice_mins * (1 - inbound_ratio), 2),
            'IN_VOICE_MINS': round(voice_mins * inbound_ratio, 2),
            'OUT_FAX_CALLS': int(fax_calls * (1 - inbound_ratio)),
            'IN_FAX_CALLS': int(fax_calls * inbound_ratio),
            'OUT_FAX_MINS': round(fax_mins * (1 - inbound_ratio), 2),
            'IN_FAX_MINS': round(fax_mins * inbound_ratio, 2),
            'PHONE_MAU': mau,
            'CALL_MAU': call_mau,
            'FAX_MAU': fax_mau,
            'HARDPHONE_CALLS': hardphone_calls,
            'SOFTPHONE_CALLS': softphone_calls,
            'MOBILE_CALLS': mobile_calls,
            'MOBILE_ANDROID_CALLS': mobile_android
        })

    return usage_data


def generate_accounts():
    """Generate account data for all accounts."""
    print(f"Generating {NUM_ACCOUNTS} accounts...")

    accounts = []

    for account_id in range(1000, 1000 + NUM_ACCOUNTS):
        if account_id % 1000 == 0:
            print(f"  Generated {account_id - 1000}/{NUM_ACCOUNTS} accounts...")

        # Determine account characteristics
        size_category, size_config = determine_account_size()
        num_users = random.randint(*size_config['users'])
        company_name = generate_company_name()
        brand_name = random.choice(BRANDS)
        package_name = random.choice(list(PACKAGES.keys()))
        tier_info = PACKAGES[package_name]

        # Generate onboarding month
        onboard_month = generate_onboarding_month()

        # Determine if new account high risk (onboarded in last 6 months from end)
        months_since_onboard = ((END_DATE.year - onboard_month.year) * 12 +
                               (END_DATE.month - onboard_month.month))
        is_new_high_risk = months_since_onboard <= 6

        # Calculate churn
        churned, churn_month = calculate_churn_month(onboard_month, size_config, is_new_high_risk)

        accounts.append({
            'account_id': account_id,
            'company': company_name,
            'brand': brand_name,
            'package': package_name,
            'tier': tier_info['tier'],
            'edition': tier_info['edition'],
            'size_category': size_category,
            'num_users': num_users,
            'onboard_month': onboard_month,
            'churned': churned,
            'churn_month': churn_month
        })

    print(f"✓ Generated {NUM_ACCOUNTS} accounts")
    return accounts


def generate_usage_data(accounts):
    """Generate usage data for all accounts."""
    print(f"\nGenerating usage data for {NUM_ACCOUNTS} accounts across {MONTHS} months...")

    usage_records = []

    for idx, account in enumerate(accounts):
        if (idx + 1) % 1000 == 0:
            print(f"  Processed {idx + 1}/{NUM_ACCOUNTS} accounts...")

        account_id = account['account_id']
        onboard_month = account['onboard_month']
        churn_month = account['churn_month']

        # Calculate how many months of data this account has
        if churn_month:
            months_of_data = ((churn_month.year - onboard_month.year) * 12 +
                            (churn_month.month - onboard_month.month))
        else:
            months_of_data = ((END_DATE.year - onboard_month.year) * 12 +
                            (END_DATE.month - onboard_month.month) + 1)

        # Generate usage pattern
        usage_pattern = generate_usage_pattern(
            account['num_users'],
            months_of_data,
            churn_month,
            onboard_month
        )

        # Create records for each month
        for month_idx, usage in enumerate(usage_pattern):
            current_month = onboard_month + relativedelta(months=month_idx)

            usage_records.append({
                'USERID': account_id,
                'MONTH': current_month.strftime('%Y-%m-01'),
                **usage
            })

    print(f"✓ Generated {len(usage_records):,} usage records")
    return usage_records


def generate_account_attributes(accounts):
    """Generate account attributes monthly data."""
    print(f"\nGenerating account attributes...")

    attributes_records = []

    for idx, account in enumerate(accounts):
        if (idx + 1) % 1000 == 0:
            print(f"  Processed {idx + 1}/{NUM_ACCOUNTS} accounts...")

        account_id = account['account_id']
        onboard_month = account['onboard_month']
        churn_month = account['churn_month']

        # Determine end month for this account
        if churn_month:
            end_month = churn_month
        else:
            end_month = END_DATE

        # Generate monthly records
        current_month = onboard_month
        while current_month <= end_month:
            # Determine status
            if churn_month and current_month >= churn_month:
                status = 'Churned'
            else:
                status = 'Active'

            attributes_records.append({
                'MONTH': current_month.strftime('%Y-%m-01'),
                'ENTERPRISE_ACCOUNT_ID': account_id,
                'COMPANY': account['company'],
                'EA_BRAND_ID': hash(account['brand']) % 1000,
                'EA_BRAND_NAME': account['brand'],
                'EA_UBRAND_ID': f"UB{hash(account['brand']) % 100}",
                'EA_UBRAND_DESCRIPTION': account['brand'],
                'EA_ACCT_STATUS': status,
                'SERVICE_ACCOUNT_ID': account_id,
                'SA_BRAND_ID': hash(account['brand']) % 1000,
                'SA_BRAND_NAME': account['brand'],
                'SA_UBRAND_ID': f"UB{hash(account['brand']) % 100}",
                'SA_UBRAND_DESCRIPTION': account['brand'],
                'SA_ACCT_STATUS': status,
                'PACKAGE_ID': hash(account['package']) % 100,
                'PACKAGE_NAME': account['package'],
                'CATALOG_PACKAGE_ID': f"CP{hash(account['package']) % 1000}",
                'CATALOG_PACKAGE_NAME': account['package'],
                'IS_TESTER': False,
                'TIER_ID': hash(account['tier']) % 10,
                'TIER_NAME': account['tier'],
                'EDITION_NAME': account['edition'],
                'EXTERNAL_ACCOUNT_ID': f"EA{account_id}",
                'BAN': f"BAN{account_id}",
                'OPCO_ID': f"OP{random.randint(1, 5)}"
            })

            current_month += relativedelta(months=1)

    print(f"✓ Generated {len(attributes_records):,} attribute records")
    return attributes_records


def generate_churn_records(accounts):
    """Generate churn records."""
    print(f"\nGenerating churn records...")

    churn_records = []
    churned_count = 0

    for account in accounts:
        if account['churned']:
            churned_count += 1
            churn_records.append({
                'USERID': account['account_id'],
                'CHURN_DATE': account['churn_month'].strftime('%Y-%m-01'),
                'CHURNED': 1
            })
        else:
            churn_records.append({
                'USERID': account['account_id'],
                'CHURN_DATE': None,
                'CHURNED': 0
            })

    print(f"✓ Generated {len(churn_records):,} churn records ({churned_count:,} churned accounts)")
    return churn_records


def main():
    """Main data generation function."""
    print("=" * 80)
    print("REALISTIC PHONE USAGE DATA GENERATOR")
    print("=" * 80)
    print(f"\nConfiguration:")
    print(f"  Accounts: {NUM_ACCOUNTS:,}")
    print(f"  Time Period: {START_DATE.strftime('%Y-%m')} to {END_DATE.strftime('%Y-%m')}")
    print(f"  Months: {MONTHS}")
    print(f"  Churn Rates:")
    print(f"    - Small accounts: 20% annual")
    print(f"    - Medium/Large accounts: 10% annual")
    print(f"    - New accounts (<6 months): 30%")
    print()

    # Generate data
    accounts = generate_accounts()
    usage_data = generate_usage_data(accounts)
    account_attributes = generate_account_attributes(accounts)
    churn_records = generate_churn_records(accounts)

    # Convert to DataFrames
    print("\nCreating DataFrames...")
    usage_df = pd.DataFrame(usage_data)
    attributes_df = pd.DataFrame(account_attributes)
    churn_df = pd.DataFrame(churn_records)

    # Save to CSV
    print("\nSaving to CSV files...")
    usage_df.to_csv('phone_usage_data.csv', index=False)
    print(f"✓ Saved phone_usage_data.csv ({len(usage_df):,} rows)")

    attributes_df.to_csv('account_attributes_monthly.csv', index=False)
    print(f"✓ Saved account_attributes_monthly.csv ({len(attributes_df):,} rows)")

    churn_df.to_csv('churn_records.csv', index=False)
    print(f"✓ Saved churn_records.csv ({len(churn_df):,} rows)")

    # Statistics
    print("\n" + "=" * 80)
    print("GENERATION COMPLETE")
    print("=" * 80)
    print(f"\nStatistics:")
    print(f"  Total Accounts: {NUM_ACCOUNTS:,}")
    print(f"  Churned Accounts: {churn_df['CHURNED'].sum():,} ({churn_df['CHURNED'].mean()*100:.1f}%)")
    print(f"  Active Accounts: {NUM_ACCOUNTS - churn_df['CHURNED'].sum():,}")
    print(f"  Total Usage Records: {len(usage_df):,}")
    print(f"  Total Attribute Records: {len(attributes_df):,}")
    print(f"  Average Months per Account: {len(usage_df) / NUM_ACCOUNTS:.1f}")
    print()


if __name__ == "__main__":
    main()
