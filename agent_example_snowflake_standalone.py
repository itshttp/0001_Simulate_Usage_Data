"""
Snowflake Multi-Agent Analysis System - STANDALONE VERSION
A Streamlit application for AI-powered data analysis using Snowflake Cortex.

This is a standalone version with all agent code included - perfect for Streamlit in Snowflake.
No external dependencies required beyond Snowflake Snowpark.
"""

import streamlit as st
import time
import pandas as pd
from typing import Optional, Dict, Any, List

# ============================================
# SNOWFLAKE SESSION MANAGEMENT
# ============================================
try:
    from snowflake.snowpark import Session
    from snowflake.snowpark.context import get_active_session
    SNOWPARK_AVAILABLE = True
except ImportError:
    SNOWPARK_AVAILABLE = False


def get_snowflake_session() -> Optional[Session]:
    """Get Snowflake session - prioritizes Streamlit in Snowflake environment."""
    # Try Streamlit in Snowflake first
    try:
        session = get_active_session()
        return session
    except:
        st.error("⚠️ This app is designed to run in Streamlit in Snowflake.")
        st.info("Please deploy this app to your Snowflake account using Streamlit in Snowflake.")
        return None


# ============================================
# AGENT CLASSES (Embedded)
# ============================================
class SnowflakeAgent:
    """Base agent class with Snowflake Cortex integration."""

    def __init__(self, session: Session, name: str, model: str = "mistral-large2"):
        self.session = session
        self.name = name
        self.model = model

    def call_llm(self, system_prompt: str, user_message: str) -> str:
        """Call Snowflake Cortex LLM."""
        try:
            full_prompt = f"{system_prompt}\n\nUser: {user_message}"
            # Escape single quotes for SQL
            escaped_prompt = full_prompt.replace("'", "''")

            query = f"""
                SELECT SNOWFLAKE.CORTEX.COMPLETE(
                    '{self.model}',
                    '{escaped_prompt}'
                ) as response
            """

            result = self.session.sql(query).collect()
            return result[0]['RESPONSE']
        except Exception as e:
            return f"LLM call failed: {str(e)}"


class DataCollectorAgent(SnowflakeAgent):
    """Generates and executes SQL queries."""

    def execute(self, user_question: str, schema_context: str = "") -> Dict[str, Any]:
        """Generate SQL and fetch data."""
        try:
            # Auto-discover schema if not provided
            if not schema_context or schema_context.strip() == "":
                try:
                    # Discover tables
                    tables_df = self.session.sql("SHOW TABLES").to_pandas()
                    if not tables_df.empty:
                        table_names = tables_df['name'].tolist() if 'name' in tables_df.columns else tables_df.iloc[:, 1].tolist()

                        # Build schema context for common tables
                        schema_lines = []
                        for table in table_names[:10]:
                            try:
                                desc_df = self.session.sql(f"DESCRIBE TABLE {table}").to_pandas()
                                col_names = desc_df['name'].tolist() if 'name' in desc_df.columns else desc_df.iloc[:, 0].tolist()
                                schema_lines.append(f"- {table} table columns: {', '.join(col_names[:15])}")
                            except:
                                schema_lines.append(f"- {table}")

                        schema_context = "\n".join(schema_lines)
                except:
                    schema_context = ""

            # Build prompt with better instructions
            system_prompt = """You are a Snowflake SQL expert.
Generate SQL queries based on user requirements.

CRITICAL RULES:
1. Return ONLY pure SQL code - no explanations, no markdown, no comments
2. Use SELECT statements to query data
3. Use EXACT column names from the schema context provided
4. For "accounts", look for SERVICE_ACCOUNT_ID or ACCOUNT_ID columns
5. For "ARR", look for ARR_CURRENT and ARR_PREVIOUS columns
6. For "MRR", look for MRR_CURRENT and MRR_PREVIOUS columns
7. For "recent" or "latest", use ORDER BY with timestamp/date DESC
8. Always include LIMIT clause (default LIMIT 100 unless user specifies different)
9. Use table names EXACTLY as shown in schema

IMPORTANT TABLE-SPECIFIC NOTES:
- ACCOUNT_ATTRIBUTES_MONTHLY: Contains account info, packages, tiers (NO revenue columns)
  - Key columns: SERVICE_ACCOUNT_ID, COMPANY, PACKAGE_NAME, TIER_NAME, MONTH
  - Does NOT have: ARR, MRR, revenue columns
- PHONE_USAGE_DATA: Contains usage metrics and revenue
  - Key columns: USERID (matches SERVICE_ACCOUNT_ID), MRR, PHONE_TOTAL_CALLS, PHONE_MAU, MONTH
  - For revenue: Use MRR column only (no ARR column exists)
- To join tables: PHONE_USAGE_DATA.USERID = ACCOUNT_ATTRIBUTES_MONTHLY.SERVICE_ACCOUNT_ID
- For trends over time: Compare same metric across different MONTH values

Return only the SQL query, nothing else."""

            user_prompt = f"""User Question: {user_question}

Database Schema:
{schema_context if schema_context else "No schema context available"}

Task: Generate a SQL query using the EXACT column names shown above. Return ONLY the SQL code."""

            # Get SQL from LLM
            llm_response = self.call_llm(system_prompt, user_prompt)

            # Clean SQL
            sql = llm_response.strip()
            sql = sql.replace("```sql", "").replace("```", "").strip()

            # Remove any leading/trailing whitespace and newlines
            sql = ' '.join(sql.split())

            # Execute query
            df = self.session.sql(sql).to_pandas()

            return {
                "status": "success",
                "query": sql,
                "data": df,
                "row_count": len(df),
                "columns": df.columns.tolist()
            }

        except Exception as e:
            error_msg = str(e)

            # Provide helpful error messages
            if "invalid identifier" in error_msg.lower():
                error_msg += "\n\n💡 Column name mismatch. Click 'Discover Available Tables' to auto-detect the correct schema."

            return {
                "status": "error",
                "error": error_msg,
                "query": sql if 'sql' in locals() else "SQL generation failed"
            }


class DataQAAgent(SnowflakeAgent):
    """Performs data quality checks."""

    def execute(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze data quality."""
        try:
            # Basic quality checks
            issues = []

            # Check for nulls
            null_counts = data.isnull().sum()
            null_cols = null_counts[null_counts > 0]
            if len(null_cols) > 0:
                for col, count in null_cols.items():
                    pct = (count / len(data)) * 100
                    issues.append(f"Column '{col}' has {count} null values ({pct:.1f}%)")

            # Check for duplicates
            dup_count = data.duplicated().sum()
            if dup_count > 0:
                issues.append(f"Found {dup_count} duplicate rows")

            # Get LLM analysis
            system_prompt = """You are a data quality analyst. Review the data summary and provide insights."""

            data_summary = f"""
Data Shape: {data.shape[0]} rows, {data.shape[1]} columns
Columns: {', '.join(data.columns.tolist())}

Data Types:
{data.dtypes.to_string()}

Summary Statistics:
{data.describe().to_string() if len(data) > 0 else "No data"}

Issues Found: {len(issues)}
{chr(10).join(issues) if issues else "No issues detected"}
"""

            llm_analysis = self.call_llm(system_prompt, f"Analyze this data quality summary:\n{data_summary}")

            return {
                "status": "success",
                "issues_found": len(issues),
                "analysis": {
                    "issues": issues,
                    "summary": llm_analysis
                },
                "summary": llm_analysis
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }


class BusinessAnalystAgent(SnowflakeAgent):
    """Provides business insights."""

    def execute(self, data: pd.DataFrame, user_question: str) -> Dict[str, Any]:
        """Generate business insights."""
        try:
            system_prompt = """You are a business analyst. Analyze the data and provide:
1. Key findings and patterns
2. Business insights
3. Actionable recommendations

Be specific and data-driven."""

            # Prepare data summary
            data_summary = f"""
Original Question: {user_question}

Data Overview:
- {data.shape[0]} rows, {data.shape[1]} columns
- Columns: {', '.join(data.columns.tolist())}

Sample Data (first 10 rows):
{data.head(10).to_string()}

Summary Statistics:
{data.describe().to_string() if len(data) > 0 else "No numeric columns"}
"""

            insights = self.call_llm(system_prompt, f"Analyze this data:\n{data_summary}")

            return {
                "status": "success",
                "insights": insights,
                "recommendations": []  # Could extract from insights
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }


class ComplianceAgent(SnowflakeAgent):
    """Checks for PII and compliance issues."""

    def execute(self, data: pd.DataFrame, query: str) -> Dict[str, Any]:
        """Check for compliance issues."""
        try:
            pii_keywords = ['email', 'ssn', 'phone', 'address', 'credit_card', 'password']
            pii_detected = []

            # Check column names
            for col in data.columns:
                col_lower = col.lower()
                for keyword in pii_keywords:
                    if keyword in col_lower:
                        pii_detected.append(f"Column '{col}' may contain {keyword.upper()} data")

            # Get LLM compliance check
            system_prompt = """You are a compliance officer. Review the query and data for privacy/security concerns."""

            compliance_summary = f"""
SQL Query:
{query}

Columns: {', '.join(data.columns.tolist())}

Potential PII Issues: {len(pii_detected)}
"""

            llm_check = self.call_llm(system_prompt, f"Review for compliance:\n{compliance_summary}")

            return {
                "approved": len(pii_detected) == 0,
                "pii_detected": pii_detected,
                "llm_check": llm_check
            }

        except Exception as e:
            return {
                "approved": True,
                "error": str(e)
            }


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

    # Check Snowpark availability
    if not SNOWPARK_AVAILABLE:
        st.error("❌ Snowflake Snowpark is required but not available.")
        st.stop()

    # Get session
    session = get_snowflake_session()
    if not session:
        st.stop()

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")

        # Connection info
        try:
            with st.expander("📊 Connection Details", expanded=False):
                st.write(f"**Database:** {session.get_current_database()}")
                st.write(f"**Schema:** {session.get_current_schema()}")
                st.write(f"**Warehouse:** {session.get_current_warehouse()}")
        except:
            pass

        st.divider()

        # LLM Selection
        st.subheader("🤖 LLM Model")
        llm_model = st.selectbox(
            "Select AI Model",
            [
                "mistral-large2",
                "snowflake-arctic",
                "llama3.1-70b",
                "llama3.1-405b",
                "llama3.2-1b",
                "llama3.2-3b",
                "reka-flash",
                "mixtral-8x7b",
                "gemma-7b"
            ],
            help="Choose Snowflake Cortex LLM model"
        )

        st.success(f"✅ Using: **{llm_model}**")

        st.divider()

        # Schema context
        st.subheader("📋 Schema Context")
        schema_context = st.text_area(
            "Database schema info (optional)",
            value=st.session_state.get('auto_schema_context', ''),
            height=150,
            placeholder="Example:\n- CUSTOMERS: id, name, email\n- ORDERS: id, customer_id, amount",
            help="Helps generate better SQL queries"
        )

    # Main area
    st.header("🔍 Ask Your Data Question")

    # Show warning if schema not discovered yet
    if not st.session_state.get('auto_schema_context'):
        st.warning("⚠️ **Recommended:** Click 'Discover Available Tables' below to auto-detect your database schema for accurate SQL generation.")

    # Discover tables button - make it more prominent
    col_btn1, col_btn2 = st.columns([1, 3])
    with col_btn1:
        discover_btn = st.button("🔍 Discover Available Tables", type="secondary", use_container_width=True)

    if discover_btn:
        with st.spinner("Discovering schema..."):
            try:
                tables_df = session.sql("SHOW TABLES").to_pandas()

                if not tables_df.empty:
                    table_names = tables_df['name'].tolist() if 'name' in tables_df.columns else tables_df.iloc[:, 1].tolist()

                    st.success(f"✅ Found {len(table_names)} tables")

                    # Display tables
                    cols = st.columns(4)
                    for idx, table in enumerate(table_names):
                        cols[idx % 4].write(f"• `{table}`")

                    # Build detailed schema context with ALL columns
                    schema_lines = []
                    progress_bar = st.progress(0)
                    for i, table in enumerate(table_names[:15]):  # Limit to 15 tables
                        try:
                            desc_df = session.sql(f"DESCRIBE TABLE {table}").to_pandas()
                            col_names = desc_df['name'].tolist() if 'name' in desc_df.columns else desc_df.iloc[:, 0].tolist()
                            # Include ALL columns for better accuracy
                            schema_lines.append(f"- {table} table columns: {', '.join(col_names)}")
                        except:
                            schema_lines.append(f"- {table}")
                        progress_bar.progress((i + 1) / min(15, len(table_names)))

                    progress_bar.empty()

                    auto_schema = "\n".join(schema_lines)
                    st.session_state['auto_schema_context'] = auto_schema

                    with st.expander("📋 Full Schema Context (Click to view)"):
                        st.code(auto_schema, language="text")

                    st.success("✅ Schema context saved! Now you can ask questions with confidence.")

                    # Show example questions based on detected tables
                    if 'ACCOUNT_ATTRIBUTES_MONTHLY' in table_names and 'PHONE_USAGE_DATA' in table_names:
                        st.info("**Try these questions (based on your actual data):**\n- Show me top 10 accounts by MRR\n- Compare MRR between months for each account\n- Show companies with their total phone calls\n- What are the most common package tiers?")

            except Exception as e:
                st.error(f"Failed to discover tables: {str(e)}")

    st.divider()

    # Question input
    user_question = st.text_area(
        "Your question:",
        placeholder="Example: What are the top 10 customers by revenue? Show me accounts with high churn risk.",
        height=100
    )

    # Buttons
    col1, col2 = st.columns([3, 1])

    with col1:
        analyze = st.button("🚀 Start Analysis", type="primary", use_container_width=True)

    with col2:
        if st.button("🔄 Reset", use_container_width=True):
            st.rerun()

    # Execute analysis
    if analyze:
        if not user_question:
            st.error("❌ Please enter a question")
        else:
            # Progress
            progress = st.progress(0)
            status = st.empty()

            # Initialize agents
            status.text("🤖 Initializing agents...")
            collector = DataCollectorAgent(session, "DataCollector", llm_model)
            qa = DataQAAgent(session, "QA", llm_model)
            analyst = BusinessAnalystAgent(session, "Analyst", llm_model)
            compliance = ComplianceAgent(session, "Compliance", llm_model)

            progress.progress(0.2)

            # Step 1: Collect data
            status.text("🔍 Generating SQL and collecting data...")
            collector_result = collector.execute(user_question, schema_context)
            progress.progress(0.4)

            if collector_result['status'] == 'error':
                st.error(f"❌ Data collection failed: {collector_result['error']}")
                st.stop()

            data = collector_result['data']

            # Step 2: QA
            status.text("✅ Checking data quality...")
            qa_result = qa.execute(data)
            progress.progress(0.6)

            # Step 3: Business analysis
            status.text("💡 Generating insights...")
            business_result = analyst.execute(data, user_question)
            progress.progress(0.8)

            # Step 4: Compliance
            status.text("🔒 Compliance check...")
            compliance_result = compliance.execute(data, collector_result['query'])
            progress.progress(1.0)

            # Clear progress
            progress.empty()
            status.empty()

            st.success("✅ Analysis complete!")

            # Display results in tabs
            tab1, tab2, tab3, tab4 = st.tabs([
                "📊 Data Results",
                "✅ Quality Check",
                "💡 Business Insights",
                "🔒 Compliance"
            ])

            with tab1:
                st.subheader("📊 Data Results")
                st.code(collector_result['query'], language='sql')

                col1, col2 = st.columns(2)
                col1.metric("Rows", collector_result['row_count'])
                col2.metric("Columns", len(collector_result['columns']))

                st.dataframe(data, use_container_width=True, height=400)

                csv = data.to_csv(index=False)
                st.download_button("📥 Download CSV", csv, "results.csv", "text/csv")

            with tab2:
                st.subheader("✅ Data Quality")
                if qa_result['status'] == 'success':
                    st.info(qa_result['summary'])

                    if qa_result['issues_found'] > 0:
                        st.warning(f"⚠️ {qa_result['issues_found']} issue(s) found")
                        for issue in qa_result['analysis']['issues']:
                            st.write(f"- {issue}")
                    else:
                        st.success("✅ No issues detected")
                else:
                    st.error(qa_result.get('error', 'QA failed'))

            with tab3:
                st.subheader("💡 Business Insights")
                if business_result['status'] == 'success':
                    st.markdown(business_result['insights'])
                else:
                    st.error(business_result.get('error', 'Analysis failed'))

            with tab4:
                st.subheader("🔒 Compliance Check")
                if compliance_result['approved']:
                    st.success("✅ No compliance issues")
                else:
                    st.warning("⚠️ Potential issues detected")
                    for issue in compliance_result['pii_detected']:
                        st.write(f"- {issue}")

                with st.expander("Details"):
                    st.write(compliance_result.get('llm_check', 'None'))


if __name__ == "__main__":
    main()
