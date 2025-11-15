# Account Usage Analytics Dashboard

An interactive Streamlit dashboard for analyzing individual account usage patterns with AI-powered insights using Snowflake Cortex.

## Features

### 📊 Core Functionality
- **Account Selection**: Search and select accounts by ID or company name
- **3x3 Grid Layout**: 9 key usage metrics displayed in an organized grid
- **Time Series Analysis**: Track metrics over time (month by month)
- **AI-Powered Insights**: Get automated insights for each metric using Snowflake Cortex

### 📈 9 Key Usage Metrics
1. **Total Calls**: Overall call volume
2. **Total Minutes**: Total usage time
3. **Voice Calls**: Voice communication volume
4. **Voice Minutes**: Voice usage duration
5. **Inbound Calls**: Incoming call volume
6. **Outbound Calls**: Outgoing call volume
7. **Monthly Active Users**: User engagement metric
8. **Hardphone Calls**: Desk phone usage
9. **Softphone Calls**: Software phone usage

### 🤖 AI Features
- **Quick Insights**: Get automatic analysis of trends and patterns
- **Custom Questions**: Ask specific questions about any metric
- **Data Summary**: View statistical overview for each metric

## Setup

### 1. Install Dependencies
```bash
pip install streamlit altair pandas
```

### 2. Configure Snowflake Connection
Create `.streamlit/secrets.toml` with your Snowflake credentials:
```toml
[connections.snowflake]
account = "your-account-identifier"
user = "your-username"
password = "your-password"
warehouse = "YOUR_WAREHOUSE"
database = "YOUR_DATABASE"
schema = "PUBLIC"
role = "ACCOUNTADMIN"
```

See `.streamlit/secrets.toml.example` for a template.

### 3. Run the Dashboard
```bash
streamlit run account_usage_dashboard.py
```

The dashboard will open in your browser at `http://localhost:8501`

## Usage Guide

### Selecting an Account
1. **Search**: Type an account ID or company name in the search box
2. **Select**: Choose an account from the filtered dropdown list
3. **View Details**: Account information appears in the sidebar

### Viewing Metrics
- Each metric is displayed as a time series chart
- Hover over charts to see detailed values
- Charts show trends from earliest to latest month

### Using AI Insights

#### Quick Insights
1. Expand the "🤖 AI Insights" section below any chart
2. Click "📊 Get Quick Insights"
3. View automated analysis of trends and patterns

#### Custom Questions
1. Expand the "🤖 AI Insights" section
2. Type your question in the text box
3. Click "❓ Ask Question"
4. Get AI-powered answers based on the data

#### Example Questions
- "Why is this metric trending upward?"
- "What's causing the spike in March?"
- "Is this usage pattern normal?"
- "How does this compare to average?"

## Data Requirements

The dashboard expects the following Snowflake tables:

### ACCOUNT_ATTRIBUTES_MONTHLY
- `SERVICE_ACCOUNT_ID`: Account identifier
- `COMPANY`: Company name
- `SA_BRAND_NAME`: Brand information
- `PACKAGE_NAME`: Package details
- `TIER_NAME`: Service tier
- `SA_ACCT_STATUS`: Account status

### PHONE_USAGE_DATA
- `USERID`: Links to SERVICE_ACCOUNT_ID
- `MONTH`: Date field (YYYY-MM-DD)
- `PHONE_TOTAL_CALLS`: Total calls
- `PHONE_TOTAL_MINUTES_OF_USE`: Total minutes
- `VOICE_CALLS`: Voice calls
- `VOICE_MINS`: Voice minutes
- `PHONE_TOTAL_NUM_INBOUND_CALLS`: Inbound calls
- `PHONE_TOTAL_NUM_OUTBOUND_CALLS`: Outbound calls
- `PHONE_MAU`: Monthly active users
- `HARDPHONE_CALLS`: Hardphone calls
- `SOFTPHONE_CALLS`: Softphone calls

## Snowflake Cortex Requirements

For AI features to work:
- Snowflake Cortex must be enabled in your account
- The `SNOWFLAKE.CORTEX.COMPLETE()` function must be available
- Sufficient compute resources for LLM inference

If Cortex is not available, the dashboard will display a warning and disable AI features.

## Performance Optimization

### Caching
- Account data cached for 10 minutes
- Usage data cached per account for 10 minutes
- Reduces query load on Snowflake

### Tips
- Use the search function to quickly find accounts
- AI insights may take a few seconds to generate
- Expand only the insights you need to minimize API calls

## Troubleshooting

### "No account data available"
- Check Snowflake connection in `secrets.toml`
- Verify tables exist in your database
- Ensure proper permissions

### "Cortex AI is not available"
- Contact your Snowflake admin to enable Cortex
- Dashboard will work without AI features
- Charts and data will still be displayed

### Charts not displaying
- Check that usage data exists for the selected account
- Verify `MONTH` field is in correct date format
- Ensure numeric fields contain valid values

## File Structure

```
.
├── account_usage_dashboard.py          # Main dashboard application
├── .streamlit/
│   ├── secrets.toml                    # Your credentials (not in git)
│   └── secrets.toml.example            # Template for credentials
└── ACCOUNT_DASHBOARD_README.md         # This file
```

## Security Notes

⚠️ **Important**: Never commit `secrets.toml` to version control!

- The file is already in `.gitignore`
- Use environment-specific configurations
- Rotate credentials regularly

## Support

For issues or questions:
1. Check this README
2. Review Snowflake connection settings
3. Verify data availability
4. Check Streamlit logs for errors

---

**Built with**: Streamlit, Altair, Snowflake Cortex AI

**Last Updated**: 2025-01-14
