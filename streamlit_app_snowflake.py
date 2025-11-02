"""
Phone Usage Analytics Dashboard - Snowflake Streamlit Version

A Streamlit dashboard for analyzing phone usage data, churn patterns,
and account metrics. This version is designed to run in Snowflake Streamlit.

Deploy this app in Snowflake Streamlit - no local setup needed!
"""

# Add required packages for Snowflake Streamlit
# snowflake:requirements
# snowflake:end

import streamlit as st
import pandas as pd

# Note: snowflake.cortex Python module is not available in Snowflake Streamlit
# We'll use SQL-based Cortex calls instead
CORTEX_AVAILABLE = False  # Python API not available in Streamlit
CORTEX_SQL_AVAILABLE = None  # Will check via SQL query

# Page configuration
st.set_page_config(
    page_title="Phone Usage Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_account_data():
    """Load account data from Snowflake."""
    query = "SELECT * FROM ACCOUNT_ATTRIBUTES_MONTHLY"
    df = st.connection("snowflake").query(query)
    df['MONTH'] = pd.to_datetime(df['MONTH'])
    return df


@st.cache_data(ttl=300)
def load_usage_data():
    """Load usage data from Snowflake."""
    query = "SELECT * FROM PHONE_USAGE_DATA"
    df = st.connection("snowflake").query(query)
    df['MONTH'] = pd.to_datetime(df['MONTH'])
    return df


@st.cache_data(ttl=300)
def load_churn_data():
    """Load churn data from Snowflake."""
    query = "SELECT * FROM CHURN_RECORDS"
    df = st.connection("snowflake").query(query)
    df['CHURN_DATE'] = pd.to_datetime(df['CHURN_DATE'])
    return df


def prepare_account_context(selected_account, latest_account, usage_data_sorted, avg_calls, avg_minutes):
    """Prepare account context summary for AI analysis."""
    # Calculate trends
    total_calls = usage_data_sorted['PHONE_TOTAL_CALLS'].tolist()
    total_minutes = usage_data_sorted['PHONE_TOTAL_MINUTES_OF_USE'].tolist()
    months = usage_data_sorted['MONTH'].tolist()
    
    # Calculate growth rate
    if len(total_calls) > 1:
        growth_rate = ((total_calls[-1] - total_calls[0]) / total_calls[0] * 100) if total_calls[0] > 0 else 0
    else:
        growth_rate = 0
    
    # Find peak and lowest months
    max_calls_idx = total_calls.index(max(total_calls))
    min_calls_idx = total_calls.index(min(total_calls))
    
    # Device usage breakdown
    hardphone = usage_data_sorted['HARDPHONE_CALLS'].sum()
    softphone = usage_data_sorted['SOFTPHONE_CALLS'].sum()
    mobile = usage_data_sorted['MOBILE_CALLS'].sum()
    
    context = f"""
Account: {selected_account}
Company: {latest_account['COMPANY']}
Package: {latest_account['PACKAGE_NAME']}
Status: {latest_account['SA_ACCT_STATUS']}
Brand: {latest_account['SA_BRAND_NAME']}

Usage Summary:
- Average Calls per Month: {avg_calls:.0f}
- Average Minutes per Month: {avg_minutes:.0f}
- Total Months of Data: {len(usage_data_sorted)}
- Growth Rate: {growth_rate:.1f}%
- Peak Usage Month: {months[max_calls_idx].strftime('%Y-%m')} ({total_calls[max_calls_idx]:.0f} calls)
- Lowest Usage Month: {months[min_calls_idx].strftime('%Y-%m')} ({total_calls[min_calls_idx]:.0f} calls)

Device Usage Breakdown:
- Hardphone Calls: {hardphone:.0f}
- Softphone Calls: {softphone:.0f}
- Mobile Calls: {mobile:.0f}
"""
    return context


def get_available_llm_models():
    """Get list of available LLM models from Snowflake Cortex.

    Returns tuple: (models_list, source_type)
    - source_type: 'sql' if from SQL query, 'fallback' if from hardcoded list
    """
    global CORTEX_SQL_AVAILABLE

    # Try querying Snowflake Cortex via SQL
    # This is the correct approach for Snowflake Streamlit
    if CORTEX_SQL_AVAILABLE is None:  # Only check once
        try:
            conn = st.connection("snowflake")
            # Try to get models using SQL
            models_df = conn.query(
                """
                SELECT model_name
                FROM TABLE(INFORMATION_SCHEMA.CORTEX_AI_MODELS())
                ORDER BY model_name
                """
            )
            if not models_df.empty and 'MODEL_NAME' in models_df.columns:
                CORTEX_SQL_AVAILABLE = True
                return models_df['MODEL_NAME'].tolist(), 'sql'
            else:
                CORTEX_SQL_AVAILABLE = False
        except Exception as e:
            CORTEX_SQL_AVAILABLE = False
    elif CORTEX_SQL_AVAILABLE:
        # SQL worked before, try again
        try:
            conn = st.connection("snowflake")
            models_df = conn.query(
                """
                SELECT model_name
                FROM TABLE(INFORMATION_SCHEMA.CORTEX_AI_MODELS())
                ORDER BY model_name
                """
            )
            if not models_df.empty and 'MODEL_NAME' in models_df.columns:
                return models_df['MODEL_NAME'].tolist(), 'sql'
        except Exception:
            pass

    # Fallback: Return a comprehensive list of known Snowflake Cortex models
    # This ensures the dashboard works even if SQL queries are not available
    fallback_models = [
        # Snowflake Arctic
        "snowflake-arctic",

        # Mistral models
        "mistral-large",
        "mistral-large2",
        "mistral-7b",
        "mixtral-8x7b",

        # Llama models
        "llama3-8b",
        "llama3-70b",
        "llama3.1-8b",
        "llama3.1-70b",
        "llama3.1-405b",
        "llama3.2-1b",
        "llama3.2-3b",

        # Gemma models
        "gemma-7b",

        # Reka models
        "reka-core",
        "reka-flash",

        # Claude models (if available in your account)
        "claude-3-5-sonnet",
        "claude-3-haiku",
        "claude-3-sonnet",
    ]

    return fallback_models, 'fallback'


def estimate_tokens(text):
    """Estimate token count from text. Rough approximation: 1 token ~= 4 characters."""
    return len(text) // 4

def generate_ai_insights(llm_provider, user_prompt, account_context):
    """Generate AI insights based on account data using Snowflake Cortex AI.
    Returns: (insights_text, input_tokens, output_tokens)
    """
    # Calculate input tokens (prompt + context)
    full_prompt = f"{user_prompt}\n\nAccount Context:\n{account_context}"
    input_tokens = estimate_tokens(full_prompt)

    try:
        # Use Snowflake Cortex AI via SQL
        conn = st.connection("snowflake")

        # Escape single quotes in the prompt for SQL
        escaped_prompt = full_prompt.replace("'", "''")

        # Call Snowflake Cortex Complete function
        query = f"""
        SELECT SNOWFLAKE.CORTEX.COMPLETE(
            '{llm_provider}',
            '{escaped_prompt}'
        ) AS response
        """

        result = conn.query(query)

        if not result.empty and 'RESPONSE' in result.columns:
            insights = result['RESPONSE'].iloc[0]

            # Calculate output tokens
            output_tokens = estimate_tokens(insights)

            return insights, input_tokens, output_tokens
        else:
            # No response from Cortex
            raise Exception("No response from Cortex AI")

    except Exception as e:
        # Fallback to template-based response if Cortex call fails
        error_msg = str(e)

        # Parse account context for template
        context_lines = account_context.split('\n')
        avg_calls_line = [line for line in context_lines if 'Average Calls per Month' in line]
        growth_line = [line for line in context_lines if 'Growth Rate' in line]

        avg_calls = avg_calls_line[0].split(':')[1].strip().split()[0] if avg_calls_line else "N/A"
        growth_rate_str = growth_line[0].split(':')[1].strip() if growth_line else "0.0%"

        try:
            growth_rate_num = float(growth_rate_str.replace('%', '').strip())
        except:
            growth_rate_num = 0.0

        insights = f"""
**Analysis (Template Mode - Cortex AI unavailable)**

⚠️ **Note:** Could not connect to Snowflake Cortex AI. Error: {error_msg}

**User Question:** {user_prompt}

**Account Summary:**
{account_context}

**Basic Analysis:**

Based on the available data:

**Usage Pattern:**
The account shows an average of {avg_calls} calls per month with a growth rate of {growth_rate_str}.
This indicates {'stable usage' if abs(growth_rate_num) <= 5 else 'changing usage patterns'}.

**Recommendations:**
1. Monitor usage trends for significant changes
2. Review account health indicators regularly
3. Consider engagement opportunities based on usage patterns

---
*Note: This is a template-based analysis. For AI-powered insights, ensure Snowflake Cortex AI is enabled and accessible.*
*To enable Cortex, contact your Snowflake administrator or check: https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-llms*
"""

        output_tokens = estimate_tokens(insights)
        return insights, input_tokens, output_tokens


def main():
    """Main dashboard application."""

    # Sidebar
    st.sidebar.title("📊 Phone Usage Analytics")
    st.sidebar.markdown("---")

    # Page selection
    page = st.sidebar.radio(
        "Navigation",
        ["🏠 Overview", "👥 Account Analytics", "📈 Usage Trends",
         "⚠️ Churn Analysis", "🎯 User Segmentation", "📅 Vintage Analysis", "🔍 Account Lookup"]
    )

    # Load data
    with st.spinner("Loading data from Snowflake..."):
        try:
            account_df = load_account_data()
            usage_df = load_usage_data()
            churn_df = load_churn_data()
        except Exception as e:
            st.error(f"Unable to load data: {e}")
            st.info("Please ensure the tables ACCOUNT_ATTRIBUTES_MONTHLY, PHONE_USAGE_DATA, and CHURN_RECORDS exist in your current schema.")
            return

    if account_df.empty or usage_df.empty:
        st.error("No data found in tables. Please load data first.")
        return

    # Sidebar filters
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filters")

    # Date range filter
    min_date = usage_df['MONTH'].min()
    max_date = usage_df['MONTH'].max()

    date_range = st.sidebar.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    # Filter data by date range
    if len(date_range) == 2:
        start_date, end_date = date_range
        usage_df = usage_df[
            (usage_df['MONTH'] >= pd.to_datetime(start_date)) &
            (usage_df['MONTH'] <= pd.to_datetime(end_date))
        ]
        account_df = account_df[
            (account_df['MONTH'] >= pd.to_datetime(start_date)) &
            (account_df['MONTH'] <= pd.to_datetime(end_date))
        ]

    # Company filter
    companies = ['All'] + sorted(account_df['COMPANY'].unique().tolist())
    selected_company = st.sidebar.selectbox("Company", companies)

    if selected_company != 'All':
        account_df = account_df[account_df['COMPANY'] == selected_company]
        user_ids = account_df['SERVICE_ACCOUNT_ID'].unique()
        usage_df = usage_df[usage_df['USERID'].isin(user_ids)]

    # Render selected page
    if page == "🏠 Overview":
        show_overview(account_df, usage_df, churn_df)
    elif page == "👥 Account Analytics":
        show_account_analytics(account_df)
    elif page == "📈 Usage Trends":
        show_usage_trends(usage_df)
    elif page == "⚠️ Churn Analysis":
        show_churn_analysis(usage_df, churn_df)
    elif page == "🎯 User Segmentation":
        show_user_segmentation(usage_df)
    elif page == "📅 Vintage Analysis":
        show_vintage_analysis(account_df, churn_df)
    elif page == "🔍 Account Lookup":
        show_account_lookup(account_df, usage_df, churn_df)


def show_overview(account_df, usage_df, churn_df):
    """Overview page with key metrics."""
    st.title("📊 Dashboard Overview")

    # KPI Metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_accounts = account_df['SERVICE_ACCOUNT_ID'].nunique()
        st.metric("Total Accounts", f"{total_accounts:,}")

    with col2:
        active_accounts = account_df[account_df['SA_ACCT_STATUS'] == 'Active']['SERVICE_ACCOUNT_ID'].nunique()
        st.metric("Active Accounts", f"{active_accounts:,}")

    with col3:
        total_churned = len(churn_df) if not churn_df.empty else 0
        churn_rate = (total_churned / total_accounts * 100) if total_accounts > 0 else 0
        st.metric("Churned Accounts", f"{total_churned:,}", f"{churn_rate:.1f}%")

    with col4:
        avg_calls = usage_df['PHONE_TOTAL_CALLS'].mean()
        st.metric("Avg Calls/User/Month", f"{avg_calls:.0f}")

    st.markdown("---")

    # Two columns for charts
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Usage Trends Over Time")

        # Aggregate usage by month
        monthly_usage = usage_df.groupby('MONTH').agg({
            'PHONE_TOTAL_CALLS': 'mean',
            'PHONE_TOTAL_MINUTES_OF_USE': 'mean'
        }).reset_index()

        # Use Streamlit line chart
        st.line_chart(
            monthly_usage,
            x='MONTH',
            y='PHONE_TOTAL_CALLS',
            height=400
        )

    with col2:
        st.subheader("Account Status Distribution")

        # Get latest status for each account
        latest_accounts = account_df.sort_values('MONTH').groupby('SERVICE_ACCOUNT_ID').last()
        status_counts = latest_accounts['SA_ACCT_STATUS'].value_counts()
        
        # Create dataframe for display
        status_df = pd.DataFrame({
            'Status': status_counts.index,
            'Count': status_counts.values
        })
        
        # Use Streamlit bar chart for distribution
        st.bar_chart(status_df, x='Status', y='Count', height=400)

    # Usage distribution
    st.markdown("---")
    st.subheader("Usage Distribution Analysis")

    col1, col2 = st.columns(2)

    with col1:
        # Average usage by company
        company_usage = usage_df.merge(
            account_df[['SERVICE_ACCOUNT_ID', 'COMPANY', 'MONTH']],
            left_on=['USERID', 'MONTH'],
            right_on=['SERVICE_ACCOUNT_ID', 'MONTH'],
            how='left'
        )

        company_avg = company_usage.groupby('COMPANY')['PHONE_TOTAL_CALLS'].mean().sort_values(ascending=False)
        company_df = pd.DataFrame({
            'Company': company_avg.index,
            'Avg Calls per Month': company_avg.values
        })

        st.bar_chart(company_df.set_index('Company'), height=400)

    with col2:
        st.subheader("User Activity Distribution")
        # User activity distribution table
        user_avg = usage_df.groupby('USERID')['PHONE_TOTAL_CALLS'].mean()
        
        # Create bins for histogram effect
        bins = pd.cut(user_avg, bins=10)
        bin_counts = bins.value_counts().sort_index()
        
        bin_df = pd.DataFrame({
            'Avg Calls Range': bin_counts.index.astype(str),
            'Number of Users': bin_counts.values
        })
        
        st.bar_chart(bin_df.set_index('Avg Calls Range'), height=400)


def show_account_analytics(account_df):
    """Account analytics page."""
    st.title("👥 Account Analytics")

    # Account metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        total_enterprises = account_df['ENTERPRISE_ACCOUNT_ID'].nunique()
        st.metric("Total Enterprise Accounts", f"{total_enterprises:,}")

    with col2:
        total_services = account_df['SERVICE_ACCOUNT_ID'].nunique()
        st.metric("Total Service Accounts", f"{total_services:,}")

    with col3:
        avg_per_enterprise = total_services / total_enterprises if total_enterprises > 0 else 0
        st.metric("Avg Service Accounts per Enterprise", f"{avg_per_enterprise:.1f}")

    st.markdown("---")

    # Two columns
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Accounts by Brand")

        latest = account_df.sort_values('MONTH').groupby('SERVICE_ACCOUNT_ID').last()
        brand_counts = latest['SA_BRAND_NAME'].value_counts()
        
        brand_df = pd.DataFrame({
            'Brand': brand_counts.index,
            'Number of Accounts': brand_counts.values
        })

        st.bar_chart(brand_df.set_index('Brand'), height=400)

    with col2:
        st.subheader("Accounts by Package")

        package_counts = latest['PACKAGE_NAME'].value_counts()
        
        package_df = pd.DataFrame({
            'Package': package_counts.index,
            'Number of Accounts': package_counts.values
        })

        st.bar_chart(package_df.set_index('Package'), height=400)

    # Account growth over time
    st.markdown("---")
    st.subheader("Account Growth Over Time")

    # Count active accounts per month
    active_by_month = account_df[account_df['SA_ACCT_STATUS'] == 'Active'].groupby('MONTH')['SERVICE_ACCOUNT_ID'].nunique().reset_index()
    active_by_month.columns = ['MONTH', 'Active Accounts']

    st.line_chart(active_by_month.set_index('MONTH'), height=400)

    # Data table
    st.markdown("---")
    st.subheader("Account Details")

    # Show latest status for each account
    display_df = latest[['COMPANY', 'SA_BRAND_NAME', 'PACKAGE_NAME',
                         'TIER_NAME', 'SA_ACCT_STATUS']].reset_index()
    display_df.columns = ['Account ID', 'Company', 'Brand', 'Package', 'Tier', 'Status']

    st.dataframe(display_df, use_container_width=True, height=400)


def show_usage_trends(usage_df):
    """Usage trends analysis page."""
    st.title("📈 Usage Trends")

    # Aggregate metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_calls = usage_df['PHONE_TOTAL_CALLS'].sum()
        st.metric("Total Calls", f"{total_calls:,}")

    with col2:
        total_minutes = usage_df['PHONE_TOTAL_MINUTES_OF_USE'].sum()
        st.metric("Total Minutes", f"{total_minutes:,.0f}")

    with col3:
        avg_voice_calls = usage_df['VOICE_CALLS'].mean()
        st.metric("Avg Voice Calls", f"{avg_voice_calls:.0f}")

    with col4:
        avg_mau = usage_df['PHONE_MAU'].mean()
        st.metric("Avg Phone MAU", f"{avg_mau:.0f}")

    st.markdown("---")

    # Time series chart
    st.subheader("Usage Metrics Over Time")

    monthly_agg = usage_df.groupby('MONTH').agg({
        'PHONE_TOTAL_CALLS': 'mean',
        'PHONE_TOTAL_MINUTES_OF_USE': 'mean',
        'VOICE_CALLS': 'mean',
        'FAX_CALLS': 'mean'
    }).reset_index()

    # Metric selector
    metric = st.selectbox(
        "Select Metric",
        ['PHONE_TOTAL_CALLS', 'PHONE_TOTAL_MINUTES_OF_USE', 'VOICE_CALLS', 'FAX_CALLS']
    )

    metric_labels = {
        'PHONE_TOTAL_CALLS': 'Average Total Calls',
        'PHONE_TOTAL_MINUTES_OF_USE': 'Average Total Minutes',
        'VOICE_CALLS': 'Average Voice Calls',
        'FAX_CALLS': 'Average Fax Calls'
    }

    # Create chart data
    chart_data = pd.DataFrame({
        'MONTH': monthly_agg['MONTH'],
        metric_labels[metric]: monthly_agg[metric]
    })

    st.line_chart(chart_data.set_index('MONTH'), height=500)

    # Multiple metrics comparison
    st.markdown("---")
    st.subheader("Call Type Breakdown")

    col1, col2 = st.columns(2)

    with col1:
        # Inbound vs Outbound
        monthly_direction = usage_df.groupby('MONTH').agg({
            'PHONE_TOTAL_NUM_INBOUND_CALLS': 'mean',
            'PHONE_TOTAL_NUM_OUTBOUND_CALLS': 'mean'
        }).reset_index()
        
        direction_chart = pd.DataFrame({
            'MONTH': monthly_direction['MONTH'],
            'Inbound': monthly_direction['PHONE_TOTAL_NUM_INBOUND_CALLS'],
            'Outbound': monthly_direction['PHONE_TOTAL_NUM_OUTBOUND_CALLS']
        })

        st.line_chart(direction_chart.set_index('MONTH'), height=400)

    with col2:
        st.subheader("Calls by Device Type")
        # Device type distribution
        device_totals = {
            'Hardphone': usage_df['HARDPHONE_CALLS'].sum(),
            'Softphone': usage_df['SOFTPHONE_CALLS'].sum(),
            'Mobile': usage_df['MOBILE_CALLS'].sum()
        }
        
        device_df = pd.DataFrame({
            'Device Type': device_totals.keys(),
            'Total Calls': device_totals.values()
        })
        
        # Calculate percentages
        total_device_calls = device_df['Total Calls'].sum()
        device_df['Percentage'] = (device_df['Total Calls'] / total_device_calls * 100).round(1)
        
        st.dataframe(device_df, use_container_width=True, height=200)
        
        # Also show as bar chart
        st.bar_chart(device_df.set_index('Device Type')['Total Calls'], height=150)


def show_churn_analysis(usage_df, churn_df):
    """Churn analysis page."""
    st.title("⚠️ Churn Analysis")

    if churn_df.empty:
        st.warning("No churn data available.")
        return

    # Churn metrics
    col1, col2, col3, col4 = st.columns(4)

    total_users = usage_df['USERID'].nunique()
    total_churned = len(churn_df)
    churn_rate = (total_churned / total_users * 100) if total_users > 0 else 0

    with col1:
        st.metric("Total Churned", f"{total_churned:,}")

    with col2:
        st.metric("Churn Rate", f"{churn_rate:.2f}%")

    with col3:
        st.metric("Active Users", f"{total_users - total_churned:,}")

    with col4:
        # Average time to churn
        if not churn_df.empty:
            avg_months = len(usage_df['MONTH'].unique())
            st.metric("Observation Period", f"{avg_months} months")

    st.markdown("---")

    # Churn timeline
    st.subheader("Churn Timeline")

    churn_by_month = churn_df.groupby(churn_df['CHURN_DATE'].dt.to_period('M')).size().reset_index()
    churn_by_month.columns = ['Month', 'Churned Users']
    churn_by_month['Month'] = churn_by_month['Month'].astype(str)

    st.bar_chart(churn_by_month.set_index('Month'), height=400)

    # Usage decline before churn
    st.markdown("---")
    st.subheader("Usage Decline Before Churn")

    # Analyze usage patterns for churned users
    churned_users = churn_df['USERID'].unique()
    churned_usage = usage_df[usage_df['USERID'].isin(churned_users)]

    # Merge with churn dates
    churned_usage = churned_usage.merge(churn_df[['USERID', 'CHURN_DATE']], on='USERID')

    # Calculate months before churn
    churned_usage['MONTHS_BEFORE_CHURN'] = (
        (churned_usage['CHURN_DATE'].dt.year - churned_usage['MONTH'].dt.year) * 12 +
        (churned_usage['CHURN_DATE'].dt.month - churned_usage['MONTH'].dt.month)
    )

    # Filter to 6 months before churn
    churned_usage = churned_usage[
        (churned_usage['MONTHS_BEFORE_CHURN'] >= -6) &
        (churned_usage['MONTHS_BEFORE_CHURN'] <= 0)
    ]

    # Aggregate by months before churn
    decline_pattern = churned_usage.groupby('MONTHS_BEFORE_CHURN').agg({
        'PHONE_TOTAL_CALLS': 'mean',
        'PHONE_TOTAL_MINUTES_OF_USE': 'mean'
    }).reset_index()

    decline_chart = pd.DataFrame({
        'Months Before Churn': decline_pattern['MONTHS_BEFORE_CHURN'],
        'Avg Calls': decline_pattern['PHONE_TOTAL_CALLS']
    })

    st.line_chart(decline_chart.set_index('Months Before Churn'), height=400)
    st.caption("Dashed line indicates churn date at month 0")

    # Churned users table
    st.markdown("---")
    st.subheader("Churned Users Details")

    display_churn = churn_df.copy()
    display_churn['CHURN_DATE'] = display_churn['CHURN_DATE'].dt.strftime('%Y-%m-%d')

    # Add average usage before churn
    avg_usage = churned_usage.groupby('USERID')['PHONE_TOTAL_CALLS'].mean().reset_index()
    avg_usage.columns = ['USERID', 'Avg Calls']

    display_churn = display_churn.merge(avg_usage, on='USERID', how='left')
    display_churn.columns = ['User ID', 'Churn Date', 'Churned', 'Avg Calls']

    st.dataframe(display_churn, use_container_width=True)


def show_user_segmentation(usage_df):
    """User segmentation page."""
    st.title("🎯 User Segmentation")

    st.markdown("""
    Users are segmented based on average monthly phone usage:
    - **Heavy Users**: >120 calls/month
    - **Medium Users**: 50-120 calls/month
    - **Light Users**: <50 calls/month
    """)

    # Calculate average usage per user
    user_avg = usage_df.groupby('USERID')['PHONE_TOTAL_CALLS'].mean().reset_index()
    user_avg.columns = ['USERID', 'Avg Calls']

    # Segment users
    def segment_user(avg_calls):
        if avg_calls > 120:
            return 'Heavy'
        elif avg_calls >= 50:
            return 'Medium'
        else:
            return 'Light'

    user_avg['Segment'] = user_avg['Avg Calls'].apply(segment_user)

    # Segment metrics
    col1, col2, col3 = st.columns(3)

    heavy_count = (user_avg['Segment'] == 'Heavy').sum()
    medium_count = (user_avg['Segment'] == 'Medium').sum()
    light_count = (user_avg['Segment'] == 'Light').sum()

    with col1:
        st.metric("Heavy Users", f"{heavy_count:,}",
                 f"{heavy_count/len(user_avg)*100:.1f}%")

    with col2:
        st.metric("Medium Users", f"{medium_count:,}",
                 f"{medium_count/len(user_avg)*100:.1f}%")

    with col3:
        st.metric("Light Users", f"{light_count:,}",
                 f"{light_count/len(user_avg)*100:.1f}%")

    st.markdown("---")

    # Visualization
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("User Segment Distribution")
        
        segment_counts = user_avg['Segment'].value_counts()
        segment_df = pd.DataFrame({
            'Segment': segment_counts.index,
            'Count': segment_counts.values
        })
        
        st.bar_chart(segment_df.set_index('Segment'), height=350)

    with col2:
        st.subheader("Segment Statistics by Call Volume")
        
        usage_with_segment = usage_df.merge(user_avg[['USERID', 'Segment']], on='USERID')
        
        # Group by segment and get statistics
        segment_stats = usage_with_segment.groupby('Segment')['PHONE_TOTAL_CALLS'].agg(['mean', 'median']).round(0)
        segment_stats.columns = ['Mean Calls', 'Median Calls']
        
        st.dataframe(segment_stats, use_container_width=True)

    # Segment trends over time
    st.markdown("---")
    st.subheader("Segment Trends Over Time")

    # Aggregate by segment and month
    monthly_segment = usage_with_segment.groupby(['MONTH', 'Segment']).agg({
        'PHONE_TOTAL_CALLS': 'mean'
    }).reset_index()

    # Create pivot table for multi-line chart
    monthly_segment_pivot = monthly_segment.pivot(index='MONTH', columns='Segment', values='PHONE_TOTAL_CALLS')
    
    st.line_chart(monthly_segment_pivot, height=400)

    # Detailed segment stats
    st.markdown("---")
    st.subheader("Detailed Segment Statistics")

    segment_stats = usage_with_segment.groupby('Segment').agg({
        'PHONE_TOTAL_CALLS': ['mean', 'median', 'std'],
        'PHONE_TOTAL_MINUTES_OF_USE': ['mean', 'median'],
        'PHONE_MAU': 'mean',
        'USERID': 'nunique'
    }).round(2)

    segment_stats.columns = ['_'.join(col).strip() for col in segment_stats.columns.values]
    segment_stats = segment_stats.reset_index()

    st.dataframe(segment_stats, use_container_width=True)


def show_vintage_analysis(account_df, churn_df):
    """Vintage analysis page showing cohort-based churn by signup month."""
    st.title("📅 Vintage Analysis")

    st.markdown("""
    Vintage (cohort) analysis tracks cumulative churn rates by signup month.
    Each vintage represents accounts that signed up in the same month.
    The X-axis shows tenure (months since signup), starting at 0.
    """)

    # Step 1: Determine signup month (first month) for each account
    signup_data = account_df.groupby('SERVICE_ACCOUNT_ID')['MONTH'].min().reset_index()
    signup_data.columns = ['SERVICE_ACCOUNT_ID', 'SIGNUP_MONTH']
    signup_data['VINTAGE'] = signup_data['SIGNUP_MONTH'].dt.to_period('M').astype(str)

    # Step 2: Merge signup data with all account data
    account_with_vintage = account_df.merge(
        signup_data[['SERVICE_ACCOUNT_ID', 'SIGNUP_MONTH', 'VINTAGE']],
        on='SERVICE_ACCOUNT_ID'
    )

    # Step 3: Calculate tenure (months since signup)
    account_with_vintage['TENURE'] = (
        (account_with_vintage['MONTH'].dt.year - account_with_vintage['SIGNUP_MONTH'].dt.year) * 12 +
        (account_with_vintage['MONTH'].dt.month - account_with_vintage['SIGNUP_MONTH'].dt.month)
    )

    # Step 4: Merge with churn data
    account_with_vintage = account_with_vintage.merge(
        churn_df[['USERID', 'CHURN_DATE']],
        left_on='SERVICE_ACCOUNT_ID',
        right_on='USERID',
        how='left'
    )

    # Calculate churn month tenure (months from signup to churn)
    account_with_vintage['CHURNED'] = account_with_vintage['CHURN_DATE'].notna()
    account_with_vintage['CHURN_TENURE'] = account_with_vintage.apply(
        lambda row: (
            (row['CHURN_DATE'].year - row['SIGNUP_MONTH'].year) * 12 +
            (row['CHURN_DATE'].month - row['SIGNUP_MONTH'].month)
        ) if pd.notna(row['CHURN_DATE']) else None,
        axis=1
    )

    # Metrics selector
    st.markdown("---")
    col1, col2 = st.columns([2, 1])

    with col1:
        metric_type = st.radio(
            "Select Metric",
            ["By Account Count", "By Revenue (if available)"],
            horizontal=True
        )

    with col2:
        min_cohort_size = st.number_input(
            "Min Cohort Size",
            min_value=1,
            max_value=1000,
            value=10,
            help="Only show vintages with at least this many accounts"
        )

    # Calculate cohort statistics
    st.markdown("---")
    st.subheader("Cohort Overview")

    # Get cohort sizes
    cohort_sizes = signup_data.groupby('VINTAGE').size().reset_index()
    cohort_sizes.columns = ['VINTAGE', 'COHORT_SIZE']
    cohort_sizes = cohort_sizes[cohort_sizes['COHORT_SIZE'] >= min_cohort_size]
    cohort_sizes = cohort_sizes.sort_values('VINTAGE')

    if cohort_sizes.empty:
        st.warning("No cohorts found matching the criteria.")
        return

    # Display cohort summary
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Vintages", len(cohort_sizes))
    with col2:
        st.metric("Earliest Vintage", cohort_sizes['VINTAGE'].min())
    with col3:
        st.metric("Latest Vintage", cohort_sizes['VINTAGE'].max())

    # Step 5: Calculate cumulative churn by vintage and tenure
    st.markdown("---")
    st.subheader("Cumulative Churn Rate by Tenure")

    # For each vintage and tenure, calculate cumulative churn rate
    churn_by_vintage_tenure = []

    for vintage in cohort_sizes['VINTAGE'].values:
        # Get all accounts in this vintage
        vintage_accounts = account_with_vintage[account_with_vintage['VINTAGE'] == vintage]
        total_accounts = vintage_accounts['SERVICE_ACCOUNT_ID'].nunique()

        # Get max tenure for this vintage
        max_tenure = vintage_accounts['TENURE'].max()

        # For each tenure month
        for tenure in range(0, int(max_tenure) + 1):
            # Count accounts that had churned by this tenure
            churned_by_tenure = vintage_accounts[
                (vintage_accounts['CHURNED']) &
                (vintage_accounts['CHURN_TENURE'] <= tenure)
            ]['SERVICE_ACCOUNT_ID'].nunique()

            cumulative_churn_rate = (churned_by_tenure / total_accounts * 100) if total_accounts > 0 else 0

            churn_by_vintage_tenure.append({
                'VINTAGE': vintage,
                'TENURE': tenure,
                'TOTAL_ACCOUNTS': total_accounts,
                'CHURNED_ACCOUNTS': churned_by_tenure,
                'CUMULATIVE_CHURN_RATE': cumulative_churn_rate
            })

    churn_df_analysis = pd.DataFrame(churn_by_vintage_tenure)

    if churn_df_analysis.empty:
        st.warning("No churn data available for analysis.")
        return

    # Get max tenure across all data for chart limits
    max_tenure_overall = int(churn_df_analysis['TENURE'].max())

    # Option to select specific vintages
    st.markdown("---")
    st.subheader("Select Vintages to Analyze")

    # Filter options
    col1, col2, col3 = st.columns(3)

    with col1:
        filter_type = st.radio(
            "Filter Vintages By:",
            ["Manual Selection", "By Quarter", "By Year", "By Segment"],
            horizontal=False
        )

    # Prepare vintage list based on filter type
    available_vintages = sorted(cohort_sizes['VINTAGE'].unique())

    if filter_type == "By Quarter":
        with col2:
            # Extract unique quarters
            quarters = sorted(list(set([v[:4] + '-Q' + str((int(v[5:7])-1)//3 + 1) for v in available_vintages])))
            selected_quarters = st.multiselect(
                "Select Quarters",
                options=quarters,
                default=quarters[-4:] if len(quarters) >= 4 else quarters
            )

        # Filter vintages by selected quarters
        selected_vintages = []
        for vintage in available_vintages:
            year = vintage[:4]
            month = int(vintage[5:7])
            quarter = f"{year}-Q{(month-1)//3 + 1}"
            if quarter in selected_quarters:
                selected_vintages.append(vintage)

    elif filter_type == "By Year":
        with col2:
            # Extract unique years
            years = sorted(list(set([v[:4] for v in available_vintages])))
            selected_years = st.multiselect(
                "Select Years",
                options=years,
                default=years[-2:] if len(years) >= 2 else years
            )

        # Filter vintages by selected years
        selected_vintages = [v for v in available_vintages if v[:4] in selected_years]

    elif filter_type == "By Segment":
        with col2:
            segment_option = st.selectbox(
                "Segment By:",
                ["Package", "Company", "Tier"]
            )

        with col3:
            # Get segment values from account data
            if segment_option == "Package":
                segment_col = 'PACKAGE_NAME'
            elif segment_option == "Company":
                segment_col = 'COMPANY'
            else:  # Tier
                segment_col = 'TIER_NAME'

            # Get unique segment values
            segment_values = sorted(account_df[segment_col].unique())
            selected_segments = st.multiselect(
                f"Select {segment_option}(s)",
                options=segment_values,
                default=segment_values[:3] if len(segment_values) >= 3 else segment_values
            )

        # Filter vintages by accounts in selected segments
        if selected_segments:
            segment_accounts = account_df[account_df[segment_col].isin(selected_segments)]['SERVICE_ACCOUNT_ID'].unique()
            segment_vintages = signup_data[signup_data['SERVICE_ACCOUNT_ID'].isin(segment_accounts)]['VINTAGE'].unique()
            selected_vintages = [v for v in available_vintages if v in segment_vintages]
        else:
            selected_vintages = []

    else:  # Manual Selection
        with col2:
            selected_vintages = st.multiselect(
                "Select vintages to compare",
                options=available_vintages,
                default=available_vintages[-6:] if len(available_vintages) >= 6 else available_vintages
            )

    # Display analysis
    st.markdown("---")
    st.subheader(f"Vintage Cohort Analysis ({len(selected_vintages)} vintages selected)")

    if selected_vintages:
        # Filter data
        filtered_churn = churn_df_analysis[churn_df_analysis['VINTAGE'].isin(selected_vintages)]

        # Ensure we have complete tenure range from 0 to max
        filtered_pivot = filtered_churn.pivot(
            index='TENURE',
            columns='VINTAGE',
            values='CUMULATIVE_CHURN_RATE'
        )

        # Reindex to ensure tenure starts at 0 and goes to max_tenure
        filtered_pivot = filtered_pivot.reindex(range(0, max_tenure_overall + 1), fill_value=None)

        st.line_chart(filtered_pivot, height=500)
        st.caption(f"X-axis: Tenure (0 to {max_tenure_overall} months) | Y-axis: Cumulative churn rate (%)")

        # Show data table
        st.markdown("### Detailed Churn Data")

        # Display summary for selected vintages
        summary_data = []
        for vintage in selected_vintages:
            vintage_data = filtered_churn[filtered_churn['VINTAGE'] == vintage]
            if not vintage_data.empty:
                max_tenure_data = vintage_data[vintage_data['TENURE'] == vintage_data['TENURE'].max()].iloc[0]
                summary_data.append({
                    'Vintage': vintage,
                    'Total Accounts': int(max_tenure_data['TOTAL_ACCOUNTS']),
                    'Max Tenure (Months)': int(max_tenure_data['TENURE']),
                    'Final Churn Rate (%)': round(max_tenure_data['CUMULATIVE_CHURN_RATE'], 2),
                    'Churned Accounts': int(max_tenure_data['CHURNED_ACCOUNTS'])
                })

        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True)

        # Optionally show raw data
        with st.expander("Show Raw Cohort Data"):
            display_data = filtered_churn.pivot_table(
                index='TENURE',
                columns='VINTAGE',
                values='CUMULATIVE_CHURN_RATE',
                aggfunc='first'
            ).round(2)
            st.dataframe(display_data, use_container_width=True)
    else:
        st.info("Please select at least one vintage to display the analysis.")

    # Additional insights
    if selected_vintages:
        st.markdown("---")
        st.subheader("Vintage Performance at Key Milestones")

        # Calculate churn rate at specific tenure milestones
        milestones = [6, 12, 24, 36]  # 6 months, 1 year, 2 years, 3 years

        milestone_data = []
        for vintage in selected_vintages:
            vintage_churn = churn_df_analysis[churn_df_analysis['VINTAGE'] == vintage]
            if vintage_churn.empty:
                continue

            row = {'Vintage': vintage}
            for milestone in milestones:
                milestone_churn = vintage_churn[vintage_churn['TENURE'] == milestone]
                if not milestone_churn.empty:
                    row[f'{milestone}M Churn %'] = round(milestone_churn.iloc[0]['CUMULATIVE_CHURN_RATE'], 2)
                else:
                    row[f'{milestone}M Churn %'] = None
            milestone_data.append(row)

        if milestone_data:
            milestone_df = pd.DataFrame(milestone_data)
            st.dataframe(milestone_df, use_container_width=True)
            st.caption("Churn rates at key tenure milestones (6, 12, 24, 36 months) for selected vintages")


def show_account_lookup(account_df, usage_df, churn_df):
    """Account lookup page with detailed usage trends."""
    st.title("🔍 Account Lookup")
    
    st.markdown("Enter an Account ID to view detailed usage trends for a specific account.")
    
    # Get unique account IDs for dropdown
    unique_accounts = sorted(account_df['SERVICE_ACCOUNT_ID'].unique())
    
    # Account selector
    selected_account = st.selectbox(
        "Select Account ID",
        options=unique_accounts,
        help="Choose an account ID from the dropdown or search"
    )
    
    if selected_account:
        # Filter data for selected account
        account_data = account_df[account_df['SERVICE_ACCOUNT_ID'] == selected_account]
        usage_data = usage_df[usage_df['USERID'] == selected_account]
        
        if account_data.empty:
            st.warning(f"No account data found for Account ID: {selected_account}")
            return
        
        if usage_data.empty:
            st.warning(f"No usage data found for Account ID: {selected_account}")
            
            # Still show account details if available
            latest_account = account_data.sort_values('MONTH').iloc[-1]
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Company", latest_account['COMPANY'])
            with col2:
                st.metric("Brand", latest_account['SA_BRAND_NAME'])
            with col3:
                st.metric("Package", latest_account['PACKAGE_NAME'])
            with col4:
                st.metric("Status", latest_account['SA_ACCT_STATUS'])
            return
        
        # Display account summary
        st.markdown("### Account Summary")
        latest_account = account_data.sort_values('MONTH').iloc[-1]
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.info(f"**Company:** {latest_account['COMPANY']}")
        with col2:
            st.info(f"**Brand:** {latest_account['SA_BRAND_NAME']}")
        with col3:
            st.info(f"**Package:** {latest_account['PACKAGE_NAME']}")
        with col4:
            st.info(f"**Status:** {latest_account['SA_ACCT_STATUS']}")
        
        # Check if account has churned
        if not churn_df.empty and selected_account in churn_df['USERID'].values:
            churn_info = churn_df[churn_df['USERID'] == selected_account].iloc[0]
            st.warning(f"⚠️ This account churned on {churn_info['CHURN_DATE'].strftime('%Y-%m-%d')}")
        
        st.markdown("---")
        
        # Sort by month (needed for all subsequent analysis)
        usage_data_sorted = usage_data.sort_values('MONTH')
        
        # Usage metrics summary
        st.markdown("### Usage Metrics Summary")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_calls = usage_data['PHONE_TOTAL_CALLS'].mean()
            st.metric("Avg Calls/Month", f"{avg_calls:.0f}")
        with col2:
            avg_minutes = usage_data['PHONE_TOTAL_MINUTES_OF_USE'].mean()
            st.metric("Avg Minutes/Month", f"{avg_minutes:.0f}")
        with col3:
            avg_voice_calls = usage_data['VOICE_CALLS'].mean()
            st.metric("Avg Voice Calls", f"{avg_voice_calls:.0f}")
        with col4:
            avg_mau = usage_data['PHONE_MAU'].mean()
            st.metric("Avg MAU", f"{avg_mau:.0f}")
        
        st.markdown("---")
        
        # AI Insights Section
        st.markdown("### 🤖 AI Insights Assistant")

        # Model pricing information (approximate Snowflake Cortex pricing per 1M tokens)
        # Based on Snowflake documentation
        model_pricing = {
            # Snowflake Arctic
            "snowflake-arctic": {"cost": 0.24, "per": "1M tokens"},

            # Mistral models
            "mistral-large": {"cost": 5.60, "per": "1M tokens"},
            "mistral-large2": {"cost": 5.60, "per": "1M tokens"},
            "mistral-7b": {"cost": 0.12, "per": "1M tokens"},
            "mixtral-8x7b": {"cost": 0.24, "per": "1M tokens"},

            # Llama models
            "llama3-8b": {"cost": 0.20, "per": "1M tokens"},
            "llama3-70b": {"cost": 2.00, "per": "1M tokens"},
            "llama3.1-8b": {"cost": 0.20, "per": "1M tokens"},
            "llama3.1-70b": {"cost": 2.00, "per": "1M tokens"},
            "llama3.1-405b": {"cost": 5.00, "per": "1M tokens"},
            "llama3.2-1b": {"cost": 0.10, "per": "1M tokens"},
            "llama3.2-3b": {"cost": 0.15, "per": "1M tokens"},

            # Gemma models
            "gemma-7b": {"cost": 0.12, "per": "1M tokens"},

            # Reka models
            "reka-core": {"cost": 3.00, "per": "1M tokens"},
            "reka-flash": {"cost": 0.15, "per": "1M tokens"},

            # Claude models (if available)
            "claude-3-5-sonnet": {"cost": 3.00, "per": "1M tokens"},
            "claude-3-haiku": {"cost": 0.25, "per": "1M tokens"},
            "claude-3-sonnet": {"cost": 3.00, "per": "1M tokens"},
        }

        # LLM Provider Selection - Use Snowflake Cortex models
        col1, col2 = st.columns([2, 3])
        with col1:
            # Get available models
            available_models, model_source = get_available_llm_models()
            models_displayed_count = len(available_models) if available_models else 0

            # Simple status indicator
            if model_source == 'sql':
                st.success(f"✅ Connected to Cortex AI ({models_displayed_count} models available)")
            else:
                st.info(f"ℹ️ Using standard Cortex model list ({models_displayed_count} models available)")

            if len(available_models) > 0:
                # Format model names with pricing if available
                model_options = []
                for model in available_models:
                    if model in model_pricing:
                        price_info = f" (~${model_pricing[model]['cost']:.2f}/{model_pricing[model]['per']} est.)"
                        model_options.append(f"{model}{price_info}")
                    else:
                        model_options.append(model)

                selected_option = st.selectbox(
                    "Select AI Model",
                    options=model_options,
                    index=0,
                    help=f"Choose the AI model from Snowflake Cortex. {models_displayed_count} model(s) available. Pricing shown is estimated based on Snowflake documentation."
                )

                # Extract actual model name (remove pricing info)
                llm_provider = selected_option.split(" (")[0]
            else:
                st.error("⚠️ No LLM models available. Please check your Snowflake Cortex configuration.")
                llm_provider = None

        # Initialize session state for prompt text
        if 'prompt_text' not in st.session_state:
            st.session_state.prompt_text = ""

        # Default prompt suggestions
        st.markdown("**💡 Suggested Prompts (click to add):**")

        default_prompts = {
            "📊 Account Status": "Provide a comprehensive analysis of this account's current status, including health indicators, engagement level, and any red flags or positive signals.",
            "📈 Trend Analysis": "Analyze the usage trends for this account over time. Identify any significant patterns, growth or decline, and seasonal variations.",
            "🔮 Future Performance": "Based on the historical data and current trends, predict the likely future performance of this account over the next 3-6 months. What trajectory is this account on?",
            "⚡ Next Actions": "What are the recommended next actions for this account? Consider account health, usage patterns, and business objectives to suggest concrete steps."
        }

        col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 0.5])

        with col1:
            btn_account = st.button("📊 Account Status", use_container_width=True, key="btn_account_status")
        with col2:
            btn_trend = st.button("📈 Trend Analysis", use_container_width=True, key="btn_trend_analysis")
        with col3:
            btn_future = st.button("🔮 Future Performance", use_container_width=True, key="btn_future_performance")
        with col4:
            btn_next = st.button("⚡ Next Actions", use_container_width=True, key="btn_next_actions")
        with col5:
            btn_clear = st.button("🗑️ Clear", use_container_width=True, help="Clear all prompts", key="btn_clear")
        
        # Handle button clicks after all buttons are defined
        if btn_account:
            if st.session_state.prompt_text:
                st.session_state.prompt_text += "\n\n" + default_prompts["📊 Account Status"]
            else:
                st.session_state.prompt_text = default_prompts["📊 Account Status"]
            st.rerun()
        if btn_trend:
            if st.session_state.prompt_text:
                st.session_state.prompt_text += "\n\n" + default_prompts["📈 Trend Analysis"]
            else:
                st.session_state.prompt_text = default_prompts["📈 Trend Analysis"]
            st.rerun()
        if btn_future:
            if st.session_state.prompt_text:
                st.session_state.prompt_text += "\n\n" + default_prompts["🔮 Future Performance"]
            else:
                st.session_state.prompt_text = default_prompts["🔮 Future Performance"]
            st.rerun()
        if btn_next:
            if st.session_state.prompt_text:
                st.session_state.prompt_text += "\n\n" + default_prompts["⚡ Next Actions"]
            else:
                st.session_state.prompt_text = default_prompts["⚡ Next Actions"]
            st.rerun()
        if btn_clear:
            st.session_state.prompt_text = ""
            st.rerun()

        # User prompt input using session state
        # Remove key so the value prop updates properly when buttons are clicked
        user_prompt = st.text_area(
            "Ask about this account's usage patterns and trends",
            value=st.session_state.prompt_text,
            placeholder="Click suggested prompts above to add them, or write your own questions...",
            height=150,
            help="Click prompt buttons above to add questions. Multiple clicks will add multiple prompts."
        )

        # Update session state when user types manually
        if user_prompt != st.session_state.prompt_text:
            st.session_state.prompt_text = user_prompt
        
        # Generate insights button
        if st.button("💡 Generate Insights", type="primary", use_container_width=True):
            if not llm_provider:
                st.error("Please ensure LLM models are available in your Snowflake environment.")
            elif user_prompt:
                # Prepare account summary for context
                account_context = prepare_account_context(
                    selected_account, latest_account, usage_data_sorted, avg_calls, avg_minutes
                )

                # Display loading
                with st.spinner(f"Analyzing with {llm_provider}..."):
                    # Generate insights with token tracking
                    insights, input_tokens, output_tokens = generate_ai_insights(llm_provider, user_prompt, account_context)

                    st.success("Analysis Complete!")
                    st.markdown("#### 📊 AI Insights")
                    st.markdown(insights)

                    # Display token usage and cost estimation
                    st.markdown("---")
                    st.markdown("#### 💰 Token Usage & Cost Summary")

                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric("Input Tokens", f"{input_tokens:,}",
                                 help="Estimated tokens in your prompt and context")
                    with col2:
                        st.metric("Output Tokens", f"{output_tokens:,}",
                                 help="Estimated tokens in the AI response")
                    with col3:
                        total_tokens = input_tokens + output_tokens
                        st.metric("Total Tokens", f"{total_tokens:,}",
                                 help="Sum of input and output tokens")
                    with col4:
                        # Calculate estimated cost based on model pricing
                        if llm_provider in model_pricing:
                            cost_per_million = model_pricing[llm_provider]["cost"]
                            estimated_cost = (total_tokens / 1_000_000) * cost_per_million
                            st.metric("Estimated Price", f"${estimated_cost:.6f}",
                                     help="Approximate cost based on published Snowflake Cortex pricing")
                        else:
                            st.metric("Estimated Price", "N/A",
                                     help="Pricing information not available for this model")

                    # Additional cost information with clear labeling
                    if llm_provider in model_pricing:
                        st.info(f"""
                        **💡 Pricing Details (Estimated):**
                        - Model: {llm_provider}
                        - Rate: ${model_pricing[llm_provider]['cost']:.2f} per {model_pricing[llm_provider]['per']}
                        - Tokens Used: {total_tokens:,} ({input_tokens:,} input + {output_tokens:,} output)
                        - Estimated Cost: ${estimated_cost:.6f}

                        ⚠️ **Note:** Token counts and pricing are estimates based on Snowflake documentation.
                        Actual usage and costs may vary. Check your Snowflake account for accurate billing information.
                        """)
                    else:
                        st.caption("⚠️ Note: Token counts are estimated (1 token ≈ 4 characters). Pricing information not available for this model.")
            else:
                st.warning("Please enter a question before generating insights.")
        
        st.markdown("---")
        
        # Usage trends over time
        st.markdown("### Usage Trends Over Time")
        
        # Primary metrics
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Total Calls & Minutes")
            primary_metrics = pd.DataFrame({
                'MONTH': usage_data_sorted['MONTH'],
                'Total Calls': usage_data_sorted['PHONE_TOTAL_CALLS'],
                'Total Minutes': usage_data_sorted['PHONE_TOTAL_MINUTES_OF_USE']
            })
            st.line_chart(primary_metrics.set_index('MONTH'), height=400)
        
        with col2:
            st.subheader("Voice & Fax Calls")
            call_types = pd.DataFrame({
                'MONTH': usage_data_sorted['MONTH'],
                'Voice Calls': usage_data_sorted['VOICE_CALLS'],
                'Fax Calls': usage_data_sorted['FAX_CALLS']
            })
            st.line_chart(call_types.set_index('MONTH'), height=400)
        
        # Inbound vs Outbound
        st.markdown("---")
        st.markdown("### Call Direction Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Inbound vs Outbound Calls")
            direction = pd.DataFrame({
                'MONTH': usage_data_sorted['MONTH'],
                'Inbound': usage_data_sorted['PHONE_TOTAL_NUM_INBOUND_CALLS'],
                'Outbound': usage_data_sorted['PHONE_TOTAL_NUM_OUTBOUND_CALLS']
            })
            st.line_chart(direction.set_index('MONTH'), height=400)
        
        with col2:
            st.subheader("Device Type Usage")
            devices = pd.DataFrame({
                'MONTH': usage_data_sorted['MONTH'],
                'Hardphone': usage_data_sorted['HARDPHONE_CALLS'],
                'Softphone': usage_data_sorted['SOFTPHONE_CALLS'],
                'Mobile': usage_data_sorted['MOBILE_CALLS']
            })
            st.line_chart(devices.set_index('MONTH'), height=400)
        
        # MAU and additional metrics
        st.markdown("---")
        st.markdown("### Monthly Active Users & Engagement")
        
        mau_data = pd.DataFrame({
            'MONTH': usage_data_sorted['MONTH'],
            'Phone MAU': usage_data_sorted['PHONE_MAU']
        })
        st.line_chart(mau_data.set_index('MONTH'), height=400)
        
        # Detailed data table
        st.markdown("---")
        st.markdown("### Detailed Usage Data")
        
        # Select columns to display
        display_columns = [
            'MONTH', 'PHONE_TOTAL_CALLS', 'PHONE_TOTAL_MINUTES_OF_USE',
            'VOICE_CALLS', 'FAX_CALLS', 'PHONE_TOTAL_NUM_INBOUND_CALLS',
            'PHONE_TOTAL_NUM_OUTBOUND_CALLS', 'HARDPHONE_CALLS', 'SOFTPHONE_CALLS',
            'MOBILE_CALLS', 'PHONE_MAU'
        ]
        
        display_table = usage_data_sorted[display_columns].copy()
        display_table['MONTH'] = display_table['MONTH'].dt.strftime('%Y-%m')
        display_table = display_table.rename(columns={
            'MONTH': 'Month',
            'PHONE_TOTAL_CALLS': 'Total Calls',
            'PHONE_TOTAL_MINUTES_OF_USE': 'Total Minutes',
            'VOICE_CALLS': 'Voice Calls',
            'FAX_CALLS': 'Fax Calls',
            'PHONE_TOTAL_NUM_INBOUND_CALLS': 'Inbound Calls',
            'PHONE_TOTAL_NUM_OUTBOUND_CALLS': 'Outbound Calls',
            'HARDPHONE_CALLS': 'Hardphone',
            'SOFTPHONE_CALLS': 'Softphone',
            'MOBILE_CALLS': 'Mobile',
            'PHONE_MAU': 'Phone MAU'
        })
        
        st.dataframe(display_table, use_container_width=True, height=400)
        
        # Download button
        csv = display_table.to_csv(index=False)
        st.download_button(
            label="📥 Download Data as CSV",
            data=csv,
            file_name=f"account_{selected_account}_usage_data.csv",
            mime="text/csv"
        )


if __name__ == "__main__":
    main()
