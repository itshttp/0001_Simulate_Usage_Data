import streamlit as st
import pandas as pd
from typing import Dict, Any, Optional, Callable, Tuple
import json
import re

st.set_page_config(
    page_title="Multi-Agent Data Analysis System",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .agent-box {
        background-color: #f0f8ff;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #dc3545;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


class BaseAgent:
    def __init__(self, agent_name: str, model_name: str = 'snowflake-arctic'):
        self.agent_name = agent_name
        self.model_name = model_name
        self.context = {}
    
    def call_llm(self, prompt: str) -> str:
        try:
            escaped_prompt = prompt.replace("'", "''")
            query = f"SELECT SNOWFLAKE.CORTEX.COMPLETE('{self.model_name}', '{escaped_prompt}') as response"
            result = st.connection("snowflake").query(query)
            
            if not result.empty:
                return str(result.iloc[0]['RESPONSE'])
            else:
                return "Unable to generate response."
        except Exception as e:
            return f"Error calling LLM: {str(e)}"
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError


class DataCollectorAgent(BaseAgent):
    
    def __init__(self, model_name: str = 'snowflake-arctic'):
        super().__init__("Data Collector Agent", model_name)
        self.available_tables = {
            "ACCOUNT_ATTRIBUTES_MONTHLY": "Account attributes with company, package, tier info",
            "PHONE_USAGE_DATA": "Phone usage metrics (calls, minutes, MAU, device types)",
            "CHURN_RECORDS": "Churn events with user ID and churn date"
        }
    
    def validate_sql_tables(self, sql: str) -> Tuple[bool, str]:
        sql_upper = sql.upper()
        available_table_names = [table.upper() for table in self.available_tables.keys()]
        
        table_pattern = re.compile(r'\b(FROM|JOIN|INTO|UPDATE)\s+([A-Z_][A-Z0-9_]*)', re.IGNORECASE)
        found_tables = set()
        
        for match in table_pattern.finditer(sql_upper):
            table_name = match.group(2)
            found_tables.add(table_name)
        
        invalid_tables = found_tables - set(available_table_names)
        
        if invalid_tables:
            return False, f"SQL references invalid table(s): {', '.join(invalid_tables)}. Only use: {', '.join(self.available_tables.keys())}"
        
        invalid_patterns = [
            r'\bCUSTOMERS\b', r'\bCUSTOMER\b',
            r'\bUSERS\b(?!\s*\.)',
            r'\bACCOUNTS\b(?!\s*\.)'
        ]
        
        for pattern in invalid_patterns:
            if re.search(pattern, sql_upper):
                if not any(valid_table in sql_upper for valid_table in available_table_names if pattern.replace(r'\b', '').replace('(', '').replace(')', '').upper() in valid_table):
                    return False, f"SQL may reference invalid table. Only use: {', '.join(self.available_tables.keys())}"
        
        return True, ""
    
    def generate_sql(self, user_request: str) -> str:
        tables_info = "\n".join([f"- {table}: {desc}" for table, desc in self.available_tables.items()])
        
        prompt = f"""You are a SQL expert for a phone usage analytics database. Generate a SQL query for Snowflake.

CRITICAL: You MUST ONLY use these exact table names (case-sensitive):
1. ACCOUNT_ATTRIBUTES_MONTHLY
2. PHONE_USAGE_DATA  
3. CHURN_RECORDS

DO NOT use any other table names like CUSTOMERS, USERS, ACCOUNTS, etc. Only use the 3 tables listed above.

Available Tables and Their Schemas:
1. ACCOUNT_ATTRIBUTES_MONTHLY:
   - SERVICE_ACCOUNT_ID (matches USERID in other tables)
   - COMPANY
   - MONTH (date)
   - PACKAGE_NAME
   - TIER_NAME
   - SA_ACCT_STATUS (Active, Suspended, Closed)
   - SA_BRAND_NAME
   - ENTERPRISE_ACCOUNT_ID

2. PHONE_USAGE_DATA:
   - USERID (matches SERVICE_ACCOUNT_ID in ACCOUNT_ATTRIBUTES_MONTHLY)
   - MONTH (date)
   - PHONE_TOTAL_CALLS
   - PHONE_TOTAL_MINUTES_OF_USE
   - VOICE_CALLS, VOICE_MINS
   - PHONE_TOTAL_NUM_INBOUND_CALLS
   - PHONE_TOTAL_NUM_OUTBOUND_CALLS
   - PHONE_MAU (Monthly Active Users)
   - HARDPHONE_CALLS, SOFTPHONE_CALLS
   - MOBILE_CALLS

3. CHURN_RECORDS:
   - USERID (matches SERVICE_ACCOUNT_ID)
   - CHURN_DATE (date)
   - CHURNED (1 = churned, 0 = not churned)

User Request: {user_request}

Generate ONLY the SQL query, no explanations or markdown. Rules:
1. ONLY use tables: ACCOUNT_ATTRIBUTES_MONTHLY, PHONE_USAGE_DATA, CHURN_RECORDS
2. Join on: PHONE_USAGE_DATA.USERID = ACCOUNT_ATTRIBUTES_MONTHLY.SERVICE_ACCOUNT_ID
3. Use proper Snowflake SQL syntax
4. Handle date filtering with MONTH column if needed
5. Return a useful result set

SQL Query (ONLY the query, no markdown, no explanations):"""
        
        sql = self.call_llm(prompt)
        sql = re.sub(r'```sql\n?', '', sql)
        sql = re.sub(r'```\n?', '', sql)
        sql = sql.strip()
        sql = sql.strip('"').strip("'")
        
        is_valid, error_msg = self.validate_sql_tables(sql)
        if not is_valid:
            sql_upper = sql.upper()
            if 'CUSTOMERS' in sql_upper or 'CUSTOMER' in sql_upper:
                sql = sql.replace('CUSTOMERS', 'ACCOUNT_ATTRIBUTES_MONTHLY')
                sql = sql.replace('CUSTOMER', 'ACCOUNT_ATTRIBUTES_MONTHLY')
            if 'USERS' in sql_upper and 'PHONE_USAGE_DATA' not in sql_upper:
                sql = sql.replace('USERS', 'PHONE_USAGE_DATA')
        
        return sql
    
    def fix_sql_table_names(self, sql: str) -> str:
        sql_upper = sql.upper()
        fixed_sql = sql
        
        replacements = {
            'CUSTOMERS': 'ACCOUNT_ATTRIBUTES_MONTHLY',
            'CUSTOMER': 'ACCOUNT_ATTRIBUTES_MONTHLY',
            'USERS': 'PHONE_USAGE_DATA',
            'USER': 'PHONE_USAGE_DATA',
            'ACCOUNTS': 'ACCOUNT_ATTRIBUTES_MONTHLY',
            'ACCOUNT': 'ACCOUNT_ATTRIBUTES_MONTHLY'
        }
        
        for wrong_name, correct_name in replacements.items():
            pattern = re.compile(re.escape(wrong_name), re.IGNORECASE)
            fixed_sql = pattern.sub(correct_name, fixed_sql)
        
        return fixed_sql
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        user_request = context.get('user_request', '')
        sql_query = self.generate_sql(user_request)
        
        is_valid, error_msg = self.validate_sql_tables(sql_query)
        if not is_valid:
            sql_query = self.fix_sql_table_names(sql_query)
            is_valid, error_msg = self.validate_sql_tables(sql_query)
            if not is_valid:
                return {
                    "status": "error",
                    "sql_query": sql_query,
                    "error": f"Invalid table reference. {error_msg} Available tables: {', '.join(self.available_tables.keys())}",
                    "agent": self.agent_name,
                    "suggestion": "The SQL query references tables that don't exist. Please ensure your request only uses: ACCOUNT_ATTRIBUTES_MONTHLY, PHONE_USAGE_DATA, or CHURN_RECORDS"
                }
        
        try:
            df = st.connection("snowflake").query(sql_query)
            return {
                "status": "success",
                "sql_query": sql_query,
                "data": df,
                "row_count": len(df),
                "agent": self.agent_name
            }
        except Exception as e:
            error_str = str(e)
            
            if "does not exist" in error_str or "not authorized" in error_str:
                fixed_sql = self.fix_sql_table_names(sql_query)
                if fixed_sql != sql_query:
                    try:
                        df = st.connection("snowflake").query(fixed_sql)
                        return {
                            "status": "success",
                            "sql_query": fixed_sql,
                            "data": df,
                            "row_count": len(df),
                            "agent": self.agent_name,
                            "note": "SQL was automatically corrected"
                        }
                    except Exception as e2:
                        pass
            
            return {
                "status": "error",
                "sql_query": sql_query,
                "error": error_str,
                "agent": self.agent_name,
                "suggestion": f"Available tables: {', '.join(self.available_tables.keys())}. Make sure your request only references these tables."
            }


class DataQAAgent(BaseAgent):
    def __init__(self, model_name: str = 'snowflake-arctic'):
        super().__init__("Data QA Agent", model_name)
    
    def validate_data(self, df: pd.DataFrame, sql_query: str) -> Dict[str, Any]:
        issues = []
        warnings = []
        
        if df.empty:
            issues.append("DataFrame is empty - no data returned")
            return {"status": "error", "issues": issues, "warnings": warnings}
        
        null_counts = df.isnull().sum()
        high_null_cols = null_counts[null_counts > len(df) * 0.1]
        if not high_null_cols.empty:
            warnings.append(f"Columns with >10% nulls: {', '.join(high_null_cols.index.tolist())}")
        
        if df.duplicated().any():
            warnings.append(f"Found {df.duplicated().sum()} duplicate rows")
        
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            for col in numeric_cols:
                if (df[col] < 0).any():
                    warnings.append(f"Negative values found in {col}")
        
        data_summary = f"""
        Data Shape: {df.shape}
        Columns: {', '.join(df.columns.tolist())}
        Sample Data:
        {df.head(5).to_string()}
        """
        
        prompt = f"""You are a data quality expert. Analyze this data and identify potential quality issues.

{data_summary}

SQL Query Used: {sql_query}

Identify:
1. Data quality issues (missing values, outliers, inconsistencies)
2. Data completeness concerns
3. Potential data integrity problems
4. Recommendations for improvement

Provide a concise assessment:"""
        
        llm_assessment = self.call_llm(prompt)
        
        return {
            "status": "success" if not issues else "warning",
            "issues": issues,
            "warnings": warnings,
            "llm_assessment": llm_assessment,
            "row_count": len(df),
            "column_count": len(df.columns),
            "null_percentage": (df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100) if not df.empty else 0
        }
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        df = context.get('data')
        sql_query = context.get('sql_query', '')
        
        if df is None:
            return {
                "status": "error",
                "error": "No data provided for QA",
                "agent": self.agent_name
            }
        
        validation_result = self.validate_data(df, sql_query)
        validation_result["agent"] = self.agent_name
        
        return validation_result


class BusinessAnalystAgent(BaseAgent):
    def __init__(self, model_name: str = 'snowflake-arctic'):
        super().__init__("Business Analyst Agent", model_name)
    
    def analyze(self, df: pd.DataFrame, user_request: str) -> str:
        summary = f"""
        Data Overview:
        - Rows: {len(df)}
        - Columns: {', '.join(df.columns.tolist())}
        """
        
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            summary += f"\n\nStatistical Summary:\n{df[numeric_cols].describe().to_string()}"
        
        summary += f"\n\nSample Data (first 10 rows):\n{df.head(10).to_string()}"
        
        prompt = f"""You are a business analyst expert in phone usage analytics and churn prediction.

User's Request: {user_request}

{summary}

Provide:
1. Key business insights from this data
2. Trends and patterns identified
3. Actionable recommendations
4. Risk indicators (especially for churn)
5. Opportunities for improvement

Be specific, data-driven, and actionable. Focus on phone usage patterns, account health, and churn risk."""
        
        return self.call_llm(prompt)
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        df = context.get('data')
        user_request = context.get('user_request', '')
        
        if df is None or df.empty:
            return {
                "status": "error",
                "error": "No data available for analysis",
                "agent": self.agent_name
            }
        
        insights = self.analyze(df, user_request)
        
        return {
            "status": "success",
            "insights": insights,
            "agent": self.agent_name
        }


class ComplianceAgent(BaseAgent):
    def __init__(self, model_name: str = 'snowflake-arctic'):
        super().__init__("Compliance Agent", model_name)
        self.pii_keywords = [
            'email', 'phone', 'ssn', 'social_security', 'credit_card',
            'address', 'zip', 'postal', 'name', 'first_name', 'last_name',
            'date_of_birth', 'dob', 'passport', 'driver_license'
        ]
    
    def check_pii(self, df: pd.DataFrame, sql_query: str) -> Dict[str, Any]:
        issues = []
        warnings = []
        
        columns_lower = [col.lower() for col in df.columns]
        pii_columns = []
        for keyword in self.pii_keywords:
            matching_cols = [col for col in columns_lower if keyword in col]
            if matching_cols:
                pii_columns.extend(matching_cols)
                warnings.append(f"Potential PII column detected: {keyword}")
        
        data_summary = f"""
        Columns: {', '.join(df.columns.tolist())}
        Sample Data:
        {df.head(3).to_string()}
        """
        
        prompt = f"""You are a data privacy and compliance expert. Analyze this data for PII (Personally Identifiable Information).

{data_summary}

SQL Query: {sql_query}

Check for:
1. PII data (names, emails, phone numbers, addresses, SSN, etc.)
2. Sensitive personal information
3. GDPR/CCPA compliance concerns
4. Data anonymization needs

Provide a compliance assessment and recommendations:"""
        
        llm_assessment = self.call_llm(prompt)
        
        return {
            "status": "warning" if warnings else "success",
            "pii_columns": pii_columns,
            "warnings": warnings,
            "llm_assessment": llm_assessment
        }
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        df = context.get('data')
        sql_query = context.get('sql_query', '')
        
        if df is None:
            return {
                "status": "error",
                "error": "No data provided for compliance check",
                "agent": self.agent_name
            }
        
        compliance_result = self.check_pii(df, sql_query)
        compliance_result["agent"] = self.agent_name
        
        return compliance_result


class AgentOrchestrator:
    def __init__(self, model_name: str = 'snowflake-arctic'):
        self.agents = {
            "collector": DataCollectorAgent(model_name),
            "qa": DataQAAgent(model_name),
            "analyst": BusinessAnalystAgent(model_name),
            "compliance": ComplianceAgent(model_name)
        }
        self.context = {}
    
    def execute_pipeline(
        self,
        user_request: str,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> Dict[str, Any]:
        results = {}
        self.context = {"user_request": user_request}
        
        if progress_callback:
            progress_callback(0.25, "Data Collection Agent working...")
        
        result = self.agents["collector"].execute(self.context)
        results["collector"] = result
        
        if result["status"] == "error":
            return results
        
        self.context["data"] = result.get("data")
        self.context["sql_query"] = result.get("sql_query")
        
        if progress_callback:
            progress_callback(0.50, "Data QA Agent working...")
        
        result = self.agents["qa"].execute(self.context)
        results["qa"] = result
        
        if progress_callback:
            progress_callback(0.75, "Business Analyst Agent working...")
        
        result = self.agents["analyst"].execute(self.context)
        results["analyst"] = result
        
        if progress_callback:
            progress_callback(0.90, "Compliance Agent working...")
        
        result = self.agents["compliance"].execute(self.context)
        results["compliance"] = result
        
        if progress_callback:
            progress_callback(1.0, "Complete!")
        
        return results


def main():
    st.title("Multi-Agent Data Analysis System")
    st.markdown("**Phone Usage Analytics - Powered by Snowflake Cortex AI**")
    st.markdown("---")
    
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'model_name' not in st.session_state:
        st.session_state.model_name = 'snowflake-arctic'
    
    with st.sidebar:
        st.header("Agent Configuration")
        
        st.markdown("---")
        st.subheader("Available Tables")
        st.info("""
        **ACCOUNT_ATTRIBUTES_MONTHLY**
        - Account info, company, package, tier
        
        **PHONE_USAGE_DATA**
        - Usage metrics: calls, minutes, MAU
        
        **CHURN_RECORDS**
        - Churn events and dates
        """)
        
        st.markdown("---")
        st.subheader("1. Data Collection Agent")
        st.info("Generates SQL queries based on your request and collects data from Snowflake tables.")
        
        st.subheader("2. Data QA Agent")
        st.info("Validates data quality, checks for nulls, duplicates, and data integrity issues.")
        
        st.subheader("3. Business Analyst Agent")
        st.info("Provides business insights, trends, and actionable recommendations.")
        
        st.info("4. Compliance Agent will automatically check for PII")
        
        st.markdown("---")
        st.subheader("LLM Model Selection")
        
        available_models = {
            'snowflake-arctic': 'Snowflake Arctic (Recommended)',
            'mistral-7b': 'Mistral 7B',
            'mistral-large': 'Mistral Large',
            'llama3-70b': 'Llama 3 70B'
        }
        
        selected_model = st.selectbox(
            "Select Model:",
            options=list(available_models.keys()),
            format_func=lambda x: available_models[x],
            index=0
        )
        st.session_state.model_name = selected_model
    
    st.header("Enter Your Analysis Request")
    
    example_requests = [
        "Show me accounts with declining call volume in the last 6 months",
        "Find accounts at high risk of churn based on usage patterns",
        "Compare usage metrics between different package tiers",
        "Analyze phone usage trends by company",
        "Identify accounts with unusual usage patterns"
    ]
    
    selected_example = st.selectbox(
        "Or select an example:",
        ["Custom request..."] + example_requests
    )
    
    if selected_example != "Custom request...":
        default_request = selected_example
    else:
        default_request = ""
    
    user_request = st.text_area(
        "Describe what data you need and what analysis you want:",
        value=default_request,
        height=100,
        help="Describe what data you need, Agent will generate SQL"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        execute_button = st.button("Execute Analysis", type="primary", use_container_width=True)
    
    if execute_button and user_request:
        orchestrator = AgentOrchestrator(st.session_state.model_name)
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def update_progress(progress, message):
            progress_bar.progress(progress)
            status_text.text(message)
        
        with st.spinner("Agents working..."):
            results = orchestrator.execute_pipeline(user_request, update_progress)
            st.session_state.results = results
        
        progress_bar.empty()
        status_text.empty()
    
    if st.session_state.results:
        results = st.session_state.results
        
        st.markdown("---")
        st.header("Analysis Results")
        
        if "collector" in results:
            collector_result = results["collector"]
            
            with st.expander("Data Collection Agent Results", expanded=True):
                if collector_result["status"] == "success":
                    st.success(f"Successfully collected {collector_result['row_count']} rows")
                    
                    st.subheader("Generated SQL Query:")
                    st.code(collector_result["sql_query"], language="sql")
                    
                    st.subheader("Data Preview:")
                    st.dataframe(collector_result["data"], use_container_width=True)
                else:
                    st.error(f"Error: {collector_result.get('error', 'Unknown error')}")
                    
                    if collector_result.get("sql_query"):
                        st.subheader("Generated SQL Query:")
                        st.code(collector_result.get("sql_query", ""), language="sql")
                    
                    if collector_result.get("suggestion"):
                        st.info(f"**Suggestion:** {collector_result['suggestion']}")
                    
                    st.markdown("""
                    **Available Tables:**
                    - `ACCOUNT_ATTRIBUTES_MONTHLY` - Account information (company, package, tier)
                    - `PHONE_USAGE_DATA` - Phone usage metrics (calls, minutes, MAU)
                    - `CHURN_RECORDS` - Churn events
                    
                    **Tip:** Make sure your request only references these tables. For example:
                    - Instead of "customers", use "accounts from ACCOUNT_ATTRIBUTES_MONTHLY"
                    - Instead of "users", use "USERID from PHONE_USAGE_DATA"
                    """)
        
        if "qa" in results:
            qa_result = results["qa"]
            
            with st.expander("Data QA Agent Results", expanded=True):
                if qa_result["status"] == "success":
                    st.success("Data quality checks passed")
                elif qa_result["status"] == "warning":
                    st.warning("Data quality warnings detected")
                else:
                    st.error("Data quality issues found")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Rows", qa_result.get("row_count", 0))
                with col2:
                    st.metric("Columns", qa_result.get("column_count", 0))
                with col3:
                    st.metric("Null %", f"{qa_result.get('null_percentage', 0):.2f}%")
                
                if qa_result.get("warnings"):
                    st.warning("**Warnings:**\n" + "\n".join(f"- {w}" for w in qa_result["warnings"]))
                
                if qa_result.get("llm_assessment"):
                    st.markdown("**LLM Assessment:**")
                    st.markdown(f'<div class="agent-box">{qa_result["llm_assessment"]}</div>', unsafe_allow_html=True)
        
        if "analyst" in results:
            analyst_result = results["analyst"]
            
            with st.expander("Business Analyst Agent Results", expanded=True):
                if analyst_result["status"] == "success":
                    st.success("Business insights generated")
                    st.markdown("**Key Insights & Recommendations:**")
                    st.markdown(f'<div class="success-box">{analyst_result["insights"]}</div>', unsafe_allow_html=True)
                else:
                    st.error(f"Error: {analyst_result.get('error', 'Unknown error')}")
        
        if "compliance" in results:
            compliance_result = results["compliance"]
            
            with st.expander("Compliance Agent Results", expanded=True):
                if compliance_result["status"] == "success":
                    st.success("No PII detected")
                elif compliance_result["status"] == "warning":
                    st.warning("Potential PII detected")
                    if compliance_result.get("warnings"):
                        st.warning("**Warnings:**\n" + "\n".join(f"- {w}" for w in compliance_result["warnings"]))
                else:
                    st.error("Compliance issues found")
                
                if compliance_result.get("llm_assessment"):
                    st.markdown("**Compliance Assessment:**")
                    st.markdown(f'<div class="agent-box">{compliance_result["llm_assessment"]}</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.download_button(
            label="Download Results as JSON",
            data=json.dumps(results, default=str, indent=2),
            file_name="agent_results.json",
            mime="application/json"
        )


if __name__ == "__main__":
    main()

