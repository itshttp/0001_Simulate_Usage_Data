"""
Business Analyst Agent
Provides business insights and recommendations based on data analysis.
"""

import re
from snowflake.snowpark import Session
from .base import BaseAgent


class BusinessAnalystAgent(BaseAgent):
    """Agent responsible for business analysis and generating actionable insights."""

    def __init__(self, session: Session, model: str = "mistral-large2"):
        """
        Initialize Business Analyst Agent.

        Args:
            session: Snowflake Snowpark session
            model: LLM model to use (default: mistral-large2)
        """
        super().__init__(session, "BusinessAnalyst", model=model)
        self.system_prompt = """You are a senior business analyst specializing in telecommunications and customer analytics.

Your tasks:
1. Identify key trends and patterns in the data
2. Analyze business impact
3. Provide 3-5 actionable business recommendations

Output format:
## Key Findings
(List 2-3 key findings)

## Trend Analysis
(Describe observed trends)

## Business Recommendations
1. [Specific recommendation]
2. [Specific recommendation]
3. [Specific recommendation]"""

    def execute(self, context: dict, user_prompt: str = "") -> dict:
        """
        Execute business analysis.

        Args:
            context: Shared context containing data and QA results
            user_prompt: Optional specific analysis focus

        Returns:
            Dictionary with status, insights, and recommendations
        """
        try:
            # Get data and QA results
            df = context.get("data")
            qa_result = context.get("data_qa_result", {})

            # Build analysis context
            data_preview = df.head(10).to_string() if df is not None else "No data"
            data_summary = df.describe().to_string() if df is not None else "No statistics"

            analysis_context = f"""
Data overview:
- Row count: {len(df) if df is not None else 0}
- Column count: {len(df.columns) if df is not None else 0}
- Data quality issues: {qa_result.get('issues_found', 0)}

Data preview:
{data_preview}

Statistical information:
{data_summary}

Data quality summary:
{qa_result.get('summary', 'None')}
"""

            if user_prompt:
                analysis_context += f"\n\nSpecial focus: {user_prompt}"

            # Generate business insights
            insights = self.call_llm(self.system_prompt, analysis_context)

            # Extract recommendations
            recommendations = self._extract_recommendations(insights)

            return {
                "status": "success",
                "agent": self.agent_name,
                "insights": insights,
                "recommendations": recommendations,
                "message": "Business analysis completed"
            }

        except Exception as e:
            return {
                "status": "error",
                "agent": self.agent_name,
                "error": str(e)
            }

    def _extract_recommendations(self, insights: str) -> list:
        """
        Extract recommendations list from insights text.

        Args:
            insights: Full insights text from LLM

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Find "recommendations" section
        lines = insights.split('\n')
        in_recommendations = False

        for line in lines:
            if 'recommendation' in line.lower():
                in_recommendations = True
                continue

            if in_recommendations:
                # Match numbered lists
                match = re.match(r'^\s*(\d+\.|\-|\*)\s*(.+)', line)
                if match:
                    recommendations.append(match.group(2).strip())
                elif line.strip() and not line.startswith('#'):
                    recommendations.append(line.strip())

        return recommendations[:5]  # Return max 5 recommendations
