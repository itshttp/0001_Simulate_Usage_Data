"""
Compliance Agent
Checks for PII and compliance issues in data and analysis results.
"""

import re
from snowflake.snowpark import Session
from .base import BaseAgent


class ComplianceAgent(BaseAgent):
    """Agent responsible for compliance and PII detection."""

    def __init__(self, session: Session, model: str = "mistral-large2"):
        """
        Initialize Compliance Agent.

        Args:
            session: Snowflake Snowpark session
            model: LLM model to use (default: mistral-large2)
        """
        super().__init__(session, "Compliance", model=model)
        self.pii_patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'credit_card': r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'
        }

    def execute(self, context: dict, user_prompt: str = "") -> dict:
        """
        Execute compliance check on all data and results.

        Args:
            context: Shared context with data and agent results
            user_prompt: Not used for compliance checks

        Returns:
            Dictionary with status, approval, and any issues found
        """
        try:
            # Collect all content to check
            check_content = []

            # Check data collection results
            if 'data_collector_result' in context:
                check_content.append(str(context['data_collector_result'].get('query', '')))

            # Check data (sample first 100 rows)
            if 'data' in context:
                df = context['data']
                if df is not None and not df.empty:
                    sample_data = df.head(100).to_string()
                    check_content.append(sample_data)

            # Check QA results
            if 'data_qa_result' in context:
                check_content.append(str(context['data_qa_result'].get('summary', '')))

            # Check business analysis results
            if 'business_result' in context:
                check_content.append(str(context['business_result'].get('insights', '')))

            all_content = '\n'.join(check_content)

            # PII detection
            pii_found = self._detect_pii(all_content)

            # Semantic check using LLM
            llm_check = self.call_llm(
                """You are a compliance expert. Check if the following content contains:
1. Personally Identifiable Information (PII): names, emails, phones, addresses, etc.
2. Sensitive financial information
3. Other privacy information

Only answer "Approved" or "Not Approved". If not approved, explain why.""",
                all_content[:3000]  # Limit length to avoid token overflow
            )

            # Determine if approved
            approved = len(pii_found) == 0 and "approved" in llm_check.lower()

            return {
                "status": "success",
                "agent": self.agent_name,
                "approved": approved,
                "pii_detected": pii_found,
                "llm_check": llm_check,
                "message": "✅ Compliance check passed" if approved else "❌ Compliance issues found",
                "issues": pii_found if not approved else []
            }

        except Exception as e:
            return {
                "status": "error",
                "agent": self.agent_name,
                "approved": False,
                "error": str(e)
            }

    def _detect_pii(self, text: str) -> list:
        """
        Detect PII using regular expressions and keyword matching.

        Args:
            text: Text content to check

        Returns:
            List of detected PII issues
        """
        found = []

        for pii_type, pattern in self.pii_patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                found.append(f"Detected {pii_type}: {len(matches)} occurrence(s)")

        # Check for common PII keywords
        pii_keywords = ['SSN', 'social security', 'passport', 'password', 'driver license']
        for keyword in pii_keywords:
            if keyword.lower() in text.lower():
                found.append(f"Detected sensitive keyword: {keyword}")

        return found
