# Data Generation Manual

This manual provides step-by-step instructions for generating phone usage data with custom parameters.

## Table of Contents
1. [Quick Start](#quick-start)
2. [Configuration Parameters](#configuration-parameters)
3. [Step-by-Step Guide](#step-by-step-guide)
4. [Advanced Options](#advanced-options)
5. [Output Files](#output-files)
6. [Troubleshooting](#troubleshooting)

---

## Quick Start

**Generate data with default settings:**

```python
# Run from Python interpreter or create a script
from datetime import datetime
import function

# Set configuration
function.NUM_ENTERPRISE_ACCOUNTS = 100
function.MOST_RECENT_MONTH = datetime(2025, 10, 1)

# Define your data options
function.COMPANIES = ['Acme Corp', 'TechStart Inc', 'Global Solutions', 'Enterprise Ltd']
function.BRANDS = [(1, 'Brand A'), (2, 'Brand B'), (3, 'Brand C')]
function.UBRANDS = [('UA1', 'UBrand Alpha'), ('UA2', 'UBrand Beta')]
function.PACKAGES = [
    (100, 'Basic Plan', 'CAT-100', 'Catalog Basic'),
    (200, 'Professional Plan', 'CAT-200', 'Catalog Professional'),
    (300, 'Enterprise Plan', 'CAT-300', 'Catalog Enterprise')
]
function.TIERS = [(1, 'Tier 1', 'Standard Edition'), (2, 'Tier 2', 'Premium Edition')]
function.OPCOS = ['OPCO-US', 'OPCO-EU', 'OPCO-APAC']

# Generate all tables
account_df, usage_df, churn_df = function.generate_all_tables(
    non_active_ratio=0.05,  # 5% churn rate
    num_months=36,          # 3 years of data
    save_to_csv=True        # Save to CSV files
)
```

---

## Configuration Parameters

### 1. **Number of Accounts**

```python
function.NUM_ENTERPRISE_ACCOUNTS = 100  # Number of enterprise accounts to generate
```

- **Default**: 100
- **Recommended Range**: 10-1000 for testing, 1000+ for production
- **Impact**: More accounts = more data volume

### 2. **Churn Rate (non_active_ratio)**

```python
non_active_ratio = 0.05  # 5% of accounts will churn
```

- **Default**: 0.05 (5%)
- **Range**: 0.0 to 1.0
- **Examples**:
  - `0.05` = 5% churn (low)
  - `0.10` = 10% churn (medium)
  - `0.20` = 20% churn (high)

### 3. **Time Period**

```python
function.MOST_RECENT_MONTH = datetime(2025, 10, 1)  # End date
num_months = 36  # Number of months of usage data
```

- **MOST_RECENT_MONTH**: Latest month in the dataset
- **num_months**: Duration of usage data (default: 36 = 3 years)
- **Note**: Account data will have 5-20 random months per account

### 4. **Usage Start Date**

```python
usage_start_date = datetime(2023, 1, 1)  # When usage tracking began
```

- **Default**: datetime(2023, 1, 1)
- **Impact**: Determines the start of usage history

### 5. **Company Names**

```python
function.COMPANIES = [
    'Acme Corp',
    'TechStart Inc',
    'Global Solutions',
    'Enterprise Ltd',
    'Innovation Labs',
    'Digital Dynamics'
]
```

- Add as many companies as you want
- Each account will be randomly assigned to one company

### 6. **Brands**

```python
function.BRANDS = [
    (1, 'Brand A'),     # (brand_id, brand_name)
    (2, 'Brand B'),
    (3, 'Brand C')
]
```

- Format: List of tuples `(id, name)`
- Used for both EA_BRAND and SA_BRAND
- IDs and names remain 1:1 throughout

### 7. **UBrands (Unified Brands)**

```python
function.UBRANDS = [
    ('UA1', 'UBrand Alpha'),  # (ubrand_id, description)
    ('UA2', 'UBrand Beta'),
    ('UA3', 'UBrand Gamma')
]
```

- Format: List of tuples `(id, description)`
- Can use numeric or alphanumeric IDs

### 8. **Packages**

```python
function.PACKAGES = [
    (100, 'Basic Plan', 'CAT-100', 'Catalog Basic'),
    (200, 'Professional Plan', 'CAT-200', 'Catalog Professional'),
    (300, 'Enterprise Plan', 'CAT-300', 'Catalog Enterprise'),
    (400, 'Ultimate Plan', 'CAT-400', 'Catalog Ultimate')
]
```

- Format: `(package_id, package_name, catalog_package_id, catalog_package_name)`
- **Package Change Logic**: 10% probability every 24 months
- More package options = more variety in upgrades/downgrades

### 9. **Tiers**

```python
function.TIERS = [
    (1, 'Tier 1', 'Standard Edition'),
    (2, 'Tier 2', 'Premium Edition'),
    (3, 'Tier 3', 'Enterprise Edition')
]
```

- Format: `(tier_id, tier_name, edition_name)`
- Tiers remain constant for each account (do not change)

### 10. **OPCOs (Operating Companies)**

```python
function.OPCOS = [
    'OPCO-US',
    'OPCO-EU',
    'OPCO-APAC',
    'OPCO-LATAM'
]
```

- List of operating company identifiers
- Each account assigned to one OPCO

---

## Step-by-Step Guide

### Method 1: Interactive Python Session

1. **Start Python with virtual environment:**
   ```bash
   ./venv/bin/python
   ```

2. **Import required modules:**
   ```python
   from datetime import datetime
   import function
   ```

3. **Set configuration (customize as needed):**
   ```python
   # Number of accounts
   function.NUM_ENTERPRISE_ACCOUNTS = 200

   # Time settings
   function.MOST_RECENT_MONTH = datetime(2025, 10, 1)

   # Companies
   function.COMPANIES = ['Acme Corp', 'TechStart Inc', 'Global Solutions']

   # Brands
   function.BRANDS = [
       (1, 'Brand A'),
       (2, 'Brand B'),
       (3, 'Brand C')
   ]

   # UBrands
   function.UBRANDS = [
       ('UA1', 'UBrand Alpha'),
       ('UA2', 'UBrand Beta')
   ]

   # Packages
   function.PACKAGES = [
       (100, 'Basic Plan', 'CAT-100', 'Catalog Basic'),
       (200, 'Professional Plan', 'CAT-200', 'Catalog Professional'),
       (300, 'Enterprise Plan', 'CAT-300', 'Catalog Enterprise')
   ]

   # Tiers
   function.TIERS = [
       (1, 'Tier 1', 'Standard Edition'),
       (2, 'Tier 2', 'Premium Edition')
   ]

   # OPCOs
   function.OPCOS = ['OPCO-US', 'OPCO-EU', 'OPCO-APAC']
   ```

4. **Generate data:**
   ```python
   # Generate with custom parameters
   account_df, usage_df, churn_df = function.generate_all_tables(
       non_active_ratio=0.10,  # 10% churn rate
       num_months=36,          # 3 years
       usage_start_date=datetime(2023, 1, 1),
       save_to_csv=True
   )
   ```

5. **Verify output:**
   ```python
   print(f"Accounts: {len(account_df)}")
   print(f"Usage records: {len(usage_df)}")
   print(f"Churned accounts: {len(churn_df)}")
   ```

### Method 2: Create a Script

1. **Create a new file `generate_data.py`:**

```python
#!/usr/bin/env python3
"""
Custom data generation script
Modify parameters as needed
"""

from datetime import datetime
import function

# ============================================================================
# CONFIGURATION - CUSTOMIZE THESE VALUES
# ============================================================================

# Number of accounts to generate
NUM_ACCOUNTS = 500

# Churn rate (0.0 to 1.0)
CHURN_RATE = 0.08  # 8%

# Time period
MOST_RECENT_MONTH = datetime(2025, 10, 1)
NUM_MONTHS = 36  # 3 years
USAGE_START_DATE = datetime(2023, 1, 1)

# Companies
COMPANIES = [
    'Acme Corporation',
    'TechStart Innovations',
    'Global Solutions Ltd',
    'Enterprise Dynamics',
    'Digital Ventures'
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
# SETUP
# ============================================================================

print("=" * 70)
print("PHONE USAGE DATA GENERATOR")
print("=" * 70)
print(f"\nConfiguration:")
print(f"  Number of Accounts: {NUM_ACCOUNTS}")
print(f"  Churn Rate: {CHURN_RATE * 100:.1f}%")
print(f"  Usage Period: {NUM_MONTHS} months")
print(f"  Most Recent Month: {MOST_RECENT_MONTH.strftime('%Y-%m-%d')}")
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

# ============================================================================
# GENERATE DATA
# ============================================================================

print("Starting data generation...")
print()

account_df, usage_df, churn_df = function.generate_all_tables(
    non_active_ratio=CHURN_RATE,
    num_months=NUM_MONTHS,
    usage_start_date=USAGE_START_DATE,
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
print(f"  - account_attributes_monthly.csv ({len(account_df):,} records)")
print(f"  - phone_usage_data.csv ({len(usage_df):,} records)")
print(f"  - churn_records.csv ({len(churn_df):,} records)")
print()
print(f"Summary Statistics:")
print(f"  - Total Accounts: {account_df['SERVICE_ACCOUNT_ID'].nunique()}")
print(f"  - Active Accounts: {len(account_df[account_df['SA_ACCT_STATUS'] == 'Active']['SERVICE_ACCOUNT_ID'].unique())}")
print(f"  - Churned Accounts: {len(churn_df)}")
print(f"  - Actual Churn Rate: {(len(churn_df) / account_df['SERVICE_ACCOUNT_ID'].nunique()) * 100:.2f}%")
print(f"  - Usage Records: {len(usage_df):,}")
print(f"  - Average Usage Records per Account: {len(usage_df) / usage_df['USERID'].nunique():.1f}")
print()
```

2. **Run the script:**
   ```bash
   ./venv/bin/python generate_data.py
   ```

---

## Advanced Options

### Generate Only Account Data

```python
account_df = function.generate_account_table(non_active_ratio=0.05)
account_df.to_csv('accounts_only.csv', index=False)
```

### Generate Only Usage Data

```python
# Requires existing account data
usage_df = function.generate_usage_table(
    account_df,
    num_months=36,
    usage_start_date=datetime(2023, 1, 1)
)
usage_df.to_csv('usage_only.csv', index=False)
```

### Generate Churn Records Separately

```python
account_records = account_df.to_dict('records')
churn_records = function.generate_churn_records(
    account_records=account_records,
    output_filename='churned_accounts.csv'
)
```

### Don't Save to CSV (Return DataFrames Only)

```python
account_df, usage_df, churn_df = function.generate_all_tables(
    non_active_ratio=0.05,
    num_months=36,
    save_to_csv=False  # Don't create CSV files
)

# Work with DataFrames in memory
print(account_df.head())
print(usage_df.describe())
```

### Visualize a Specific Account

```python
# View detailed usage trends for one account
user_id = 1000  # First account
function.plot_user_timeseries(user_id, usage_df, churn_df)
```

### View Churned Accounts

```python
# Show details of first churned account
function.show_churned_account(
    account_index=0,
    account_df=account_df,
    usage_df=usage_df,
    churn_df=churn_df
)
```

### Find Non-Active Accounts

```python
non_active_df = function.find_non_active_accounts(
    account_df,
    show_details=True
)
```

---

## Output Files

### 1. account_attributes_monthly.csv

**Description**: Monthly account attributes with all account information.

**Columns**:
- `MONTH`: Date (YYYY-MM-DD)
- `ENTERPRISE_ACCOUNT_ID`: Enterprise account identifier
- `COMPANY`: Company name
- `EA_BRAND_ID`, `EA_BRAND_NAME`: Enterprise account brand
- `EA_UBRAND_ID`, `EA_UBRAND_DESCRIPTION`: Enterprise unified brand
- `EA_ACCT_STATUS`: Enterprise account status (always 'Active')
- `SERVICE_ACCOUNT_ID`: Service account identifier (used as USERID)
- `SA_BRAND_ID`, `SA_BRAND_NAME`: Service account brand
- `SA_UBRAND_ID`, `SA_UBRAND_DESCRIPTION`: Service unified brand
- `SA_ACCT_STATUS`: Service account status ('Active', 'Suspended', 'Closed')
- `PACKAGE_ID`, `PACKAGE_NAME`: Current package
- `CATALOG_PACKAGE_ID`, `CATALOG_PACKAGE_NAME`: Catalog package
- `IS_TESTER`: Boolean flag
- `TIER_ID`, `TIER_NAME`, `EDITION_NAME`: Tier information
- `EXTERNAL_ACCOUNT_ID`: External identifier
- `BAN`: Billing account number
- `OPCO_ID`: Operating company

**Key Features**:
- Each account has 5-20 random months of data
- All attributes constant except `SA_ACCT_STATUS` and `PACKAGE_NAME`
- Package changes occur at ~10% probability every 24 months

### 2. phone_usage_data.csv

**Description**: Monthly phone usage metrics for each user.

**Columns**:
- `USERID`: User identifier (matches SERVICE_ACCOUNT_ID)
- `MONTH`: Date (YYYY-MM-DD)
- `PHONE_TOTAL_CALLS`: Total number of calls
- `PHONE_TOTAL_MINUTES_OF_USE`: Total minutes of phone usage
- `VOICE_CALLS`, `VOICE_MINS`: Voice call metrics
- `FAX_CALLS`, `FAX_MINS`: Fax metrics
- `PHONE_TOTAL_NUM_INBOUND_CALLS`, `PHONE_TOTAL_NUM_OUTBOUND_CALLS`: Call direction
- `PHONE_TOTAL_INBOUND_MIN`, `PHONE_TOTAL_OUTBOUND_MIN`: Minutes by direction
- `OUT_VOICE_CALLS`, `IN_VOICE_CALLS`: Voice calls by direction
- `OUT_VOICE_MINS`, `IN_VOICE_MINS`: Voice minutes by direction
- `OUT_FAX_CALLS`, `IN_FAX_CALLS`: Fax calls by direction
- `OUT_FAX_MINS`, `IN_FAX_MINS`: Fax minutes by direction
- `PHONE_MAU`, `CALL_MAU`, `FAX_MAU`: Monthly active user metrics
- `HARDPHONE_CALLS`, `SOFTPHONE_CALLS`, `MOBILE_CALLS`, `MOBILE_ANDROID_CALLS`: Device usage

**Key Features**:
- Includes growth phase, seasonality, and trend patterns
- Churned users show decline before churn date
- User profiles: heavy, medium, light usage patterns

### 3. churn_records.csv

**Description**: Records of churned accounts.

**Columns**:
- `USERID`: User identifier
- `CHURN_DATE`: Date when account churned
- `CHURNED`: Flag (always 1)

**Key Features**:
- Only includes accounts that churned (SA_ACCT_STATUS = 'Suspended' or 'Closed')
- Churn date matches when status changed in account table

---

## Troubleshooting

### Error: "Configuration constants must be set"

**Solution**: Ensure all required constants are defined before calling functions:

```python
function.NUM_ENTERPRISE_ACCOUNTS = 100
function.MOST_RECENT_MONTH = datetime(2025, 10, 1)
function.COMPANIES = ['Company A', 'Company B']
function.BRANDS = [(1, 'Brand A'), (2, 'Brand B')]
function.UBRANDS = [('U1', 'UBrand 1')]
function.PACKAGES = [(100, 'Package A', 'CAT-100', 'Catalog A')]
function.TIERS = [(1, 'Tier 1', 'Standard')]
function.OPCOS = ['OPCO-1']
```

### Error: "ImportError: generate_user_usage"

**Solution**: Ensure `generate_phone_usage_data.py` is in the same directory as `function.py`.

### Data Volume Too Large

**Solution**: Reduce parameters:
- Decrease `NUM_ENTERPRISE_ACCOUNTS`
- Reduce `num_months`
- Lower `non_active_ratio`

### Want More Variety

**Solution**: Add more options to:
- `COMPANIES`
- `BRANDS`
- `PACKAGES`
- `TIERS`

### Need Reproducible Results

**Solution**: Set random seed at the beginning:

```python
import random
import numpy as np

random.seed(42)
np.random.seed(42)
```

---

## Complete Example

Here's a complete example generating a realistic dataset:

```python
#!/usr/bin/env python3
from datetime import datetime
import function

# Configuration
function.NUM_ENTERPRISE_ACCOUNTS = 1000  # 1000 accounts
function.MOST_RECENT_MONTH = datetime(2025, 10, 1)

function.COMPANIES = [
    'Global Telecom Inc',
    'Enterprise Communications Ltd',
    'Business Phone Solutions',
    'Corporate Networks LLC',
    'Digital Voice Systems'
]

function.BRANDS = [
    (1, 'Premium Voice'),
    (2, 'Business Plus'),
    (3, 'Standard Connect')
]

function.UBRANDS = [
    ('UC1', 'Unified Communications Alpha'),
    ('UC2', 'Unified Communications Beta')
]

function.PACKAGES = [
    (100, 'Small Business', 'CAT-100', 'SB Catalog'),
    (200, 'Medium Business', 'CAT-200', 'MB Catalog'),
    (300, 'Large Business', 'CAT-300', 'LB Catalog'),
    (400, 'Enterprise', 'CAT-400', 'ENT Catalog')
]

function.TIERS = [
    (1, 'Basic', 'Standard'),
    (2, 'Professional', 'Professional'),
    (3, 'Enterprise', 'Enterprise')
]

function.OPCOS = ['OPCO-US', 'OPCO-EU', 'OPCO-APAC']

# Generate data with 7% churn rate over 3 years
account_df, usage_df, churn_df = function.generate_all_tables(
    non_active_ratio=0.07,
    num_months=36,
    usage_start_date=datetime(2022, 10, 1),
    save_to_csv=True
)

print(f"\n✓ Generated {len(account_df)} account records")
print(f"✓ Generated {len(usage_df)} usage records")
print(f"✓ Generated {len(churn_df)} churn records")
```

---

## Next Steps

After generating data:

1. **Load into Snowflake**: Use `snowflake_loader.py` to upload CSV files
2. **View Dashboard**: Run the Streamlit dashboard to visualize
3. **Analyze Patterns**: Use the test functions to explore data characteristics

For loading into Snowflake, see `SNOWFLAKE_SETUP.md`.

For running the dashboard, see `STREAMLIT_DASHBOARD.md`.
