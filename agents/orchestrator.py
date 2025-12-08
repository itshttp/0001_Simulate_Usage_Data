"""
Agent Orchestrator
Coordinates the execution of multiple agents in a pipeline.
"""

import time
from snowflake.snowpark import Session
from .data_collector import DataCollectorAgent
from .data_qa import DataQAAgent
from .business_analyst import BusinessAnalystAgent
from .compliance import ComplianceAgent


class AgentOrchestrator:
    """Orchestrates the execution of multiple agents in sequence."""

    def __init__(self, session: Session, llm_model: str = "mistral-large2"):
        """
        Initialize orchestrator with all agents.

        Args:
            session: Snowflake Snowpark session
            llm_model: LLM model to use for all agents (default: mistral-large2)
        """
        self.session = session
        self.llm_model = llm_model
        self.agents = {
            "collector": DataCollectorAgent(session, model=llm_model),
            "qa": DataQAAgent(session, model=llm_model),
            "analyst": BusinessAnalystAgent(session, model=llm_model),
            "compliance": ComplianceAgent(session, model=llm_model)
        }
        self.context = {}
        self.execution_log = []

    def run_pipeline(self, user_prompts: dict, progress_callback=None) -> dict:
        """
        Execute complete multi-agent pipeline.

        Args:
            user_prompts: Dictionary containing prompts for each agent
                {
                    "collector": "SQL query requirement",
                    "qa": "Data check focus (optional)",
                    "analyst": "Analysis focus (optional)",
                    "available_tables": ["table1", "table2"]  # optional
                }
            progress_callback: Optional callback function for progress updates
                Called with (progress_value, status_message)

        Returns:
            Dictionary containing all agent results and context
        """

        # Initialize context
        if "available_tables" in user_prompts:
            self.context["available_tables"] = user_prompts["available_tables"]

        if "metadata_context" in user_prompts:
            self.context["metadata_context"] = user_prompts["metadata_context"]

        if "user_question" in user_prompts:
            self.context["user_question"] = user_prompts["user_question"]

        # Step 1: Data Collection
        self._log_step("Starting data collection...")
        if progress_callback:
            progress_callback(0.25, "🔍 Data Collection Agent working...")

        # Use user_question if provided, otherwise use collector prompt
        collection_prompt = user_prompts.get("user_question", "") or user_prompts.get("collector", "")

        result = self.agents["collector"].execute(
            self.context,
            collection_prompt
        )
        self.context["data_collector_result"] = result

        if result["status"] == "error":
            return {"error": "Data collection failed", "details": result}

        self.context["data"] = result["data"]

        # Step 2: Data Quality Check
        self._log_step("Starting data quality check...")
        if progress_callback:
            progress_callback(0.50, "✅ Data QA Agent working...")

        result = self.agents["qa"].execute(
            self.context,
            user_prompts.get("qa", "")
        )
        self.context["data_qa_result"] = result

        if result["status"] == "error":
            return {"error": "Data check failed", "details": result}

        # Step 3: Business Analysis
        self._log_step("Starting business analysis...")
        if progress_callback:
            progress_callback(0.75, "💡 Business Analyst Agent working...")

        result = self.agents["analyst"].execute(
            self.context,
            user_prompts.get("analyst", "")
        )
        self.context["business_result"] = result

        if result["status"] == "error":
            return {"error": "Business analysis failed", "details": result}

        # Step 4: Compliance Check
        self._log_step("Starting compliance check...")
        if progress_callback:
            progress_callback(0.90, "🔒 Compliance Agent working...")

        result = self.agents["compliance"].execute(self.context)
        self.context["compliance_result"] = result

        if progress_callback:
            progress_callback(1.0, "✨ Complete!")

        return self.context

    def _log_step(self, message: str):
        """
        Log execution steps with timestamp.

        Args:
            message: Log message to record
        """
        log_entry = {
            "timestamp": time.time(),
            "message": message
        }
        self.execution_log.append(log_entry)
