"""
Base Agent Class
Provides common functionality for all agents in the system.
"""

from snowflake.snowpark import Session


class BaseAgent:
    """Base class for all agents in the multi-agent system."""

    def __init__(self, session: Session, agent_name: str):
        """
        Initialize base agent.

        Args:
            session: Snowflake Snowpark session
            agent_name: Name identifier for this agent
        """
        self.session = session
        self.agent_name = agent_name
        self.model = "mistral-large2"  # Can change to llama3.1-70b or others

    def call_llm(self, system_prompt: str, user_message: str) -> str:
        """
        Call Snowflake Cortex LLM.

        Args:
            system_prompt: System instructions for the LLM
            user_message: User message/query

        Returns:
            LLM response as string
        """
        try:
            full_prompt = f"{system_prompt}\n\nUser: {user_message}"

            # Use SQL to call Cortex Complete function
            query = f"""
                SELECT SNOWFLAKE.CORTEX.COMPLETE(
                    '{self.model}',
                    '{full_prompt.replace("'", "''")}'
                ) as response
            """

            result = self.session.sql(query).collect()
            response = result[0]['RESPONSE']
            return response
        except Exception as e:
            return f"LLM call failed: {str(e)}"

    def execute(self, context: dict, user_prompt: str = "") -> dict:
        """
        Execute agent's main task.

        Args:
            context: Shared context dictionary with data and results
            user_prompt: Optional user prompt for this agent

        Returns:
            Dictionary with execution results
        """
        raise NotImplementedError("Subclasses must implement execute method")
