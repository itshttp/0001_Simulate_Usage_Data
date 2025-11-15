"""
Account Usage Analytics Dashboard

A Streamlit dashboard for analyzing individual account usage patterns over time
with AI-powered insights using Snowflake Cortex.

Features:
- Account selection with search functionality
- 9 key usage metrics displayed in a 3x3 grid
- Time series visualization (month over month)
- AI-powered insights for each metric using Snowflake Cortex
"""

import streamlit as st
import pandas as pd
import altair as alt

# Page configuration
st.set_page_config(
    page_title="Account Usage Analytics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding: 0rem 1rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
        padding: 0.5rem;
        font-size: 0.9rem;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .metric-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .insight-box {
        background-color: #f0f8ff;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=600)
def load_account_data():
    """Load account attributes data."""
    try:
        query = """
        SELECT DISTINCT
            SERVICE_ACCOUNT_ID,
            COMPANY,
            SA_BRAND_NAME,
            PACKAGE_NAME,
            TIER_NAME
        FROM ACCOUNT_ATTRIBUTES_MONTHLY
        ORDER BY SERVICE_ACCOUNT_ID
        """
        return st.connection("snowflake").query(query)
    except Exception as e:
        st.error(f"Error loading account data: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=600)
def load_usage_data_for_account(account_id):
    """Load usage data for a specific account."""
    try:
        query = f"""
        SELECT
            MONTH,
            PHONE_TOTAL_CALLS,
            PHONE_TOTAL_MINUTES_OF_USE,
            VOICE_CALLS,
            VOICE_MINS,
            PHONE_TOTAL_NUM_INBOUND_CALLS,
            PHONE_TOTAL_NUM_OUTBOUND_CALLS,
            PHONE_MAU,
            HARDPHONE_CALLS,
            SOFTPHONE_CALLS
        FROM PHONE_USAGE_DATA
        WHERE USERID = {account_id}
        ORDER BY MONTH
        """
        df = st.connection("snowflake").query(query)
        df['MONTH'] = pd.to_datetime(df['MONTH'])
        return df
    except Exception as e:
        st.error(f"Error loading usage data: {e}")
        return pd.DataFrame()


def get_account_info(account_id):
    """Get account information for display."""
    try:
        query = f"""
        SELECT
            SERVICE_ACCOUNT_ID,
            COMPANY,
            SA_BRAND_NAME,
            PACKAGE_NAME,
            TIER_NAME,
            SA_ACCT_STATUS
        FROM ACCOUNT_ATTRIBUTES_MONTHLY
        WHERE SERVICE_ACCOUNT_ID = {account_id}
        LIMIT 1
        """
        return st.connection("snowflake").query(query)
    except Exception as e:
        st.error(f"Error loading account info: {e}")
        return pd.DataFrame()


def check_cortex_availability():
    """Check if Snowflake Cortex is available."""
    try:
        query = "SELECT SNOWFLAKE.CORTEX.COMPLETE('mistral-7b', 'test') as result"
        st.connection("snowflake").query(query)
        return True
    except Exception:
        return False


@st.cache_data(ttl=600)
def load_churn_data_for_account(account_id):
    """Load churn data for a specific account."""
    try:
        query = f"""
        SELECT
            CHURNED,
            CHURN_DATE
        FROM CHURN_RECORDS
        WHERE USERID = {account_id}
        """
        df = st.connection("snowflake").query(query)
        if not df.empty:
            return {
                'churned': df.iloc[0]['CHURNED'] == 1,
                'churn_date': df.iloc[0]['CHURN_DATE'] if df.iloc[0]['CHURNED'] == 1 else None
            }
        return {'churned': False, 'churn_date': None}
    except Exception:
        return {'churned': False, 'churn_date': None}


def get_llm_insights(metric_name, data_summary, model_name='mistral-7b', user_question=None):
    """Get AI insights for a metric using Snowflake Cortex."""
    try:
        if user_question:
            prompt = f"""You are a data analyst. The user is looking at {metric_name} data.

Data Summary:
{data_summary}

User Question: {user_question}

Provide a concise, helpful answer based on the data."""
        else:
            prompt = f"""You are a data analyst. Analyze the {metric_name} data and provide key insights.

Data Summary:
{data_summary}

Provide 3-4 key insights about trends, patterns, or anomalies. Be concise and actionable."""

        # Use Snowflake Cortex via SQL
        escaped_prompt = prompt.replace("'", "''")
        query = f"SELECT SNOWFLAKE.CORTEX.COMPLETE('{model_name}', '{escaped_prompt}') as insight"
        result = st.connection("snowflake").query(query)

        if not result.empty:
            return result.iloc[0]['INSIGHT']
        else:
            return "Unable to generate insights at this time."
    except Exception as e:
        return f"Error generating insights: {str(e)}"


def create_metric_chart(df, metric_col, metric_name, color='#1f77b4'):
    """Create a time series chart for a metric using Altair."""
    if df.empty:
        return None

    # Prepare data
    chart_df = df[['MONTH', metric_col]].copy()
    chart_df.columns = ['Month', 'Value']

    # Create line chart with area fill
    line = alt.Chart(chart_df).mark_line(
        point=True,
        color=color,
        strokeWidth=3
    ).encode(
        x=alt.X('Month:T', title='Month', axis=alt.Axis(format='%Y-%m')),
        y=alt.Y('Value:Q', title='Value'),
        tooltip=[
            alt.Tooltip('Month:T', title='Month', format='%Y-%m'),
            alt.Tooltip('Value:Q', title='Value', format=',.2f')
        ]
    )

    # Add area fill
    area = alt.Chart(chart_df).mark_area(
        opacity=0.3,
        color=color
    ).encode(
        x=alt.X('Month:T'),
        y=alt.Y('Value:Q')
    )

    # Combine line and area
    chart = (area + line).properties(
        title=metric_name,
        height=300,
        width='container'
    ).configure_title(
        fontSize=16,
        font='sans-serif',
        anchor='start'
    )

    return chart


def create_data_summary(df, metric_col):
    """Create a data summary for LLM analysis."""
    if df.empty or metric_col not in df.columns:
        return "No data available"

    summary = f"""
- Total months: {len(df)}
- Average value: {df[metric_col].mean():.2f}
- Minimum: {df[metric_col].min():.2f}
- Maximum: {df[metric_col].max():.2f}
- Latest value: {df[metric_col].iloc[-1]:.2f}
- Trend: {'Increasing' if df[metric_col].iloc[-1] > df[metric_col].iloc[0] else 'Decreasing'}
"""
    return summary


def create_overall_summary(usage_df, churn_info=None):
    """Create a comprehensive summary of all 9 usage metrics with churn context."""
    if usage_df.empty:
        return "No data available"

    metrics = [
        ('PHONE_TOTAL_CALLS', 'Total Calls'),
        ('PHONE_TOTAL_MINUTES_OF_USE', 'Total Minutes'),
        ('VOICE_CALLS', 'Voice Calls'),
        ('VOICE_MINS', 'Voice Minutes'),
        ('PHONE_TOTAL_NUM_INBOUND_CALLS', 'Inbound Calls'),
        ('PHONE_TOTAL_NUM_OUTBOUND_CALLS', 'Outbound Calls'),
        ('PHONE_MAU', 'Monthly Active Users'),
        ('HARDPHONE_CALLS', 'Hardphone Calls'),
        ('SOFTPHONE_CALLS', 'Softphone Calls'),
    ]

    summary = f"Account Usage Overview ({len(usage_df)} months of data):\n\n"

    # Add churn status if available
    if churn_info:
        if churn_info['churned']:
            summary += f"⚠️ **IMPORTANT: This account CHURNED on {churn_info['churn_date']}**\n\n"
        else:
            summary += f"✓ Account Status: Active (has not churned)\n\n"

    # Calculate risk indicators
    risk_indicators = []

    for metric_col, metric_name in metrics:
        if metric_col in usage_df.columns:
            avg_val = usage_df[metric_col].mean()
            latest_val = usage_df[metric_col].iloc[-1]
            first_val = usage_df[metric_col].iloc[0]

            # Calculate percentage change
            if first_val > 0:
                pct_change = ((latest_val - first_val) / first_val) * 100
            else:
                pct_change = 0

            # Determine trend and risk
            if pct_change > 0:
                trend = f"↗️ Increasing (+{pct_change:.1f}%)"
            elif pct_change < 0:
                trend = f"↘️ Decreasing ({pct_change:.1f}%)"
                # Declining usage is a risk indicator
                if abs(pct_change) > 30:
                    risk_indicators.append(f"{metric_name} dropped {abs(pct_change):.1f}%")
            else:
                trend = "➡️ Stable"

            # Check if latest value is significantly below average (another risk indicator)
            if latest_val < avg_val * 0.7:  # 30% below average
                risk_indicators.append(f"{metric_name} is 30%+ below average")

            summary += f"{metric_name}:\n"
            summary += f"  - Average: {avg_val:.2f}\n"
            summary += f"  - First Month: {first_val:.2f}\n"
            summary += f"  - Latest: {latest_val:.2f}\n"
            summary += f"  - Trend: {trend}\n\n"

    # Add risk indicators summary
    if risk_indicators:
        summary += f"\n🚨 **Risk Indicators Detected ({len(risk_indicators)}):**\n"
        for indicator in risk_indicators:
            summary += f"  - {indicator}\n"

    return summary


def extract_churn_risk(llm_response):
    """Extract churn risk score (0-10) from LLM response."""
    import re

    # Look for patterns like "risk: 7", "risk level: 7", "7/10", "churn risk: 7"
    patterns = [
        r'risk(?:\s+level)?(?:\s+score)?:\s*(\d+(?:\.\d+)?)',
        r'(\d+(?:\.\d+)?)\s*/\s*10',
        r'churn(?:\s+risk)?:\s*(\d+(?:\.\d+)?)',
        r'score:\s*(\d+(?:\.\d+)?)'
    ]

    for pattern in patterns:
        match = re.search(pattern, llm_response.lower())
        if match:
            risk_score = float(match.group(1))
            # Ensure it's between 0 and 10
            return min(max(risk_score, 0), 10)

    # Default to 5 if no risk score found
    return 5.0


def main():
    """Main application."""

    # Initialize session state for insights
    if 'insights' not in st.session_state:
        st.session_state.insights = {}

    # Header
    st.title("📈 Account Usage Analytics Dashboard")
    st.markdown("Analyze individual account usage patterns with AI-powered insights")

    # LLM Model Selection
    st.markdown("---")
    st.markdown("### 🤖 Snowflake Cortex AI - Model Selection")

    col1, col2 = st.columns([3, 4])

    with col1:
        # Snowflake Cortex available models
        # Source: https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions
        available_models = {
            'snowflake-arctic': '❄️ Snowflake Arctic - Enterprise-Grade (Recommended)',
            'mistral-7b': '🟢 Mistral 7B - Fast & Efficient',
            'mistral-large': '🔵 Mistral Large - Most Capable & Accurate',
            'mixtral-8x7b': '🟡 Mixtral 8x7B - Balanced Performance',
            'llama2-70b-chat': '🟣 Llama 2 70B Chat - Conversational',
            'llama3-8b': '🟢 Llama 3 8B - Latest Meta Model (Fast)',
            'llama3-70b': '🔵 Llama 3 70B - Latest Meta Model (Powerful)',
            'gemma-7b': '🟠 Gemma 7B - Google DeepMind',
            'reka-flash': '⚡ Reka Flash - Multimodal Support'
        }

        selected_model = st.selectbox(
            "Select Snowflake Cortex LLM Model:",
            options=list(available_models.keys()),
            format_func=lambda x: available_models[x],
            index=0,
            help="All models are provided by Snowflake Cortex. Select based on your needs: Fast (7B-8B), Balanced (Mixtral), or Most Capable (Large/70B)"
        )

        # Store in session state
        st.session_state.selected_model = selected_model

    with col2:
        st.info(f"""
        **Currently Selected:** {available_models[selected_model]}

        **Provider:** Snowflake Cortex AI

        **Model ID:** `{selected_model}`

        💡 *All models run directly in Snowflake - no external API calls*
        """)

    st.markdown("---")

    # Check Cortex availability
    cortex_available = check_cortex_availability()
    if not cortex_available:
        st.warning("⚠️ Snowflake Cortex AI features are not available. Insight buttons will be disabled.")

    # Sidebar - Account Selection
    st.sidebar.header("🔍 Account Selection")

    # Load account data
    with st.spinner("Loading accounts..."):
        accounts_df = load_account_data()

    if accounts_df.empty:
        st.error("No account data available. Please check your Snowflake connection.")
        return

    # Create account options with company names
    accounts_df['DISPLAY_NAME'] = accounts_df.apply(
        lambda x: f"{x['SERVICE_ACCOUNT_ID']} - {x['COMPANY']}", axis=1
    )

    # Account selection
    search_term = st.sidebar.text_input("🔎 Search Account ID or Company", "")

    # Filter accounts based on search
    if search_term:
        filtered_accounts = accounts_df[
            accounts_df['DISPLAY_NAME'].str.contains(search_term, case=False, na=False)
        ]
    else:
        filtered_accounts = accounts_df

    if filtered_accounts.empty:
        st.sidebar.warning("No accounts found matching your search.")
        return

    # Dropdown selection
    selected_account_display = st.sidebar.selectbox(
        "Select Account",
        filtered_accounts['DISPLAY_NAME'].tolist(),
        help="Select an account to view usage analytics"
    )

    # Get selected account ID
    selected_account_id = int(selected_account_display.split(' - ')[0])

    # Clear insights when account changes
    if 'current_account_id' not in st.session_state:
        st.session_state.current_account_id = selected_account_id
    elif st.session_state.current_account_id != selected_account_id:
        # Account changed - clear all insights
        st.session_state.insights = {}
        st.session_state.current_account_id = selected_account_id

    # Display account information
    st.sidebar.markdown("---")
    st.sidebar.subheader("📋 Account Details")

    account_info = get_account_info(selected_account_id)
    if not account_info.empty:
        info = account_info.iloc[0]
        st.sidebar.markdown(f"""
        - **Account ID**: {info['SERVICE_ACCOUNT_ID']}
        - **Company**: {info['COMPANY']}
        - **Brand**: {info['SA_BRAND_NAME']}
        - **Package**: {info['PACKAGE_NAME']}
        - **Tier**: {info['TIER_NAME']}
        - **Status**: {info['SA_ACCT_STATUS']}
        """)

    # Main content
    st.markdown(f"## Usage Analytics for Account: {selected_account_id}")

    # Load usage data
    with st.spinner("Loading usage data..."):
        usage_df = load_usage_data_for_account(selected_account_id)

    if usage_df.empty:
        st.warning(f"No usage data found for account {selected_account_id}")
        return

    # Display date range
    st.info(f"📅 Data Period: {usage_df['MONTH'].min().strftime('%Y-%m')} to {usage_df['MONTH'].max().strftime('%Y-%m')}")

    # Overall Insights Section
    st.markdown("---")
    st.markdown("### 📊 Overall Account Analysis")

    col_prompt, col_button = st.columns([4, 1])

    with col_prompt:
        # Default prompt for overall insights
        default_prompt = """You are a churn prediction expert. Analyze this account's usage data and provide:

1. Overall usage trends and behavioral patterns
2. Key concerns and red flags for churn
3. Specific risk indicators detected

**IMPORTANT - Churn Risk Scoring Guidelines (0-10):**
- 0-2: Active growth, increasing engagement → LOW RISK
- 3-4: Stable usage, minor fluctuations → LOW-MEDIUM RISK
- 5-6: Declining trends (10-30% drops), reduced engagement → MEDIUM RISK
- 7-8: Significant decline (30-50%+ drops), multiple risk indicators → HIGH RISK
- 9-10: Severe decline (50%+ drops), account already churned, critical risk → CRITICAL RISK

**Risk Indicators to Consider:**
- Declining call volume or minutes (especially >30% drops)
- Decreasing Monthly Active Users (MAU)
- Drop in both inbound and outbound activity
- Latest usage significantly below average
- Multiple declining metrics simultaneously
- Account churn status (if provided)

**Required Format:** Your response MUST include the line:
Churn Risk: X/10

Where X is your risk score based on the guidelines above."""

        custom_prompt = st.text_area(
            "Customize analysis prompt (or use default):",
            value=default_prompt,
            height=150,
            help="Modify this prompt to customize the overall analysis"
        )

    with col_button:
        st.markdown("<br>", unsafe_allow_html=True)  # Spacer
        generate_overall = st.button("🔍 Generate Overall Insights", use_container_width=True)

    # Generate and display overall insights
    if generate_overall or ('overall_insights' in st.session_state.insights and 'overall_prompt' in st.session_state.insights):
        if generate_overall:
            if cortex_available:
                with st.spinner("Analyzing all metrics..."):
                    # Load churn data for this account
                    churn_info = load_churn_data_for_account(selected_account_id)

                    # Create comprehensive data summary with churn context
                    overall_data = create_overall_summary(usage_df, churn_info)

                    # Get insights from LLM
                    model = st.session_state.get('selected_model', 'snowflake-arctic')
                    overall_insights = get_llm_insights(
                        "Overall Account Usage",
                        overall_data,
                        model_name=model,
                        user_question=custom_prompt
                    )

                    # Extract churn risk
                    churn_risk = extract_churn_risk(overall_insights)

                    # Store in session state
                    st.session_state.insights['overall_insights'] = overall_insights
                    st.session_state.insights['churn_risk'] = churn_risk
                    st.session_state.insights['overall_prompt'] = custom_prompt
            else:
                st.warning("Cortex AI is not available")

        # Display insights if they exist
        if 'overall_insights' in st.session_state.insights:
            # Display insights
            st.markdown("**📈 Analysis Results:**")
            st.markdown(f'<div class="insight-box">{st.session_state.insights["overall_insights"]}</div>', unsafe_allow_html=True)

            # Display churn risk with red progress bar
            if 'churn_risk' in st.session_state.insights:
                risk_score = st.session_state.insights['churn_risk']

                st.markdown("**⚠️ Churn Risk Assessment:**")

                # Create color gradient based on risk level
                if risk_score <= 3:
                    risk_color = "#28a745"  # Green
                    risk_label = "Low Risk"
                elif risk_score <= 6:
                    risk_color = "#ffc107"  # Yellow
                    risk_label = "Medium Risk"
                elif risk_score <= 8:
                    risk_color = "#fd7e14"  # Orange
                    risk_label = "High Risk"
                else:
                    risk_color = "#dc3545"  # Red
                    risk_label = "Critical Risk"

                # Display risk score and bar
                col_risk1, col_risk2 = st.columns([1, 3])

                with col_risk1:
                    st.metric("Risk Score", f"{risk_score:.1f}/10", delta=risk_label, delta_color="inverse")

                with col_risk2:
                    # Create progress bar with custom color
                    progress_percent = risk_score / 10
                    st.markdown(f"""
                    <div style="margin-top: 20px;">
                        <div style="background-color: #e0e0e0; border-radius: 10px; height: 30px; overflow: hidden;">
                            <div style="background-color: {risk_color}; width: {progress_percent*100}%; height: 100%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; transition: width 0.3s ease;">
                                {risk_score:.1f}/10 - {risk_label}
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    st.markdown("---")

    # Define metrics to display
    metrics = [
        ('PHONE_TOTAL_CALLS', 'Total Calls', '#1f77b4'),
        ('PHONE_TOTAL_MINUTES_OF_USE', 'Total Minutes', '#ff7f0e'),
        ('VOICE_CALLS', 'Voice Calls', '#2ca02c'),
        ('VOICE_MINS', 'Voice Minutes', '#d62728'),
        ('PHONE_TOTAL_NUM_INBOUND_CALLS', 'Inbound Calls', '#9467bd'),
        ('PHONE_TOTAL_NUM_OUTBOUND_CALLS', 'Outbound Calls', '#8c564b'),
        ('PHONE_MAU', 'Monthly Active Users', '#e377c2'),
        ('HARDPHONE_CALLS', 'Hardphone Calls', '#7f7f7f'),
        ('SOFTPHONE_CALLS', 'Softphone Calls', '#bcbd22'),
    ]

    # Create 3x3 grid
    for row in range(3):
        cols = st.columns(3)
        for col_idx in range(3):
            metric_idx = row * 3 + col_idx
            if metric_idx < len(metrics):
                metric_col, metric_name, color = metrics[metric_idx]

                with cols[col_idx]:
                    # Create chart
                    chart = create_metric_chart(usage_df, metric_col, metric_name, color)
                    if chart is not None:
                        st.altair_chart(chart, use_container_width=True)
                    else:
                        st.warning("No data available for this metric")

                    # Create expandable section for AI insights
                    with st.expander(f"🤖 AI Insights for {metric_name}", expanded=False):
                        # Data summary
                        data_summary = create_data_summary(usage_df, metric_col)

                        # Keys for storing insights in session state
                        quick_insights_key = f"quick_insights_{metric_idx}"
                        custom_insights_key = f"custom_insights_{metric_idx}"

                        # Quick insights button
                        if st.button(f"📊 Get Quick Insights", key=f"quick_{metric_idx}"):
                            if cortex_available:
                                with st.spinner("Generating insights..."):
                                    model = st.session_state.get('selected_model', 'mistral-7b')
                                    insights = get_llm_insights(metric_name, data_summary, model_name=model)
                                    # Store in session state
                                    st.session_state.insights[quick_insights_key] = insights
                            else:
                                st.warning("Cortex AI is not available")

                        # Display quick insights if they exist
                        if quick_insights_key in st.session_state.insights:
                            st.markdown("**📊 Quick Insights:**")
                            st.markdown(f'<div class="insight-box">{st.session_state.insights[quick_insights_key]}</div>', unsafe_allow_html=True)

                        # Custom question
                        st.markdown("---")
                        st.markdown("**Ask a Custom Question:**")
                        user_question = st.text_input(
                            "Your question",
                            placeholder=f"e.g., What's causing the trend in {metric_name}?",
                            key=f"question_{metric_idx}"
                        )

                        if st.button(f"❓ Ask Question", key=f"ask_{metric_idx}"):
                            if user_question:
                                if cortex_available:
                                    with st.spinner("Analyzing..."):
                                        model = st.session_state.get('selected_model', 'mistral-7b')
                                        insights = get_llm_insights(metric_name, data_summary, model_name=model, user_question=user_question)
                                        # Store in session state
                                        st.session_state.insights[custom_insights_key] = {
                                            'question': user_question,
                                            'answer': insights
                                        }
                                else:
                                    st.warning("Cortex AI is not available")
                            else:
                                st.warning("Please enter a question first")

                        # Display custom insights if they exist
                        if custom_insights_key in st.session_state.insights:
                            st.markdown("**❓ Your Question:**")
                            st.markdown(f"*{st.session_state.insights[custom_insights_key]['question']}*")
                            st.markdown("**Answer:**")
                            st.markdown(f'<div class="insight-box">{st.session_state.insights[custom_insights_key]["answer"]}</div>', unsafe_allow_html=True)

    # Footer
    st.markdown("---")
    st.markdown("**💡 Tip**: Expand any metric's AI Insights section to get automated analysis or ask custom questions!")


if __name__ == "__main__":
    main()
