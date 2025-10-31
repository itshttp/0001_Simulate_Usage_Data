import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

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

def generate_user_usage(user_id, num_months, base_values, is_churned=False, churn_month=None):
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
        
        # Calculate month timestamp
        start_date = datetime(2023, 1, 1)
        current_date = start_date + timedelta(days=30 * month_idx)
        month_data['MONTH'] = current_date.strftime('%Y-%m-%d')
        
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
    # Generate data
    num_users = 100
    num_months = 36  # 3 years of data
    num_churned_users = 20

    all_data = []

    for user_idx in range(num_users):
        user_id = 1000 + user_idx
        
        # Assign user profile
        profile_type = random.choice(['heavy', 'medium', 'light'])
        base_values = user_profiles[profile_type]
        
        # Determine if user churns
        is_churned = user_idx < num_churned_users
        churn_month = random.randint(18, 30) if is_churned else None
        
        # Generate usage data
        user_data = generate_user_usage(user_id, num_months, base_values, is_churned, churn_month)
        all_data.extend(user_data)

    # Create DataFrame
    df = pd.DataFrame(all_data)

    # Reorder columns to match the schema
    column_order = [
        'USERID',
        'MONTH',
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

    # Generate churn records
    churned_users = df[df['USERID'] < 1000 + num_churned_users]['USERID'].unique()
    churn_data = []

    for user_id in churned_users:
        user_months = df[df['USERID'] == user_id]['MONTH'].values
        churn_month_idx = random.randint(18, 30)
        churn_date = user_months[churn_month_idx] if churn_month_idx < len(user_months) else user_months[-1]
        
        churn_data.append({
            'USERID': user_id,
            'CHURN_DATE': churn_date,
            'CHURNED': 1
        })

    churn_df = pd.DataFrame(churn_data)

    # Save to CSV
    df.to_csv('phone_usage_data.csv', index=False)
    churn_df.to_csv('churn_records.csv', index=False)

    print(f"Generated {len(df)} records for {num_users} users over {num_months} months")
    print(f"Generated {len(churn_df)} churn records")
    print(f"\nData summary:")
    print(f"- Total users: {num_users}")
    print(f"- Churned users: {num_churned_users}")
    print(f"- Active users: {num_users - num_churned_users}")
    print(f"- Time period: {num_months} months")
    print(f"\nSample of usage data:")
    print(df.head(10))
    print(f"\nSample of churn data:")
    print(churn_df.head(10))
