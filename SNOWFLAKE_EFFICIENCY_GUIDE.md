# Snowflake Efficiency Guide

This guide provides best practices and optimization strategies to reduce Snowflake costs and improve query performance.

## Table of Contents

1. [Query Optimization](#query-optimization)
2. [Table Optimization](#table-optimization)
3. [Warehouse Configuration](#warehouse-configuration)
4. [Data Loading Best Practices](#data-loading-best-practices)
5. [Cost Monitoring](#cost-monitoring)
6. [Common Patterns and Anti-Patterns](#common-patterns-and-anti-patterns)

---

## Query Optimization

### 1. Always Use WHERE Clauses

**❌ Bad:**
```sql
SELECT * FROM PHONE_USAGE_DATA;
```

**✅ Good:**
```sql
SELECT * FROM PHONE_USAGE_DATA 
WHERE MONTH >= '2024-01-01' AND MONTH <= '2024-12-31';
```

**Impact:** Reduces data scanned by 70-90% for date-filtered queries.

### 2. Select Specific Columns

**❌ Bad:**
```sql
SELECT * FROM ACCOUNT_ATTRIBUTES_MONTHLY;
```

**✅ Good:**
```sql
SELECT SERVICE_ACCOUNT_ID, COMPANY, PACKAGE_NAME, SA_ACCT_STATUS
FROM ACCOUNT_ATTRIBUTES_MONTHLY
WHERE MONTH >= '2024-01-01';
```

**Impact:** Reduces data transfer and improves query performance.

### 3. Use LIMIT for Exploratory Queries

**❌ Bad:**
```sql
SELECT * FROM PHONE_USAGE_DATA ORDER BY MONTH DESC;
```

**✅ Good:**
```sql
SELECT * FROM PHONE_USAGE_DATA 
ORDER BY MONTH DESC 
LIMIT 100;
```

**Impact:** Prevents accidentally scanning entire tables during exploration.

### 4. Leverage Materialized Views

**❌ Bad:**
```sql
-- Running this aggregation repeatedly
SELECT 
    USERID,
    MONTH,
    SUM(PHONE_TOTAL_CALLS) AS TOTAL_CALLS,
    AVG(PHONE_MAU) AS AVG_MAU
FROM PHONE_USAGE_DATA
GROUP BY USERID, MONTH;
```

**✅ Good:**
```sql
-- Use pre-computed materialized view
SELECT * FROM MV_MONTHLY_USAGE_BY_ACCOUNT
WHERE USERID = 12345;
```

**Impact:** 80-90% cost reduction for aggregated queries.

---

## Table Optimization

### 1. Add Clustering Keys

Clustering keys enable automatic micro-partition pruning, significantly improving query performance on filtered data.

**When to Use:**
- Tables with frequent filters on specific columns
- Large tables (>1GB)
- Queries that filter on date ranges or IDs

**Example:**
```sql
-- Add clustering key to optimize date/user filtered queries
ALTER TABLE PHONE_USAGE_DATA 
CLUSTER BY (USERID, MONTH);

ALTER TABLE ACCOUNT_ATTRIBUTES_MONTHLY 
CLUSTER BY (SERVICE_ACCOUNT_ID, MONTH);
```

**Impact:** 30-50% faster queries on filtered data.

**Monitoring:**
```sql
-- Check clustering depth (should be < 1.0)
SELECT SYSTEM$CLUSTERING_DEPTH('PHONE_USAGE_DATA');

-- Re-cluster if depth > 1.0
ALTER TABLE PHONE_USAGE_DATA RECLUSTER;
```

### 2. Use Materialized Views for Common Aggregations

Create materialized views for frequently accessed aggregations:

```sql
CREATE MATERIALIZED VIEW MV_MONTHLY_USAGE_BY_ACCOUNT AS
SELECT 
    USERID,
    MONTH,
    SUM(PHONE_TOTAL_CALLS) AS TOTAL_CALLS,
    AVG(PHONE_MAU) AS AVG_MAU
FROM PHONE_USAGE_DATA
GROUP BY USERID, MONTH;
```

**Benefits:**
- Pre-computed results eliminate redundant calculations
- 80-90% cost reduction for aggregated queries
- 30-50% faster dashboard load times

**Refresh:**
```sql
-- Refresh after bulk data loads
ALTER MATERIALIZED VIEW MV_MONTHLY_USAGE_BY_ACCOUNT REFRESH;
```

---

## Warehouse Configuration

### 1. Choose Appropriate Warehouse Size

**Warehouse Size Guide:**

| Size | Credits/Hour | Best For |
|------|--------------|----------|
| XSMALL | 1 | Dashboards, light workloads, development |
| SMALL | 2 | Medium workloads, regular analytics |
| MEDIUM | 4 | Heavy analytics, large data processing |
| LARGE | 8 | Very large datasets, production workloads |
| X-LARGE+ | 16+ | Enterprise-scale processing |

**Recommendation:** Start with XSMALL for dashboards and development. Scale up only when needed.

### 2. Optimize Auto-Suspend

**❌ Bad:**
```sql
CREATE WAREHOUSE MY_WH
WITH AUTO_SUSPEND = 300;  -- 5 minutes
```

**✅ Good:**
```sql
CREATE WAREHOUSE MY_WH
WITH AUTO_SUSPEND = 60;  -- 1 minute for dashboards
```

**Impact:** 20-30% reduction in idle costs.

**Guidelines:**
- **Dashboards/Streamlit apps:** 60 seconds
- **Scheduled jobs:** 300 seconds (5 minutes)
- **Development:** 60-120 seconds

### 3. Enable Auto-Resume

Always enable auto-resume for automatic warehouse startup:

```sql
CREATE WAREHOUSE MY_WH
WITH AUTO_SUSPEND = 60
AUTO_RESUME = TRUE;
```

---

## Data Loading Best Practices

### 1. Use Bulk Loading Methods

**✅ Good:**
```python
# Use write_pandas for bulk loading
from snowflake.connector.pandas_tools import write_pandas

success, nchunks, nrows, output = write_pandas(
    conn=conn,
    df=df,
    table_name='PHONE_USAGE_DATA',
    auto_create_table=False
)
```

**❌ Bad:**
```python
# Don't insert row by row
for row in df.iterrows():
    cursor.execute(f"INSERT INTO TABLE VALUES (...)")
```

### 2. Filter Data Before Loading to Python

**❌ Bad:**
```python
# Loading entire table
df = session.table("PHONE_USAGE_DATA").to_pandas()
filtered_df = df[df['MONTH'] >= '2024-01-01']
```

**✅ Good:**
```python
# Filter in Snowflake before loading
from snowflake.snowpark.functions import col, lit

df = session.table("PHONE_USAGE_DATA").filter(
    col("MONTH") >= lit('2024-01-01')
).to_pandas()
```

**Impact:** Reduces data transfer and memory usage.

### 3. Use Snowpark DataFrame Operations

When possible, use Snowpark DataFrame operations instead of converting to pandas:

```python
# Good: Operations in Snowflake
result = session.table("PHONE_USAGE_DATA").filter(
    col("MONTH") >= lit('2024-01-01')
).group_by("USERID").agg(
    sum(col("PHONE_TOTAL_CALLS")).alias("TOTAL_CALLS")
).to_pandas()
```

---

## Cost Monitoring

### 1. Monitor Query History

Use the query performance monitor script:

```bash
python monitor_query_performance.py --days 7
```

This will show:
- Most expensive queries
- Query patterns (SELECT *, no WHERE clauses, etc.)
- Warehouse usage and costs
- Table clustering status

### 2. Check Query History in Snowflake

```sql
-- Most expensive queries
SELECT 
    QUERY_ID,
    QUERY_TEXT,
    TOTAL_ELAPSED_TIME / 1000 AS ELAPSED_SECONDS,
    BYTES_SCANNED,
    PARTITIONS_SCANNED
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE START_TIME >= DATEADD(DAY, -7, CURRENT_TIMESTAMP())
ORDER BY BYTES_SCANNED DESC
LIMIT 20;
```

### 3. Monitor Warehouse Usage

```sql
-- Warehouse credit usage
SELECT 
    WAREHOUSE_NAME,
    SUM(CREDITS_USED) AS TOTAL_CREDITS,
    AVG(CREDITS_USED) AS AVG_CREDITS
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE START_TIME >= DATEADD(DAY, -7, CURRENT_TIMESTAMP())
GROUP BY WAREHOUSE_NAME
ORDER BY TOTAL_CREDITS DESC;
```

---

## Common Patterns and Anti-Patterns

### Anti-Pattern 1: Full Table Scans

**❌ Problem:**
```sql
SELECT * FROM PHONE_USAGE_DATA;
```

**✅ Solution:**
```sql
SELECT * FROM PHONE_USAGE_DATA 
WHERE MONTH >= '2024-01-01' AND MONTH <= '2024-12-31';
```

### Anti-Pattern 2: No Clustering Keys

**❌ Problem:**
Large tables without clustering keys on frequently filtered columns.

**✅ Solution:**
```sql
ALTER TABLE PHONE_USAGE_DATA CLUSTER BY (USERID, MONTH);
```

### Anti-Pattern 3: Repeated Aggregations

**❌ Problem:**
Running the same aggregation query multiple times.

**✅ Solution:**
Create a materialized view and query it instead.

### Anti-Pattern 4: Over-Sized Warehouses

**❌ Problem:**
Using LARGE warehouse for dashboard queries.

**✅ Solution:**
Use XSMALL or SMALL for dashboards. Scale up only when needed.

### Anti-Pattern 5: Long Auto-Suspend Times

**❌ Problem:**
Auto-suspend set to 300+ seconds for dashboards.

**✅ Solution:**
Set auto-suspend to 60 seconds for interactive workloads.

---

## Quick Reference Checklist

### Before Running Queries
- [ ] Added WHERE clauses to filter data
- [ ] Selected only needed columns (not SELECT *)
- [ ] Used LIMIT for exploratory queries
- [ ] Checked if materialized view exists for aggregation

### Table Setup
- [ ] Added clustering keys to frequently filtered columns
- [ ] Created materialized views for common aggregations
- [ ] Monitored clustering depth (should be < 1.0)

### Warehouse Configuration
- [ ] Chose appropriate warehouse size (start with XSMALL)
- [ ] Set auto-suspend to 60 seconds for dashboards
- [ ] Enabled auto-resume

### Monitoring
- [ ] Run query performance monitor weekly
- [ ] Check for expensive queries
- [ ] Monitor warehouse usage and costs
- [ ] Review query patterns for optimization opportunities

---

## Expected Impact

Following these best practices can result in:

- **50-70% reduction** in compute costs from query optimization
- **30-50% faster** queries with clustering keys
- **80-90% cost reduction** for aggregated queries using materialized views
- **20-30% reduction** in idle costs from warehouse tuning
- **40-60% faster** query execution times overall

---

## Tools and Scripts

This project includes several tools to help with optimization:

1. **`add_clustering_keys.py`** - Add clustering keys to tables
2. **`create_materialized_views.py`** - Create materialized views for common aggregations
3. **`monitor_query_performance.py`** - Monitor query costs and performance
4. **`setup_snowflake_infrastructure.py`** - Set up optimized warehouse configuration

---

## Additional Resources

- [Snowflake Query Performance Tuning](https://docs.snowflake.com/en/user-guide/query-performance-tuning)
- [Snowflake Clustering Keys](https://docs.snowflake.com/en/user-guide/tables-clustering-keys)
- [Snowflake Materialized Views](https://docs.snowflake.com/en/user-guide/views-materialized)
- [Snowflake Warehouse Best Practices](https://docs.snowflake.com/en/user-guide/warehouses-best-practices)

---

## Questions or Issues?

If you encounter issues or have questions about optimization:

1. Run `monitor_query_performance.py` to identify expensive queries
2. Check query history in Snowflake for patterns
3. Review this guide for relevant best practices
4. Consider adding clustering keys or materialized views if appropriate





