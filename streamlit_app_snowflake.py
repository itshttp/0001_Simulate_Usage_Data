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


@st.cache_data(ttl=600)  # Cache for 10 minutes (increased for stable data)
def load_account_data():
    """
    Load account data from Snowflake.
    EFFICIENCY: Select only needed columns instead of SELECT *
    """
    query = """
    SELECT 
        MONTH,
        ENTERPRISE_ACCOUNT_ID,
        SERVICE_ACCOUNT_ID,
        COMPANY,
        EA_BRAND_ID,
        EA_BRAND_NAME,
        EA_UBRAND_ID,
        EA_UBRAND_DESCRIPTION,
        EA_ACCT_STATUS,
        SA_BRAND_ID,
        SA_BRAND_NAME,
        SA_UBRAND_ID,
        SA_UBRAND_DESCRIPTION,
        SA_ACCT_STATUS,
        PACKAGE_ID,
        PACKAGE_NAME,
        CATALOG_PACKAGE_ID,
        CATALOG_PACKAGE_NAME,
        IS_TESTER,
        TIER_ID,
        TIER_NAME,
        EDITION_NAME,
        EXTERNAL_ACCOUNT_ID,
        BAN,
        OPCO_ID
    FROM ACCOUNT_ATTRIBUTES_MONTHLY
    """
    df = st.connection("snowflake").query(query)
    df['MONTH'] = pd.to_datetime(df['MONTH'])
    return df


@st.cache_data(ttl=600)  # Cache for 10 minutes (increased for stable data)
def load_usage_data():
    """
    Load usage data from Snowflake.
    EFFICIENCY: Select only needed columns instead of SELECT *
    """
    query = """
    SELECT
        USERID,
        MONTH,
        PACKAGE_TIER,
        MRR,
        PHONE_TOTAL_CALLS,
        PHONE_TOTAL_MINUTES_OF_USE,
        VOICE_CALLS,
        VOICE_MINS,
        FAX_CALLS,
        FAX_MINS,
        PHONE_TOTAL_NUM_INBOUND_CALLS,
        PHONE_TOTAL_NUM_OUTBOUND_CALLS,
        PHONE_TOTAL_INBOUND_MIN,
        PHONE_TOTAL_OUTBOUND_MIN,
        OUT_VOICE_CALLS,
        IN_VOICE_CALLS,
        OUT_VOICE_MINS,
        IN_VOICE_MINS,
        OUT_FAX_CALLS,
        IN_FAX_CALLS,
        OUT_FAX_MINS,
        IN_FAX_MINS,
        PHONE_MAU,
        CALL_MAU,
        FAX_MAU,
        HARDPHONE_CALLS,
        SOFTPHONE_CALLS,
        MOBILE_CALLS,
        MOBILE_ANDROID_CALLS
    FROM PHONE_USAGE_DATA
    """
    df = st.connection("snowflake").query(query)
    df['MONTH'] = pd.to_datetime(df['MONTH'])
    return df


@st.cache_data(ttl=600)  # Cache for 10 minutes (increased for stable data)
def load_churn_data():
    """
    Load churn data from Snowflake.
    EFFICIENCY: CHURN_RECORDS is small, but explicit column selection is still best practice
    """
    query = """
    SELECT 
        USERID,
        CHURN_DATE,
        CHURNED
    FROM CHURN_RECORDS
    """
    df = st.connection("snowflake").query(query)
    df['CHURN_DATE'] = pd.to_datetime(df['CHURN_DATE'])
    return df


@st.cache_data(ttl=60)  # Cache for 1 minute
def load_users_and_roles():
    """Load users and their roles from Snowflake."""
    try:
        conn = st.connection("snowflake")

        # Get all users from INFORMATION_SCHEMA
        users_query = """
        SELECT
            NAME,
            CREATED_ON,
            LOGIN_NAME,
            DISPLAY_NAME,
            DISABLED,
            DEFAULT_ROLE,
            DEFAULT_WAREHOUSE,
            HAS_PASSWORD,
            COMMENT
        FROM SNOWFLAKE.ACCOUNT_USAGE.USERS
        WHERE DELETED_ON IS NULL
        ORDER BY NAME
        """
        users_df = conn.query(users_query)

        return users_df
    except Exception as e:
        st.error(f"Error loading users: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=60)
def load_roles():
    """Load all roles from Snowflake."""
    try:
        conn = st.connection("snowflake")

        # Get all roles from ACCOUNT_USAGE
        roles_query = """
        SELECT
            NAME,
            CREATED_ON,
            DELETED_ON,
            COMMENT,
            OWNER
        FROM SNOWFLAKE.ACCOUNT_USAGE.ROLES
        WHERE DELETED_ON IS NULL
        ORDER BY NAME
        """
        roles_df = conn.query(roles_query)

        return roles_df
    except Exception as e:
        st.error(f"Error loading roles: {e}")
        return pd.DataFrame()


def get_grants_for_user(username):
    """Get all grants for a specific user."""
    try:
        conn = st.connection("snowflake")

        # Get grants to user from ACCOUNT_USAGE
        grants_query = f"""
        SELECT
            CREATED_ON,
            ROLE,
            GRANTEE_NAME,
            GRANTED_BY,
            DELETED_ON
        FROM SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_USERS
        WHERE GRANTEE_NAME = '{username}'
        AND DELETED_ON IS NULL
        ORDER BY CREATED_ON DESC
        """
        grants_df = conn.query(grants_query)

        return grants_df
    except Exception as e:
        st.error(f"Error loading grants for user {username}: {e}")
        return pd.DataFrame()


def get_grants_for_role(role_name):
    """Get all grants for a specific role."""
    try:
        conn = st.connection("snowflake")

        # Get grants to role from ACCOUNT_USAGE
        grants_query = f"""
        SELECT
            CREATED_ON,
            PRIVILEGE,
            GRANTED_ON,
            NAME,
            TABLE_CATALOG,
            TABLE_SCHEMA,
            GRANTED_TO,
            GRANTEE_NAME,
            GRANT_OPTION,
            GRANTED_BY
        FROM SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_ROLES
        WHERE GRANTEE_NAME = '{role_name}'
        AND DELETED_ON IS NULL
        ORDER BY CREATED_ON DESC
        """
        grants_df = conn.query(grants_query)

        return grants_df
    except Exception as e:
        st.error(f"Error loading grants for role {role_name}: {e}")
        return pd.DataFrame()


def get_users_with_role(role_name):
    """Get all users with a specific role."""
    try:
        conn = st.connection("snowflake")

        # Get grants of role to users from ACCOUNT_USAGE
        grants_query = f"""
        SELECT
            CREATED_ON,
            ROLE,
            GRANTEE_NAME,
            GRANTED_TO,
            GRANTED_BY
        FROM SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_USERS
        WHERE ROLE = '{role_name}'
        AND DELETED_ON IS NULL
        ORDER BY GRANTEE_NAME
        """
        grants_df = conn.query(grants_query)

        return grants_df
    except Exception as e:
        st.error(f"Error loading users with role {role_name}: {e}")
        return pd.DataFrame()


def prepare_account_context(selected_account, latest_account, usage_data_sorted, avg_calls, avg_minutes):
    """Prepare account context summary for AI analysis."""
    # Calculate trends
    total_calls = usage_data_sorted['PHONE_TOTAL_CALLS'].tolist()
    total_minutes = usage_data_sorted['PHONE_TOTAL_MINUTES_OF_USE'].tolist()
    mrr_values = usage_data_sorted['MRR'].tolist()
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

    # Revenue metrics
    current_mrr = mrr_values[-1] if len(mrr_values) > 0 else 0
    avg_mrr = usage_data_sorted[usage_data_sorted['MRR'] > 0]['MRR'].mean()
    total_revenue = usage_data_sorted['MRR'].sum()
    current_tier = usage_data_sorted['PACKAGE_TIER'].iloc[-1] if len(usage_data_sorted) > 0 else "Unknown"

    # Calculate MRR growth
    if len(mrr_values) > 1 and mrr_values[0] > 0:
        mrr_growth = ((mrr_values[-1] - mrr_values[0]) / mrr_values[0] * 100)
    else:
        mrr_growth = 0

    # Check if we have account data (it might be None or a dict-like object)
    has_account_data = latest_account is not None and isinstance(latest_account, (dict, pd.Series))

    if has_account_data:
        context = f"""
Account: {selected_account}
Company: {latest_account.get('COMPANY', 'N/A')}
Package: {latest_account.get('PACKAGE_NAME', 'N/A')}
Status: {latest_account.get('SA_ACCT_STATUS', 'N/A')}
Brand: {latest_account.get('SA_BRAND_NAME', 'N/A')}

Revenue Metrics:
- Current Package Tier: {current_tier}
- Current MRR: ${current_mrr:.2f}
- Average MRR: ${avg_mrr:.2f}
- Total Revenue (All Months): ${total_revenue:,.2f}
- MRR Growth: {mrr_growth:+.1f}%

Usage Summary:
- Average Calls per Month: {avg_calls:.0f}
- Average Minutes per Month: {avg_minutes:.0f}
- Total Months of Data: {len(usage_data_sorted)}
- Usage Growth Rate: {growth_rate:.1f}%
- Peak Usage Month: {months[max_calls_idx].strftime('%Y-%m')} ({total_calls[max_calls_idx]:.0f} calls)
- Lowest Usage Month: {months[min_calls_idx].strftime('%Y-%m')} ({total_calls[min_calls_idx]:.0f} calls)

Device Usage Breakdown:
- Hardphone Calls: {hardphone:.0f}
- Softphone Calls: {softphone:.0f}
- Mobile Calls: {mobile:.0f}
"""
    else:
        # Simplified context when account data is not available
        context = f"""
User ID: {selected_account}
Data Source: Simulated Phone Usage Data

Revenue Metrics:
- Current Package Tier: {current_tier}
- Current MRR: ${current_mrr:.2f}
- Average MRR: ${avg_mrr:.2f}
- Total Revenue (All Months): ${total_revenue:,.2f}
- MRR Growth: {mrr_growth:+.1f}%

Usage Summary:
- Average Calls per Month: {avg_calls:.0f}
- Average Minutes per Month: {avg_minutes:.0f}
- Total Months of Data: {len(usage_data_sorted)}
- Usage Growth Rate: {growth_rate:.1f}%
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
        ["🏠 Overview", "💰 Revenue Analytics", "👥 Account Analytics", "📈 Usage Trends",
         "⚠️ Churn Analysis", "🎯 User Segmentation", "📅 Vintage Analysis",
         "📊 9BOX & Insights"]
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
    elif page == "💰 Revenue Analytics":
        show_revenue_analytics(usage_df, churn_df)
    elif page == "👥 Account Analytics":
        show_account_analytics(account_df)
    elif page == "📈 Usage Trends":
        show_usage_trends(usage_df)
    elif page == "⚠️ Churn Analysis":
        show_churn_analysis(usage_df, churn_df)
    elif page == "🎯 User Segmentation":
        show_user_segmentation(usage_df)
    elif page == "📅 Vintage Analysis":
        show_vintage_analysis(usage_df, churn_df)
    elif page == "📊 9BOX & Insights":
        show_account_lookup(account_df, usage_df, churn_df)


def show_overview(account_df, usage_df, churn_df):
    """Overview page with key metrics."""
    st.title("📊 Dashboard Overview")

    # KPI Metrics Row 1
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

    # KPI Metrics Row 2 - Revenue Metrics
    st.markdown("### 💰 Revenue Metrics")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        # Total MRR (most recent month)
        latest_month = usage_df['MONTH'].max()
        latest_mrr = usage_df[usage_df['MONTH'] == latest_month]['MRR'].sum()
        st.metric("Current MRR", f"${latest_mrr:,.2f}")

    with col2:
        # Average MRR per user
        avg_mrr = usage_df[usage_df['MRR'] > 0]['MRR'].mean()
        st.metric("Avg MRR per User", f"${avg_mrr:.2f}")

    with col3:
        # ARR (Annual Recurring Revenue)
        arr = latest_mrr * 12
        st.metric("Estimated ARR", f"${arr:,.2f}")

    with col4:
        # Calculate MRR growth (comparing latest month to previous month)
        months_sorted = sorted(usage_df['MONTH'].unique())
        if len(months_sorted) >= 2:
            prev_month = months_sorted[-2]
            prev_mrr = usage_df[usage_df['MONTH'] == prev_month]['MRR'].sum()
            mrr_growth = ((latest_mrr - prev_mrr) / prev_mrr * 100) if prev_mrr > 0 else 0
            st.metric("MRR Growth (MoM)", f"{mrr_growth:+.1f}%")
        else:
            st.metric("MRR Growth (MoM)", "N/A")

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

    # Package Tier and Revenue Distribution
    st.markdown("---")
    st.subheader("Package Tier & Revenue Distribution")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Users by Package Tier**")
        # Get latest package tier for each user
        latest_usage = usage_df.sort_values('MONTH').groupby('USERID').last()
        tier_counts = latest_usage['PACKAGE_TIER'].value_counts()

        tier_df = pd.DataFrame({
            'Package Tier': tier_counts.index,
            'Number of Users': tier_counts.values
        })

        st.bar_chart(tier_df.set_index('Package Tier'), height=350)

    with col2:
        st.markdown("**MRR by Package Tier**")
        # Calculate total MRR by package tier (most recent month)
        latest_month_usage = usage_df[usage_df['MONTH'] == latest_month]
        tier_mrr = latest_month_usage.groupby('PACKAGE_TIER')['MRR'].sum().sort_values(ascending=False)

        tier_mrr_df = pd.DataFrame({
            'Package Tier': tier_mrr.index,
            'Total MRR': tier_mrr.values
        })

        st.bar_chart(tier_mrr_df.set_index('Package Tier'), height=350)

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


def show_revenue_analytics(usage_df, churn_df):
    """Revenue analytics page with MRR and package tier analysis."""
    st.title("💰 Revenue Analytics")

    # Revenue KPIs
    col1, col2, col3, col4 = st.columns(4)

    latest_month = usage_df['MONTH'].max()
    latest_month_data = usage_df[usage_df['MONTH'] == latest_month]

    with col1:
        total_mrr = latest_month_data['MRR'].sum()
        st.metric("Current MRR", f"${total_mrr:,.2f}")

    with col2:
        active_users = latest_month_data[latest_month_data['MRR'] > 0]['USERID'].nunique()
        st.metric("Paying Users", f"{active_users:,}")

    with col3:
        avg_arpu = total_mrr / active_users if active_users > 0 else 0
        st.metric("ARPU (Avg Rev/User)", f"${avg_arpu:.2f}")

    with col4:
        arr = total_mrr * 12
        st.metric("ARR", f"${arr:,.2f}")

    st.markdown("---")

    # MRR Trends
    st.subheader("MRR Trends Over Time")

    # Aggregate MRR by month
    monthly_mrr = usage_df.groupby('MONTH').agg({
        'MRR': 'sum',
        'USERID': 'nunique'
    }).reset_index()
    monthly_mrr.columns = ['MONTH', 'Total MRR', 'Active Users']

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Total MRR by Month**")
        mrr_chart = pd.DataFrame({
            'MONTH': monthly_mrr['MONTH'],
            'MRR': monthly_mrr['Total MRR']
        })
        st.line_chart(mrr_chart.set_index('MONTH'), height=400)

    with col2:
        st.markdown("**Active Paying Users**")
        users_chart = pd.DataFrame({
            'MONTH': monthly_mrr['MONTH'],
            'Active Users': monthly_mrr['Active Users']
        })
        st.line_chart(users_chart.set_index('MONTH'), height=400)

    # Package Tier Analysis
    st.markdown("---")
    st.subheader("Revenue by Package Tier")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**MRR Distribution by Tier**")
        # Current month MRR by tier
        tier_mrr = latest_month_data.groupby('PACKAGE_TIER')['MRR'].sum().sort_values(ascending=False)

        tier_mrr_df = pd.DataFrame({
            'Package Tier': tier_mrr.index,
            'MRR': tier_mrr.values
        })

        st.bar_chart(tier_mrr_df.set_index('Package Tier'), height=400)

        # Show percentages
        total = tier_mrr.sum()
        st.markdown("**Percentage of Total MRR:**")
        for tier, mrr in tier_mrr.items():
            pct = (mrr / total * 100) if total > 0 else 0
            st.write(f"- {tier}: ${mrr:,.2f} ({pct:.1f}%)")

    with col2:
        st.markdown("**Average MRR per User by Tier**")
        # Calculate average MRR per user by tier
        tier_stats = latest_month_data[latest_month_data['MRR'] > 0].groupby('PACKAGE_TIER').agg({
            'MRR': ['mean', 'count']
        }).round(2)

        tier_stats.columns = ['Avg MRR', 'User Count']
        tier_stats = tier_stats.sort_values('Avg MRR', ascending=False)

        st.dataframe(tier_stats, use_container_width=True)

        st.markdown("**Key Insights:**")
        highest_tier = tier_stats['Avg MRR'].idxmax()
        highest_avg = tier_stats['Avg MRR'].max()
        st.write(f"- Highest ARPU: {highest_tier} (${highest_avg:.2f})")

        most_users_tier = tier_stats['User Count'].idxmax()
        most_users = tier_stats['User Count'].max()
        st.write(f"- Most Users: {most_users_tier} ({int(most_users):,} users)")

    # MRR Trends by Package Tier
    st.markdown("---")
    st.subheader("MRR Trends by Package Tier")

    monthly_tier_mrr = usage_df.groupby(['MONTH', 'PACKAGE_TIER'])['MRR'].sum().reset_index()
    tier_pivot = monthly_tier_mrr.pivot(index='MONTH', columns='PACKAGE_TIER', values='MRR')

    st.line_chart(tier_pivot, height=500)

    # Revenue Retention and Churn Impact
    st.markdown("---")
    st.subheader("Revenue Retention & Churn Impact")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**MRR Lost to Churn**")

        if not churn_df.empty:
            # Merge churn data with usage data to calculate lost revenue
            churned_users = churn_df['USERID'].unique()
            churned_usage = usage_df[usage_df['USERID'].isin(churned_users)]

            # Merge with churn dates
            churned_usage = churned_usage.merge(churn_df[['USERID', 'CHURN_DATE']], on='USERID')

            # Calculate MRR lost each month (MRR in the month before churn)
            churned_usage['MONTHS_TO_CHURN'] = (
                (churned_usage['CHURN_DATE'].dt.year - churned_usage['MONTH'].dt.year) * 12 +
                (churned_usage['CHURN_DATE'].dt.month - churned_usage['MONTH'].dt.month)
            )

            # Get MRR from month before churn (MONTHS_TO_CHURN == 1)
            pre_churn_mrr = churned_usage[churned_usage['MONTHS_TO_CHURN'] == 1].groupby(
                churned_usage[churned_usage['MONTHS_TO_CHURN'] == 1]['CHURN_DATE'].dt.to_period('M')
            )['MRR'].sum().reset_index()

            pre_churn_mrr.columns = ['Churn Month', 'Lost MRR']
            pre_churn_mrr['Churn Month'] = pre_churn_mrr['Churn Month'].astype(str)

            if not pre_churn_mrr.empty:
                st.bar_chart(pre_churn_mrr.set_index('Churn Month'), height=400)

                total_lost = pre_churn_mrr['Lost MRR'].sum()
                st.write(f"**Total MRR Lost to Churn:** ${total_lost:,.2f}")
            else:
                st.info("No churn data available for revenue analysis.")
        else:
            st.info("No churn data available.")

    with col2:
        st.markdown("**Revenue Retention Analysis**")

        # Calculate MRR retention rate (month-over-month)
        months = sorted(usage_df['MONTH'].unique())
        retention_data = []

        for i in range(1, len(months)):
            prev_month = months[i-1]
            curr_month = months[i]

            # Users who had MRR in previous month
            prev_users = set(usage_df[(usage_df['MONTH'] == prev_month) & (usage_df['MRR'] > 0)]['USERID'])
            # Users who still have MRR in current month
            curr_users = set(usage_df[(usage_df['MONTH'] == curr_month) & (usage_df['MRR'] > 0)]['USERID'])

            # Users retained
            retained_users = prev_users & curr_users

            # Calculate revenue retention
            prev_mrr_retained = usage_df[
                (usage_df['MONTH'] == prev_month) &
                (usage_df['USERID'].isin(retained_users))
            ]['MRR'].sum()

            curr_mrr_retained = usage_df[
                (usage_df['MONTH'] == curr_month) &
                (usage_df['USERID'].isin(retained_users))
            ]['MRR'].sum()

            retention_rate = (curr_mrr_retained / prev_mrr_retained * 100) if prev_mrr_retained > 0 else 0

            retention_data.append({
                'Month': curr_month,
                'Retention Rate': retention_rate
            })

        if retention_data:
            retention_df = pd.DataFrame(retention_data)
            st.line_chart(retention_df.set_index('Month'), height=400)

            avg_retention = retention_df['Retention Rate'].mean()
            st.write(f"**Avg Revenue Retention Rate:** {avg_retention:.1f}%")
        else:
            st.info("Not enough data to calculate retention.")

    # Package Tier Migration Analysis
    st.markdown("---")
    st.subheader("Package Tier Migration")

    st.markdown("""
    Track how users move between package tiers over time.
    """)

    # Detect tier changes
    user_tier_changes = []
    for user_id in usage_df['USERID'].unique():
        user_data = usage_df[usage_df['USERID'] == user_id].sort_values('MONTH')
        tiers = user_data['PACKAGE_TIER'].tolist()
        months = user_data['MONTH'].tolist()

        for i in range(1, len(tiers)):
            if tiers[i] != tiers[i-1]:
                user_tier_changes.append({
                    'USERID': user_id,
                    'From Tier': tiers[i-1],
                    'To Tier': tiers[i],
                    'Month': months[i],
                    'Change Type': 'Upgrade' if tiers[i] > tiers[i-1] else 'Downgrade'
                })

    if user_tier_changes:
        changes_df = pd.DataFrame(user_tier_changes)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Tier Changes by Type**")
            change_counts = changes_df['Change Type'].value_counts()
            change_count_df = pd.DataFrame({
                'Change Type': change_counts.index,
                'Count': change_counts.values
            })
            st.bar_chart(change_count_df.set_index('Change Type'), height=300)

        with col2:
            st.markdown("**Recent Tier Changes**")
            recent_changes = changes_df.sort_values('Month', ascending=False).head(10)
            display_changes = recent_changes[['USERID', 'From Tier', 'To Tier', 'Month', 'Change Type']].copy()
            display_changes['Month'] = display_changes['Month'].dt.strftime('%Y-%m')
            st.dataframe(display_changes, use_container_width=True, height=300)
    else:
        st.info("No package tier changes detected in the data.")


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

    # Create tabs for different segmentation views
    tab1, tab2, tab3 = st.tabs(["📞 By Usage", "💰 By Revenue", "📦 By Package Tier"])

    # Tab 1: Usage-based segmentation
    with tab1:
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

    # Tab 2: Revenue-based segmentation
    with tab2:
        st.markdown("""
        Users are segmented based on average monthly MRR:
        - **High Value**: >$100/month
        - **Medium Value**: $50-$100/month
        - **Low Value**: <$50/month
        """)

        # Calculate average MRR per user
        user_mrr = usage_df[usage_df['MRR'] > 0].groupby('USERID')['MRR'].mean().reset_index()
        user_mrr.columns = ['USERID', 'Avg MRR']

        # Segment users by revenue
        def segment_by_revenue(avg_mrr):
            if avg_mrr > 100:
                return 'High Value'
            elif avg_mrr >= 50:
                return 'Medium Value'
            else:
                return 'Low Value'

        user_mrr['Revenue Segment'] = user_mrr['Avg MRR'].apply(segment_by_revenue)

        # Segment metrics
        col1, col2, col3 = st.columns(3)

        high_count = (user_mrr['Revenue Segment'] == 'High Value').sum()
        medium_count = (user_mrr['Revenue Segment'] == 'Medium Value').sum()
        low_count = (user_mrr['Revenue Segment'] == 'Low Value').sum()

        with col1:
            st.metric("High Value Users", f"{high_count:,}",
                     f"{high_count/len(user_mrr)*100:.1f}%")

        with col2:
            st.metric("Medium Value Users", f"{medium_count:,}",
                     f"{medium_count/len(user_mrr)*100:.1f}%")

        with col3:
            st.metric("Low Value Users", f"{low_count:,}",
                     f"{low_count/len(user_mrr)*100:.1f}%")

        st.markdown("---")

        # Visualization
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Revenue Segment Distribution")

            segment_counts = user_mrr['Revenue Segment'].value_counts()
            segment_df = pd.DataFrame({
                'Segment': segment_counts.index,
                'Count': segment_counts.values
            })

            st.bar_chart(segment_df.set_index('Segment'), height=350)

        with col2:
            st.subheader("Revenue Statistics by Segment")

            # Merge with usage data
            usage_with_revenue_segment = usage_df[usage_df['MRR'] > 0].merge(
                user_mrr[['USERID', 'Revenue Segment']], on='USERID'
            )

            # Group by segment and get statistics
            revenue_stats = usage_with_revenue_segment.groupby('Revenue Segment')['MRR'].agg(['mean', 'median']).round(2)
            revenue_stats.columns = ['Mean MRR', 'Median MRR']

            st.dataframe(revenue_stats, use_container_width=True)

        # Revenue segment trends over time
        st.markdown("---")
        st.subheader("MRR Trends by Revenue Segment")

        # Aggregate by segment and month
        monthly_revenue_segment = usage_with_revenue_segment.groupby(['MONTH', 'Revenue Segment']).agg({
            'MRR': 'mean'
        }).reset_index()

        # Create pivot table for multi-line chart
        monthly_revenue_pivot = monthly_revenue_segment.pivot(index='MONTH', columns='Revenue Segment', values='MRR')

        st.line_chart(monthly_revenue_pivot, height=400)

        # Total revenue contribution by segment
        st.markdown("---")
        st.subheader("Revenue Contribution by Segment")

        latest_month = usage_df['MONTH'].max()
        latest_usage = usage_df[usage_df['MONTH'] == latest_month].merge(
            user_mrr[['USERID', 'Revenue Segment']], on='USERID', how='inner'
        )

        segment_revenue = latest_usage.groupby('Revenue Segment')['MRR'].sum().sort_values(ascending=False)
        total_revenue = segment_revenue.sum()

        revenue_contribution = pd.DataFrame({
            'Segment': segment_revenue.index,
            'Total MRR': segment_revenue.values,
            'Percentage': (segment_revenue.values / total_revenue * 100).round(1)
        })

        st.dataframe(revenue_contribution, use_container_width=True)

    # Tab 3: Package Tier segmentation
    with tab3:
        st.markdown("""
        Users segmented by their current package tier.
        """)

        # Get latest package tier for each user
        latest_month = usage_df['MONTH'].max()
        user_tiers = usage_df[usage_df['MONTH'] == latest_month][['USERID', 'PACKAGE_TIER', 'MRR']].copy()

        # Tier metrics
        tier_counts = user_tiers['PACKAGE_TIER'].value_counts()

        st.subheader("Users by Package Tier")
        col1, col2, col3, col4 = st.columns(4)

        tiers = ['Basic', 'Standard', 'Premium', 'Enterprise']
        cols = [col1, col2, col3, col4]

        for tier, col in zip(tiers, cols):
            count = tier_counts.get(tier, 0)
            pct = (count / len(user_tiers) * 100) if len(user_tiers) > 0 else 0
            with col:
                st.metric(tier, f"{count:,}", f"{pct:.1f}%")

        st.markdown("---")

        # Visualization
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Package Tier Distribution")

            tier_df = pd.DataFrame({
                'Package Tier': tier_counts.index,
                'Count': tier_counts.values
            })

            st.bar_chart(tier_df.set_index('Package Tier'), height=350)

        with col2:
            st.subheader("Revenue by Package Tier")

            tier_revenue = user_tiers.groupby('PACKAGE_TIER')['MRR'].sum().sort_values(ascending=False)

            tier_revenue_df = pd.DataFrame({
                'Package Tier': tier_revenue.index,
                'Total MRR': tier_revenue.values
            })

            st.bar_chart(tier_revenue_df.set_index('Package Tier'), height=350)

        # Detailed package tier statistics
        st.markdown("---")
        st.subheader("Package Tier Statistics")

        tier_stats = user_tiers.groupby('PACKAGE_TIER').agg({
            'MRR': ['mean', 'median', 'sum'],
            'USERID': 'count'
        }).round(2)

        tier_stats.columns = ['Avg MRR', 'Median MRR', 'Total MRR', 'User Count']
        tier_stats = tier_stats.sort_values('Avg MRR', ascending=False)

        st.dataframe(tier_stats, use_container_width=True)

        # Package tier trends over time
        st.markdown("---")
        st.subheader("Package Tier User Trends")

        monthly_tier_users = usage_df.groupby(['MONTH', 'PACKAGE_TIER'])['USERID'].nunique().reset_index()
        tier_users_pivot = monthly_tier_users.pivot(index='MONTH', columns='PACKAGE_TIER', values='USERID')

        st.line_chart(tier_users_pivot, height=400)


def show_vintage_analysis(usage_df, churn_df):
    """Vintage analysis page showing cohort-based churn by signup month."""
    st.title("📅 Vintage Analysis")

    st.markdown("""
    Vintage (cohort) analysis tracks cumulative churn rates by signup period.

    **How to read this chart:**
    - Each line represents a cohort (vintage) of users who signed up in the same period
    - **X-axis**: Months on Book (0 = signup month, increases each month after signup)
    - **Y-axis**: Cumulative Churn Rate (%) - percentage of the cohort that has churned
    - Lines should trend upward over time as more users churn

    **Granularity Options:**
    - **Manual Selection**: Choose specific monthly vintages to compare
    - **By Quarter**: Aggregate vintages by quarter (e.g., 2024-Q1, 2024-Q2)
    - **By Year**: Aggregate vintages by year (e.g., 2023, 2024)
    """)

    # Step 1: Determine signup month (first month) for each user from usage data
    signup_data = usage_df.groupby('USERID')['MONTH'].min().reset_index()
    signup_data.columns = ['USERID', 'SIGNUP_MONTH']
    signup_data['VINTAGE'] = signup_data['SIGNUP_MONTH'].dt.to_period('M').astype(str)

    # Step 2: Merge signup data with all usage data
    usage_with_vintage = usage_df.merge(
        signup_data[['USERID', 'SIGNUP_MONTH', 'VINTAGE']],
        on='USERID'
    )

    # Step 3: Calculate tenure (months since signup)
    usage_with_vintage['TENURE'] = (
        (usage_with_vintage['MONTH'].dt.year - usage_with_vintage['SIGNUP_MONTH'].dt.year) * 12 +
        (usage_with_vintage['MONTH'].dt.month - usage_with_vintage['SIGNUP_MONTH'].dt.month)
    )

    # Step 4: Merge with churn data
    usage_with_vintage = usage_with_vintage.merge(
        churn_df[['USERID', 'CHURN_DATE']],
        on='USERID',
        how='left'
    )

    # Calculate churn month tenure (months from signup to churn)
    usage_with_vintage['CHURNED'] = usage_with_vintage['CHURN_DATE'].notna()
    usage_with_vintage['CHURN_TENURE'] = usage_with_vintage.apply(
        lambda row: (
            (row['CHURN_DATE'].year - row['SIGNUP_MONTH'].year) * 12 +
            (row['CHURN_DATE'].month - row['SIGNUP_MONTH'].month)
        ) if pd.notna(row['CHURN_DATE']) else None,
        axis=1
    )

    # Metrics selector
    st.markdown("---")
    col1, col2 = st.columns([2, 1])

    with col2:
        min_cohort_size = st.number_input(
            "Min Cohort Size",
            min_value=1,
            max_value=1000,
            value=5,
            help="Only show vintages with at least this many users"
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
        # Get all users in this vintage
        vintage_users = usage_with_vintage[usage_with_vintage['VINTAGE'] == vintage]
        total_users = vintage_users['USERID'].nunique()

        # Get max tenure for this vintage
        max_tenure = vintage_users['TENURE'].max()

        # For each tenure month from 0 to max
        for tenure in range(0, int(max_tenure) + 1):
            # Count users that had churned BY (on or before) this tenure
            # This ensures cumulative counting
            churned_by_tenure = vintage_users[
                (vintage_users['CHURNED']) &
                (vintage_users['CHURN_TENURE'] <= tenure)
            ]['USERID'].nunique()

            cumulative_churn_rate = (churned_by_tenure / total_users * 100) if total_users > 0 else 0

            churn_by_vintage_tenure.append({
                'VINTAGE': vintage,
                'TENURE': tenure,
                'TOTAL_USERS': total_users,
                'CHURNED_USERS': churned_by_tenure,
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
            ["Manual Selection", "By Quarter", "By Year"],
            horizontal=False,
            key="vintage_filter_type"
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
                default=quarters,  # Select all quarters by default
                key=f"vintage_quarters_{len(quarters)}"  # Key changes with data
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
                default=years,  # Select all years by default
                key=f"vintage_years_{len(years)}"  # Key changes with data
            )

        # Filter vintages by selected years
        selected_vintages = [v for v in available_vintages if v[:4] in selected_years]

    else:  # Manual Selection
        with col2:
            selected_vintages = st.multiselect(
                "Select vintages to compare",
                options=available_vintages,
                default=available_vintages,  # Select all vintages by default
                key=f"vintage_manual_{len(available_vintages)}"  # Key changes with data
            )

    # Display analysis
    st.markdown("---")

    if selected_vintages:
        # Filter data
        filtered_churn = churn_df_analysis[churn_df_analysis['VINTAGE'].isin(selected_vintages)].copy()

        # Aggregate data based on filter type
        if filter_type == "By Quarter":
            st.subheader(f"Vintage Cohort Analysis - Quarterly ({len(selected_quarters)} quarters selected)")

            # Add quarter column to filtered_churn
            filtered_churn['QUARTER'] = filtered_churn['VINTAGE'].apply(
                lambda v: v[:4] + '-Q' + str((int(v[5:7])-1)//3 + 1)
            )

            # Aggregate by quarter and tenure
            quarterly_churn = filtered_churn.groupby(['QUARTER', 'TENURE']).agg({
                'TOTAL_USERS': 'sum',
                'CHURNED_USERS': 'sum'
            }).reset_index()

            # Recalculate cumulative churn rate for aggregated data
            quarterly_churn['CUMULATIVE_CHURN_RATE'] = (
                quarterly_churn['CHURNED_USERS'] / quarterly_churn['TOTAL_USERS'] * 100
            ).fillna(0)

            # Create pivot for chart
            display_pivot = quarterly_churn.pivot(
                index='TENURE',
                columns='QUARTER',
                values='CUMULATIVE_CHURN_RATE'
            )

            # Reindex to ensure tenure starts at 0 and goes to max_tenure
            display_pivot = display_pivot.reindex(range(0, max_tenure_overall + 1), fill_value=None)

            st.line_chart(display_pivot, height=500)
            st.caption(f"**Months on Book:** 0 to {max_tenure_overall} months | **Cumulative Churn Rate:** Percentage of cohort churned | **Granularity:** Quarterly")

            # Show data table
            st.markdown("### Detailed Churn Data by Quarter")

            # Display summary for selected quarters
            summary_data = []
            for quarter in sorted(quarterly_churn['QUARTER'].unique()):
                quarter_data = quarterly_churn[quarterly_churn['QUARTER'] == quarter]
                if not quarter_data.empty:
                    max_tenure_data = quarter_data[quarter_data['TENURE'] == quarter_data['TENURE'].max()].iloc[0]
                    summary_data.append({
                        'Quarter': quarter,
                        'Total Users': int(max_tenure_data['TOTAL_USERS']),
                        'Max Tenure (Months)': int(max_tenure_data['TENURE']),
                        'Final Churn Rate (%)': round(max_tenure_data['CUMULATIVE_CHURN_RATE'], 2),
                        'Churned Users': int(max_tenure_data['CHURNED_USERS'])
                    })

            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df, use_container_width=True)

            # Optionally show raw data
            with st.expander("Show Raw Cohort Data"):
                st.dataframe(display_pivot.round(2), use_container_width=True)

        elif filter_type == "By Year":
            st.subheader(f"Vintage Cohort Analysis - Yearly ({len(selected_years)} years selected)")

            # Add year column to filtered_churn
            filtered_churn['YEAR'] = filtered_churn['VINTAGE'].apply(lambda v: v[:4])

            # Aggregate by year and tenure
            yearly_churn = filtered_churn.groupby(['YEAR', 'TENURE']).agg({
                'TOTAL_USERS': 'sum',
                'CHURNED_USERS': 'sum'
            }).reset_index()

            # Recalculate cumulative churn rate for aggregated data
            yearly_churn['CUMULATIVE_CHURN_RATE'] = (
                yearly_churn['CHURNED_USERS'] / yearly_churn['TOTAL_USERS'] * 100
            ).fillna(0)

            # Create pivot for chart
            display_pivot = yearly_churn.pivot(
                index='TENURE',
                columns='YEAR',
                values='CUMULATIVE_CHURN_RATE'
            )

            # Reindex to ensure tenure starts at 0 and goes to max_tenure
            display_pivot = display_pivot.reindex(range(0, max_tenure_overall + 1), fill_value=None)

            st.line_chart(display_pivot, height=500)
            st.caption(f"**Months on Book:** 0 to {max_tenure_overall} months | **Cumulative Churn Rate:** Percentage of cohort churned | **Granularity:** Yearly")

            # Show data table
            st.markdown("### Detailed Churn Data by Year")

            # Display summary for selected years
            summary_data = []
            for year in sorted(yearly_churn['YEAR'].unique()):
                year_data = yearly_churn[yearly_churn['YEAR'] == year]
                if not year_data.empty:
                    max_tenure_data = year_data[year_data['TENURE'] == year_data['TENURE'].max()].iloc[0]
                    summary_data.append({
                        'Year': year,
                        'Total Users': int(max_tenure_data['TOTAL_USERS']),
                        'Max Tenure (Months)': int(max_tenure_data['TENURE']),
                        'Final Churn Rate (%)': round(max_tenure_data['CUMULATIVE_CHURN_RATE'], 2),
                        'Churned Users': int(max_tenure_data['CHURNED_USERS'])
                    })

            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df, use_container_width=True)

            # Optionally show raw data
            with st.expander("Show Raw Cohort Data"):
                st.dataframe(display_pivot.round(2), use_container_width=True)

        else:  # Manual Selection - keep monthly granularity
            st.subheader(f"Vintage Cohort Analysis - Monthly ({len(selected_vintages)} vintages selected)")

            # Ensure we have complete tenure range from 0 to max
            display_pivot = filtered_churn.pivot(
                index='TENURE',
                columns='VINTAGE',
                values='CUMULATIVE_CHURN_RATE'
            )

            # Reindex to ensure tenure starts at 0 and goes to max_tenure
            display_pivot = display_pivot.reindex(range(0, max_tenure_overall + 1), fill_value=None)

            st.line_chart(display_pivot, height=500)
            st.caption(f"**Months on Book:** 0 to {max_tenure_overall} months | **Cumulative Churn Rate:** Percentage of cohort churned | **Granularity:** Monthly")

            # Show data table
            st.markdown("### Detailed Churn Data by Month")

            # Display summary for selected vintages
            summary_data = []
            for vintage in selected_vintages:
                vintage_data = filtered_churn[filtered_churn['VINTAGE'] == vintage]
                if not vintage_data.empty:
                    max_tenure_data = vintage_data[vintage_data['TENURE'] == vintage_data['TENURE'].max()].iloc[0]
                    summary_data.append({
                        'Vintage': vintage,
                        'Total Users': int(max_tenure_data['TOTAL_USERS']),
                        'Max Tenure (Months)': int(max_tenure_data['TENURE']),
                        'Final Churn Rate (%)': round(max_tenure_data['CUMULATIVE_CHURN_RATE'], 2),
                        'Churned Users': int(max_tenure_data['CHURNED_USERS'])
                    })

            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df, use_container_width=True)

            # Optionally show raw data
            with st.expander("Show Raw Cohort Data"):
                st.dataframe(display_pivot.round(2), use_container_width=True)

        # Additional insights - adapt to filter type
        st.markdown("---")
        st.subheader("Cohort Performance at Key Milestones")

        # Calculate churn rate at specific tenure milestones
        milestones = [6, 12, 24, 36]  # 6 months, 1 year, 2 years, 3 years

        if filter_type == "By Quarter":
            milestone_data = []
            for quarter in sorted(quarterly_churn['QUARTER'].unique()):
                quarter_churn = quarterly_churn[quarterly_churn['QUARTER'] == quarter]
                if quarter_churn.empty:
                    continue

                row = {'Quarter': quarter}
                for milestone in milestones:
                    milestone_churn = quarter_churn[quarter_churn['TENURE'] == milestone]
                    if not milestone_churn.empty:
                        row[f'{milestone}M Churn %'] = round(milestone_churn.iloc[0]['CUMULATIVE_CHURN_RATE'], 2)
                    else:
                        row[f'{milestone}M Churn %'] = None
                milestone_data.append(row)

            if milestone_data:
                milestone_df = pd.DataFrame(milestone_data)
                st.dataframe(milestone_df, use_container_width=True)
                st.caption("Churn rates at key tenure milestones (6, 12, 24, 36 months) for selected quarters")

        elif filter_type == "By Year":
            milestone_data = []
            for year in sorted(yearly_churn['YEAR'].unique()):
                year_churn = yearly_churn[yearly_churn['YEAR'] == year]
                if year_churn.empty:
                    continue

                row = {'Year': year}
                for milestone in milestones:
                    milestone_churn = year_churn[year_churn['TENURE'] == milestone]
                    if not milestone_churn.empty:
                        row[f'{milestone}M Churn %'] = round(milestone_churn.iloc[0]['CUMULATIVE_CHURN_RATE'], 2)
                    else:
                        row[f'{milestone}M Churn %'] = None
                milestone_data.append(row)

            if milestone_data:
                milestone_df = pd.DataFrame(milestone_data)
                st.dataframe(milestone_df, use_container_width=True)
                st.caption("Churn rates at key tenure milestones (6, 12, 24, 36 months) for selected years")

        else:  # Manual Selection
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

    else:
        st.info("Please select at least one vintage to display the analysis.")


def show_account_lookup(account_df, usage_df, churn_df):
    """9BOX & Insights page with detailed usage trends and AI analysis."""
    st.title("📊 9BOX & Insights")

    st.markdown("Select a User ID to view detailed usage and revenue trends.")

    # Get unique user IDs from usage data (this is what we actually have)
    unique_users = sorted(usage_df['USERID'].unique())

    # Account selector
    selected_account = st.selectbox(
        "Select User ID",
        options=unique_users,
        help="Choose a user ID from the dropdown or search"
    )

    if selected_account:
        # Filter data for selected user
        usage_data = usage_df[usage_df['USERID'] == selected_account]

        # Try to get account data if available (may not exist for simulated users)
        account_data = account_df[account_df['SERVICE_ACCOUNT_ID'] == selected_account]

        if usage_data.empty:
            st.warning(f"No usage data found for User ID: {selected_account}")
            return

        # Display account summary
        st.markdown("### Account Summary")

        # If we have account data from ACCOUNT_ATTRIBUTES_MONTHLY, show it
        if not account_data.empty:
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
        else:
            # For simulated users, show what we have from usage data
            st.info(f"**User ID:** {selected_account} | **Data Source:** Simulated Phone Usage Data")
        
        # Check if account has churned
        if not churn_df.empty and selected_account in churn_df['USERID'].values:
            churn_info = churn_df[churn_df['USERID'] == selected_account].iloc[0]
            if pd.notna(churn_info['CHURN_DATE']):
                st.warning(f"⚠️ This account churned on {churn_info['CHURN_DATE'].strftime('%Y-%m-%d')}")
            else:
                st.warning("⚠️ This account has churned (date unavailable)")
        
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

        # Revenue metrics
        st.markdown("### Revenue Metrics")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            latest_mrr = usage_data_sorted['MRR'].iloc[-1] if len(usage_data_sorted) > 0 else 0
            st.metric("Current MRR", f"${latest_mrr:.2f}")
        with col2:
            avg_mrr = usage_data[usage_data['MRR'] > 0]['MRR'].mean()
            st.metric("Avg MRR", f"${avg_mrr:.2f}")
        with col3:
            total_revenue = usage_data['MRR'].sum()
            st.metric("Total Revenue (All Months)", f"${total_revenue:,.2f}")
        with col4:
            # Get package tier (from latest month)
            current_tier = usage_data_sorted['PACKAGE_TIER'].iloc[-1] if len(usage_data_sorted) > 0 else "Unknown"
            st.metric("Package Tier", current_tier)
        
        st.markdown("---")

        # Quick Q&A Section
        st.markdown("### 💬 Ask Questions About This Account")

        # Get available models for Q&A
        qa_models, qa_model_source = get_available_llm_models()

        # Model selector (shared across Q&A and Advanced Insights)
        if qa_models and len(qa_models) > 0:
            selected_qa_model = st.selectbox(
                "Select AI Model",
                options=qa_models,
                key="shared_model_selector",
                help="Choose an AI model (applies to both Q&A and Advanced Insights)"
            )
        else:
            selected_qa_model = None

        col1, col2 = st.columns([3, 1])

        with col1:
            if qa_models and len(qa_models) > 0:

                # Question input
                user_question = st.text_input(
                    "Your Question",
                    placeholder="e.g., What trends do you see in this account's usage? Is this account at risk of churning?",
                    key="user_question_input"
                )

                # Ask button
                if st.button("🔍 Ask", type="primary", key="ask_button"):
                    if user_question:
                        with st.spinner(f"Thinking with {selected_qa_model}..."):
                            # Prepare context
                            account_info = latest_account if not account_data.empty else None
                            account_context = prepare_account_context(
                                selected_account, account_info, usage_data_sorted, avg_calls, avg_minutes
                            )

                            # Create prompt
                            qa_prompt = f"""Based on the following account information, please answer this question:

Question: {user_question}

Account Context:
{account_context}

Please provide a clear, concise answer based on the data provided."""

                            # Generate response
                            try:
                                answer, input_tokens, output_tokens = generate_ai_insights(
                                    selected_qa_model,
                                    qa_prompt,
                                    ""  # No additional context needed
                                )

                                # Display answer
                                st.markdown("#### 💡 Answer:")
                                st.markdown(answer)

                                # Show token usage
                                total_tokens = input_tokens + output_tokens
                                st.caption(f"Token usage: {input_tokens:,} input + {output_tokens:,} output = {total_tokens:,} total")

                            except Exception as e:
                                st.error(f"Error generating answer: {str(e)}")
                    else:
                        st.warning("Please enter a question first.")
            else:
                st.info("AI models not available. Please check your Snowflake Cortex configuration.")

        with col2:
            st.markdown("**Quick Tips:**")
            st.markdown("""
            - Ask about trends
            - Request predictions
            - Seek recommendations
            - Compare metrics
            """)

        st.markdown("---")

        # AI Insights Section
        st.markdown("### 🤖 AI Insights Assistant (Advanced)")

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

        # Use the shared model selector from Q&A section
        # Display model pricing information
        if selected_qa_model and selected_qa_model in model_pricing:
            st.info(f"**Current Model:** {selected_qa_model} (~${model_pricing[selected_qa_model]['cost']:.2f}/{model_pricing[selected_qa_model]['per']} est.)")
        elif selected_qa_model:
            st.info(f"**Current Model:** {selected_qa_model}")

        # Set llm_provider to the shared selection
        llm_provider = selected_qa_model

        col1, col2 = st.columns([2, 3])

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
                # Pass latest_account if available, otherwise None
                account_info = latest_account if not account_data.empty else None
                account_context = prepare_account_context(
                    selected_account, account_info, usage_data_sorted, avg_calls, avg_minutes
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

        # Revenue trends
        st.markdown("### Revenue Trends Over Time")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Monthly Recurring Revenue (MRR)")
            mrr_chart = pd.DataFrame({
                'MONTH': usage_data_sorted['MONTH'],
                'MRR': usage_data_sorted['MRR']
            })
            st.line_chart(mrr_chart.set_index('MONTH'), height=400)

        with col2:
            st.subheader("Package Tier History")
            # Show package tier changes over time
            tier_history = usage_data_sorted[['MONTH', 'PACKAGE_TIER']].copy()
            tier_history['MONTH_STR'] = tier_history['MONTH'].dt.strftime('%Y-%m')

            st.dataframe(
                tier_history[['MONTH_STR', 'PACKAGE_TIER']].rename(
                    columns={'MONTH_STR': 'Month', 'PACKAGE_TIER': 'Package Tier'}
                ),
                use_container_width=True,
                height=400
            )

        # Usage trends over time
        st.markdown("---")
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
            'MONTH', 'PACKAGE_TIER', 'MRR', 'PHONE_TOTAL_CALLS', 'PHONE_TOTAL_MINUTES_OF_USE',
            'VOICE_CALLS', 'FAX_CALLS', 'PHONE_TOTAL_NUM_INBOUND_CALLS',
            'PHONE_TOTAL_NUM_OUTBOUND_CALLS', 'HARDPHONE_CALLS', 'SOFTPHONE_CALLS',
            'MOBILE_CALLS', 'PHONE_MAU'
        ]

        display_table = usage_data_sorted[display_columns].copy()
        display_table['MONTH'] = display_table['MONTH'].dt.strftime('%Y-%m')
        display_table = display_table.rename(columns={
            'MONTH': 'Month',
            'PACKAGE_TIER': 'Package Tier',
            'MRR': 'MRR',
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


def show_access_roles_dashboard():
    """Access and Roles Management Dashboard."""
    st.title("🔐 Access & Roles Dashboard")
    st.markdown("Monitor and manage user access, roles, and permissions across your Snowflake account.")

    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["👥 Users", "🎭 Roles", "🔍 User Details", "📊 Role Details"])

    # Tab 1: Users Overview
    with tab1:
        st.header("Users Overview")

        with st.spinner("Loading users..."):
            users_df = load_users_and_roles()

        if not users_df.empty:
            # Display key metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                total_users = len(users_df)
                st.metric("Total Users", f"{total_users:,}")

            with col2:
                # Count users by has_password (if column exists)
                if 'HAS_PASSWORD' in users_df.columns:
                    password_users = users_df[users_df['HAS_PASSWORD'] == 'true'].shape[0]
                    st.metric("Password Auth", f"{password_users:,}")
                else:
                    st.metric("N/A", "-")

            with col3:
                # Count disabled users
                if 'DISABLED' in users_df.columns:
                    disabled_users = users_df[users_df['DISABLED'] == 'true'].shape[0]
                    st.metric("Disabled Users", f"{disabled_users:,}")
                else:
                    st.metric("N/A", "-")

            with col4:
                # Count users with default role
                if 'DEFAULT_ROLE' in users_df.columns:
                    users_with_role = users_df[users_df['DEFAULT_ROLE'].notna()].shape[0]
                    st.metric("With Default Role", f"{users_with_role:,}")
                else:
                    st.metric("N/A", "-")

            st.markdown("---")

            # Search and filter
            search_term = st.text_input("🔍 Search Users", placeholder="Enter username...")

            # Filter users based on search
            if search_term:
                if 'NAME' in users_df.columns:
                    filtered_users = users_df[users_df['NAME'].str.contains(search_term, case=False, na=False)]
                else:
                    filtered_users = users_df
            else:
                filtered_users = users_df

            # Display users table
            st.subheader(f"Users ({len(filtered_users)} shown)")

            # Select columns to display
            display_columns = []
            if 'NAME' in filtered_users.columns:
                display_columns.append('NAME')
            if 'CREATED_ON' in filtered_users.columns:
                display_columns.append('CREATED_ON')
            if 'LOGIN_NAME' in filtered_users.columns:
                display_columns.append('LOGIN_NAME')
            if 'DISPLAY_NAME' in filtered_users.columns:
                display_columns.append('DISPLAY_NAME')
            if 'DEFAULT_ROLE' in filtered_users.columns:
                display_columns.append('DEFAULT_ROLE')
            if 'DEFAULT_WAREHOUSE' in filtered_users.columns:
                display_columns.append('DEFAULT_WAREHOUSE')
            if 'DISABLED' in filtered_users.columns:
                display_columns.append('DISABLED')

            if display_columns:
                st.dataframe(
                    filtered_users[display_columns],
                    use_container_width=True,
                    height=400
                )
            else:
                st.dataframe(filtered_users, use_container_width=True, height=400)

            # Download button
            csv = filtered_users.to_csv(index=False)
            st.download_button(
                label="📥 Download Users Data",
                data=csv,
                file_name="snowflake_users.csv",
                mime="text/csv"
            )
        else:
            st.warning("No users found or insufficient permissions to view users.")

    # Tab 2: Roles Overview
    with tab2:
        st.header("Roles Overview")

        with st.spinner("Loading roles..."):
            roles_df = load_roles()

        if not roles_df.empty:
            # Display key metrics
            col1, col2, col3 = st.columns(3)

            with col1:
                total_roles = len(roles_df)
                st.metric("Total Roles", f"{total_roles:,}")

            with col2:
                # Count custom roles (excluding system roles)
                if 'NAME' in roles_df.columns:
                    system_roles = ['ACCOUNTADMIN', 'SECURITYADMIN', 'SYSADMIN', 'USERADMIN', 'PUBLIC']
                    custom_roles = roles_df[~roles_df['NAME'].isin(system_roles)].shape[0]
                    st.metric("Custom Roles", f"{custom_roles:,}")
                else:
                    st.metric("N/A", "-")

            with col3:
                # Count system roles
                if 'NAME' in roles_df.columns:
                    system_roles_count = roles_df[roles_df['NAME'].isin(system_roles)].shape[0]
                    st.metric("System Roles", f"{system_roles_count:,}")
                else:
                    st.metric("N/A", "-")

            st.markdown("---")

            # Search roles
            search_role = st.text_input("🔍 Search Roles", placeholder="Enter role name...")

            # Filter roles based on search
            if search_role:
                if 'NAME' in roles_df.columns:
                    filtered_roles = roles_df[roles_df['NAME'].str.contains(search_role, case=False, na=False)]
                else:
                    filtered_roles = roles_df
            else:
                filtered_roles = roles_df

            # Display roles table
            st.subheader(f"Roles ({len(filtered_roles)} shown)")

            # Select columns to display
            display_columns = []
            if 'CREATED_ON' in filtered_roles.columns:
                display_columns.append('CREATED_ON')
            if 'NAME' in filtered_roles.columns:
                display_columns.append('NAME')
            if 'COMMENT' in filtered_roles.columns:
                display_columns.append('COMMENT')
            if 'OWNER' in filtered_roles.columns:
                display_columns.append('OWNER')

            if display_columns:
                st.dataframe(
                    filtered_roles[display_columns],
                    use_container_width=True,
                    height=400
                )
            else:
                st.dataframe(filtered_roles, use_container_width=True, height=400)

            # Download button
            csv = filtered_roles.to_csv(index=False)
            st.download_button(
                label="📥 Download Roles Data",
                data=csv,
                file_name="snowflake_roles.csv",
                mime="text/csv"
            )
        else:
            st.warning("No roles found or insufficient permissions to view roles.")

    # Tab 3: User Details
    with tab3:
        st.header("User Access Details")
        st.markdown("View detailed access information for a specific user.")

        if not users_df.empty and 'NAME' in users_df.columns:
            # User selection
            selected_user = st.selectbox(
                "Select User",
                options=sorted(users_df['NAME'].tolist()),
                key="user_detail_select"
            )

            if selected_user:
                st.subheader(f"Access Details for: {selected_user}")

                # User information
                user_info = users_df[users_df['NAME'] == selected_user].iloc[0]

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**User Information**")
                    if 'LOGIN_NAME' in user_info:
                        st.text(f"Login Name: {user_info.get('LOGIN_NAME', 'N/A')}")
                    if 'DISPLAY_NAME' in user_info:
                        st.text(f"Display Name: {user_info.get('DISPLAY_NAME', 'N/A')}")
                    if 'DEFAULT_ROLE' in user_info:
                        st.text(f"Default Role: {user_info.get('DEFAULT_ROLE', 'N/A')}")
                    if 'DEFAULT_WAREHOUSE' in user_info:
                        st.text(f"Default Warehouse: {user_info.get('DEFAULT_WAREHOUSE', 'N/A')}")

                with col2:
                    st.markdown("**Account Status**")
                    if 'DISABLED' in user_info:
                        st.text(f"Disabled: {user_info.get('DISABLED', 'N/A')}")
                    if 'CREATED_ON' in user_info:
                        st.text(f"Created On: {user_info.get('CREATED_ON', 'N/A')}")
                    if 'HAS_PASSWORD' in user_info:
                        st.text(f"Has Password: {user_info.get('HAS_PASSWORD', 'N/A')}")

                st.markdown("---")

                # Get grants for this user
                with st.spinner(f"Loading grants for {selected_user}..."):
                    user_grants = get_grants_for_user(selected_user)

                if not user_grants.empty:
                    st.subheader("Roles Granted to User")
                    st.dataframe(user_grants, use_container_width=True, height=300)

                    # Download button
                    csv = user_grants.to_csv(index=False)
                    st.download_button(
                        label=f"📥 Download {selected_user}'s Grants",
                        data=csv,
                        file_name=f"grants_{selected_user}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info(f"No grants found for user {selected_user}.")
        else:
            st.warning("No users available for detailed view.")

    # Tab 4: Role Details
    with tab4:
        st.header("Role Permissions Details")
        st.markdown("View detailed permissions and users assigned to a specific role.")

        if not roles_df.empty and 'NAME' in roles_df.columns:
            # Role selection
            selected_role = st.selectbox(
                "Select Role",
                options=sorted(roles_df['NAME'].tolist()),
                key="role_detail_select"
            )

            if selected_role:
                st.subheader(f"Details for Role: {selected_role}")

                # Role information
                role_info = roles_df[roles_df['NAME'] == selected_role].iloc[0]

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Role Information**")
                    if 'CREATED_ON' in role_info:
                        st.text(f"Created On: {role_info.get('CREATED_ON', 'N/A')}")
                    if 'OWNER' in role_info:
                        st.text(f"Owner: {role_info.get('OWNER', 'N/A')}")

                with col2:
                    st.markdown("**Description**")
                    if 'COMMENT' in role_info:
                        comment = role_info.get('COMMENT', 'No description available')
                        st.text(comment if comment else 'No description available')

                st.markdown("---")

                # Create sub-tabs for grants and users
                subtab1, subtab2 = st.tabs(["📋 Permissions", "👥 Users with Role"])

                with subtab1:
                    # Get grants for this role
                    with st.spinner(f"Loading permissions for {selected_role}..."):
                        role_grants = get_grants_for_role(selected_role)

                    if not role_grants.empty:
                        st.subheader("Permissions Granted to Role")

                        # Add filters for grant type
                        if 'PRIVILEGE' in role_grants.columns:
                            privilege_filter = st.multiselect(
                                "Filter by Privilege Type",
                                options=sorted(role_grants['PRIVILEGE'].unique().tolist()),
                                default=[]
                            )

                            if privilege_filter:
                                filtered_grants = role_grants[role_grants['PRIVILEGE'].isin(privilege_filter)]
                            else:
                                filtered_grants = role_grants

                            st.dataframe(filtered_grants, use_container_width=True, height=400)

                            # Download button
                            csv = filtered_grants.to_csv(index=False)
                            st.download_button(
                                label=f"📥 Download {selected_role}'s Permissions",
                                data=csv,
                                file_name=f"permissions_{selected_role}.csv",
                                mime="text/csv"
                            )
                        else:
                            st.dataframe(role_grants, use_container_width=True, height=400)
                    else:
                        st.info(f"No grants found for role {selected_role}.")

                with subtab2:
                    # Get users with this role
                    with st.spinner(f"Loading users with {selected_role}..."):
                        users_with_role = get_users_with_role(selected_role)

                    if not users_with_role.empty:
                        st.subheader(f"Users Granted {selected_role}")
                        st.dataframe(users_with_role, use_container_width=True, height=400)

                        # Download button
                        csv = users_with_role.to_csv(index=False)
                        st.download_button(
                            label=f"📥 Download Users with {selected_role}",
                            data=csv,
                            file_name=f"users_with_{selected_role}.csv",
                            mime="text/csv"
                        )
                    else:
                        st.info(f"No users found with role {selected_role}.")
        else:
            st.warning("No roles available for detailed view.")


if __name__ == "__main__":
    main()
