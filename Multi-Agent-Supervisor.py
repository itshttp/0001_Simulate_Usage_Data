import streamlit as st  # type: ignore
import pandas as pd
from typing import Dict, Any, Optional, Callable, Tuple, List
import json
import re

st.set_page_config(
    page_title="Multi-Agent Data Analysis System (Supervisor)",
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
    .supervisor-box {
        background-color: #e7f3ff;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #0066cc;
        margin: 1rem 0;
        font-weight: bold;
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


class SupervisorAgent(BaseAgent):
    """Supervisor Agent that uses LLM to coordinate worker agents"""
    
    def __init__(self, model_name: str = 'snowflake-arctic'):
        super().__init__("Supervisor Agent", model_name)
        self.available_agents = {
            "collector": "Data Collector Agent - Generates SQL and collects data from Snowflake",
            "qa": "Data QA Agent - Validates data quality and checks for issues",
            "analyst": "Business Analyst Agent - Provides business insights and recommendations",
            "compliance": "Compliance Agent - Checks for PII and compliance issues"
        }
        self.execution_history = []
    
    def decide_next_action(
        self,
        user_request: str,
        current_context: Dict[str, Any],
        completed_agents: List[str],
        agent_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use LLM to decide which agent to run next or if we should stop"""
        
        # Build execution summary
        execution_summary = []
        for agent_name in completed_agents:
            if agent_name in agent_results:
                result = agent_results[agent_name]
                status = result.get("status", "unknown")
                execution_summary.append(
                    f"- {agent_name}: {status}"
                    + (f" - {result.get('error', '')}" if status == "error" else "")
                )
        
        context_summary = {
            "has_data": "data" in current_context and current_context["data"] is not None,
            "has_sql": "sql_query" in current_context,
            "data_rows": len(current_context.get("data", [])) if current_context.get("data") is not None else 0
        }
        
        prompt = f"""You are a Supervisor Agent coordinating a team of worker agents for data analysis.

USER REQUEST: {user_request}

AVAILABLE WORKER AGENTS:
1. collector - Data Collector Agent: Generates SQL queries and collects data from Snowflake tables
2. qa - Data QA Agent: Validates data quality, checks for nulls, duplicates, and data integrity
3. analyst - Business Analyst Agent: Provides business insights, trends, and actionable recommendations
4. compliance - Compliance Agent: Checks for PII (Personally Identifiable Information) and compliance issues

CURRENT EXECUTION STATUS:
Completed Agents: {', '.join(completed_agents) if completed_agents else 'None'}
Execution Summary:
{chr(10).join(execution_summary) if execution_summary else 'No agents executed yet'}

CURRENT CONTEXT:
- Has data collected: {context_summary['has_data']}
- Has SQL query: {context_summary['has_sql']}
- Data rows: {context_summary['data_rows']}

DECISION RULES:
1. Always start with "collector" agent if no data has been collected
2. If collector fails, try to fix the issue or stop execution
3. After collector succeeds, decide if QA is needed (usually yes)
4. After QA, decide if business analysis is needed (usually yes if data is good)
5. Compliance check should typically run after data is collected
6. If any agent fails critically, you may need to stop or retry
7. You can skip agents if they're not relevant to the user request

Based on the user request and current status, decide:
1. Which agent should run next (or "STOP" if done)
2. Why this decision makes sense
3. Any special instructions for the next agent

Respond in JSON format:
{{
    "next_agent": "agent_name or STOP",
    "reasoning": "explanation of decision",
    "instructions": "any special instructions for the agent"
}}"""
        
        response = self.call_llm(prompt)
        
        # Parse LLM response
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                decision = json.loads(json_match.group(0))
            else:
                # Fallback: try to parse the whole response
                decision = json.loads(response)
        except:
            # Fallback decision logic
            if not completed_agents:
                decision = {
                    "next_agent": "collector",
                    "reasoning": "Starting with data collection as no agents have run yet",
                    "instructions": "Collect data based on user request"
                }
            elif "collector" not in completed_agents:
                decision = {
                    "next_agent": "collector",
                    "reasoning": "Data collection is required first",
                    "instructions": "Collect data based on user request"
                }
            elif "qa" not in completed_agents and context_summary["has_data"]:
                decision = {
                    "next_agent": "qa",
                    "reasoning": "Data QA should run after data collection",
                    "instructions": "Validate the collected data quality"
                }
            elif "analyst" not in completed_agents and context_summary["has_data"]:
                decision = {
                    "next_agent": "analyst",
                    "reasoning": "Business analysis should run after QA",
                    "instructions": "Provide business insights"
                }
            elif "compliance" not in completed_agents and context_summary["has_data"]:
                decision = {
                    "next_agent": "compliance",
                    "reasoning": "Compliance check should run before completion",
                    "instructions": "Check for PII and compliance issues"
                }
            else:
                decision = {
                    "next_agent": "STOP",
                    "reasoning": "All necessary agents have completed",
                    "instructions": "Execution complete"
                }
        
        decision["raw_response"] = response
        return decision
    
    def should_retry_agent(
        self,
        agent_name: str,
        result: Dict[str, Any],
        retry_count: int,
        max_retries: int = 2
    ) -> bool:
        """Decide if an agent should be retried after failure"""
        if retry_count >= max_retries:
            return False
        
        if result.get("status") == "error":
            error = result.get("error", "").lower()
            # Retry on certain types of errors
            retryable_errors = [
                "does not exist",
                "invalid table",
                "syntax error",
                "timeout"
            ]
            return any(err in error for err in retryable_errors)
        
        return False


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
                sql = re.sub(re.compile(r'\bCUSTOMERS\b', re.IGNORECASE), 'ACCOUNT_ATTRIBUTES_MONTHLY', sql)
                sql = re.sub(re.compile(r'\bCUSTOMER\b', re.IGNORECASE), 'ACCOUNT_ATTRIBUTES_MONTHLY', sql)
            if 'USERS' in sql_upper and 'PHONE_USAGE_DATA' not in sql_upper:
                sql = re.sub(re.compile(r'\bUSERS\b', re.IGNORECASE), 'PHONE_USAGE_DATA', sql)
        
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
        supervisor_instructions = context.get('supervisor_instructions', '')
        
        # Incorporate supervisor instructions if provided
        if supervisor_instructions:
            user_request = f"{user_request}\n\nSupervisor Instructions: {supervisor_instructions}"
        
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
        supervisor_instructions = context.get('supervisor_instructions', '')
        
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
        supervisor_instructions = context.get('supervisor_instructions', '')
        
        if df is None or df.empty:
            return {
                "status": "error",
                "error": "No data available for analysis",
                "agent": self.agent_name
            }
        
        # Incorporate supervisor instructions if provided
        if supervisor_instructions:
            user_request = f"{user_request}\n\nSupervisor Instructions: {supervisor_instructions}"
        
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
        supervisor_instructions = context.get('supervisor_instructions', '')
        
        if df is None:
            return {
                "status": "error",
                "error": "No data provided for compliance check",
                "agent": self.agent_name
            }
        
        compliance_result = self.check_pii(df, sql_query)
        compliance_result["agent"] = self.agent_name
        
        return compliance_result


class SupervisorOrchestrator:
    """Orchestrator that uses Supervisor Agent to coordinate worker agents"""
    
    def __init__(self, model_name: str = 'snowflake-arctic'):
        self.supervisor = SupervisorAgent(model_name)
        self.workers = {
            "collector": DataCollectorAgent(model_name),
            "qa": DataQAAgent(model_name),
            "analyst": BusinessAnalystAgent(model_name),
            "compliance": ComplianceAgent(model_name)
        }
        self.context = {}
        self.execution_history = []
        self.agent_results = {}
        self.retry_counts = {}
    
    def execute_pipeline(
        self,
        user_request: str,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> Dict[str, Any]:
        """Execute pipeline using supervisor to coordinate agents"""
        self.context = {"user_request": user_request}
        self.execution_history = []
        self.agent_results = {}
        self.retry_counts = {}
        
        completed_agents = []
        max_iterations = 10  # Prevent infinite loops
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # Supervisor decides next action
            if progress_callback:
                progress_callback(
                    min(0.9, iteration * 0.1),
                    f"Supervisor Agent deciding next action (iteration {iteration})..."
                )
            
            decision = self.supervisor.decide_next_action(
                user_request=user_request,
                current_context=self.context,
                completed_agents=completed_agents,
                agent_results=self.agent_results
            )
            
            next_agent = decision.get("next_agent", "").lower()
            reasoning = decision.get("reasoning", "")
            instructions = decision.get("instructions", "")
            
            # Store supervisor decision in history
            self.execution_history.append({
                "iteration": iteration,
                "decision": decision,
                "completed_agents": completed_agents.copy()
            })
            
            # Check if we should stop
            if next_agent == "stop" or next_agent == "":
                if progress_callback:
                    progress_callback(1.0, "Supervisor decided to stop - execution complete!")
                break
            
            # Validate agent exists
            if next_agent not in self.workers:
                if progress_callback:
                    progress_callback(1.0, f"Supervisor requested unknown agent: {next_agent}. Stopping.")
                break
            
            # Execute the agent
            agent_key = next_agent
            if progress_callback:
                agent_display_name = self.workers[agent_key].agent_name
                progress_callback(
                    min(0.9, iteration * 0.1 + 0.05),
                    f"{agent_display_name} executing... (Supervisor: {reasoning})"
                )
            
            # Add supervisor instructions to context
            self.context["supervisor_instructions"] = instructions
            
            # Execute worker agent
            result = self.workers[agent_key].execute(self.context)
            self.agent_results[agent_key] = result
            
            # Update context with results
            if result.get("status") == "success":
                if "data" in result:
                    self.context["data"] = result["data"]
                if "sql_query" in result:
                    self.context["sql_query"] = result["sql_query"]
            
            # Check if we should retry
            if result.get("status") == "error":
                retry_count = self.retry_counts.get(agent_key, 0)
                if self.supervisor.should_retry_agent(agent_key, result, retry_count):
                    self.retry_counts[agent_key] = retry_count + 1
                    if progress_callback:
                        progress_callback(
                            min(0.9, iteration * 0.1 + 0.05),
                            f"Supervisor decided to retry {agent_key} (attempt {retry_count + 2})"
                        )
                    continue  # Retry same agent
            
            # Mark agent as completed (even if failed, don't retry indefinitely)
            if agent_key not in completed_agents:
                completed_agents.append(agent_key)
        
        # Prepare final results
        final_results = {
            "supervisor_decisions": self.execution_history,
            "agent_results": self.agent_results,
            "completed_agents": completed_agents,
            "iterations": iteration
        }
        
        return final_results


def main():
    st.title("Multi-Agent Data Analysis System (Supervisor Framework)")
    st.markdown("**Phone Usage Analytics - Powered by Snowflake Cortex AI**")
    st.markdown("**🤖 Supervisor Agent coordinates worker agents dynamically**")
    st.markdown("---")
    
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'model_name' not in st.session_state:
        st.session_state.model_name = 'snowflake-arctic'
    
    with st.sidebar:
        st.header("Supervisor Framework")
        st.info("""
        **Supervisor Agent** uses LLM to:
        - Decide which agents to run
        - Determine execution order
        - Handle errors and retries
        - Coordinate worker agents dynamically
        """)
        
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
        st.subheader("Worker Agents")
        st.info("""
        **1. Data Collector Agent**
        Generates SQL and collects data
        
        **2. Data QA Agent**
        Validates data quality
        
        **3. Business Analyst Agent**
        Provides insights and recommendations
        
        **4. Compliance Agent**
        Checks for PII and compliance
        """)
        
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
        help="Supervisor Agent will coordinate worker agents to fulfill your request"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        execute_button = st.button("Execute Analysis", type="primary", use_container_width=True)
    
    if execute_button and user_request:
        orchestrator = SupervisorOrchestrator(st.session_state.model_name)
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def update_progress(progress, message):
            progress_bar.progress(progress)
            status_text.text(message)
        
        with st.spinner("Supervisor coordinating agents..."):
            results = orchestrator.execute_pipeline(user_request, update_progress)
            st.session_state.results = results
        
        progress_bar.empty()
        status_text.empty()
    
    if st.session_state.results:
        results = st.session_state.results
        
        st.markdown("---")
        st.header("Analysis Results")
        
        # Show supervisor decisions
        if "supervisor_decisions" in results:
            with st.expander("🤖 Supervisor Agent Decisions", expanded=True):
                st.markdown("**Supervisor Agent Coordination Log:**")
                for decision_log in results["supervisor_decisions"]:
                    decision = decision_log["decision"]
                    next_agent = decision.get("next_agent", "Unknown")
                    reasoning = decision.get("reasoning", "")
                    
                    st.markdown(f"""
                    <div class="supervisor-box">
                    <strong>Iteration {decision_log['iteration']}:</strong> Supervisor decided to run <strong>{next_agent}</strong><br>
                    <strong>Reasoning:</strong> {reasoning}
                    </div>
                    """, unsafe_allow_html=True)
                
                st.metric("Total Iterations", results.get("iterations", 0))
                st.metric("Agents Completed", len(results.get("completed_agents", [])))
        
        # Show agent results
        agent_results = results.get("agent_results", {})
        
        if "collector" in agent_results:
            collector_result = agent_results["collector"]
            
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
        
        if "qa" in agent_results:
            qa_result = agent_results["qa"]
            
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
        
        if "analyst" in agent_results:
            analyst_result = agent_results["analyst"]
            
            with st.expander("Business Analyst Agent Results", expanded=True):
                if analyst_result["status"] == "success":
                    st.success("Business insights generated")
                    st.markdown("**Key Insights & Recommendations:**")
                    st.markdown(f'<div class="success-box">{analyst_result["insights"]}</div>', unsafe_allow_html=True)
                else:
                    st.error(f"Error: {analyst_result.get('error', 'Unknown error')}")
        
        if "compliance" in agent_results:
            compliance_result = agent_results["compliance"]
            
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
            file_name="supervisor_agent_results.json",
            mime="application/json"
        )


if __name__ == "__main__":
    main()
