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

CRITICAL RULES:
1. Return ONLY pure SQL code - no explanations, no markdown, no comments
2. Use SELECT statements to query data
3. If table names are not specified, use common naming patterns (e.g., ACCOUNTS, CUSTOMERS, USERS, ORDERS, etc.)
4. Always use proper column names based on the context provided
5. For "recent" or "latest" records, use ORDER BY with a timestamp/date column DESC
6. Limit results when asked for "top N" or specific count

Return only the SQL query, nothing else."""

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
            metadata_context = context.get('metadata_context', '').strip()

            # If no tables specified and no meaningful metadata, try to discover tables automatically
            if not available_tables and not metadata_context:
                try:
                    self.log("No table information provided. Discovering available tables...")
                    discovered_tables_df = self.session.sql("SHOW TABLES").to_pandas()
                    if not discovered_tables_df.empty:
                        # Extract table names from the result
                        table_names_col = 'name' if 'name' in discovered_tables_df.columns else discovered_tables_df.columns[1]
                        available_tables = discovered_tables_df[table_names_col].tolist()
                        self.log(f"Discovered {len(available_tables)} tables: {', '.join(available_tables[:5])}...")

                        # Also try to get column info for better SQL generation
                        schema_lines = []
                        for table_name in available_tables[:10]:
                            try:
                                desc_df = self.session.sql(f"DESCRIBE TABLE {table_name}").to_pandas()
                                if not desc_df.empty:
                                    col_names_col = 'name' if 'name' in desc_df.columns else desc_df.columns[0]
                                    cols = desc_df[col_names_col].tolist()[:10]
                                    schema_lines.append(f"- {table_name}: {', '.join(cols)}")
                            except:
                                schema_lines.append(f"- {table_name}")

                        if schema_lines:
                            metadata_context = "\n".join(schema_lines)
                            self.log(f"Auto-generated schema context for {len(schema_lines)} tables")
                except Exception as e:
                    self.log(f"Could not auto-discover tables: {str(e)}")

            # Build enhanced prompt with metadata
            enhanced_prompt = f"""User Question: {user_prompt}

Database Information:"""

            if available_tables:
                enhanced_prompt += f"\nAvailable tables: {', '.join(available_tables)}"
            else:
                enhanced_prompt += "\nAvailable tables: Not specified - use SHOW TABLES to discover, or infer common patterns"

            if metadata_context:
                enhanced_prompt += f"\n\nSchema Context:\n{metadata_context}"

            enhanced_prompt += "\n\nTask: Generate a SQL query to answer the user's question. Return ONLY the SQL code."

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
            error_message = str(e)

            # Check if it's a table not found error
            if "does not exist or not authorized" in error_message.lower():
                # Try to discover available tables
                try:
                    discovered_tables_df = self.session.sql("SHOW TABLES").to_pandas()
                    if not discovered_tables_df.empty:
                        table_names_col = 'name' if 'name' in discovered_tables_df.columns else discovered_tables_df.columns[1]
                        discovered_tables = discovered_tables_df[table_names_col].tolist()
                        error_message += f"\n\n💡 Available tables in your database: {', '.join(discovered_tables[:20])}"
                        error_message += "\n\nPlease click '🔍 Discover Available Tables & Auto-Fill Schema' button to automatically populate the database schema, then try again."
                except:
                    error_message += "\n\n💡 Please click '🔍 Discover Available Tables & Auto-Fill Schema' button to see what tables are available."

            return {
                "status": "error",
                "agent": self.agent_name,
                "error": error_message,
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
