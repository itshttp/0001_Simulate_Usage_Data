# Vintage Analysis Guide

## Overview

The Vintage Analysis page provides cohort-based churn analysis by tracking accounts grouped by their signup month (vintage). This allows you to understand how different cohorts perform over time.

## Key Concepts

### Vintage (Cohort)
A vintage represents all accounts that signed up in the same month.
- Example: "2023-01" vintage = all accounts that first appeared in January 2023

### Tenure
Months since signup, starting at 0.
- Month 0 = Signup month
- Month 1 = First month after signup
- Month 12 = One year after signup

### Cumulative Churn Rate
Percentage of the original cohort that has churned by each tenure milestone.
- Starts at 0% at tenure 0
- Increases over time as accounts churn
- Allows comparison of cohort performance

## Features

### 1. Cohort Overview
- Total number of vintages
- Earliest and latest vintage dates
- Cohort size filtering (minimum accounts required)

### 2. Cumulative Churn Curves
**Main Chart**: Shows all vintages simultaneously
- X-axis: Tenure (months since signup, starting at 0)
- Y-axis: Cumulative churn rate (%)
- Each line represents one vintage cohort
- Newer vintages have shorter lines (less tenure data)

**Key Insight**: Compare how different vintages perform at the same tenure points

### 3. Vintage Comparison
- Select specific vintages to compare
- Filter noise by focusing on cohorts of interest
- Side-by-side performance analysis

### 4. Detailed Metrics
For each selected vintage, see:
- Total accounts in cohort
- Maximum tenure (months of data available)
- Final cumulative churn rate
- Total churned accounts

### 5. Milestone Analysis
Churn rates at key tenure points:
- 6 months
- 12 months (1 year)
- 24 months (2 years)
- 36 months (3 years)

Quickly compare cohorts at standardized intervals.

## How to Use

### Step 1: Access the Page
1. Open Streamlit dashboard
2. Select "📅 Vintage Analysis" from navigation

### Step 2: Configure Filters
**Minimum Cohort Size**:
- Default: 10 accounts
- Increase to focus on larger, more statistically significant cohorts
- Decrease to see smaller or newer cohorts

### Step 3: Interpret the Main Chart
**What to look for**:
- **Steep curves** = High churn, fast
- **Flat curves** = Low churn, stable cohort
- **Diverging lines** = Cohort performance varies over time
- **Parallel lines** = Consistent performance across cohorts

**Example Patterns**:
```
High Churn Cohort:     Low Churn Cohort:
    20%                     5%
    │  ╱                    │  ╱
    │ ╱                     │ ╱
    │╱                      │╱
    └────────              └────────
    0  12  24              0  12  24
```

### Step 4: Compare Specific Vintages
1. Use the multiselect to choose vintages
2. Compare early vs. recent cohorts
3. Identify trends (improving or worsening)

### Step 5: Review Milestone Data
Check the milestone table to answer questions like:
- "What's our typical 1-year churn rate?"
- "Are newer cohorts performing better than older ones?"
- "At what tenure does churn stabilize?"

## Use Cases

### 1. Product Improvements
**Question**: Did the Q2 2024 product update reduce churn?

**Analysis**:
- Compare vintages before June 2024 vs. after
- Look at 3-month and 6-month churn rates
- If newer vintages show lower churn at same tenure → improvement working

### 2. Seasonal Patterns
**Question**: Do accounts signed up in Q4 churn more than Q1 signups?

**Analysis**:
- Group vintages by quarter
- Compare December cohorts vs. March cohorts
- Identify if signup timing affects retention

### 3. Churn Prediction
**Question**: Based on historical cohorts, what churn rate should we expect for new accounts?

**Analysis**:
- Look at recent vintages (last 6-12 months)
- Check their 3-month and 6-month churn rates
- Use as baseline for projections

### 4. Cohort Maturity
**Question**: When does churn rate stabilize for a cohort?

**Analysis**:
- Look at mature cohorts (24+ months tenure)
- Find the tenure where curve flattens
- Typically churn slows after 12-18 months

## Data Requirements

The analysis uses:
- **Account data** (`ACCOUNT_ATTRIBUTES_MONTHLY`): Determines signup month
- **Churn data** (`CHURN_RECORDS`): Tracks churn dates

**Signup Month Determination**:
- First appearance of an account in `ACCOUNT_ATTRIBUTES_MONTHLY`
- Month with earliest date for each `SERVICE_ACCOUNT_ID`

**Churn Detection**:
- From `CHURN_RECORDS` table
- Mapped to tenure: months between signup and churn date

## Calculation Details

### Cumulative Churn Rate Formula
```
For Vintage V at Tenure T:

Cumulative Churn Rate = (Accounts Churned by Tenure T / Total Accounts in Vintage V) × 100
```

### Example
Vintage: 2023-01 (100 accounts signed up)

| Tenure | Churned by This Month | Cumulative Churn Rate |
|--------|----------------------|-----------------------|
| 0      | 0                    | 0%                    |
| 1      | 2                    | 2%                    |
| 3      | 5                    | 5%                    |
| 6      | 8                    | 8%                    |
| 12     | 12                   | 12%                   |

The curve shows: 0% → 2% → 5% → 8% → 12% over 12 months

## Tips for Analysis

### Best Practices

1. **Filter small cohorts**: Set minimum cohort size to 50+ for reliable patterns
2. **Compare apples to apples**: Look at same tenure points across cohorts
3. **Focus on recent cohorts**: Last 12 months for current performance
4. **Track trends**: Are newer vintages improving or declining?
5. **Combine with other metrics**: Cross-reference with usage data

### Common Pitfalls

❌ **Don't compare different tenure points**
- Wrong: "2023-01 at month 12 vs 2024-01 at month 3"
- Right: "2023-01 at month 3 vs 2024-01 at month 3"

❌ **Don't ignore cohort size**
- Small cohorts (<10 accounts) can be noisy
- Use minimum cohort size filter

❌ **Don't forget newer cohorts have less data**
- A 2-month old cohort can only show 0-2 months tenure
- Incomplete curves are normal for recent vintages

### Interpretation Examples

**Scenario 1: Improving Retention**
```
2023 vintages: 15% churn at 12 months
2024 vintages: 8% churn at 12 months
→ Retention is improving
```

**Scenario 2: Early Churn Problem**
```
All cohorts: Steep increase 0-3 months, then flattens
→ Onboarding issue, focus on first 90 days
```

**Scenario 3: Long-term Decay**
```
Steady linear increase over 24+ months
→ No stabilization, continuous attrition
→ Need long-term engagement initiatives
```

## Integration with Other Analyses

### With Usage Trends
- Identify if low-usage cohorts churn more
- Compare usage patterns of high-churn vs low-churn vintages

### With Segmentation
- Segment vintages by package type
- Compare churn curves for different tiers

### With Account Attributes
- Filter by company size, industry, region
- Identify which customer profiles have best retention

## Future Enhancements

Planned features:
- Revenue-weighted churn rates
- Vintage comparison tests (statistical significance)
- Cohort LTV projections
- Export cohort data for deeper analysis

---

## Quick Reference

| Element | What it Shows |
|---------|---------------|
| **X-axis (Tenure)** | Months since signup (0 = signup month) |
| **Y-axis** | Cumulative % of cohort that churned |
| **Each Line** | One vintage cohort |
| **Longer Lines** | Older cohorts with more tenure data |
| **Shorter Lines** | Newer cohorts with less tenure data |
| **Steep Slope** | High churn rate |
| **Flat Slope** | Low churn rate, stable |

## Support

For questions or feature requests:
- Review this guide
- Check FULL_REFRESH_GUIDE.md for data refresh
- See DATA_GENERATION_MANUAL.md for data setup
