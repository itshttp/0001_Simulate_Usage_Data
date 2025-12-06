"""
Data QA Agent
Performs data quality checks and validation.
"""

import pandas as pd
from snowflake.snowpark import Session
from .base import BaseAgent


class DataQAAgent(BaseAgent):
    """Agent responsible for data quality analysis and validation."""

    def __init__(self, session: Session, model: str = "mistral-large2"):
        """
        Initialize Data QA Agent.

        Args:
            session: Snowflake Snowpark session
            model: LLM model to use (default: mistral-large2)
        """
        super().__init__(session, "DataQA", model=model)
        self.standard_checks = [
            "missing_values",
            "data_types",
            "outliers",
            "duplicates",
            "basic_stats"
        ]

    def execute(self, context: dict, user_prompt: str = "") -> dict:
        """
        Execute data quality checks.

        Args:
            context: Shared context containing data to check
            user_prompt: Optional custom analysis requirements

        Returns:
            Dictionary with status, analysis results, and summary
        """
        try:
            df = context.get("data")
            if df is None or df.empty:
                return {
                    "status": "error",
                    "agent": self.agent_name,
                    "error": "No data available for analysis"
                }

            # Perform standard QC checks
            analysis = self._standard_qc(df)

            # If custom prompt provided, add additional analysis
            if user_prompt:
                custom_analysis = self.call_llm(
                    "You are a data quality analyst. Analyze the data based on user requirements:",
                    f"{user_prompt}\n\nData overview:\n{df.describe().to_string()}"
                )
                analysis["custom_analysis"] = custom_analysis

            # Generate summary
            summary = self.call_llm(
                "You are a data quality analyst. Provide a concise summary of the following data quality check results (3-5 sentences):",
                str(analysis)
            )

            return {
                "status": "success",
                "agent": self.agent_name,
                "analysis": analysis,
                "summary": summary,
                "issues_found": len(analysis.get("issues", [])),
                "message": "Data quality check completed"
            }

        except Exception as e:
            return {
                "status": "error",
                "agent": self.agent_name,
                "error": str(e)
            }

    def _standard_qc(self, df: pd.DataFrame) -> dict:
        """
        Perform standard data quality checks.

        Args:
            df: DataFrame to analyze

        Returns:
            Dictionary with check results
        """
        issues = []

        # 1. Missing values check
        missing = df.isnull().sum()
        missing_pct = (missing / len(df) * 100).round(2)
        if missing.any():
            missing_info = {col: f"{missing[col]} ({missing_pct[col]}%)"
                           for col in missing[missing > 0].index}
            issues.append(f"Missing values found: {missing_info}")

        # 2. Duplicate check
        duplicates = df.duplicated().sum()
        if duplicates > 0:
            issues.append(f"Found {duplicates} duplicate rows ({duplicates/len(df)*100:.2f}%)")

        # 3. Data type information
        dtypes_info = df.dtypes.astype(str).to_dict()

        # 4. Basic statistics
        numeric_cols = df.select_dtypes(include=['number']).columns
        stats = {}
        if len(numeric_cols) > 0:
            stats = df[numeric_cols].describe().to_dict()

        return {
            "checks_performed": self.standard_checks,
            "issues": issues,
            "data_shape": {"rows": df.shape[0], "columns": df.shape[1]},
            "data_types": dtypes_info,
            "numeric_stats": stats,
            "missing_summary": missing[missing > 0].to_dict() if missing.any() else {}
        }
