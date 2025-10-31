import random
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import csv
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Import phone usage generation functions and user_profiles
try:
    from generate_phone_usage_data import generate_user_usage, user_profiles
except ImportError:
    # Fallback if generate_phone_usage_data is not available
    generate_user_usage = None
    user_profiles = None



def generate_month_sequence(num_months):
    """Generate a sequence of months going backwards from the most recent month."""
    # Access module-level variables via globals()
    g = globals()
    MOST_RECENT_MONTH = g.get('MOST_RECENT_MONTH', datetime.now().replace(day=1))
    
    months = []
    for i in range(num_months):
        month = MOST_RECENT_MONTH - relativedelta(months=i)
        months.append(month)
    return sorted(months)  # Sort chronologically (oldest to newest)

def generate_account_data(non_active_ratio = 0.05):
    """Generate random account data for all enterprise accounts and months."""
    # Access module-level variables via globals()
    g = globals()
    NUM_ENTERPRISE_ACCOUNTS = g.get('NUM_ENTERPRISE_ACCOUNTS', 100)
    COMPANIES = g.get('COMPANIES', [])
    BRANDS = g.get('BRANDS', [])
    UBRANDS = g.get('UBRANDS', [])
    PACKAGES = g.get('PACKAGES', [])
    TIERS = g.get('TIERS', [])
    OPCOS = g.get('OPCOS', [])
    
    if not all([COMPANIES, BRANDS, UBRANDS, PACKAGES, TIERS, OPCOS]):
        raise ValueError("Configuration constants (COMPANIES, BRANDS, UBRANDS, PACKAGES, TIERS, OPCOS) must be set before calling this function")
    
    records = []
    
    for ea_id in range(1, NUM_ENTERPRISE_ACCOUNTS + 1):
        # Generate 5 to 20 months of data for this enterprise account
        num_months = random.randint(5, 20)
        months = generate_month_sequence(num_months)
        
        # Pick FIXED attributes for this enterprise account (same across all months)
        company = random.choice(COMPANIES)
        ea_brand_id, ea_brand_name = random.choice(BRANDS)
        ea_ubrand_id, ea_ubrand_description = random.choice(UBRANDS)
        ea_acct_status = 'Active'  # EA status is always Active
        
        # Service account attributes - FIXED for this customer
        service_account_id = random.randint(1000, 9999)
        sa_brand_id, sa_brand_name = random.choice(BRANDS)
        sa_ubrand_id, sa_ubrand_description = random.choice(UBRANDS)
        
        # Package and tier - FIXED for this customer
        package_id, package_name, catalog_package_id, catalog_package_name = random.choice(PACKAGES)
        tier_id, tier_name, edition_name = random.choice(TIERS)
        
        # Other FIXED attributes
        is_tester = random.choice([True, False])
        external_account_id = f'EXT-{ea_id:08d}'
        ban = f'BAN-{random.randint(100000, 999999)}'
        opco_id = random.choice(OPCOS)
        
        # Determine if this account will become non-active (5% chance)
        will_become_inactive = random.random() < non_active_ratio
        inactive_from_month = None
        
        if will_become_inactive:
            # Choose a random month (not the first one) when account becomes inactive
            inactive_from_index = random.randint(1, len(months) - 1)
            inactive_from_month = months[inactive_from_index]
        
        for month in months:
            # Check if we should stop generating records (account became inactive)
            if inactive_from_month and month >= inactive_from_month:
                break
            
            # SA_ACCT_STATUS is the only dynamic field
            # It's Active until the account becomes inactive
            sa_acct_status = 'Active'
            
            record = {
                'MONTH': month.strftime('%Y-%m-%d'),
                'ENTERPRISE_ACCOUNT_ID': ea_id,
                'COMPANY': company,
                'EA_BRAND_ID': ea_brand_id,
                'EA_BRAND_NAME': ea_brand_name,
                'EA_UBRAND_ID': ea_ubrand_id,
                'EA_UBRAND_DESCRIPTION': ea_ubrand_description,
                'EA_ACCT_STATUS': ea_acct_status,
                'SERVICE_ACCOUNT_ID': service_account_id,
                'SA_BRAND_ID': sa_brand_id,
                'SA_BRAND_NAME': sa_brand_name,
                'SA_UBRAND_ID': sa_ubrand_id,
                'SA_UBRAND_DESCRIPTION': sa_ubrand_description,
                'SA_ACCT_STATUS': sa_acct_status,
                'PACKAGE_ID': package_id,
                'PACKAGE_NAME': package_name,
                'CATALOG_PACKAGE_ID': catalog_package_id,
                'CATALOG_PACKAGE_NAME': catalog_package_name,
                'IS_TESTER': is_tester,
                'TIER_ID': tier_id,
                'TIER_NAME': tier_name,
                'EDITION_NAME': edition_name,
                'EXTERNAL_ACCOUNT_ID': external_account_id,
                'BAN': ban,
                'OPCO_ID': opco_id
            }
            records.append(record)
        
        # If account became inactive, add the final record with non-active status
        if will_become_inactive and inactive_from_month:
            non_active_status = random.choice(['Suspended', 'Closed'])
            
            record = {
                'MONTH': inactive_from_month.strftime('%Y-%m-%d'),
                'ENTERPRISE_ACCOUNT_ID': ea_id,
                'COMPANY': company,
                'EA_BRAND_ID': ea_brand_id,
                'EA_BRAND_NAME': ea_brand_name,
                'EA_UBRAND_ID': ea_ubrand_id,
                'EA_UBRAND_DESCRIPTION': ea_ubrand_description,
                'EA_ACCT_STATUS': ea_acct_status,
                'SERVICE_ACCOUNT_ID': service_account_id,
                'SA_BRAND_ID': sa_brand_id,
                'SA_BRAND_NAME': sa_brand_name,
                'SA_UBRAND_ID': sa_ubrand_id,
                'SA_UBRAND_DESCRIPTION': sa_ubrand_description,
                'SA_ACCT_STATUS': non_active_status,  # Non-active status
                'PACKAGE_ID': package_id,
                'PACKAGE_NAME': package_name,
                'CATALOG_PACKAGE_ID': catalog_package_id,
                'CATALOG_PACKAGE_NAME': catalog_package_name,
                'IS_TESTER': is_tester,
                'TIER_ID': tier_id,
                'TIER_NAME': tier_name,
                'EDITION_NAME': edition_name,
                'EXTERNAL_ACCOUNT_ID': external_account_id,
                'BAN': ban,
                'OPCO_ID': opco_id
            }
            records.append(record)
    
    return records

def save_to_csv(records, filename='account_attributes_monthly.csv'):
    """Save records to CSV file."""
    if not records:
        print("No records to save!")
        return
    
    fieldnames = records[0].keys()
    
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    
    print(f"Generated {len(records)} records saved to {filename}")

def generate_insert_statements(records, output_file='insert_statements.sql', batch_size=100):
    """Generate SQL INSERT statements for Snowflake."""
    with open(output_file, 'w') as f:
        for i in range(0, len(records), batch_size):
            batch = records[i:i+batch_size]
            
            f.write("INSERT INTO MY_DATABASE.PUBLIC.ACCOUNT_ATTRIBUTES_MONTHLY\n")
            f.write("(MONTH, ENTERPRISE_ACCOUNT_ID, COMPANY, EA_BRAND_ID, EA_BRAND_NAME, ")
            f.write("EA_UBRAND_ID, EA_UBRAND_DESCRIPTION, EA_ACCT_STATUS, SERVICE_ACCOUNT_ID, ")
            f.write("SA_BRAND_ID, SA_BRAND_NAME, SA_UBRAND_ID, SA_UBRAND_DESCRIPTION, SA_ACCT_STATUS, ")
            f.write("PACKAGE_ID, PACKAGE_NAME, CATALOG_PACKAGE_ID, CATALOG_PACKAGE_NAME, IS_TESTER, ")
            f.write("TIER_ID, TIER_NAME, EDITION_NAME, EXTERNAL_ACCOUNT_ID, BAN, OPCO_ID)\n")
            f.write("VALUES\n")
            
            values = []
            for record in batch:
                value_str = (
                    f"('{record['MONTH']}', {record['ENTERPRISE_ACCOUNT_ID']}, "
                    f"'{record['COMPANY']}', {record['EA_BRAND_ID']}, '{record['EA_BRAND_NAME']}', "
                    f"'{record['EA_UBRAND_ID']}', '{record['EA_UBRAND_DESCRIPTION']}', '{record['EA_ACCT_STATUS']}', "
                    f"{record['SERVICE_ACCOUNT_ID']}, {record['SA_BRAND_ID']}, '{record['SA_BRAND_NAME']}', "
                    f"'{record['SA_UBRAND_ID']}', '{record['SA_UBRAND_DESCRIPTION']}', '{record['SA_ACCT_STATUS']}', "
                    f"{record['PACKAGE_ID']}, '{record['PACKAGE_NAME']}', '{record['CATALOG_PACKAGE_ID']}', "
                    f"'{record['CATALOG_PACKAGE_NAME']}', {record['IS_TESTER']}, "
                    f"{record['TIER_ID']}, '{record['TIER_NAME']}', '{record['EDITION_NAME']}', "
                    f"'{record['EXTERNAL_ACCOUNT_ID']}', '{record['BAN']}', '{record['OPCO_ID']}')"
                )
                values.append(value_str)
            
            f.write(',\n'.join(values))
            f.write(';\n\n')
    
    print(f"SQL INSERT statements saved to {output_file}")

def generate_churn_records(account_records=None, csv_filename=None, output_filename='churn_records.csv'):
    """
    Generate churn records from account data.
    
    Args:
        account_records: List of account record dictionaries (optional if csv_filename is provided)
        csv_filename: Path to CSV file containing account records (optional if account_records is provided)
        output_filename: Output filename for churn records CSV
    
    Returns:
        List of churn record dictionaries with keys: USERID, CHURN_DATE, CHURNED
    """
    # Load data from CSV if provided, otherwise use account_records
    if csv_filename:
        df = pd.read_csv(csv_filename)
        # Convert MONTH to datetime if it's a string
        if df['MONTH'].dtype == 'object':
            df['MONTH'] = pd.to_datetime(df['MONTH'])
    elif account_records:
        df = pd.DataFrame(account_records)
        # Convert MONTH to datetime if it's a string
        if df['MONTH'].dtype == 'object':
            df['MONTH'] = pd.to_datetime(df['MONTH'])
    else:
        raise ValueError("Either account_records or csv_filename must be provided")
    
    # Sort by SERVICE_ACCOUNT_ID and MONTH to ensure chronological order
    df = df.sort_values(['SERVICE_ACCOUNT_ID', 'MONTH'])
    
    # Find accounts that churned (SA_ACCT_STATUS is 'Suspended' or 'Closed')
    churn_statuses = ['Suspended', 'Closed']
    churned_accounts = df[df['SA_ACCT_STATUS'].isin(churn_statuses)]
    
    # Group by SERVICE_ACCOUNT_ID and get the first churn date for each account
    churn_records_list = []
    
    for service_account_id in churned_accounts['SERVICE_ACCOUNT_ID'].unique():
        account_churn_records = churned_accounts[
            churned_accounts['SERVICE_ACCOUNT_ID'] == service_account_id
        ]
        
        # Get the earliest churn date for this account
        first_churn_date = account_churn_records['MONTH'].min()
        
        churn_record = {
            'USERID': int(service_account_id),  # Use SERVICE_ACCOUNT_ID as USERID
            'CHURN_DATE': first_churn_date.strftime('%Y-%m-%d') if isinstance(first_churn_date, pd.Timestamp) else str(first_churn_date),
            'CHURNED': 1
        }
        churn_records_list.append(churn_record)
    
    # Save to CSV if output filename is provided
    if output_filename:
        churn_df = pd.DataFrame(churn_records_list)
        churn_df.to_csv(output_filename, index=False)
        print(f"Generated {len(churn_records_list)} churn records saved to {output_filename}")
    
    return churn_records_list

################################################################################
# High-level functions for pandas DataFrame generation and analysis
################################################################################

def generate_account_table(non_active_ratio=0.05):
    """
    Generate account data and return as pandas DataFrame.
    
    Args:
        non_active_ratio: Ratio of accounts that become inactive (default 0.05)
    
    Returns:
        pandas DataFrame with account attributes monthly data
    """
    # Generate account records
    account_records = generate_account_data(non_active_ratio=non_active_ratio)
    
    # Convert to DataFrame
    account_df = pd.DataFrame(account_records)
    account_df['MONTH'] = pd.to_datetime(account_df['MONTH'])
    
    # Sort by SERVICE_ACCOUNT_ID and MONTH for consistency
    account_df = account_df.sort_values(['SERVICE_ACCOUNT_ID', 'MONTH']).reset_index(drop=True)
    
    print(f"Generated account table: {account_df.shape[0]} records, {account_df['SERVICE_ACCOUNT_ID'].nunique()} unique service accounts")
    
    return account_df



def generate_usage_table(account_df, num_months=36, usage_start_date=None):
    """
    Generate phone usage data based on account table and return as pandas DataFrame.
    
    Args:
        account_df: pandas DataFrame with account data
        num_months: Number of months of usage data to generate (default 36)
        usage_start_date: Start date for usage data (default: datetime(2023, 1, 1))
    
    Returns:
        pandas DataFrame with phone usage data
    """
    if generate_user_usage is None or user_profiles is None:
        raise ImportError("generate_user_usage and user_profiles must be imported from generate_phone_usage_data")
    
    if usage_start_date is None:
        usage_start_date = datetime(2023, 1, 1)
    
    # Generate churn records from account data
    account_records = account_df.to_dict('records')
    # Convert MONTH back to string format for churn_records function
    for record in account_records:
        if isinstance(record['MONTH'], pd.Timestamp):
            record['MONTH'] = record['MONTH'].strftime('%Y-%m-%d')
    
    churn_records = generate_churn_records(account_records=account_records, output_filename=None)
    
    # Get unique service account IDs (these will be our USERIDs)
    unique_service_accounts = account_df['SERVICE_ACCOUNT_ID'].unique()
    
    # Create churn mapping
    churn_dict = {}
    for record in churn_records:
        churn_dict[record['USERID']] = pd.to_datetime(record['CHURN_DATE'])
    
    # Generate usage data for all service accounts
    all_usage_data = []
    
    for service_account_id in unique_service_accounts:
        user_id = int(service_account_id)
        
        # Assign user profile randomly
        profile_type = random.choice(['heavy', 'medium', 'light'])
        base_values = user_profiles[profile_type]
        
        # Check if user churned and calculate churn month
        is_churned = user_id in churn_dict
        churn_month = None
        
        if is_churned:
            churn_date = churn_dict[user_id]
            months_diff = (churn_date.year - usage_start_date.year) * 12 + (churn_date.month - usage_start_date.month)
            if 0 <= months_diff < num_months:
                churn_month = months_diff
            else:
                is_churned = False  # Churn date outside our range
        
        # Generate usage data for this user
        user_data = generate_user_usage(user_id, num_months, base_values, is_churned, churn_month)
        all_usage_data.extend(user_data)
    
    # Convert to DataFrame
    usage_df = pd.DataFrame(all_usage_data)
    usage_df['MONTH'] = pd.to_datetime(usage_df['MONTH'])
    
    # Reorder columns to match schema
    column_order = [
        'USERID', 'MONTH', 'PHONE_TOTAL_CALLS', 'PHONE_TOTAL_MINUTES_OF_USE',
        'VOICE_CALLS', 'VOICE_MINS', 'FAX_CALLS', 'FAX_MINS',
        'PHONE_TOTAL_NUM_INBOUND_CALLS', 'PHONE_TOTAL_NUM_OUTBOUND_CALLS',
        'PHONE_TOTAL_INBOUND_MIN', 'PHONE_TOTAL_OUTBOUND_MIN',
        'OUT_VOICE_CALLS', 'IN_VOICE_CALLS', 'OUT_VOICE_MINS', 'IN_VOICE_MINS',
        'OUT_FAX_CALLS', 'IN_FAX_CALLS', 'OUT_FAX_MINS', 'IN_FAX_MINS',
        'PHONE_MAU', 'CALL_MAU', 'FAX_MAU', 'HARDPHONE_CALLS',
        'SOFTPHONE_CALLS', 'MOBILE_CALLS', 'MOBILE_ANDROID_CALLS'
    ]
    
    usage_df = usage_df[column_order]
    usage_df = usage_df.sort_values(['USERID', 'MONTH']).reset_index(drop=True)
    
    print(f"Generated usage table: {usage_df.shape[0]} records, {usage_df['USERID'].nunique()} unique users")
    
    return usage_df



def generate_all_tables(non_active_ratio=0.05, num_months=36, usage_start_date=None, save_to_csv=True):
    """
    Generate both Account and Usage tables as pandas DataFrames.
    
    Args:
        non_active_ratio: Ratio of accounts that become inactive (default 0.05)
        num_months: Number of months of usage data to generate (default 36)
        usage_start_date: Start date for usage data (default: datetime(2023, 1, 1))
        save_to_csv: Whether to save DataFrames to CSV files (default True)
    
    Returns:
        Tuple of (account_df, usage_df, churn_df) as pandas DataFrames
    """
    print("=" * 60)
    print("Generating Account and Usage Tables")
    print("=" * 60)
    
    # Step 1: Generate Account Table
    print("\nStep 1: Generating Account Table...")
    account_df = generate_account_table(non_active_ratio=non_active_ratio)
    
    # Step 2: Generate Churn Records
    print("\nStep 2: Generating Churn Records...")
    account_records = account_df.to_dict('records')
    # Convert MONTH to string for churn_records function
    for record in account_records:
        if isinstance(record['MONTH'], pd.Timestamp):
            record['MONTH'] = record['MONTH'].strftime('%Y-%m-%d')
    
    churn_records = generate_churn_records(
        account_records=account_records,
        output_filename='churn_records.csv' if save_to_csv else None
    )
    churn_df = pd.DataFrame(churn_records)
    if not churn_df.empty:
        churn_df['CHURN_DATE'] = pd.to_datetime(churn_df['CHURN_DATE'])
    print(f"✓ Generated {len(churn_df)} churn records")
    
    # Step 3: Generate Usage Table
    print("\nStep 3: Generating Usage Table...")
    usage_df = generate_usage_table(account_df, num_months=num_months, usage_start_date=usage_start_date)
    
    # Step 4: Save to CSV if requested
    if save_to_csv:
        print("\nStep 4: Saving Tables to CSV...")
        account_df.to_csv('account_attributes_monthly.csv', index=False)
        print("✓ Account table saved to 'account_attributes_monthly.csv'")
        usage_df.to_csv('phone_usage_data.csv', index=False)
        print("✓ Usage table saved to 'phone_usage_data.csv'")
    
    print("\n" + "=" * 60)
    print("Generation Complete!")
    print("=" * 60)
    print(f"\nSummary:")
    print(f"  Account Table: {account_df.shape[0]} records, {account_df.shape[1]} columns")
    print(f"  Usage Table: {usage_df.shape[0]} records, {usage_df.shape[1]} columns")
    print(f"  Churn Records: {len(churn_df)} records")
    
    return account_df, usage_df, churn_df



def plot_user_timeseries(user_id, usage_df=None, churn_df=None):
    """
    Plot time series trends for all usage features for a single user.
    
    Args:
        user_id: The USERID to plot
        usage_df: pandas DataFrame with usage data (required)
        churn_df: pandas DataFrame with churn records (optional, for churn date visualization)
    """
    if usage_df is None:
        raise ValueError("usage_df must be provided")
    
    # Filter data for the specific user
    user_data = usage_df[usage_df['USERID'] == user_id].copy()
    
    if user_data.empty:
        print(f"No data found for USERID: {user_id}")
        return
    
    # Sort by MONTH
    user_data = user_data.sort_values('MONTH')
    
    # Get all usage features (exclude USERID, MONTH, and IS_CHURNED if present)
    exclude_cols = ['USERID', 'MONTH', 'IS_CHURNED']
    usage_features = [col for col in user_data.columns if col not in exclude_cols]
    
    # Group features into logical categories for better visualization
    feature_groups = {
        'Total Metrics': ['PHONE_TOTAL_CALLS', 'PHONE_TOTAL_MINUTES_OF_USE'],
        'Voice/Fax Totals': ['VOICE_CALLS', 'VOICE_MINS', 'FAX_CALLS', 'FAX_MINS'],
        'Inbound/Outbound Totals': ['PHONE_TOTAL_NUM_INBOUND_CALLS', 'PHONE_TOTAL_NUM_OUTBOUND_CALLS', 
                                    'PHONE_TOTAL_INBOUND_MIN', 'PHONE_TOTAL_OUTBOUND_MIN'],
        'Voice Inbound/Outbound': ['OUT_VOICE_CALLS', 'IN_VOICE_CALLS', 'OUT_VOICE_MINS', 'IN_VOICE_MINS'],
        'FAX Inbound/Outbound': ['OUT_FAX_CALLS', 'IN_FAX_CALLS', 'OUT_FAX_MINS', 'IN_FAX_MINS'],
        'Monthly Active Users': ['PHONE_MAU', 'CALL_MAU', 'FAX_MAU'],
        'Device Types': ['HARDPHONE_CALLS', 'SOFTPHONE_CALLS', 'MOBILE_CALLS', 'MOBILE_ANDROID_CALLS']
    }
    
    # Check if user churned
    churned = False
    churn_date = None
    if churn_df is not None and not churn_df.empty:
        churn_info = churn_df[churn_df['USERID'] == user_id]
        if not churn_info.empty:
            churned = True
            churn_date = pd.to_datetime(churn_info.iloc[0]['CHURN_DATE'])
    
    # Create subplots for each group
    num_groups = len(feature_groups)
    fig, axes = plt.subplots(num_groups, 1, figsize=(15, 4 * num_groups))
    
    # Handle single subplot case
    if num_groups == 1:
        axes = [axes]
    
    colors = plt.cm.tab10(range(10))
    
    for idx, (group_name, features) in enumerate(feature_groups.items()):
        ax = axes[idx]
        
        # Plot each feature in the group
        for i, feature in enumerate(features):
            if feature in user_data.columns:
                ax.plot(user_data['MONTH'], user_data[feature], 
                       marker='o', linewidth=2, markersize=4, 
                       label=feature, color=colors[i % len(colors)], alpha=0.8)
        
        # Add vertical line for churn date if applicable
        if churned and churn_date and churn_date >= user_data['MONTH'].min() and churn_date <= user_data['MONTH'].max():
            ax.axvline(x=churn_date, color='red', linestyle='--', linewidth=2, 
                      label='Churn Date', alpha=0.7)
        
        ax.set_title(f'{group_name} - User ID: {user_id}', fontsize=12, fontweight='bold')
        ax.set_xlabel('Month')
        ax.set_ylabel('Value')
        ax.legend(loc='best', fontsize=8)
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.show()
    
    # Print summary statistics
    print(f"\n{'='*60}")
    print(f"Time Series Summary for USERID: {user_id}")
    print(f"{'='*60}")
    print(f"Date Range: {user_data['MONTH'].min().strftime('%Y-%m-%d')} to {user_data['MONTH'].max().strftime('%Y-%m-%d')}")
    print(f"Number of Months: {len(user_data)}")
    
    if churned:
        print(f"Status: CHURNED (Churn Date: {churn_date.strftime('%Y-%m-%d')})")
    else:
        print(f"Status: ACTIVE")
    
    print(f"\nAverage Usage Metrics:")
    numeric_cols = user_data.select_dtypes(include=[np.number]).columns
    avg_metrics = user_data[numeric_cols].mean().sort_values(ascending=False)
    print(avg_metrics.head(10).to_string())
    
    return user_data



def show_churned_account(account_index=0, account_df=None, usage_df=None, churn_df=None):
    """
    Display a churned account with account details and usage trends.
    
    Args:
        account_index: Index of churned account to show (default: 0 for first churned account)
        account_df: pandas DataFrame with account data (required)
        usage_df: pandas DataFrame with usage data (required)
        churn_df: pandas DataFrame with churn records (required)
    """
    # Check if data is available
    if churn_df is None or churn_df.empty:
        print("No churn data available. churn_df must be provided.")
        return
    
    if account_df is None:
        print("Account DataFrame not available. account_df must be provided.")
        return
    
    if usage_df is None:
        print("Usage DataFrame not available. usage_df must be provided.")
        return
    
    # Get the churned user ID
    if account_index >= len(churn_df):
        print(f"Account index {account_index} out of range. Only {len(churn_df)} churned accounts available.")
        return
    
    churned_user_id = churn_df.iloc[account_index]['USERID']
    churn_date = pd.to_datetime(churn_df.iloc[account_index]['CHURN_DATE'])
    
    print("="*70)
    print(f"CHURNED ACCOUNT DETAILS - USERID: {churned_user_id}")
    print("="*70)
    
    # Get account information
    # Convert SERVICE_ACCOUNT_ID to int for comparison
    account_info = account_df[account_df['SERVICE_ACCOUNT_ID'] == churned_user_id].copy()
    
    if not account_info.empty:
        # Get the most recent account record before churn
        account_info = account_info[account_info['MONTH'] <= churn_date]
        if not account_info.empty:
            latest_account = account_info.sort_values('MONTH').iloc[-1]
            
            print("\n📋 Account Information:")
            print(f"  Enterprise Account ID: {latest_account['ENTERPRISE_ACCOUNT_ID']}")
            print(f"  Service Account ID: {latest_account['SERVICE_ACCOUNT_ID']}")
            print(f"  Company: {latest_account['COMPANY']}")
            print(f"  Package: {latest_account['PACKAGE_NAME']} ({latest_account['CATALOG_PACKAGE_NAME']})")
            print(f"  Tier: {latest_account['TIER_NAME']} ({latest_account['EDITION_NAME']})")
            print(f"  Brand: {latest_account['EA_BRAND_NAME']}")
            print(f"  Account Status: {latest_account['SA_ACCT_STATUS']}")
            print(f"  External Account ID: {latest_account['EXTERNAL_ACCOUNT_ID']}")
            print(f"  BAN: {latest_account['BAN']}")
            print(f"  OPCO ID: {latest_account['OPCO_ID']}")
    
    print(f"\n\n📅 Churn Information:")
    print(f"  Churn Date: {churn_date.strftime('%Y-%m-%d')}")
    print(f"  Churn Status: {churn_df.iloc[account_index]['CHURNED']}")
    
    # Get usage data for this user
    user_usage = usage_df[usage_df['USERID'] == churned_user_id].copy()
    
    if not user_usage.empty:
        user_usage = user_usage.sort_values('MONTH')
        print(f"\n\n📊 Usage Statistics:")
        print(f"  Total Months of Data: {len(user_usage)}")
        print(f"  Date Range: {user_usage['MONTH'].min().strftime('%Y-%m-%d')} to {user_usage['MONTH'].max().strftime('%Y-%m-%d')}")
        print(f"\n  Average Metrics:")
        print(f"    Total Calls: {user_usage['PHONE_TOTAL_CALLS'].mean():.2f}")
        print(f"    Total Minutes: {user_usage['PHONE_TOTAL_MINUTES_OF_USE'].mean():.2f}")
        print(f"    Voice Calls: {user_usage['VOICE_CALLS'].mean():.2f}")
        print(f"    Voice Minutes: {user_usage['VOICE_MINS'].mean():.2f}")
    
    # Plot the time series
    print(f"\n\n📈 Generating Usage Time Series Plot...")
    plot_user_timeseries(churned_user_id, usage_df=user_usage, churn_df=churn_df)
    
    return {
        'user_id': churned_user_id,
        'churn_date': churn_date,
        'account_info': account_info if not account_info.empty else None,
        'usage_data': user_usage
    }



def find_non_active_accounts(account_df, show_details=True):
    """
    Find all non-active accounts (Suspended or Closed).
    
    Args:
        account_df: pandas DataFrame with account data (required)
        show_details: Whether to display detailed information (default True)
    
    Returns:
        pandas DataFrame with non-active accounts
    """
    if account_df is None:
        raise ValueError("account_df must be provided")
    
    # Find non-active accounts (Suspended or Closed)
    non_active_statuses = ['Suspended', 'Closed']
    non_active_accounts = account_df[account_df['SA_ACCT_STATUS'].isin(non_active_statuses)].copy()
    
    if non_active_accounts.empty:
        print("No non-active accounts found.")
        return pd.DataFrame()
    
    # Get unique service account IDs
    unique_non_active = non_active_accounts['SERVICE_ACCOUNT_ID'].unique()
    
    print("="*70)
    print(f"NON-ACTIVE ACCOUNTS SUMMARY")
    print("="*70)
    print(f"\nTotal Non-Active Accounts: {len(unique_non_active)}")
    
    # Count by status
    status_counts = non_active_accounts['SA_ACCT_STATUS'].value_counts()
    print(f"\nStatus Breakdown:")
    for status, count in status_counts.items():
        print(f"  {status}: {count} records")
    
    if show_details:
        print(f"\n" + "="*70)
        print("NON-ACTIVE ACCOUNT DETAILS")
        print("="*70)
        
        # Get the latest record for each non-active account
        account_details = []
        
        for service_account_id in unique_non_active:
            account_data = non_active_accounts[non_active_accounts['SERVICE_ACCOUNT_ID'] == service_account_id]
            # Get the most recent record (when account became non-active)
            latest_record = account_data.sort_values('MONTH').iloc[-1]
            
            # Get first record to see when account started
            first_record = account_data.sort_values('MONTH').iloc[0]
            
            account_details.append({
                'SERVICE_ACCOUNT_ID': service_account_id,
                'ENTERPRISE_ACCOUNT_ID': latest_record['ENTERPRISE_ACCOUNT_ID'],
                'COMPANY': latest_record['COMPANY'],
                'STATUS': latest_record['SA_ACCT_STATUS'],
                'NON_ACTIVE_DATE': latest_record['MONTH'],
                'ACCOUNT_START_DATE': first_record['MONTH'],
                'MONTHS_ACTIVE': len(account_data),
                'PACKAGE': latest_record['PACKAGE_NAME'],
                'TIER': latest_record['TIER_NAME'],
                'BRAND': latest_record['EA_BRAND_NAME'],
                'EXTERNAL_ACCOUNT_ID': latest_record['EXTERNAL_ACCOUNT_ID']
            })
        
        details_df = pd.DataFrame(account_details)
        details_df = details_df.sort_values('NON_ACTIVE_DATE')
        
        print(f"\n{len(details_df)} Non-Active Accounts:")
        print("-"*70)
        
        for idx, row in details_df.iterrows():
            print(f"\n{idx + 1}. SERVICE ACCOUNT ID: {row['SERVICE_ACCOUNT_ID']}")
            print(f"   Enterprise Account ID: {row['ENTERPRISE_ACCOUNT_ID']}")
            print(f"   Company: {row['COMPANY']}")
            print(f"   Status: {row['STATUS']}")
            print(f"   Account Start Date: {row['ACCOUNT_START_DATE'].strftime('%Y-%m-%d') if hasattr(row['ACCOUNT_START_DATE'], 'strftime') else row['ACCOUNT_START_DATE']}")
            print(f"   Non-Active Date: {row['NON_ACTIVE_DATE'].strftime('%Y-%m-%d') if hasattr(row['NON_ACTIVE_DATE'], 'strftime') else row['NON_ACTIVE_DATE']}")
            print(f"   Months Active: {row['MONTHS_ACTIVE']}")
            print(f"   Package: {row['PACKAGE']}")
            print(f"   Tier: {row['TIER']}")
            print(f"   Brand: {row['BRAND']}")
            print(f"   External Account ID: {row['EXTERNAL_ACCOUNT_ID']}")
        
        print(f"\n" + "="*70)
        print("Summary DataFrame:")
        print(details_df.to_string(index=False))
        
        return details_df
    else:
        return non_active_accounts



def get_non_active_account_details(service_account_id, account_df, usage_df=None):
    """
    Get detailed information for a specific non-active account.
    
    Args:
        service_account_id: The SERVICE_ACCOUNT_ID to look up
        account_df: pandas DataFrame with account data (required)
        usage_df: pandas DataFrame with usage data (optional, for usage statistics)
    """
    if account_df is None:
        raise ValueError("account_df must be provided")
    
    # Find account
    account_data = account_df[account_df['SERVICE_ACCOUNT_ID'] == service_account_id].copy()
    
    if account_data.empty:
        print(f"No account found with SERVICE_ACCOUNT_ID: {service_account_id}")
        return None
    
    account_data = account_data.sort_values('MONTH')
    
    # Check if it's non-active
    non_active_statuses = ['Suspended', 'Closed']
    is_non_active = account_data['SA_ACCT_STATUS'].isin(non_active_statuses).any()
    
    print("="*70)
    print(f"ACCOUNT DETAILS - SERVICE ACCOUNT ID: {service_account_id}")
    print("="*70)
    
    latest = account_data.iloc[-1]
    first = account_data.iloc[0]
    
    print(f"\nStatus: {latest['SA_ACCT_STATUS']}")
    if is_non_active:
        non_active_record = account_data[account_data['SA_ACCT_STATUS'].isin(non_active_statuses)].iloc[0]
        print(f"  (Non-Active since: {non_active_record['MONTH']})")
    
    print(f"\nAccount Information:")
    print(f"  Enterprise Account ID: {latest['ENTERPRISE_ACCOUNT_ID']}")
    print(f"  Company: {latest['COMPANY']}")
    print(f"  Package: {latest['PACKAGE_NAME']}")
    print(f"  Tier: {latest['TIER_NAME']}")
    print(f"  Brand: {latest['EA_BRAND_NAME']}")
    
    print(f"\nTimeline:")
    print(f"  Start Date: {first['MONTH']}")
    print(f"  End Date: {latest['MONTH']}")
    print(f"  Total Months: {len(account_data)}")
    
    # Show status timeline
    status_changes = account_data[['MONTH', 'SA_ACCT_STATUS']].drop_duplicates()
    if len(status_changes) > 1:
        print(f"\nStatus Timeline:")
        for _, row in status_changes.iterrows():
            print(f"  {row['MONTH']}: {row['SA_ACCT_STATUS']}")
    
    # Check if there's usage data
    if usage_df is not None:
        user_usage = usage_df[usage_df['USERID'] == service_account_id]
        if not user_usage.empty:
            print(f"\nUsage Data Available: {len(user_usage)} records")
            print(f"  Average Calls: {user_usage['PHONE_TOTAL_CALLS'].mean():.2f}")
            print(f"  Average Minutes: {user_usage['PHONE_TOTAL_MINUTES_OF_USE'].mean():.2f}")
    
    return account_data


def list_user_ids(usage_df, churn_df=None, limit=20):
    """
    List available USERIDs in the usage dataset.
    
    Args:
        usage_df: pandas DataFrame with usage data (required)
        churn_df: pandas DataFrame with churn records (optional, to show churn status)
        limit: Maximum number of USERIDs to display (default 20)
    """
    if usage_df is None:
        raise ValueError("usage_df must be provided")
    
    user_ids = sorted(usage_df['USERID'].unique())
    print(f"Available USERIDs: {len(user_ids)} total users")
    print(f"\nFirst {limit} USERIDs:")
    for i, uid in enumerate(user_ids[:limit], 1):
        churn_status = ""
        if churn_df is not None and not churn_df.empty and uid in churn_df['USERID'].values:
            churn_status = " (CHURNED)"
        print(f"  {i:3d}. USERID: {uid}{churn_status}")
    
    if len(user_ids) > limit:
        print(f"  ... and {len(user_ids) - limit} more users")

