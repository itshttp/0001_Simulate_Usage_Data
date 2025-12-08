import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

# Define package tiers and base monthly prices (as of 2023)
PACKAGE_TIERS = {
    'Basic': {'base_price': 29.99, 'weight': 0.25},
    'Standard': {'base_price': 59.99, 'weight': 0.35},
    'Premium': {'base_price': 99.99, 'weight': 0.25},
    'Enterprise': {'base_price': 199.99, 'weight': 0.15}
}

# Annual price increase rate
ANNUAL_PRICE_INCREASE = 0.10  # 10% per year

def generate_seasonality(month_index, amplitude=0.15):
    """Generate seasonal variation (higher in winter/summer, lower in spring/fall)"""
    # Peaks around December (month 12) and July (month 7)
    seasonal_factor = amplitude * np.sin(2 * np.pi * month_index / 12 + np.pi/2)
    return seasonal_factor

def generate_growth_phase(months, growth_months=6):
    """Generate initial growth phase that gradually increases"""
    growth_pattern = []
    for i in range(months):
        if i < growth_months:
            # Sigmoid growth curve
            growth_factor = 1 / (1 + np.exp(-1.5 * (i - growth_months/2)))
        else:
            growth_factor = 1.0
        growth_pattern.append(growth_factor)
    return np.array(growth_pattern)

def generate_trend(months, start_month=6):
    """Generate long-term trend after growth phase"""
    trend = []
    for i in range(months):
        if i < start_month:
            trend.append(0)
        else:
            # 20% gradual increase, 10% gradual decrease pattern
            cycle_length = 24  # 24 month cycle
            position = (i - start_month) % cycle_length
            if position < cycle_length * 0.6:  # 60% of time increasing
                trend_factor = 0.20 * (position / (cycle_length * 0.6))
            else:  # 40% of time decreasing
                peak_value = 0.20
                decrease_position = position - (cycle_length * 0.6)
                trend_factor = peak_value - (0.10 * (decrease_position / (cycle_length * 0.4)))
            trend.append(trend_factor)
    return np.array(trend)

def generate_churn_decline(months, churn_month, decline_months=6):
    """Generate decline pattern before churn"""
    decline_pattern = np.ones(months)
    if churn_month > decline_months:
        decline_start = churn_month - decline_months
        for i in range(decline_start, churn_month):
            # Exponential decline
            months_before_churn = churn_month - i
            decline_factor = 0.3 + 0.7 * (months_before_churn / decline_months)
            decline_pattern[i] = decline_factor
        # After churn, usage goes to near zero or zero
        decline_pattern[churn_month:] = np.random.uniform(0, 0.05, months - churn_month)
    return decline_pattern

def calculate_mrr(package_tier, signup_date, current_date, account_size='medium', is_churned=False, churn_date=None):
    """
    Calculate Monthly Recurring Revenue based on:
    - Package tier base price
    - Years since signup (10% increase per year)
    - Account size (larger accounts get 5-15% discount)
    - Randomness for variation
    - Churn status
    """
    # If churned and past churn date, MRR is 0
    if is_churned and churn_date and current_date >= churn_date:
        return 0.0

    # Get base price for package tier
    base_price = PACKAGE_TIERS[package_tier]['base_price']

    # Calculate years since signup
    years_since_signup = (current_date - signup_date).days / 365.25

    # Apply annual price increase
    price_with_inflation = base_price * ((1 + ANNUAL_PRICE_INCREASE) ** years_since_signup)

    # Apply account size discount (larger accounts get discounts)
    if account_size == 'heavy':
        discount = np.random.uniform(0.10, 0.15)  # 10-15% discount
    elif account_size == 'medium':
        discount = np.random.uniform(0.05, 0.10)  # 5-10% discount
    else:  # light
        discount = 0.0  # No discount for small accounts

    price_after_discount = price_with_inflation * (1 - discount)

    # Add some randomness (±5%)
    randomness = np.random.uniform(0.95, 1.05)
    final_price = price_after_discount * randomness

    return round(final_price, 2)

def generate_user_usage(user_id, num_months, base_values, package_tier, signup_date, account_size, is_churned=False, churn_month=None):
    """Generate usage data for a single user"""

    # Generate base patterns
    growth = generate_growth_phase(num_months)
    trend = generate_trend(num_months)

    # Generate churn decline if applicable
    if is_churned and churn_month:
        churn_decline = generate_churn_decline(num_months, churn_month)
    else:
        churn_decline = np.ones(num_months)

    usage_data = []

    for month_idx in range(num_months):
        month_data = {'USERID': user_id}

        # Calculate month timestamp starting from signup_date
        current_date = signup_date + timedelta(days=30 * month_idx)
        month_data['MONTH'] = current_date.strftime('%Y-%m-%d')

        # Add package tier
        month_data['PACKAGE_TIER'] = package_tier

        # Calculate churn date if applicable
        churn_date = None
        if is_churned and churn_month:
            churn_date = signup_date + timedelta(days=30 * churn_month)

        # Calculate MRR
        mrr = calculate_mrr(
            package_tier=package_tier,
            signup_date=signup_date,
            current_date=current_date,
            account_size=account_size,
            is_churned=is_churned,
            churn_date=churn_date
        )
        month_data['MRR'] = mrr

        # Get seasonality
        seasonality = generate_seasonality(month_idx % 12)

        # Calculate multiplier
        multiplier = growth[month_idx] * (1 + trend[month_idx]) * (1 + seasonality) * churn_decline[month_idx]

        # Add random noise
        noise = np.random.normal(1.0, 0.05)
        multiplier *= noise

        # Generate each metric
        for metric, base_value in base_values.items():
            if 'FLOAT' in metric or 'MINS' in metric or 'MIN' in metric:
                value = base_value * multiplier * np.random.uniform(0.9, 1.1)
                month_data[metric] = round(value, 2)
            else:  # NUMBER fields
                value = int(base_value * multiplier * np.random.uniform(0.9, 1.1))
                month_data[metric] = max(0, value)

        usage_data.append(month_data)

    return usage_data

# Define base values for different user profiles (representing mature usage levels)
user_profiles = {
    'heavy': {
        'PHONE_TOTAL_CALLS': 150,
        'PHONE_TOTAL_MINUTES_OF_USE': 450.0,
        'VOICE_CALLS': 120,
        'VOICE_MINS': 380.0,
        'FAX_CALLS': 5,
        'FAX_MINS': 15.0,
        'PHONE_TOTAL_NUM_INBOUND_CALLS': 80,
        'PHONE_TOTAL_NUM_OUTBOUND_CALLS': 70,
        'PHONE_TOTAL_INBOUND_MIN': 240.0,
        'PHONE_TOTAL_OUTBOUND_MIN': 210.0,
        'OUT_VOICE_CALLS': 70,
        'IN_VOICE_CALLS': 50,
        'OUT_VOICE_MINS': 210.0,
        'IN_VOICE_MINS': 170.0,
        'OUT_FAX_CALLS': 3,
        'IN_FAX_CALLS': 2,
        'OUT_FAX_MINS': 9.0,
        'IN_FAX_MINS': 6.0,
        'PHONE_MAU': 28,
        'CALL_MAU': 25,
        'FAX_MAU': 4,
        'HARDPHONE_CALLS': 100,
        'SOFTPHONE_CALLS': 50,
        'MOBILE_CALLS': 30,
        'MOBILE_ANDROID_CALLS': 15,
    },
    'medium': {
        'PHONE_TOTAL_CALLS': 80,
        'PHONE_TOTAL_MINUTES_OF_USE': 240.0,
        'VOICE_CALLS': 65,
        'VOICE_MINS': 210.0,
        'FAX_CALLS': 3,
        'FAX_MINS': 8.0,
        'PHONE_TOTAL_NUM_INBOUND_CALLS': 45,
        'PHONE_TOTAL_NUM_OUTBOUND_CALLS': 35,
        'PHONE_TOTAL_INBOUND_MIN': 130.0,
        'PHONE_TOTAL_OUTBOUND_MIN': 110.0,
        'OUT_VOICE_CALLS': 35,
        'IN_VOICE_CALLS': 30,
        'OUT_VOICE_MINS': 110.0,
        'IN_VOICE_MINS': 100.0,
        'OUT_FAX_CALLS': 2,
        'IN_FAX_CALLS': 1,
        'OUT_FAX_MINS': 5.0,
        'IN_FAX_MINS': 3.0,
        'PHONE_MAU': 20,
        'CALL_MAU': 18,
        'FAX_MAU': 2,
        'HARDPHONE_CALLS': 50,
        'SOFTPHONE_CALLS': 30,
        'MOBILE_CALLS': 15,
        'MOBILE_ANDROID_CALLS': 8,
    },
    'light': {
        'PHONE_TOTAL_CALLS': 35,
        'PHONE_TOTAL_MINUTES_OF_USE': 100.0,
        'VOICE_CALLS': 30,
        'VOICE_MINS': 90.0,
        'FAX_CALLS': 1,
        'FAX_MINS': 3.0,
        'PHONE_TOTAL_NUM_INBOUND_CALLS': 20,
        'PHONE_TOTAL_NUM_OUTBOUND_CALLS': 15,
        'PHONE_TOTAL_INBOUND_MIN': 55.0,
        'PHONE_TOTAL_OUTBOUND_MIN': 45.0,
        'OUT_VOICE_CALLS': 15,
        'IN_VOICE_CALLS': 15,
        'OUT_VOICE_MINS': 45.0,
        'IN_VOICE_MINS': 45.0,
        'OUT_FAX_CALLS': 1,
        'IN_FAX_CALLS': 0,
        'OUT_FAX_MINS': 2.0,
        'IN_FAX_MINS': 1.0,
        'PHONE_MAU': 12,
        'CALL_MAU': 10,
        'FAX_MAU': 1,
        'HARDPHONE_CALLS': 20,
        'SOFTPHONE_CALLS': 15,
        'MOBILE_CALLS': 5,
        'MOBILE_ANDROID_CALLS': 3,
    }
}

if __name__ == "__main__":
    # Define the data parameters
    latest_month = datetime(2025, 11, 1)  # November 2025
    earliest_signup = datetime(2023, 11, 1)  # 24 months of vintages
    signup_period_months = 24

    # Calculate average signups per month (target ~500, with Q4 having 50% more)
    # Total users calculation: 18 regular months * 500 + 6 Q4 months * 750 = 9000 + 4500 = 13500
    # Let's use a smaller number for testing: scale down by factor of 10
    base_signups_per_month = 50  # Will be 75 in Q4

    all_data = []
    all_users = []
    user_id_counter = 10000

    print(f"Generating data from {earliest_signup.strftime('%Y-%m')} to {latest_month.strftime('%Y-%m')}")
    print(f"Base signups per month: {base_signups_per_month} (Q4: {int(base_signups_per_month * 1.5)})")

    # Generate users for each signup month
    for month_offset in range(signup_period_months):
        signup_date = earliest_signup + timedelta(days=30 * month_offset)
        signup_month = signup_date.month

        # Q4 months (Oct=10, Nov=11, Dec=12) get 50% more signups
        is_q4 = signup_month in [10, 11, 12]
        num_signups = int(base_signups_per_month * 1.5) if is_q4 else base_signups_per_month

        for _ in range(num_signups):
            user_id = user_id_counter
            user_id_counter += 1

            # Assign user profile
            profile_type = random.choice(['heavy', 'medium', 'light'])
            base_values = user_profiles[profile_type]

            # Assign package tier
            if profile_type == 'heavy':
                tier_choices = ['Premium', 'Enterprise', 'Standard']
                tier_weights = [0.5, 0.3, 0.2]
            elif profile_type == 'medium':
                tier_choices = ['Standard', 'Premium', 'Basic']
                tier_weights = [0.5, 0.3, 0.2]
            else:
                tier_choices = ['Basic', 'Standard', 'Premium']
                tier_weights = [0.5, 0.3, 0.2]

            package_tier = random.choices(tier_choices, weights=tier_weights, k=1)[0]

            # Calculate months on book until latest_month
            months_on_book = ((latest_month.year - signup_date.year) * 12 +
                            (latest_month.month - signup_date.month))

            # Determine churn status
            # 5% churn at month 3
            # 10% annual churn rate (additional ~0.87% per month) after month 3
            is_churned = False
            churn_month = None

            # Early churn (5% at month 3)
            if random.random() < 0.05:
                is_churned = True
                churn_month = 3
            # Annual 10% churn rate for remaining users (after month 3)
            elif months_on_book > 3:
                # Monthly churn probability to achieve ~10% annual
                monthly_churn_prob = 1 - (0.9 ** (1/12))  # ~0.87% per month
                remaining_months = months_on_book - 3

                # Check each month if user churns
                for month in range(4, months_on_book + 1):
                    if random.random() < monthly_churn_prob:
                        is_churned = True
                        churn_month = month
                        break

            # Store user info
            all_users.append({
                'user_id': user_id,
                'signup_date': signup_date,
                'profile_type': profile_type,
                'package_tier': package_tier,
                'base_values': base_values,
                'is_churned': is_churned,
                'churn_month': churn_month,
                'months_on_book': months_on_book
            })

    print(f"\nGenerated {len(all_users)} users across {signup_period_months} months")

    # Generate usage data for all users
    print("\nGenerating usage data...")
    for idx, user_info in enumerate(all_users):
        if (idx + 1) % 100 == 0:
            print(f"  Processing user {idx + 1}/{len(all_users)}...")

        user_data = generate_user_usage(
            user_id=user_info['user_id'],
            num_months=user_info['months_on_book'] + 1,  # +1 to include signup month
            base_values=user_info['base_values'],
            package_tier=user_info['package_tier'],
            signup_date=user_info['signup_date'],
            account_size=user_info['profile_type'],
            is_churned=user_info['is_churned'],
            churn_month=user_info['churn_month']
        )
        all_data.extend(user_data)

    # Create DataFrame
    df = pd.DataFrame(all_data)

    # Reorder columns to match the schema
    column_order = [
        'USERID',
        'MONTH',
        'PACKAGE_TIER',
        'MRR',
        'PHONE_TOTAL_CALLS',
        'PHONE_TOTAL_MINUTES_OF_USE',
        'VOICE_CALLS',
        'VOICE_MINS',
        'FAX_CALLS',
        'FAX_MINS',
        'PHONE_TOTAL_NUM_INBOUND_CALLS',
        'PHONE_TOTAL_NUM_OUTBOUND_CALLS',
        'PHONE_TOTAL_INBOUND_MIN',
        'PHONE_TOTAL_OUTBOUND_MIN',
        'OUT_VOICE_CALLS',
        'IN_VOICE_CALLS',
        'OUT_VOICE_MINS',
        'IN_VOICE_MINS',
        'OUT_FAX_CALLS',
        'IN_FAX_CALLS',
        'OUT_FAX_MINS',
        'IN_FAX_MINS',
        'PHONE_MAU',
        'CALL_MAU',
        'FAX_MAU',
        'HARDPHONE_CALLS',
        'SOFTPHONE_CALLS',
        'MOBILE_CALLS',
        'MOBILE_ANDROID_CALLS'
    ]

    df = df[column_order]

    # Generate churn records from user info
    churn_data = []
    churned_count = 0

    for user_info in all_users:
        if user_info['is_churned'] and user_info['churn_month'] is not None:
            # Calculate actual churn date
            churn_date = user_info['signup_date'] + timedelta(days=30 * user_info['churn_month'])

            churn_data.append({
                'USERID': user_info['user_id'],
                'CHURN_DATE': churn_date.strftime('%Y-%m-%d'),
                'CHURNED': 1
            })
            churned_count += 1

    churn_df = pd.DataFrame(churn_data)

    # Calculate churn statistics
    total_users = len(all_users)
    churn_rate = (churned_count / total_users * 100) if total_users > 0 else 0

    # Calculate vintage statistics
    signup_months = df.groupby('USERID')['MONTH'].min().reset_index()
    signup_months['VINTAGE'] = pd.to_datetime(signup_months['MONTH']).dt.to_period('M').astype(str)
    vintage_counts = signup_months['VINTAGE'].value_counts().sort_index()

    # Save to CSV
    df.to_csv('phone_usage_data.csv', index=False)
    churn_df.to_csv('churn_records.csv', index=False)

    print(f"\n{'='*60}")
    print(f"DATA GENERATION COMPLETE")
    print(f"{'='*60}")
    print(f"\nGenerated {len(df):,} usage records for {total_users:,} users")
    print(f"Generated {len(churn_df):,} churn records ({churn_rate:.1f}% churn rate)")
    print(f"\nData Summary:")
    print(f"  Total users: {total_users:,}")
    print(f"  Churned users: {churned_count:,}")
    print(f"  Active users: {total_users - churned_count:,}")
    print(f"  Vintages: {len(vintage_counts)}")
    print(f"  Data period: {earliest_signup.strftime('%Y-%m')} to {latest_month.strftime('%Y-%m')}")
    print(f"\nVintage distribution (first 5):")
    for vintage, count in vintage_counts.head(5).items():
        print(f"  {vintage}: {count:,} users")
    print(f"\nSample of usage data:")
    print(df.head(10))
    print(f"\nSample of churn data:")
    print(churn_df.head(10))
