# Streamlit Dashboard Guide

An interactive web-based analytics dashboard for visualizing and analyzing phone usage data stored in Snowflake.

## Features

### 📊 Overview Page
- **Key Metrics**: Total accounts, active accounts, churn rate, average usage
- **Usage Trends**: Interactive time series charts
- **Account Distribution**: Status breakdown pie chart
- **Company Analytics**: Average usage by company
- **User Activity**: Distribution histogram

### 👥 Account Analytics
- **Account Metrics**: Enterprise and service account counts
- **Brand Analysis**: Account distribution by brand
- **Package Distribution**: Accounts by package type
- **Growth Trends**: Account growth over time
- **Detailed Table**: Searchable account details

### 📈 Usage Trends
- **Aggregate Metrics**: Total calls, minutes, voice calls, MAU
- **Time Series**: Interactive charts with metric selection
- **Call Type Breakdown**: Inbound vs outbound analysis
- **Device Distribution**: Hardphone, softphone, mobile usage
- **Direction Analysis**: Call patterns by direction

### ⚠️ Churn Analysis
- **Churn Metrics**: Total churned users, churn rate
- **Churn Timeline**: Monthly churn visualization
- **Decline Patterns**: Usage decline before churn
- **Predictive Indicators**: 6-month pre-churn analysis
- **Churned User Details**: Complete churn records table

### 🎯 User Segmentation
- **Segment Distribution**: Heavy, medium, light users
- **Segment Metrics**: Count and percentage by segment
- **Usage Patterns**: Box plots and distributions
- **Trend Analysis**: Segment trends over time
- **Detailed Statistics**: Mean, median, std dev by segment

## Prerequisites

1. **Snowflake Data**: Ensure data is loaded (see [SNOWFLAKE_SETUP.md](SNOWFLAKE_SETUP.md))
2. **Environment**: Python 3.8+ with virtual environment
3. **Credentials**: `.env` file with Snowflake credentials

## Quick Start

### 1. Install Dependencies

```bash
# Activate your virtual environment
source venv/bin/activate

# Install Streamlit and Plotly (if not already installed)
pip install streamlit plotly
```

### 2. Verify Snowflake Connection

Make sure your `.env` file exists and has valid credentials:

```bash
# Test connection
python snowflake_loader.py --test
```

### 3. Run the Dashboard

```bash
streamlit run streamlit_app.py
```

The dashboard will open automatically in your browser at `http://localhost:8501`

## Dashboard Navigation

### Sidebar Controls

**Navigation Menu:**
- 🏠 Overview - High-level KPIs and trends
- 👥 Account Analytics - Account distribution and growth
- 📈 Usage Trends - Detailed usage metrics
- ⚠️ Churn Analysis - Churn patterns and predictions
- 🎯 User Segmentation - User behavior analysis

**Global Filters:**
- **Date Range**: Filter data by time period
- **Company**: Filter by specific company or view all

### Interactive Features

1. **Hover Tooltips**: Hover over charts for detailed values
2. **Zoom**: Click and drag to zoom into chart areas
3. **Pan**: Shift + click and drag to pan
4. **Reset**: Double-click to reset zoom
5. **Download**: Download charts as PNG (camera icon)

## Pages Detailed

### Overview Page

**Purpose**: Executive summary with key metrics and trends

**Key Visualizations:**
- Total accounts vs active accounts metrics
- Churn rate with percentage change
- Average usage per user per month
- Usage trend line chart
- Account status pie chart
- Company usage bar chart
- User activity histogram

**Use Cases:**
- Daily executive briefings
- Quick health checks
- Identifying anomalies

### Account Analytics Page

**Purpose**: Deep dive into account structure and growth

**Key Visualizations:**
- Enterprise vs service account metrics
- Brand distribution bar charts
- Package distribution bar charts
- Account growth time series
- Tier analysis
- Searchable account details table

**Use Cases:**
- Account planning
- Brand performance analysis
- Package adoption tracking
- Growth forecasting

### Usage Trends Page

**Purpose**: Analyze usage patterns and metrics over time

**Key Visualizations:**
- Metric selector for different usage types
- Time series with trend lines
- Inbound vs outbound call comparison
- Device type pie chart
- Voice vs fax breakdown

**Use Cases:**
- Usage forecasting
- Capacity planning
- Product adoption analysis
- Feature usage tracking

### Churn Analysis Page

**Purpose**: Understand churn patterns and predict future churn

**Key Visualizations:**
- Churn timeline bar chart
- Monthly churn rate
- 6-month pre-churn decline pattern
- Average usage before churn
- Churned user details table

**Use Cases:**
- Churn prediction
- Retention strategy planning
- Early warning identification
- Customer success interventions

**Key Insights:**
- Usage typically declines 6 months before churn
- Declining usage is a strong predictor
- Can identify at-risk accounts early

### User Segmentation Page

**Purpose**: Analyze user behavior by usage level

**Segments:**
- **Heavy Users**: >120 calls/month
- **Medium Users**: 50-120 calls/month
- **Light Users**: <50 calls/month

**Key Visualizations:**
- Segment distribution pie chart
- Box plots by segment
- Segment trends over time
- Detailed statistics table

**Use Cases:**
- Targeted marketing campaigns
- Feature development prioritization
- Support resource allocation
- Pricing strategy optimization

## Customization

### Change Segment Thresholds

Edit the `segment_user()` function in `streamlit_app.py`:

```python
def segment_user(avg_calls):
    if avg_calls > 150:  # Change from 120
        return 'Heavy'
    elif avg_calls >= 75:  # Change from 50
        return 'Medium'
    else:
        return 'Light'
```

### Add Custom Metrics

Add new metrics to any page by querying the DataFrames:

```python
# Example: Add new metric
custom_metric = usage_df['YOUR_COLUMN'].sum()
st.metric("Custom Metric", f"{custom_metric:,}")
```

### Modify Color Schemes

Colors are defined in the chart creation:

```python
# Example: Change color palette
color_discrete_map={'Heavy': '#YOUR_COLOR',
                    'Medium': '#YOUR_COLOR',
                    'Light': '#YOUR_COLOR'}
```

## Performance Optimization

### Data Caching

The dashboard uses `@st.cache_data` to cache Snowflake queries for 5 minutes:

```python
@st.cache_data(ttl=300)  # 5 minutes
def load_usage_data():
    # Query runs only once every 5 minutes
```

**To adjust cache time:**
```python
@st.cache_data(ttl=600)  # 10 minutes
@st.cache_data(ttl=60)   # 1 minute
```

### Clear Cache

If data changes in Snowflake, clear the cache:
1. Press `C` in the browser
2. Or use the menu: `☰ → Clear cache`

### Optimize Queries

For large datasets, add WHERE clauses to queries:

```python
# Example: Load only recent data
query = """
    SELECT * FROM PHONE_USAGE_DATA
    WHERE MONTH >= DATEADD(month, -6, CURRENT_DATE())
"""
```

## Deployment Options

### Option 1: Local Deployment

Run on your local machine:

```bash
streamlit run streamlit_app.py
```

Access at: `http://localhost:8501`

### Option 2: Streamlit Cloud

Deploy to Streamlit Cloud (free):

1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Add secrets (Snowflake credentials) in settings

### Option 3: Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501"]
```

Run:
```bash
docker build -t phone-usage-dashboard .
docker run -p 8501:8501 --env-file .env phone-usage-dashboard
```

### Option 4: Snowflake Streamlit

Deploy directly in Snowflake (requires Snowflake Streamlit feature):

1. Upload `streamlit_app.py` to Snowflake stage
2. Create Streamlit app in Snowflake UI
3. No need for `.env` file (uses Snowflake session)

## Troubleshooting

### Connection Errors

**Error**: "Failed to connect to Snowflake"

**Solutions:**
1. Check `.env` file exists and has correct credentials
2. Test connection: `python snowflake_loader.py --test`
3. Verify warehouse is running in Snowflake UI
4. Check network/firewall settings

### No Data Displayed

**Error**: "Unable to load data"

**Solutions:**
1. Verify data exists: `python snowflake_loader.py --summary`
2. Check table names match (case-sensitive)
3. Ensure user has SELECT permissions
4. Clear cache and refresh

### Slow Performance

**Symptoms**: Dashboard takes long to load

**Solutions:**
1. Reduce date range filter
2. Increase cache TTL
3. Optimize Snowflake queries
4. Use larger Snowflake warehouse
5. Add query filters

### Charts Not Rendering

**Solutions:**
1. Clear browser cache
2. Try different browser
3. Check browser console for errors
4. Verify Plotly is installed: `pip list | grep plotly`

## Advanced Features

### Export Data

Add export functionality to any page:

```python
# Example: Export to CSV
csv = df.to_csv(index=False)
st.download_button(
    label="Download CSV",
    data=csv,
    file_name="usage_data.csv",
    mime="text/csv"
)
```

### Add Alerts

Create threshold-based alerts:

```python
# Example: Churn rate alert
if churn_rate > 10:
    st.warning(f"⚠️ High churn rate: {churn_rate:.1f}%")
```

### Custom Date Filters

Add preset date ranges:

```python
preset = st.selectbox("Preset", ["Last 30 Days", "Last 90 Days", "YTD", "Custom"])
if preset == "Last 30 Days":
    start_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now()
```

## Security Best Practices

1. ✅ **Never commit `.env`** - Already in `.gitignore`
2. ✅ **Use Streamlit secrets** - For cloud deployment
3. ✅ **Restrict warehouse access** - Use read-only user
4. ✅ **Enable MFA** - On Snowflake account
5. ✅ **Monitor usage** - Check Snowflake credits

## Configuration File

Create `.streamlit/config.toml` for custom settings:

```toml
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"

[server]
port = 8501
enableCORS = false
enableXsrfProtection = true
```

## Support

For issues:
- **Dashboard bugs**: Check `streamlit_app.py` code
- **Data issues**: Check Snowflake tables
- **Connection issues**: See [SNOWFLAKE_SETUP.md](SNOWFLAKE_SETUP.md)
- **Streamlit docs**: [docs.streamlit.io](https://docs.streamlit.io)

## Next Steps

Once your dashboard is running:
1. Share with stakeholders
2. Set up scheduled data refreshes
3. Add custom metrics for your use case
4. Deploy to production
5. Create alerts and notifications
6. Integrate with other tools (Slack, email, etc.)

Happy analyzing! 📊
