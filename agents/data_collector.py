"""
Data Collector Agent
Generates and executes SQL queries based on user requirements.
"""

import re
from snowflake.snowpark import Session
from .base import BaseAgent


class DataCollectorAgent(BaseAgent):
    """Agent responsible for collecting data from Snowflake using AI-generated SQL."""

    def __init__(self, session: Session, model: str = "mistral-large2"):
        """
        Initialize Data Collector Agent.

        Args:
            session: Snowflake Snowpark session
            model: LLM model to use (default: mistral-large2)
        """
        super().__init__(session, "DataCollector", model=model)
        self.system_prompt = """You are a Snowflake SQL expert.
Generate SQL queries based on user requirements.
Return only pure SQL code without any explanation.
Use SELECT statements to query data."""

    def execute(self, context: dict, user_prompt: str) -> dict:
        """
        Execute data collection by generating and running SQL query.

        Args:
            context: Shared context with available_tables if provided
            user_prompt: User's data query requirement

        Returns:
            Dictionary with status, query, data, and metadata
        """
        try:
            # Get available tables (optional)
            available_tables = context.get('available_tables', [])
            metadata_context = context.get('metadata_context', '')

            # Build enhanced prompt with metadata
            enhanced_prompt = f"""Requirement: {user_prompt}

Available tables: {', '.join(available_tables) if available_tables else 'Infer table names based on requirements'}"""

            if metadata_context:
                enhanced_prompt += f"\n\nDatabase Schema Context:\n{metadata_context}"

            enhanced_prompt += "\n\nGenerate SQL query:"

            # Generate SQL
            llm_response = self.call_llm(self.system_prompt, enhanced_prompt)

            # Extract SQL
            sql_query = self._extract_sql(llm_response)

            # Execute query
            df = self.session.sql(sql_query).to_pandas()

            return {
                "status": "success",
                "agent": self.agent_name,
                "query": sql_query,
                "data": df,
                "row_count": len(df),
                "columns": df.columns.tolist(),
                "message": f"Successfully collected {len(df)} rows of data"
            }

        except Exception as e:
            return {
                "status": "error",
                "agent": self.agent_name,
                "error": str(e),
                "query": sql_query if 'sql_query' in locals() else "SQL generation failed"
            }

    def _extract_sql(self, llm_response: str) -> str:
        """
        Extract SQL from LLM response, removing markdown and extra text.

        Args:
            llm_response: Raw LLM response

        Returns:
            Cleaned SQL query string
        """
        # Remove markdown code block markers
        sql = llm_response.strip()
        sql = re.sub(r'^```sql\s*', '', sql, flags=re.IGNORECASE)
        sql = re.sub(r'^```\s*', '', sql)
        sql = re.sub(r'\s*```$', '', sql)

        # Keep only the first SELECT statement
        sql = sql.strip()
        if not sql.upper().startswith('SELECT'):
            # Try to find SELECT statement
            match = re.search(r'(SELECT\s+.*?)(?:;|\Z)', sql, re.IGNORECASE | re.DOTALL)
            if match:
                sql = match.group(1)

        return sql.strip()
