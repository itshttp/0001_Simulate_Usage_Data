"""
Snowflake Multi-Agent Analysis System
A Streamlit application for AI-powered data analysis using Snowflake Cortex.

This app can run:
- In Streamlit in Snowflake (uses get_active_session)
- Locally (uses credentials from .streamlit/secrets.toml or .env file)
"""

import streamlit as st
import time
import os
from typing import Optional

# Try importing from different sources
try:
    from snowflake.snowpark import Session
    from snowflake.snowpark.context import get_active_session
    SNOWPARK_AVAILABLE = True
except ImportError:
    SNOWPARK_AVAILABLE = False
    st.error("Snowflake Snowpark not available. Install with: pip install snowflake-snowpark-python")

# Import agents from the local agents package
try:
    from agents import AgentOrchestrator
    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False
    st.error("Agents package not available. Make sure you're running this from the project directory.")


# ============================================
# SESSION MANAGEMENT
# ============================================
def get_snowflake_session() -> Optional[Session]:
    """
    Get Snowflake session from Streamlit secrets or environment variables.
    Tries multiple approaches in this order:
    1. Streamlit in Snowflake (get_active_session)
    2. Streamlit secrets.toml
    3. Environment variables (.env)

    Returns:
        Snowflake Session or None if connection fails
    """
    # Try 1: Streamlit in Snowflake environment
    try:
        session = get_active_session()
        st.sidebar.success("✅ Connected via Snowflake Streamlit")
        return session
    except:
        pass

    # Try 2: Streamlit secrets
    try:
        if hasattr(st, 'secrets') and 'connections' in st.secrets and 'snowflake' in st.secrets.connections:
            connection_params = {
                "account": st.secrets.connections.snowflake.account,
                "user": st.secrets.connections.snowflake.user,
                "password": st.secrets.connections.snowflake.password,
                "warehouse": st.secrets.connections.snowflake.warehouse,
                "database": st.secrets.connections.snowflake.database,
                "schema": st.secrets.connections.snowflake.schema,
            }
            if hasattr(st.secrets.connections.snowflake, 'role'):
                connection_params["role"] = st.secrets.connections.snowflake.role

            session = Session.builder.configs(connection_params).create()
            st.sidebar.success("✅ Connected via Streamlit secrets")
            return session
    except Exception as e:
        st.sidebar.warning(f"Streamlit secrets connection failed: {str(e)}")

    # Try 3: Environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()

        connection_params = {
            "account": os.getenv("SNOWFLAKE_ACCOUNT"),
            "user": os.getenv("SNOWFLAKE_USER"),
            "password": os.getenv("SNOWFLAKE_PASSWORD"),
            "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
            "database": os.getenv("SNOWFLAKE_DATABASE"),
            "schema": os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC"),
        }

        if os.getenv("SNOWFLAKE_ROLE"):
            connection_params["role"] = os.getenv("SNOWFLAKE_ROLE")

        # Check if all required params are present
        if all([connection_params["account"], connection_params["user"],
                connection_params["password"], connection_params["warehouse"],
                connection_params["database"]]):
            session = Session.builder.configs(connection_params).create()
            st.sidebar.success("✅ Connected via .env file")
            return session
        else:
            st.sidebar.warning("⚠️ Missing required environment variables")
    except Exception as e:
        st.sidebar.warning(f"Environment variables connection failed: {str(e)}")

    return None


# ============================================
# STREAMLIT UI
# ============================================
def main():
    st.set_page_config(
        page_title="Snowflake AI Agent System",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("🤖 Snowflake Multi-Agent Analysis System")
    st.markdown("*AI-Powered Data Analysis with Snowflake Cortex*")

    # Check prerequisites
    if not SNOWPARK_AVAILABLE:
        st.error("❌ Snowflake Snowpark is not available. Please install: `pip install snowflake-snowpark-python`")
        st.stop()

    if not AGENTS_AVAILABLE:
        st.error("❌ Agents package not found. Make sure you're running from the project root directory.")
        st.stop()

    # Get Snowflake Session
    session = get_snowflake_session()

    if not session:
        st.error("❌ Failed to connect to Snowflake. Please check your credentials.")
        st.info("""
        **Connection Options:**
        1. **Streamlit in Snowflake**: Deploy this app to Snowflake
        2. **Local with secrets.toml**: Add credentials to `.streamlit/secrets.toml`
        3. **Local with .env**: Add credentials to `.env` file

        See `.env.example` for the required format.
        """)
        st.stop()

    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        # Display connection info
        try:
            current_db = session.get_current_database()
            current_schema = session.get_current_schema()
            current_warehouse = session.get_current_warehouse()

            with st.expander("📊 Connection Details", expanded=False):
                st.write(f"**Database:** {current_db}")
                st.write(f"**Schema:** {current_schema}")
                st.write(f"**Warehouse:** {current_warehouse}")
        except:
            pass

        st.divider()

        # LLM Model Selection
        st.subheader("🤖 LLM Model Selection")
        llm_model = st.selectbox(
            "Select AI Model",
            options=[
                "snowflake-arctic",
                "mistral-large2",
                "llama3.1-70b",
                "llama3.1-405b",
                "llama3.2-1b",
                "llama3.2-3b",
                "reka-flash",
                "mixtral-8x7b",
                "gemma-7b",
                "mistral-7b"
            ],
            index=1,  # Default to mistral-large2
            help="Choose which Snowflake Cortex LLM model to use for all agents"
        )

        st.info(f"**Selected Model:** {llm_model}")

        st.divider()

        # Agent Configuration
        st.subheader("⚙️ Agent Settings")

        with st.expander("📋 Schema Context (Optional)", expanded=False):
            default_schema = st.session_state.get('auto_schema_context', '')
            metadata_context = st.text_area(
                "Database Schema Information",
                value=default_schema,
                placeholder="Example:\n- CUSTOMERS table: customer_id, name, email\n- ORDERS table: order_id, customer_id, amount",
                height=150,
                help="Provide schema information to help generate better SQL queries"
            )

        with st.expander("🔍 Analysis Focus (Optional)", expanded=False):
            analyst_prompt = st.text_area(
                "What should the analysis focus on?",
                value="Analyze patterns, trends, and provide actionable insights",
                height=100,
                help="Customize what the Business Analyst agent should focus on"
            )

        st.divider()

        # Quick Actions
        st.subheader("🚀 Quick Actions")
        if st.button("🔄 Clear Cache", use_container_width=True):
            st.cache_data.clear()
            st.session_state.clear()
            st.success("Cache cleared!")
            st.rerun()

    # Main interface
    st.header("🔍 Ask Your Data Question")

    # Database Discovery Button
    col_discover, col_info = st.columns([2, 3])

    with col_discover:
        if st.button("🔍 Discover Available Tables", use_container_width=True,
                    help="Auto-discover database schema"):
            with st.spinner("Discovering database schema..."):
                try:
                    # Get all tables
                    tables_df = session.sql("SHOW TABLES").to_pandas()

                    if not tables_df.empty:
                        table_names = tables_df['name'].tolist() if 'name' in tables_df.columns else tables_df.iloc[:, 1].tolist()

                        st.success(f"✅ Found {len(table_names)} tables")

                        # Display in columns
                        cols = st.columns(4)
                        for idx, table in enumerate(table_names):
                            cols[idx % 4].write(f"• `{table}`")

                        # Build schema context
                        schema_lines = []
                        progress_bar = st.progress(0)

                        for i, table in enumerate(table_names[:15]):  # Limit to 15 tables
                            try:
                                desc_df = session.sql(f"DESCRIBE TABLE {table}").to_pandas()
                                if not desc_df.empty:
                                    col_names = desc_df['name'].tolist() if 'name' in desc_df.columns else desc_df.iloc[:, 0].tolist()
                                    cols_str = ', '.join(col_names[:12])
                                    if len(col_names) > 12:
                                        cols_str += f" ... ({len(col_names)} columns)"
                                    schema_lines.append(f"- {table}: {cols_str}")
                            except:
                                schema_lines.append(f"- {table}")

                            progress_bar.progress((i + 1) / min(15, len(table_names)))

                        progress_bar.empty()

                        # Save to session state
                        auto_schema = "\n".join(schema_lines)
                        st.session_state['auto_schema_context'] = auto_schema

                        with st.expander("📋 Auto-Generated Schema Context"):
                            st.code(auto_schema, language="text")

                        st.info("💡 Schema context has been auto-filled in the sidebar!")

                        # Generate example questions
                        if 'ACCOUNT_ATTRIBUTES_MONTHLY' in table_names:
                            st.info("**Suggested questions:**\n- Show top 10 accounts by current ARR\n- Which accounts have the highest churn risk?\n- What's the total MRR this month?")
                    else:
                        st.warning("No tables found in current schema")

                except Exception as e:
                    st.error(f"Failed to discover schema: {str(e)}")

    with col_info:
        if not st.session_state.get('auto_schema_context'):
            st.info("💡 Click 'Discover Available Tables' to auto-detect your database schema for better results")

    st.divider()

    # User Question Input
    user_question = st.text_area(
        "Enter your data analysis question:",
        placeholder="Example: What are the top 10 customers by revenue this year? Show accounts with churn risk above 0.8",
        height=120,
        help="Ask a question about your data. The AI agents will work together to answer it."
    )

    # Action Buttons
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        analyze_button = st.button("🚀 Start Analysis", type="primary", use_container_width=True)

    with col2:
        if st.button("🔄 Reset", use_container_width=True):
            st.rerun()

    with col3:
        show_help = st.button("❓ Help", use_container_width=True)

    if show_help:
        st.info("""
        **How to use:**
        1. Select your preferred AI model in the sidebar
        2. Optionally click 'Discover Available Tables' to auto-detect schema
        3. Enter your question in natural language
        4. Click 'Start Analysis' to run the multi-agent pipeline

        **The agents will:**
        - 🔍 Generate and execute SQL queries
        - ✅ Perform quality checks on the data
        - 💡 Provide business insights and recommendations
        - 🔒 Check for compliance and privacy issues
        """)

    # Execute Analysis
    if analyze_button:
        if not user_question or not user_question.strip():
            st.error("❌ Please enter a question")
        else:
            # Create progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()

            def update_progress(value: float, text: str):
                """Update progress bar and status text"""
                progress_bar.progress(value)
                status_text.text(text)

            # Initialize orchestrator
            update_progress(0.1, "🤖 Initializing AI agents...")
            orchestrator = AgentOrchestrator(session, llm_model=llm_model)

            # Prepare prompts
            user_prompts = {
                "user_question": user_question,
                "analyst": analyst_prompt if 'analyst_prompt' in locals() else "Analyze patterns and provide insights",
                "metadata_context": metadata_context if 'metadata_context' in locals() else st.session_state.get('auto_schema_context', ''),
                "collector": "",
                "qa": ""
            }

            # Execute pipeline
            with st.spinner("AI agents are working on your request..."):
                results = orchestrator.run_pipeline(user_prompts, update_progress)

            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()

            # Check for errors
            if "error" in results:
                st.error(f"❌ Analysis failed: {results['error']}")

                if "details" in results:
                    with st.expander("📋 Error Details"):
                        st.json(results["details"])

                st.stop()

            # Display results
            st.success("✅ Analysis completed successfully!")

            # Create result tabs
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "📊 Data Results",
                "✅ Quality Check",
                "💡 Business Insights",
                "🔒 Compliance",
                "📋 Execution Log"
            ])

            # Tab 1: Data Results
            with tab1:
                st.subheader("📊 Collected Data")
                collector_result = results.get('data_collector_result', {})

                if collector_result.get('status') == 'success':
                    # Show SQL query
                    st.markdown("**Generated SQL Query:**")
                    st.code(collector_result['query'], language='sql')

                    # Show metrics
                    col1, col2 = st.columns(2)
                    col1.metric("📏 Rows", collector_result['row_count'])
                    col2.metric("📊 Columns", len(collector_result['columns']))

                    # Show data
                    st.dataframe(
                        collector_result['data'],
                        use_container_width=True,
                        height=400
                    )

                    # Download button
                    csv = collector_result['data'].to_csv(index=False)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name="analysis_results.csv",
                        mime="text/csv"
                    )
                else:
                    st.error(f"❌ {collector_result.get('error', 'Data collection failed')}")

            # Tab 2: Quality Check
            with tab2:
                st.subheader("✅ Data Quality Analysis")
                qa_result = results.get('data_qa_result', {})

                if qa_result.get('status') == 'success':
                    # Summary
                    st.markdown("### 📝 Summary")
                    st.info(qa_result['summary'])

                    # Issues
                    issues_count = qa_result.get('issues_found', 0)
                    if issues_count > 0:
                        st.warning(f"⚠️ Found {issues_count} quality issue(s)")
                        for issue in qa_result['analysis'].get('issues', []):
                            st.write(f"- {issue}")
                    else:
                        st.success("✅ No quality issues detected")

                    # Detailed analysis
                    with st.expander("🔍 Detailed Quality Analysis"):
                        st.json(qa_result['analysis'])
                else:
                    st.error(f"❌ {qa_result.get('error', 'Quality check failed')}")

            # Tab 3: Business Insights
            with tab3:
                st.subheader("💡 Business Insights & Recommendations")
                business_result = results.get('business_result', {})

                if business_result.get('status') == 'success':
                    st.markdown(business_result['insights'])

                    # Show recommendations if available
                    if business_result.get('recommendations'):
                        st.markdown("### 🎯 Key Recommendations")
                        for i, rec in enumerate(business_result['recommendations'], 1):
                            st.info(f"**{i}.** {rec}")
                else:
                    st.error(f"❌ {business_result.get('error', 'Analysis failed')}")

            # Tab 4: Compliance Check
            with tab4:
                st.subheader("🔒 Compliance & Privacy Check")
                compliance_result = results.get('compliance_result', {})

                if compliance_result.get('approved'):
                    st.success("✅ Compliance check passed - No privacy concerns detected")
                else:
                    st.error("❌ Compliance issues detected")

                    if compliance_result.get('pii_detected'):
                        st.warning("**Issues found:**")
                        for issue in compliance_result['pii_detected']:
                            st.write(f"- {issue}")

                with st.expander("🔍 Detailed Compliance Report"):
                    st.write(compliance_result.get('llm_check', 'No additional details'))

            # Tab 5: Execution Log
            with tab5:
                st.subheader("📋 Execution Timeline")

                if hasattr(orchestrator, 'execution_log'):
                    for log in orchestrator.execution_log:
                        timestamp = time.strftime('%H:%M:%S', time.localtime(log['timestamp']))
                        st.text(f"⏱️ {timestamp} - {log['message']}")
                else:
                    st.write("No execution log available")


# ============================================
# RUN APPLICATION
# ============================================
if __name__ == "__main__":
    main()
