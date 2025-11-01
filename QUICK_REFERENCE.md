# Quick Reference Guide

Fast reference for common data generation scenarios.

## Common Scenarios

### 1. Small Test Dataset (Quick)
```python
# 50 accounts, 5% churn, 1 year of data
./venv/bin/python -c "
from datetime import datetime
import function

function.NUM_ENTERPRISE_ACCOUNTS = 50
function.MOST_RECENT_MONTH = datetime(2025, 10, 1)
function.COMPANIES = ['Company A', 'Company B', 'Company C']
function.BRANDS = [(1, 'Brand A'), (2, 'Brand B')]
function.UBRANDS = [('U1', 'UBrand 1')]
function.PACKAGES = [(100, 'Basic', 'CAT-100', 'Basic'), (200, 'Pro', 'CAT-200', 'Pro')]
function.TIERS = [(1, 'Tier 1', 'Standard')]
function.OPCOS = ['OPCO-US']

function.generate_all_tables(non_active_ratio=0.05, num_months=12, save_to_csv=True)
"
```

### 2. Medium Production Dataset
```python
# 500 accounts, 8% churn, 3 years of data
./venv/bin/python generate_data.py
# (Edit generate_data.py first: NUM_ACCOUNTS=500, CHURN_RATE=0.08)
```

### 3. Large Production Dataset
```python
# 5000 accounts, 10% churn, 3 years of data
./venv/bin/python -c "
from datetime import datetime
import function

function.NUM_ENTERPRISE_ACCOUNTS = 5000
function.MOST_RECENT_MONTH = datetime(2025, 10, 1)

# ... (full configuration)

function.generate_all_tables(non_active_ratio=0.10, num_months=36)
"
```

### 4. High Churn Dataset
```python
# 200 accounts, 25% churn, 2 years
./venv/bin/python generate_data.py
# (Edit: NUM_ACCOUNTS=200, CHURN_RATE=0.25, NUM_MONTHS=24)
```

### 5. Low Churn Dataset
```python
# 1000 accounts, 2% churn, 5 years
./venv/bin/python generate_data.py
# (Edit: NUM_ACCOUNTS=1000, CHURN_RATE=0.02, NUM_MONTHS=60)
```

## Parameter Quick Reference

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `NUM_ENTERPRISE_ACCOUNTS` | 100 | 10-10000+ | Number of accounts |
| `non_active_ratio` | 0.05 | 0.0-1.0 | Churn rate (5% = 0.05) |
| `num_months` | 36 | 1-120+ | Months of usage data |
| `MOST_RECENT_MONTH` | Current | Any date | Latest month in dataset |
| `COMPANIES` | - | 1+ | List of company names |
| `BRANDS` | - | 1+ | List of (id, name) tuples |
| `PACKAGES` | - | 1+ | List of package options |

## Churn Rate Examples

| Churn Rate | Description | Use Case |
|------------|-------------|----------|
| 0.02 (2%) | Very low | Stable enterprise customers |
| 0.05 (5%) | Low | Standard B2B |
| 0.10 (10%) | Medium | Mixed customer base |
| 0.15 (15%) | High | Competitive market |
| 0.25 (25%) | Very high | High turnover scenario |

## Time Period Examples

| Months | Years | Use Case |
|--------|-------|----------|
| 12 | 1 | Quick test/recent data |
| 24 | 2 | Short-term analysis |
| 36 | 3 | Standard (default) |
| 48 | 4 | Long-term patterns |
| 60 | 5 | Multi-year trends |

## Common Commands

### Run Default Script
```bash
./venv/bin/python generate_data.py
```

### Check Generated Files
```bash
ls -lh *.csv
```

### View File Sizes
```bash
wc -l *.csv
```

### Preview Account Data
```bash
head -20 account_attributes_monthly.csv
```

### Preview Usage Data
```bash
head -20 phone_usage_data.csv
```

### Count Accounts
```bash
# Total accounts
cut -d',' -f8 account_attributes_monthly.csv | sort -u | tail -n +2 | wc -l

# Churned accounts
wc -l churn_records.csv
```

### Check Package Distribution
```bash
cut -d',' -f15 account_attributes_monthly.csv | sort | uniq -c
```

## Python Interactive Examples

### Generate and Explore
```python
from datetime import datetime
import function
import pandas as pd

# Configure
function.NUM_ENTERPRISE_ACCOUNTS = 100
function.MOST_RECENT_MONTH = datetime(2025, 10, 1)
# ... (set other config)

# Generate
account_df, usage_df, churn_df = function.generate_all_tables(
    non_active_ratio=0.05,
    num_months=36,
    save_to_csv=False  # Don't save, just explore
)

# Explore
print(account_df.head())
print(account_df['COMPANY'].value_counts())
print(usage_df.describe())
print(f"Churn rate: {len(churn_df) / account_df['SERVICE_ACCOUNT_ID'].nunique() * 100:.2f}%")
```

### View Specific Account
```python
account_id = 1000
account_info = account_df[account_df['SERVICE_ACCOUNT_ID'] == account_id]
usage_info = usage_df[usage_df['USERID'] == account_id]

print(account_info)
print(usage_info.describe())
```

### Analyze Churned Users
```python
churned_ids = churn_df['USERID'].values
churned_usage = usage_df[usage_df['USERID'].isin(churned_ids)]

print(f"Churned users: {len(churned_ids)}")
print(f"Avg usage before churn: {churned_usage['PHONE_TOTAL_CALLS'].mean():.0f} calls")
```

## Troubleshooting Quick Fixes

### "Configuration constants must be set"
```python
# Set ALL required configs:
function.COMPANIES = ['Company A']
function.BRANDS = [(1, 'Brand A')]
function.UBRANDS = [('U1', 'UBrand 1')]
function.PACKAGES = [(100, 'Package A', 'CAT-100', 'Catalog A')]
function.TIERS = [(1, 'Tier 1', 'Edition 1')]
function.OPCOS = ['OPCO-1']
```

### Files Too Large
```python
# Reduce these:
NUM_ACCOUNTS = 50  # instead of 1000
num_months = 12    # instead of 36
```

### Need Reproducible Results
```python
import random
import numpy as np

random.seed(42)
np.random.seed(42)

# Then generate data
```

### Memory Issues
```python
# Generate in batches or reduce:
NUM_ACCOUNTS = 100  # Smaller batch
save_to_csv = True  # Free memory after saving
```

## File Outputs Reference

| File | Contents | Typical Size (100 accounts) |
|------|----------|----------------------------|
| `account_attributes_monthly.csv` | Account attributes by month | ~100-200 KB |
| `phone_usage_data.csv` | Usage metrics by user/month | ~400-500 KB |
| `churn_records.csv` | Churned account records | ~1-5 KB |

## Next Steps After Generation

1. **Verify data**: Check CSV files are created
2. **Load to Snowflake**: Use `snowflake_loader.py`
3. **View dashboard**: Run `streamlit_app.py`
4. **Analyze patterns**: Use test functions

## Support

- Full manual: `DATA_GENERATION_MANUAL.md`
- Snowflake setup: `SNOWFLAKE_SETUP.md`
- Dashboard guide: `STREAMLIT_DASHBOARD.md`
