# Deploy to Snowflake Streamlit

This guide shows how to deploy the dashboard directly in Snowflake using Snowflake Streamlit (Streamlit in Snowflake).

## Benefits of Snowflake Streamlit

✅ **No local setup required** - Runs entirely in Snowflake
✅ **No credentials needed** - Uses Snowflake's built-in authentication
✅ **Direct data access** - No connection overhead
✅ **Share easily** - Just share the Snowflake URL
✅ **Secure** - All data stays in Snowflake

## Prerequisites

1. Snowflake account with **Streamlit enabled**
2. Data loaded in Snowflake (ACCOUNT_ATTRIBUTES_MONTHLY, PHONE_USAGE_DATA, CHURN_RECORDS)
3. Role with permissions to create Streamlit apps

## Deployment Steps

### Option 1: Create Streamlit App in Snowflake UI (Easiest)

#### Step 1: Log into Snowflake

Navigate to: https://app.snowflake.com/FOB96555/ehb83410/

#### Step 2: Navigate to Streamlit

1. Click **Streamlit** in the left sidebar
2. Click **+ Streamlit App** button

#### Step 3: Configure App

Fill in the form:
- **App name**: `Phone Usage Analytics`
- **Warehouse**: `MY_FIRST_WH`
- **App location**:
  - Database: `MY_DATABASE`
  - Schema: `PUBLIC`

**IMPORTANT:** Click **"Packages"** and add:
```
plotly
```

Click **Create**

#### Step 4: Copy the Code

1. Delete all default code in the editor
2. Copy the entire contents of `streamlit_app_snowflake.py`
3. Paste into the Snowflake Streamlit editor

#### Step 5: Run the App

Click **Run** button (top right)

The dashboard will start running in Snowflake!

### Option 2: Deploy via SQL Commands

#### Step 1: Create Stage (if not exists)

```sql
CREATE STAGE IF NOT EXISTS streamlit_stage;
```

#### Step 2: Upload File to Stage

Using SnowSQL command line:

```bash
snowsql -a FOB96555 -u ITSHTTP

PUT file:///path/to/streamlit_app_snowflake.py @streamlit_stage AUTO_COMPRESS=FALSE;
```

Or use the Snowflake UI:
1. Go to **Databases** → **MY_DATABASE** → **PUBLIC** → **Stages**
2. Create new stage or use existing
3. Upload `streamlit_app_snowflake.py`

#### Step 3: Create Streamlit App from Stage

```sql
CREATE STREAMLIT MY_DATABASE.PUBLIC.PHONE_USAGE_ANALYTICS
    ROOT_LOCATION = '@MY_DATABASE.PUBLIC.streamlit_stage'
    MAIN_FILE = 'streamlit_app_snowflake.py'
    QUERY_WAREHOUSE = MY_FIRST_WH;
```

#### Step 4: Grant Permissions

```sql
-- Grant access to other users (optional)
GRANT USAGE ON STREAMLIT MY_DATABASE.PUBLIC.PHONE_USAGE_ANALYTICS TO ROLE PUBLIC;
```

### Option 3: Copy-Paste Method (Quickest)

#### Step 1: Open File

Open `streamlit_app_snowflake.py` in any text editor

#### Step 2: Copy All Code

Select all and copy (Ctrl+A, Ctrl+C)

#### Step 3: Create App in Snowflake

1. Go to Snowflake UI → **Streamlit** → **+ Streamlit App**
2. Name: `Phone Usage Analytics`
3. Warehouse: `MY_FIRST_WH`
4. Location: `MY_DATABASE.PUBLIC`
5. **Click "Packages"** and add: `plotly`
6. Click **Create**

#### Step 4: Paste Code

1. Clear default code
2. Paste your copied code
3. Click **Run**

Done! 🎉

## Key Differences from Local Version

### 1. Connection Method

**Local version:**
```python
conn = snowflake.connector.connect(
    account=os.getenv('SNOWFLAKE_ACCOUNT'),
    ...
)
```

**Snowflake version:**
```python
df = st.connection("snowflake").query(query)
```

### 2. No Environment Variables

- ❌ No `.env` file needed
- ❌ No credentials in code
- ✅ Uses Snowflake's built-in session

### 3. Simplified Dependencies

Only needs:
- `streamlit` (built-in to Snowflake)
- `pandas` (built-in to Snowflake)
- `plotly` (may need to add in packages)

## Adding Plotly Dependency

If Plotly isn't available, you can specify packages:

### Method 1: In Snowflake UI

When creating the app, click **Packages** and add:
```
plotly
```

### Method 2: In Code

Add at the top of your file:
```python
# Snowflake will auto-install these
# /// script
# dependencies = ["plotly"]
# ///
```

## Accessing Your Dashboard

### Get the URL

After deployment, Snowflake provides a URL like:
```
https://app.snowflake.com/FOB96555/ehb83410/#/streamlit-apps/MY_DATABASE.PUBLIC.PHONE_USAGE_ANALYTICS
```

### Share with Team

1. Copy the Streamlit app URL
2. Share with team members who have Snowflake access
3. They can view instantly (no setup needed)

## Managing the App

### View Existing Apps

```sql
SHOW STREAMLIT IN SCHEMA MY_DATABASE.PUBLIC;
```

### Edit the App

1. Go to **Streamlit** in Snowflake UI
2. Find your app
3. Click to open
4. Edit code
5. Click **Run** to update

### Delete the App

```sql
DROP STREAMLIT MY_DATABASE.PUBLIC.PHONE_USAGE_ANALYTICS;
```

### Change Warehouse

```sql
ALTER STREAMLIT MY_DATABASE.PUBLIC.PHONE_USAGE_ANALYTICS
SET QUERY_WAREHOUSE = LARGER_WAREHOUSE;
```

## Permissions

### Grant Access to Roles

```sql
-- Allow specific role to use the app
GRANT USAGE ON STREAMLIT MY_DATABASE.PUBLIC.PHONE_USAGE_ANALYTICS
TO ROLE ANALYST_ROLE;

-- Allow role to view data
GRANT SELECT ON TABLE ACCOUNT_ATTRIBUTES_MONTHLY TO ROLE ANALYST_ROLE;
GRANT SELECT ON TABLE PHONE_USAGE_DATA TO ROLE ANALYST_ROLE;
GRANT SELECT ON TABLE CHURN_RECORDS TO ROLE ANALYST_ROLE;
```

### Remove Access

```sql
REVOKE USAGE ON STREAMLIT MY_DATABASE.PUBLIC.PHONE_USAGE_ANALYTICS
FROM ROLE ANALYST_ROLE;
```

## Customization

### Change Table Names

If your tables have different names, edit the queries:

```python
# Change this:
query = "SELECT * FROM ACCOUNT_ATTRIBUTES_MONTHLY"

# To this:
query = "SELECT * FROM YOUR_SCHEMA.YOUR_TABLE_NAME"
```

### Add Filters

Add more Snowflake-specific filters:

```python
# Example: Filter by user role
current_role = st.experimental_user.role
if current_role == 'MANAGER':
    query += " WHERE COMPANY IN ('Company A', 'Company B')"
```

### Performance Optimization

For large datasets, add WHERE clauses:

```python
query = """
    SELECT * FROM PHONE_USAGE_DATA
    WHERE MONTH >= DATEADD(month, -6, CURRENT_DATE())
"""
```

## Troubleshooting

### Error: "Table not found"

**Solution:** Check that tables exist in the current schema:
```sql
SELECT * FROM ACCOUNT_ATTRIBUTES_MONTHLY LIMIT 1;
```

### Error: "Permission denied"

**Solution:** Grant SELECT permissions:
```sql
GRANT SELECT ON ALL TABLES IN SCHEMA PUBLIC TO ROLE YOUR_ROLE;
```

### Error: "Warehouse not found"

**Solution:** Verify warehouse exists and is running:
```sql
SHOW WAREHOUSES;
ALTER WAREHOUSE MY_FIRST_WH RESUME;
```

### Slow Performance

**Solutions:**
1. Use a larger warehouse
2. Add date filters to queries
3. Increase cache TTL in code
4. Create materialized views for aggregations

### No Data Showing

**Check:**
1. Tables have data: `SELECT COUNT(*) FROM PHONE_USAGE_DATA;`
2. Current schema is correct: `SELECT CURRENT_SCHEMA();`
3. Role has permissions: `SHOW GRANTS TO ROLE YOUR_ROLE;`

## Cost Considerations

Snowflake Streamlit apps consume warehouse credits:

- **Idle**: Minimal cost (auto-suspends)
- **Active use**: Based on warehouse size
- **Tip**: Use smaller warehouse (X-Small) for dashboards

### Monitor Usage

```sql
-- Check Streamlit app query history
SELECT * FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY())
WHERE QUERY_TEXT LIKE '%PHONE_USAGE%'
ORDER BY START_TIME DESC
LIMIT 100;
```

## Best Practices

1. ✅ **Use small warehouse** - X-Small is usually sufficient
2. ✅ **Set auto-suspend** - Warehouse suspends when idle
3. ✅ **Add WHERE clauses** - Filter data in SQL, not Python
4. ✅ **Use caching** - `@st.cache_data` reduces queries
5. ✅ **Limit data** - Don't load entire tables if not needed

## Advanced Features

### Multi-page Apps

Create separate Python files for each page:

```
streamlit_app_snowflake.py (main)
pages/
  ├── 1_overview.py
  ├── 2_accounts.py
  └── 3_usage.py
```

### Scheduled Refreshes

Use Snowflake Tasks to refresh data:

```sql
CREATE TASK refresh_usage_data
  WAREHOUSE = MY_FIRST_WH
  SCHEDULE = 'USING CRON 0 2 * * * UTC'
AS
  -- Your data refresh logic here
  CALL refresh_phone_usage_data();
```

### Email Reports

Combine with Snowflake email notifications:

```sql
CREATE NOTIFICATION INTEGRATION email_integration
  TYPE=EMAIL
  ENABLED=TRUE;
```

## Support Resources

- **Snowflake Streamlit Docs**: [docs.snowflake.com/en/developer-guide/streamlit](https://docs.snowflake.com/en/developer-guide/streamlit)
- **Streamlit Docs**: [docs.streamlit.io](https://docs.streamlit.io)
- **Community**: [community.snowflake.com](https://community.snowflake.com)

## Summary

**To deploy in Snowflake:**

1. ✅ Use `streamlit_app_snowflake.py` (not the local version)
2. ✅ Create Streamlit app in Snowflake UI
3. ✅ Copy-paste the code
4. ✅ Click Run

**That's it!** Your dashboard is live in Snowflake! 🎉

No local setup, no credentials, no hassle - just copy, paste, and run!
