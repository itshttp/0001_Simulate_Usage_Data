"""
Snowflake Multi-Agent Supervisor System with LLM Selection
A comprehensive Streamlit application for AI-powered data analysis using Snowflake Cortex.

This system includes:
- Supervisor Agent to orchestrate all agents
- Data Table Search Agent
- Metadata Agent
- Data Pull Agent (SQL generation)
- Data QC Agent
- Data Compliance Agent
- Data Visualization Agent
- Support for multiple LLMs (Snowflake Arctic, Llama, OpenAI, Sonnet, etc.)
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any
import json

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
    try:
        session = get_active_session()
        return session
    except:
        st.error("⚠️ This app is designed to run in Streamlit in Snowflake.")
        st.info("Please deploy this app to your Snowflake account using Streamlit in Snowflake.")
        return None


# ============================================
# LLM CONFIGURATION
# ============================================
LLM_MODELS = {
    "Snowflake Arctic": "snowflake-arctic",
    "Mistral Large 2": "mistral-large2",
    "Llama 3.1 405B": "llama3.1-405b",
    "Llama 3.1 70B": "llama3.1-70b",
    "Llama 3.2 3B": "llama3.2-3b",
    "Llama 3.2 1B": "llama3.2-1b",
    "Mixtral 8x7B": "mixtral-8x7b",
    "Reka Flash": "reka-flash",
    "Gemma 7B": "gemma-7b"
}


# ============================================
# BASE AGENT CLASS
# ============================================
class SnowflakeAgent:
    """Base agent class with Snowflake Cortex integration."""

    def __init__(self, session: Session, name: str, model: str = "mistral-large2"):
        self.session = session
        self.name = name
        self.model = model
        self.execution_log = []

    def call_llm(self, system_prompt: str, user_message: str) -> str:
        """Call Snowflake Cortex LLM."""
        try:
            full_prompt = f"{system_prompt}\n\nUser: {user_message}"
            escaped_prompt = full_prompt.replace("'", "''")

            query = f"""
                SELECT SNOWFLAKE.CORTEX.COMPLETE(
                    '{self.model}',
                    '{escaped_prompt}'
                ) as response
            """

            result = self.session.sql(query).collect()
            response = result[0]['RESPONSE']

            self.execution_log.append({
                "agent": self.name,
                "model": self.model,
                "prompt": user_message[:200] + "...",
                "response": response[:200] + "..."
            })

            return response
        except Exception as e:
            error_msg = f"LLM call failed: {str(e)}"
            self.execution_log.append({
                "agent": self.name,
                "error": error_msg
            })
            return error_msg


# ============================================
# SPECIALIZED AGENTS
# ============================================

class DataTableSearchAgent(SnowflakeAgent):
    """Agent to discover and search all available tables and their columns."""

    def execute(self) -> Dict[str, Any]:
        """Discover all tables and their schemas."""
        try:
            # Get all tables
            tables_df = self.session.sql("SHOW TABLES").to_pandas()

            if tables_df.empty:
                return {
                    "status": "error",
                    "error": "No tables found in current schema"
                }

            table_names = tables_df['name'].tolist() if 'name' in tables_df.columns else tables_df.iloc[:, 1].tolist()

            # Get detailed schema for each table
            table_schemas = {}
            for table in table_names:
                try:
                    desc_df = self.session.sql(f"DESCRIBE TABLE {table}").to_pandas()
                    columns_info = []

                    for _, row in desc_df.iterrows():
                        col_name = row['name'] if 'name' in row else row.iloc[0]
                        col_type = row['type'] if 'type' in row else row.iloc[1]
                        columns_info.append({
                            "name": col_name,
                            "type": str(col_type)
                        })

                    table_schemas[table] = {
                        "columns": columns_info,
                        "column_names": [c["name"] for c in columns_info]
                    }
                except Exception as e:
                    table_schemas[table] = {
                        "error": str(e)
                    }

            return {
                "status": "success",
                "table_count": len(table_names),
                "tables": table_names,
                "schemas": table_schemas
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }


class MetadataAgent(SnowflakeAgent):
    """Agent to process metadata from table search and user inputs."""

    def execute(self, table_search_result: Dict[str, Any], user_metadata: str = "") -> Dict[str, Any]:
        """Process metadata and create enhanced schema context."""
        try:
            if table_search_result.get("status") != "success":
                return {
                    "status": "error",
                    "error": "Invalid table search result"
                }

            schemas = table_search_result.get("schemas", {})

            # Build comprehensive schema context
            schema_lines = []
            for table, info in schemas.items():
                if "error" in info:
                    schema_lines.append(f"- {table}: Error retrieving schema")
                else:
                    col_types = info.get("columns", [])

                    # Detailed column info with types
                    col_details = [f"{c['name']} ({c['type']})" for c in col_types]
                    schema_lines.append(f"- {table}:")
                    schema_lines.append(f"  Columns: {', '.join(col_details)}")

            schema_context = "\n".join(schema_lines)

            # Use LLM to enhance metadata with user input
            if user_metadata:
                system_prompt = """You are a metadata analyst. Combine the database schema
                with user-provided metadata to create an enhanced understanding of the data structure.
                Identify relationships, key fields, and important notes."""

                user_prompt = f"""Database Schema:
{schema_context}

User Metadata/Notes:
{user_metadata}

Task: Provide an enhanced metadata summary highlighting key relationships and important fields."""

                enhanced_metadata = self.call_llm(system_prompt, user_prompt)
            else:
                enhanced_metadata = schema_context

            return {
                "status": "success",
                "schema_context": schema_context,
                "enhanced_metadata": enhanced_metadata,
                "table_count": len(schemas)
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }


class DataPullAgent(SnowflakeAgent):
    """Agent to generate SQL and pull data based on user questions."""

    def execute(self, user_question: str, metadata_context: str) -> Dict[str, Any]:
        """Generate SQL and fetch data."""
        try:
            system_prompt = """You are a Snowflake SQL expert.
Generate SQL queries based on user requirements.

CRITICAL RULES:
1. Return ONLY pure SQL code - no explanations, no markdown, no comments
2. Use SELECT statements to query data
3. Use EXACT column names from the schema context provided
4. For "recent" or "latest", use ORDER BY with timestamp/date DESC
5. Always include LIMIT clause (default LIMIT 100 unless user specifies different)
6. Use table names EXACTLY as shown in schema
7. Consider table relationships when joining
8. For aggregations, use appropriate GROUP BY clauses

Return only the SQL query, nothing else."""

            user_prompt = f"""User Question: {user_question}

Database Schema and Metadata:
{metadata_context}

Task: Generate a SQL query using the EXACT column names shown above. Return ONLY the SQL code."""

            # Get SQL from LLM
            llm_response = self.call_llm(system_prompt, user_prompt)

            # Clean SQL
            sql = llm_response.strip()
            sql = sql.replace("```sql", "").replace("```", "").strip()
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
            return {
                "status": "error",
                "error": str(e),
                "query": sql if 'sql' in locals() else "SQL generation failed"
            }


class DataQCAgent(SnowflakeAgent):
    """Agent to perform comprehensive data quality checks."""

    def execute(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Perform detailed data quality analysis."""
        try:
            qc_results = {
                "null_analysis": {},
                "duplicate_analysis": {},
                "type_analysis": {},
                "statistical_summary": {},
                "issues": []
            }

            # 1. Null value analysis
            null_counts = data.isnull().sum()
            null_cols = null_counts[null_counts > 0]
            if len(null_cols) > 0:
                for col, count in null_cols.items():
                    pct = (count / len(data)) * 100
                    qc_results["null_analysis"][col] = {
                        "count": int(count),
                        "percentage": round(pct, 2)
                    }
                    if pct > 10:
                        qc_results["issues"].append(f"Column '{col}' has {count} null values ({pct:.1f}%)")

            # 2. Duplicate analysis
            dup_count = data.duplicated().sum()
            qc_results["duplicate_analysis"] = {
                "duplicate_rows": int(dup_count),
                "unique_rows": int(len(data) - dup_count)
            }
            if dup_count > 0:
                qc_results["issues"].append(f"Found {dup_count} duplicate rows")

            # 3. Data type analysis
            for col in data.columns:
                qc_results["type_analysis"][col] = str(data[col].dtype)

            # 4. Statistical summary for numeric columns
            numeric_cols = data.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                stats = data[numeric_cols].describe().to_dict()
                qc_results["statistical_summary"] = stats

            # Get LLM analysis
            system_prompt = """You are a data quality expert. Review the QC results and provide:
1. Overall data quality assessment
2. Critical issues that need attention
3. Recommendations for data improvement"""

            qc_summary = f"""
Data Shape: {data.shape[0]} rows, {data.shape[1]} columns

Null Analysis: {json.dumps(qc_results['null_analysis'], indent=2)}
Duplicate Analysis: {json.dumps(qc_results['duplicate_analysis'], indent=2)}
Issues Found: {len(qc_results['issues'])}
"""

            llm_analysis = self.call_llm(system_prompt, f"Analyze this data quality report:\n{qc_summary}")

            return {
                "status": "success",
                "qc_results": qc_results,
                "llm_analysis": llm_analysis,
                "issues_found": len(qc_results["issues"])
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }


class DataComplianceAgent(SnowflakeAgent):
    """Agent to check data compliance, PII, and security issues."""

    def execute(self, data: pd.DataFrame, query: str) -> Dict[str, Any]:
        """Perform comprehensive compliance checks."""
        try:
            compliance_results = {
                "pii_detected": [],
                "security_concerns": [],
                "compliance_level": "COMPLIANT"
            }

            # PII detection patterns
            pii_patterns = {
                'email': ['email', 'e-mail', 'mail'],
                'ssn': ['ssn', 'social_security', 'social security'],
                'phone': ['phone', 'telephone', 'mobile', 'cell'],
                'address': ['address', 'street', 'city', 'zip', 'postal'],
                'credit_card': ['credit_card', 'creditcard', 'cc', 'card_number'],
                'password': ['password', 'pwd', 'passwd'],
                'dob': ['birth', 'dob', 'birthdate'],
                'ip_address': ['ip_address', 'ipaddress']
            }

            # Check column names for PII
            for col in data.columns:
                col_lower = col.lower()
                for pii_type, patterns in pii_patterns.items():
                    for pattern in patterns:
                        if pattern in col_lower:
                            compliance_results["pii_detected"].append({
                                "column": col,
                                "pii_type": pii_type.upper(),
                                "severity": "HIGH" if pii_type in ['ssn', 'credit_card', 'password'] else "MEDIUM"
                            })
                            compliance_results["compliance_level"] = "REVIEW_REQUIRED"

            # Check query for sensitive operations
            query_lower = query.lower()
            sensitive_keywords = ['delete', 'drop', 'truncate', 'update', 'alter']
            for keyword in sensitive_keywords:
                if keyword in query_lower:
                    compliance_results["security_concerns"].append(f"Query contains {keyword.upper()} operation")
                    compliance_results["compliance_level"] = "REVIEW_REQUIRED"

            # Get LLM compliance analysis
            system_prompt = """You are a data compliance and privacy officer. Review the compliance report and provide:
1. Risk assessment
2. Compliance recommendations
3. Required actions if any violations found"""

            compliance_summary = f"""
SQL Query: {query}

Columns: {', '.join(data.columns.tolist())}

PII Detected: {len(compliance_results['pii_detected'])}
Security Concerns: {len(compliance_results['security_concerns'])}
Compliance Level: {compliance_results['compliance_level']}
"""

            llm_analysis = self.call_llm(system_prompt, f"Review this compliance report:\n{compliance_summary}")

            return {
                "status": "success",
                "compliance_results": compliance_results,
                "llm_analysis": llm_analysis,
                "approved": compliance_results["compliance_level"] == "COMPLIANT"
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "approved": False
            }


class DataVisualizationAgent(SnowflakeAgent):
    """Agent to create visualizations based on data and user questions."""

    def execute(self, data: pd.DataFrame, user_question: str) -> Dict[str, Any]:
        """Generate visualizations and insights."""
        try:
            visualizations = []

            # Analyze data to determine best visualizations
            numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
            categorical_cols = data.select_dtypes(include=['object', 'category']).columns.tolist()

            # 1. Create visualization configs for Streamlit native charts
            if len(numeric_cols) >= 2:
                # Scatter chart data
                visualizations.append({
                    "type": "scatter",
                    "title": f"{numeric_cols[0]} vs {numeric_cols[1]}",
                    "x_col": numeric_cols[0],
                    "y_col": numeric_cols[1],
                    "data": data[[numeric_cols[0], numeric_cols[1]]]
                })

            if len(numeric_cols) >= 1 and len(categorical_cols) >= 1:
                # Bar chart - aggregate data
                agg_data = data.groupby(categorical_cols[0])[numeric_cols[0]].sum().reset_index()
                visualizations.append({
                    "type": "bar",
                    "title": f"{numeric_cols[0]} by {categorical_cols[0]}",
                    "data": agg_data,
                    "x_col": categorical_cols[0],
                    "y_col": numeric_cols[0]
                })

            if len(numeric_cols) >= 1:
                # Line chart for trends (if data can be sorted)
                visualizations.append({
                    "type": "line",
                    "title": f"Trend: {numeric_cols[0]}",
                    "data": data[numeric_cols[:min(3, len(numeric_cols))]],
                    "columns": numeric_cols[:min(3, len(numeric_cols))]
                })

            # Area chart for numeric data
            if len(numeric_cols) >= 1:
                visualizations.append({
                    "type": "area",
                    "title": f"Area Chart: {', '.join(numeric_cols[:min(2, len(numeric_cols))])}",
                    "data": data[numeric_cols[:min(2, len(numeric_cols))]]
                })

            # Get LLM insights about visualizations
            system_prompt = """You are a data visualization expert. Based on the data and user question, provide:
1. Key insights from the data
2. Recommended visualizations
3. Patterns or trends observed
4. Actionable recommendations"""

            data_summary = f"""
User Question: {user_question}

Data Overview:
- {data.shape[0]} rows, {data.shape[1]} columns
- Numeric columns: {', '.join(numeric_cols) if numeric_cols else 'None'}
- Categorical columns: {', '.join(categorical_cols) if categorical_cols else 'None'}

Sample Data (first 5 rows):
{data.head(5).to_string()}

Statistical Summary:
{data.describe().to_string() if len(numeric_cols) > 0 else "No numeric data"}
"""

            llm_insights = self.call_llm(system_prompt, f"Analyze and provide insights:\n{data_summary}")

            return {
                "status": "success",
                "visualizations": visualizations,
                "insights": llm_insights,
                "chart_count": len(visualizations)
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }


class SupervisorAgent(SnowflakeAgent):
    """Supervisor agent to orchestrate all other agents."""

    def __init__(self, session: Session, model: str = "mistral-large2"):
        super().__init__(session, "Supervisor", model)
        self.workflow_log = []

    def orchestrate(self, user_question: str, user_metadata: str, agent_models: Dict[str, str]) -> Dict[str, Any]:
        """Orchestrate the entire workflow."""
        try:
            workflow_result = {
                "steps": [],
                "status": "in_progress"
            }

            # Step 1: Data Table Search
            self.workflow_log.append("Starting Data Table Search...")
            table_search_agent = DataTableSearchAgent(self.session, "TableSearch", agent_models.get("table_search", self.model))
            table_result = table_search_agent.execute()
            workflow_result["steps"].append({
                "step": "Table Search",
                "status": table_result.get("status"),
                "result": table_result
            })

            if table_result.get("status") != "success":
                workflow_result["status"] = "error"
                workflow_result["error"] = "Table search failed"
                return workflow_result

            # Step 2: Metadata Processing
            self.workflow_log.append("Processing Metadata...")
            metadata_agent = MetadataAgent(self.session, "Metadata", agent_models.get("metadata", self.model))
            metadata_result = metadata_agent.execute(table_result, user_metadata)
            workflow_result["steps"].append({
                "step": "Metadata",
                "status": metadata_result.get("status"),
                "result": metadata_result
            })

            if metadata_result.get("status") != "success":
                workflow_result["status"] = "error"
                workflow_result["error"] = "Metadata processing failed"
                return workflow_result

            # Step 3: Data Pull
            self.workflow_log.append("Pulling Data...")
            data_pull_agent = DataPullAgent(self.session, "DataPull", agent_models.get("data_pull", self.model))
            data_result = data_pull_agent.execute(user_question, metadata_result.get("enhanced_metadata"))
            workflow_result["steps"].append({
                "step": "Data Pull",
                "status": data_result.get("status"),
                "result": data_result
            })

            if data_result.get("status") != "success":
                workflow_result["status"] = "error"
                workflow_result["error"] = f"Data pull failed: {data_result.get('error')}"
                return workflow_result

            data = data_result.get("data")

            # Step 4: Data QC
            self.workflow_log.append("Performing Data Quality Checks...")
            qc_agent = DataQCAgent(self.session, "DataQC", agent_models.get("qc", self.model))
            qc_result = qc_agent.execute(data)
            workflow_result["steps"].append({
                "step": "Data QC",
                "status": qc_result.get("status"),
                "result": qc_result
            })

            # Step 5: Compliance Check
            self.workflow_log.append("Checking Compliance...")
            compliance_agent = DataComplianceAgent(self.session, "Compliance", agent_models.get("compliance", self.model))
            compliance_result = compliance_agent.execute(data, data_result.get("query"))
            workflow_result["steps"].append({
                "step": "Compliance",
                "status": compliance_result.get("status"),
                "result": compliance_result
            })

            # Step 6: Visualization
            self.workflow_log.append("Generating Visualizations...")
            viz_agent = DataVisualizationAgent(self.session, "Visualization", agent_models.get("visualization", self.model))
            viz_result = viz_agent.execute(data, user_question)
            workflow_result["steps"].append({
                "step": "Visualization",
                "status": viz_result.get("status"),
                "result": viz_result
            })

            # Final summary from Supervisor
            system_prompt = """You are a supervisor agent coordinating data analysis.
            Provide a brief executive summary of the entire analysis workflow."""

            summary_prompt = f"""
Workflow completed with {len(workflow_result['steps'])} steps.

User Question: {user_question}
Data Retrieved: {data_result.get('row_count')} rows
QC Issues: {qc_result.get('issues_found', 0)}
Compliance: {'APPROVED' if compliance_result.get('approved') else 'REVIEW REQUIRED'}

Provide an executive summary."""

            executive_summary = self.call_llm(system_prompt, summary_prompt)
            workflow_result["executive_summary"] = executive_summary
            workflow_result["status"] = "success"

            return workflow_result

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "workflow_log": self.workflow_log
            }


# ============================================
# STREAMLIT UI
# ============================================
def main():
    st.set_page_config(
        page_title="Snowflake Supervisor Multi-Agent System",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("🎯 Snowflake Supervisor Multi-Agent System")
    st.markdown("*AI-Powered Multi-Agent Data Analysis with Intelligent Supervision*")

    # Check Snowpark availability
    if not SNOWPARK_AVAILABLE:
        st.error("❌ Snowflake Snowpark is required but not available.")
        st.stop()

    # Get session
    session = get_snowflake_session()
    if not session:
        st.stop()

    # Sidebar Configuration
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

        # Supervisor LLM Selection
        st.subheader("🎯 Supervisor LLM")
        supervisor_llm = st.selectbox(
            "Supervisor Agent Model",
            list(LLM_MODELS.keys()),
            index=0,
            help="LLM model for the Supervisor Agent"
        )

        st.divider()

        # Individual Agent LLM Selection
        st.subheader("🤖 Agent LLM Models")

        with st.expander("Agent Model Selection", expanded=False):
            table_search_llm = st.selectbox(
                "Table Search Agent",
                list(LLM_MODELS.keys()),
                index=1,
                key="table_search"
            )

            metadata_llm = st.selectbox(
                "Metadata Agent",
                list(LLM_MODELS.keys()),
                index=1,
                key="metadata"
            )

            data_pull_llm = st.selectbox(
                "Data Pull Agent",
                list(LLM_MODELS.keys()),
                index=0,
                key="data_pull"
            )

            qc_llm = st.selectbox(
                "Data QC Agent",
                list(LLM_MODELS.keys()),
                index=1,
                key="qc"
            )

            compliance_llm = st.selectbox(
                "Compliance Agent",
                list(LLM_MODELS.keys()),
                index=0,
                key="compliance"
            )

            viz_llm = st.selectbox(
                "Visualization Agent",
                list(LLM_MODELS.keys()),
                index=1,
                key="viz"
            )

        # Show selected models summary
        st.success(f"✅ Supervisor: **{supervisor_llm}**")

        st.divider()

        # Metadata input
        st.subheader("📋 Optional Metadata")
        user_metadata = st.text_area(
            "Additional context (optional)",
            height=100,
            placeholder="Example: Customer table contains active users only. Revenue is in USD.",
            help="Provide additional context about your data"
        )

    # Main area
    st.header("🔍 Ask Your Data Question")

    # Question input
    user_question = st.text_area(
        "Your question:",
        placeholder="Example: What are the top 10 customers by revenue? Show me trends in monthly sales.",
        height=100
    )

    # Action buttons
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        analyze = st.button("🚀 Start Multi-Agent Analysis", type="primary", use_container_width=True)

    with col2:
        quick_discover = st.button("🔍 Quick Table Discovery", type="secondary", use_container_width=True)

    with col3:
        if st.button("🔄 Reset", use_container_width=True):
            st.rerun()

    # Quick Table Discovery
    if quick_discover:
        with st.spinner("Discovering tables..."):
            try:
                search_agent = DataTableSearchAgent(session, "QuickSearch", LLM_MODELS[table_search_llm])
                result = search_agent.execute()

                if result.get("status") == "success":
                    st.success(f"✅ Found {result['table_count']} tables")

                    # Display tables
                    cols = st.columns(4)
                    for idx, table in enumerate(result['tables']):
                        cols[idx % 4].write(f"• `{table}`")

                    # Show detailed schema
                    with st.expander("📋 Detailed Schema", expanded=True):
                        for table, info in result['schemas'].items():
                            st.subheader(f"📊 {table}")
                            if "error" in info:
                                st.error(f"Error: {info['error']}")
                            else:
                                cols_df = pd.DataFrame(info['columns'])
                                st.dataframe(cols_df, use_container_width=True)
                else:
                    st.error(f"❌ Discovery failed: {result.get('error')}")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

    # Full Multi-Agent Analysis
    if analyze:
        if not user_question:
            st.error("❌ Please enter a question")
        else:
            # Progress tracking
            progress = st.progress(0)
            status = st.empty()

            # Prepare agent models
            agent_models = {
                "table_search": LLM_MODELS[table_search_llm],
                "metadata": LLM_MODELS[metadata_llm],
                "data_pull": LLM_MODELS[data_pull_llm],
                "qc": LLM_MODELS[qc_llm],
                "compliance": LLM_MODELS[compliance_llm],
                "visualization": LLM_MODELS[viz_llm]
            }

            # Initialize Supervisor
            status.text("🎯 Initializing Supervisor Agent...")
            supervisor = SupervisorAgent(session, LLM_MODELS[supervisor_llm])
            progress.progress(0.1)

            # Execute workflow
            status.text("🚀 Starting Multi-Agent Workflow...")
            workflow_result = supervisor.orchestrate(user_question, user_metadata, agent_models)
            progress.progress(1.0)

            # Clear progress
            progress.empty()
            status.empty()

            if workflow_result.get("status") == "error":
                st.error(f"❌ Workflow failed: {workflow_result.get('error')}")
                with st.expander("Workflow Log"):
                    st.json(workflow_result)
                st.stop()

            st.success("✅ Multi-Agent Analysis Complete!")

            # Executive Summary
            st.header("📊 Executive Summary")
            st.info(workflow_result.get("executive_summary", "No summary available"))

            # Display results in tabs
            tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
                "📊 Data Results",
                "📋 Table Discovery",
                "🔍 Metadata",
                "✅ Quality Check",
                "🔒 Compliance",
                "📈 Visualizations",
                "🎯 Workflow Log"
            ])

            # Extract step results
            steps = workflow_result.get("steps", [])
            step_dict = {step["step"]: step["result"] for step in steps}

            # Tab 1: Data Results
            with tab1:
                st.subheader("📊 Data Results")
                data_result = step_dict.get("Data Pull", {})

                if data_result.get("status") == "success":
                    st.code(data_result.get("query", ""), language='sql')

                    col1, col2 = st.columns(2)
                    col1.metric("Rows", data_result.get("row_count", 0))
                    col2.metric("Columns", len(data_result.get("columns", [])))

                    data = data_result.get("data")
                    if data is not None and not data.empty:
                        st.dataframe(data, use_container_width=True, height=400)

                        csv = data.to_csv(index=False)
                        st.download_button("📥 Download CSV", csv, "results.csv", "text/csv")
                else:
                    st.error(f"❌ {data_result.get('error', 'Data pull failed')}")

            # Tab 2: Table Discovery
            with tab2:
                st.subheader("📋 Table Discovery")
                table_result = step_dict.get("Table Search", {})

                if table_result.get("status") == "success":
                    st.metric("Tables Found", table_result.get("table_count", 0))

                    for table, info in table_result.get("schemas", {}).items():
                        with st.expander(f"📊 {table}"):
                            if "error" in info:
                                st.error(info["error"])
                            else:
                                cols_df = pd.DataFrame(info.get("columns", []))
                                st.dataframe(cols_df, use_container_width=True)

            # Tab 3: Metadata
            with tab3:
                st.subheader("🔍 Metadata Analysis")
                metadata_result = step_dict.get("Metadata", {})

                if metadata_result.get("status") == "success":
                    st.text_area("Schema Context", metadata_result.get("schema_context", ""), height=200)
                    st.markdown("**Enhanced Metadata:**")
                    st.info(metadata_result.get("enhanced_metadata", ""))

            # Tab 4: Quality Check
            with tab4:
                st.subheader("✅ Data Quality Check")
                qc_result = step_dict.get("Data QC", {})

                if qc_result.get("status") == "success":
                    st.metric("Issues Found", qc_result.get("issues_found", 0))

                    qc_data = qc_result.get("qc_results", {})

                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**Null Analysis:**")
                        if qc_data.get("null_analysis"):
                            st.json(qc_data["null_analysis"])
                        else:
                            st.success("No null values found")

                    with col2:
                        st.markdown("**Duplicate Analysis:**")
                        st.json(qc_data.get("duplicate_analysis", {}))

                    st.markdown("**LLM Analysis:**")
                    st.info(qc_result.get("llm_analysis", ""))

            # Tab 5: Compliance
            with tab5:
                st.subheader("🔒 Compliance Check")
                compliance_result = step_dict.get("Compliance", {})

                if compliance_result.get("status") == "success":
                    if compliance_result.get("approved"):
                        st.success("✅ Compliance Approved")
                    else:
                        st.warning("⚠️ Compliance Review Required")

                    comp_data = compliance_result.get("compliance_results", {})

                    if comp_data.get("pii_detected"):
                        st.markdown("**PII Detected:**")
                        pii_df = pd.DataFrame(comp_data["pii_detected"])
                        st.dataframe(pii_df, use_container_width=True)

                    if comp_data.get("security_concerns"):
                        st.markdown("**Security Concerns:**")
                        for concern in comp_data["security_concerns"]:
                            st.warning(concern)

                    st.markdown("**LLM Analysis:**")
                    st.info(compliance_result.get("llm_analysis", ""))

            # Tab 6: Visualizations
            with tab6:
                st.subheader("📈 Data Visualizations")
                viz_result = step_dict.get("Visualization", {})

                if viz_result.get("status") == "success":
                    st.markdown("**Insights:**")
                    st.info(viz_result.get("insights", ""))

                    visualizations = viz_result.get("visualizations", [])
                    if visualizations:
                        for viz in visualizations:
                            st.markdown(f"**{viz['title']}**")

                            # Render based on chart type using Streamlit native charts
                            if viz["type"] == "scatter":
                                st.scatter_chart(viz["data"], x=viz["x_col"], y=viz["y_col"])
                            elif viz["type"] == "bar":
                                st.bar_chart(viz["data"].set_index(viz["x_col"]))
                            elif viz["type"] == "line":
                                st.line_chart(viz["data"])
                            elif viz["type"] == "area":
                                st.area_chart(viz["data"])
                            else:
                                st.dataframe(viz["data"], use_container_width=True)

                            st.divider()
                    else:
                        st.info("No visualizations generated for this dataset")

            # Tab 7: Workflow Log
            with tab7:
                st.subheader("🎯 Workflow Execution Log")
                st.json(workflow_result)


if __name__ == "__main__":
    main()
