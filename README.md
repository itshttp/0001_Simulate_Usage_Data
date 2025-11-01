# Phone Usage Data Simulator

A Python toolkit for generating realistic enterprise account and phone usage data with churn patterns. Perfect for testing analytics systems, training machine learning models, or creating demo datasets.

## Features

- Generate enterprise account data with multiple attributes (brands, packages, tiers, etc.)
- Simulate realistic phone usage patterns with:
  - Seasonal variations (higher usage in winter/summer)
  - Growth phases (initial adoption period)
  - Long-term trends (cyclical increase/decrease patterns)
  - Churn decline patterns (gradual usage drop before account closure)
- Support for multiple user profiles (heavy, medium, light users)
- Automatic churn record generation
- Visualization tools for analyzing usage trends
- Export to CSV and SQL INSERT statements

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### Generate All Data

```python
from function import generate_all_tables

# Set configuration constants
NUM_ENTERPRISE_ACCOUNTS = 100
MOST_RECENT_MONTH = datetime.now().replace(day=1)

# Define your reference data
COMPANIES = ['Company A', 'Company B', 'Company C']
BRANDS = [(1, 'Brand1'), (2, 'Brand2')]
UBRANDS = [('U1', 'UBrand1'), ('U2', 'UBrand2')]
PACKAGES = [(1, 'Basic', 101, 'Basic Package'), (2, 'Premium', 102, 'Premium Package')]
TIERS = [(1, 'Tier1', 'Standard'), (2, 'Tier2', 'Enterprise')]
OPCOS = ['OPCO1', 'OPCO2', 'OPCO3']

# Update globals for the module
import function
function.NUM_ENTERPRISE_ACCOUNTS = NUM_ENTERPRISE_ACCOUNTS
function.MOST_RECENT_MONTH = MOST_RECENT_MONTH
function.COMPANIES = COMPANIES
function.BRANDS = BRANDS
function.UBRANDS = UBRANDS
function.PACKAGES = PACKAGES
function.TIERS = TIERS
function.OPCOS = OPCOS

# Generate all tables
account_df, usage_df, churn_df = generate_all_tables(
    non_active_ratio=0.05,  # 5% of accounts will churn
    num_months=36,          # 36 months of usage data
    save_to_csv=True        # Save to CSV files
)
```

### Output Files

The above code generates three CSV files:

1. **account_attributes_monthly.csv** - Enterprise account attributes by month
2. **phone_usage_data.csv** - Phone usage metrics by user and month
3. **churn_records.csv** - Churn events with user ID and churn date

## Data Schema

### Account Attributes Table

| Column | Description |
|--------|-------------|
| MONTH | Month of the record |
| ENTERPRISE_ACCOUNT_ID | Enterprise account identifier |
| SERVICE_ACCOUNT_ID | Service account identifier (used as USERID in usage data) |
| COMPANY | Company name |
| EA_BRAND_ID, EA_BRAND_NAME | Enterprise account brand |
| SA_BRAND_ID, SA_BRAND_NAME | Service account brand |
| SA_ACCT_STATUS | Account status (Active, Suspended, Closed) |
| PACKAGE_ID, PACKAGE_NAME | Package details |
| TIER_ID, TIER_NAME | Tier information |
| IS_TESTER | Boolean flag for test accounts |

### Phone Usage Table

| Column | Description |
|--------|-------------|
| USERID | User identifier (matches SERVICE_ACCOUNT_ID) |
| MONTH | Month of usage |
| PHONE_TOTAL_CALLS | Total number of calls |
| PHONE_TOTAL_MINUTES_OF_USE | Total minutes of phone usage |
| VOICE_CALLS, VOICE_MINS | Voice call metrics |
| FAX_CALLS, FAX_MINS | Fax usage metrics |
| PHONE_TOTAL_NUM_INBOUND_CALLS | Total inbound calls |
| PHONE_TOTAL_NUM_OUTBOUND_CALLS | Total outbound calls |
| PHONE_MAU, CALL_MAU, FAX_MAU | Monthly active users metrics |
| HARDPHONE_CALLS, SOFTPHONE_CALLS | Device type usage |
| MOBILE_CALLS, MOBILE_ANDROID_CALLS | Mobile usage metrics |

### Churn Records Table

| Column | Description |
|--------|-------------|
| USERID | User identifier |
| CHURN_DATE | Date when user churned |
| CHURNED | Churn flag (1 = churned) |

## Usage Patterns

The simulator generates realistic usage patterns:

### Growth Phase
New users start with lower usage and gradually increase over 6 months following a sigmoid growth curve.

### Seasonality
Usage varies by season with peaks in winter (December) and summer (July), approximately 15% variation.

### Long-term Trends
After the growth phase, usage follows a 24-month cycle:
- 60% of time: gradual increase up to 20%
- 40% of time: gradual decrease of 10%

### Churn Decline
Users who churn show declining usage 6 months before churn:
- Exponential decline starting 6 months before churn
- Usage drops to near-zero after churn date

## Analysis Functions

### Visualize User Usage Trends

```python
from function import plot_user_timeseries

# Plot all usage metrics for a specific user
plot_user_timeseries(
    user_id=1234,
    usage_df=usage_df,
    churn_df=churn_df
)
```

### Show Churned Account Details

```python
from function import show_churned_account

# Display first churned account with full details and plots
show_churned_account(
    account_index=0,
    account_df=account_df,
    usage_df=usage_df,
    churn_df=churn_df
)
```

### Find Non-Active Accounts

```python
from function import find_non_active_accounts

# List all suspended or closed accounts
non_active_df = find_non_active_accounts(
    account_df=account_df,
    show_details=True
)
```

### List Available Users

```python
from function import list_user_ids

# Show all user IDs with churn status
list_user_ids(
    usage_df=usage_df,
    churn_df=churn_df,
    limit=20
)
```

## User Profiles

Three user profiles are available with different usage levels:

### Heavy Users
- 150 calls/month, 450 minutes
- High activity across all channels
- 28 phone MAU

### Medium Users
- 80 calls/month, 240 minutes
- Moderate activity
- 20 phone MAU

### Light Users
- 35 calls/month, 100 minutes
- Basic usage
- 12 phone MAU

## Advanced Usage

### Generate Only Account Data

```python
from function import generate_account_table

account_df = generate_account_table(non_active_ratio=0.05)
```

### Generate Only Usage Data

```python
from function import generate_usage_table

usage_df = generate_usage_table(
    account_df=account_df,
    num_months=36,
    usage_start_date=datetime(2023, 1, 1)
)
```

### Generate SQL INSERT Statements

```python
from function import generate_account_data, generate_insert_statements

records = generate_account_data(non_active_ratio=0.05)
generate_insert_statements(
    records,
    output_file='insert_statements.sql',
    batch_size=100
)
```

### Load Data to Snowflake

The toolkit includes a Snowflake loader module for directly loading data into Snowflake tables.

📖 **See [SNOWFLAKE_SETUP.md](SNOWFLAKE_SETUP.md) for detailed setup instructions and troubleshooting.**

#### Quick Setup

1. Install Snowflake dependencies:
```bash
pip install snowflake-connector-python python-dotenv
```

2. Configure credentials:
```bash
cp .env.example .env
# Edit .env and fill in your Snowflake credentials
```

3. Test connection:
```python
from snowflake_loader import test_connection

test_connection()
```

#### Load Data from DataFrames

```python
from snowflake_loader import load_all_data

# After generating data with generate_all_tables()
load_all_data(
    from_dataframes=True,
    account_df=account_df,
    usage_df=usage_df,
    churn_df=churn_df,
    truncate=False  # Set True to replace existing data
)
```

#### Load Data from CSV Files

```python
from snowflake_loader import load_all_data

# Load from saved CSV files
load_all_data(from_dataframes=False)
```

#### Verify Data Loaded

```python
from snowflake_loader import show_table_summary

show_table_summary()
```

#### Command Line Usage

```bash
# Test connection
python snowflake_loader.py --test

# Load data from CSV files
python snowflake_loader.py

# Load with truncate (replace existing data)
python snowflake_loader.py --truncate

# Show table summary
python snowflake_loader.py --summary
```

## Configuration

Before generating data, set these global variables in the `function` module:

```python
import function

function.NUM_ENTERPRISE_ACCOUNTS = 100  # Number of enterprise accounts
function.MOST_RECENT_MONTH = datetime(2025, 10, 1)  # Most recent month
function.COMPANIES = ['Company A', 'Company B']
function.BRANDS = [(1, 'Brand1'), (2, 'Brand2')]
function.UBRANDS = [('U1', 'UBrand1')]
function.PACKAGES = [(1, 'Basic', 101, 'Basic Package')]
function.TIERS = [(1, 'Standard', 'Standard Edition')]
function.OPCOS = ['OPCO1', 'OPCO2']
```

## Files

### Core Modules
- **function.py** - Main module with data generation and analysis functions
- **generate_phone_usage_data.py** - Phone usage pattern simulation engine

### Database Integration
- **snowflake_loader.py** - Snowflake database integration module
- **.env.example** - Template for Snowflake credentials (copy to .env)

### Interactive Dashboard
- **streamlit_app.py** - Streamlit web dashboard (local version)
- **streamlit_app_snowflake.py** - Streamlit dashboard for Snowflake deployment ⭐
- **start_dashboard.sh** - Convenient script to launch local dashboard

### Analysis & Visualization
- **test_functions.ipynb** - Jupyter notebook for testing and visualization

### Configuration
- **requirements.txt** - Python dependencies
- **.gitignore** - Git ignore rules (keeps secrets safe)

### Documentation
- **README.md** - This file (main documentation)
- **QUICK_START.md** - 5-minute quick start guide
- **SNOWFLAKE_SETUP.md** - Snowflake integration guide
- **STREAMLIT_DASHBOARD.md** - Local dashboard setup guide
- **SNOWFLAKE_STREAMLIT_DEPLOYMENT.md** - Deploy to Snowflake Streamlit ⭐

## Requirements

### Core Dependencies
- Python 3.8+
- pandas >= 1.5.0
- numpy >= 1.20.0
- python-dateutil >= 2.8.0

### Optional: Visualizations
- matplotlib >= 3.5.0
- seaborn >= 0.12.0

### Optional: Snowflake Integration
- snowflake-connector-python >= 3.0.0
- python-dotenv >= 1.0.0

## Streamlit Dashboard

An interactive web-based analytics dashboard for visualizing the phone usage data.

### Deployment Options

**Option 1: Run in Snowflake (Recommended)** ⭐

Deploy directly in Snowflake Streamlit - no local setup required!

```
1. Log into Snowflake UI
2. Go to Streamlit → + Streamlit App
3. Copy code from streamlit_app_snowflake.py
4. Paste and click Run
```

📖 **See [SNOWFLAKE_STREAMLIT_DEPLOYMENT.md](SNOWFLAKE_STREAMLIT_DEPLOYMENT.md)** for step-by-step guide.

**Option 2: Run Locally**

Run on your local machine:

```bash
# Install Streamlit
pip install streamlit plotly

# Run the dashboard
streamlit run streamlit_app.py
```

📖 **See [STREAMLIT_DASHBOARD.md](STREAMLIT_DASHBOARD.md)** for local setup guide.

### Features

- **🏠 Overview**: KPIs, trends, and summary metrics
- **👥 Account Analytics**: Account distribution and growth analysis
- **📈 Usage Trends**: Time series charts with interactive filters
- **⚠️ Churn Analysis**: Churn patterns and prediction indicators
- **🎯 User Segmentation**: Heavy, medium, and light user analysis

### Which Version to Use?

| Feature | Snowflake Streamlit | Local Streamlit |
|---------|---------------------|-----------------|
| Setup Required | None | Virtual env + dependencies |
| Credentials | Built-in | `.env` file needed |
| Sharing | Share Snowflake URL | Host yourself |
| Performance | Runs in Snowflake | Depends on machine |
| **Recommended For** | **Production use** | Development/testing |

## Examples

See `test_functions.ipynb` for detailed examples and usage demonstrations.

## License

This project is for data simulation and testing purposes.
