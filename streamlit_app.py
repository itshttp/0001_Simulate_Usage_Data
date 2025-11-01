"""
Phone Usage Analytics Dashboard

A Streamlit dashboard for analyzing phone usage data, churn patterns,
and account metrics from Snowflake.

Run with: streamlit run streamlit_app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import snowflake.connector
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Page configuration
st.set_page_config(
    page_title="Phone Usage Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load environment variables
load_dotenv()


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


@st.cache_resource
def get_snowflake_connection():
    """Create and cache Snowflake connection."""
    try:
        conn = snowflake.connector.connect(
            account=os.getenv('SNOWFLAKE_ACCOUNT'),
            user=os.getenv('SNOWFLAKE_USER'),
            password=os.getenv('SNOWFLAKE_PASSWORD'),
            warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
            database=os.getenv('SNOWFLAKE_DATABASE'),
            schema=os.getenv('SNOWFLAKE_SCHEMA'),
            role=os.getenv('SNOWFLAKE_ROLE') if os.getenv('SNOWFLAKE_ROLE') else None
        )
        return conn
    except Exception as e:
        st.error(f"Failed to connect to Snowflake: {e}")
        st.info("Please check your .env file and ensure all credentials are correct.")
        return None


@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_account_data():
    """Load account data from Snowflake."""
    conn = get_snowflake_connection()
    if conn is None:
        return pd.DataFrame()

    query = "SELECT * FROM ACCOUNT_ATTRIBUTES_MONTHLY"
    df = pd.read_sql(query, conn)
    df['MONTH'] = pd.to_datetime(df['MONTH'])
    return df


@st.cache_data(ttl=300)
def load_usage_data():
    """Load usage data from Snowflake."""
    conn = get_snowflake_connection()
    if conn is None:
        return pd.DataFrame()

    query = "SELECT * FROM PHONE_USAGE_DATA"
    df = pd.read_sql(query, conn)
    df['MONTH'] = pd.to_datetime(df['MONTH'])
    return df


@st.cache_data(ttl=300)
def load_churn_data():
    """Load churn data from Snowflake."""
    conn = get_snowflake_connection()
    if conn is None:
        return pd.DataFrame()

    query = "SELECT * FROM CHURN_RECORDS"
    df = pd.read_sql(query, conn)
    df['CHURN_DATE'] = pd.to_datetime(df['CHURN_DATE'])
    return df


def main():
    """Main dashboard application."""

    # Sidebar
    st.sidebar.title("📊 Phone Usage Analytics")
    st.sidebar.markdown("---")

    # Page selection
    page = st.sidebar.radio(
        "Navigation",
        ["🏠 Overview", "👥 Account Analytics", "📈 Usage Trends",
         "⚠️ Churn Analysis", "🎯 User Segmentation"]
    )

    # Load data
    with st.spinner("Loading data from Snowflake..."):
        account_df = load_account_data()
        usage_df = load_usage_data()
        churn_df = load_churn_data()

    if account_df.empty or usage_df.empty:
        st.error("Unable to load data. Please check Snowflake connection.")
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

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=monthly_usage['MONTH'],
            y=monthly_usage['PHONE_TOTAL_CALLS'],
            mode='lines+markers',
            name='Avg Calls',
            line=dict(color='#1f77b4', width=2)
        ))

        fig.update_layout(
            height=400,
            xaxis_title="Month",
            yaxis_title="Average Calls per User",
            hovermode='x unified'
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Account Status Distribution")

        # Get latest status for each account
        latest_accounts = account_df.sort_values('MONTH').groupby('SERVICE_ACCOUNT_ID').last()
        status_counts = latest_accounts['SA_ACCT_STATUS'].value_counts()

        fig = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="",
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig.update_layout(height=400)
        fig.update_traces(textposition='inside', textinfo='percent+label')

        st.plotly_chart(fig, use_container_width=True)

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

        fig = px.bar(
            x=company_avg.index,
            y=company_avg.values,
            labels={'x': 'Company', 'y': 'Avg Calls per Month'},
            title="Average Usage by Company"
        )
        fig.update_layout(height=400, showlegend=False)

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # User activity histogram
        user_avg = usage_df.groupby('USERID')['PHONE_TOTAL_CALLS'].mean()

        fig = px.histogram(
            user_avg,
            nbins=30,
            labels={'value': 'Avg Calls per Month', 'count': 'Number of Users'},
            title="User Activity Distribution"
        )
        fig.update_layout(height=400, showlegend=False)

        st.plotly_chart(fig, use_container_width=True)


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

        fig = px.bar(
            x=brand_counts.index,
            y=brand_counts.values,
            labels={'x': 'Brand', 'y': 'Number of Accounts'},
            color=brand_counts.values,
            color_continuous_scale='Blues'
        )
        fig.update_layout(height=400, showlegend=False)

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Accounts by Package")

        package_counts = latest['PACKAGE_NAME'].value_counts()

        fig = px.bar(
            x=package_counts.index,
            y=package_counts.values,
            labels={'x': 'Package', 'y': 'Number of Accounts'},
            color=package_counts.values,
            color_continuous_scale='Greens'
        )
        fig.update_layout(height=400, showlegend=False)

        st.plotly_chart(fig, use_container_width=True)

    # Account growth over time
    st.markdown("---")
    st.subheader("Account Growth Over Time")

    # Count active accounts per month
    active_by_month = account_df[account_df['SA_ACCT_STATUS'] == 'Active'].groupby('MONTH')['SERVICE_ACCOUNT_ID'].nunique().reset_index()
    active_by_month.columns = ['MONTH', 'Active Accounts']

    fig = px.line(
        active_by_month,
        x='MONTH',
        y='Active Accounts',
        markers=True,
        title=""
    )
    fig.update_layout(height=400)

    st.plotly_chart(fig, use_container_width=True)

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

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=monthly_agg['MONTH'],
        y=monthly_agg[metric],
        mode='lines+markers',
        name=metric_labels[metric],
        line=dict(width=3)
    ))

    fig.update_layout(
        height=500,
        xaxis_title="Month",
        yaxis_title=metric_labels[metric],
        hovermode='x unified'
    )

    st.plotly_chart(fig, use_container_width=True)

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

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=monthly_direction['MONTH'],
            y=monthly_direction['PHONE_TOTAL_NUM_INBOUND_CALLS'],
            mode='lines+markers',
            name='Inbound',
            line=dict(color='#2ecc71')
        ))
        fig.add_trace(go.Scatter(
            x=monthly_direction['MONTH'],
            y=monthly_direction['PHONE_TOTAL_NUM_OUTBOUND_CALLS'],
            mode='lines+markers',
            name='Outbound',
            line=dict(color='#3498db')
        ))

        fig.update_layout(
            height=400,
            title="Inbound vs Outbound Calls",
            xaxis_title="Month",
            yaxis_title="Average Calls"
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Device type distribution
        device_totals = {
            'Hardphone': usage_df['HARDPHONE_CALLS'].sum(),
            'Softphone': usage_df['SOFTPHONE_CALLS'].sum(),
            'Mobile': usage_df['MOBILE_CALLS'].sum()
        }

        fig = px.pie(
            values=list(device_totals.values()),
            names=list(device_totals.keys()),
            title="Calls by Device Type"
        )
        fig.update_layout(height=400)

        st.plotly_chart(fig, use_container_width=True)


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

    fig = px.bar(
        churn_by_month,
        x='Month',
        y='Churned Users',
        title="",
        color='Churned Users',
        color_continuous_scale='Reds'
    )
    fig.update_layout(height=400)

    st.plotly_chart(fig, use_container_width=True)

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

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=decline_pattern['MONTHS_BEFORE_CHURN'],
        y=decline_pattern['PHONE_TOTAL_CALLS'],
        mode='lines+markers',
        name='Avg Calls',
        line=dict(color='#e74c3c', width=3)
    ))

    fig.add_vline(x=0, line_dash="dash", line_color="gray", annotation_text="Churn Date")

    fig.update_layout(
        height=400,
        xaxis_title="Months Before Churn",
        yaxis_title="Average Total Calls",
        hovermode='x unified'
    )

    st.plotly_chart(fig, use_container_width=True)

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
        # Pie chart
        segment_counts = user_avg['Segment'].value_counts()

        fig = px.pie(
            values=segment_counts.values,
            names=segment_counts.index,
            title="User Segment Distribution",
            color=segment_counts.index,
            color_discrete_map={'Heavy': '#e74c3c', 'Medium': '#f39c12', 'Light': '#3498db'}
        )
        fig.update_layout(height=400)

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Box plot
        usage_with_segment = usage_df.merge(user_avg[['USERID', 'Segment']], on='USERID')

        fig = px.box(
            usage_with_segment,
            x='Segment',
            y='PHONE_TOTAL_CALLS',
            color='Segment',
            color_discrete_map={'Heavy': '#e74c3c', 'Medium': '#f39c12', 'Light': '#3498db'},
            title="Call Distribution by Segment"
        )
        fig.update_layout(height=400, showlegend=False)

        st.plotly_chart(fig, use_container_width=True)

    # Segment trends over time
    st.markdown("---")
    st.subheader("Segment Trends Over Time")

    # Aggregate by segment and month
    monthly_segment = usage_with_segment.groupby(['MONTH', 'Segment']).agg({
        'PHONE_TOTAL_CALLS': 'mean'
    }).reset_index()

    fig = px.line(
        monthly_segment,
        x='MONTH',
        y='PHONE_TOTAL_CALLS',
        color='Segment',
        color_discrete_map={'Heavy': '#e74c3c', 'Medium': '#f39c12', 'Light': '#3498db'},
        markers=True
    )

    fig.update_layout(
        height=400,
        xaxis_title="Month",
        yaxis_title="Average Calls per User"
    )

    st.plotly_chart(fig, use_container_width=True)

    # Detailed segment stats
    st.markdown("---")
    st.subheader("Segment Statistics")

    segment_stats = usage_with_segment.groupby('Segment').agg({
        'PHONE_TOTAL_CALLS': ['mean', 'median', 'std'],
        'PHONE_TOTAL_MINUTES_OF_USE': ['mean', 'median'],
        'PHONE_MAU': 'mean',
        'USERID': 'nunique'
    }).round(2)

    segment_stats.columns = ['_'.join(col).strip() for col in segment_stats.columns.values]
    segment_stats = segment_stats.reset_index()

    st.dataframe(segment_stats, use_container_width=True)


if __name__ == "__main__":
    main()
