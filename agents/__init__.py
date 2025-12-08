"""
Multi-Agent System for Data Analysis

This package provides a multi-agent system for automated data collection,
quality assurance, business analysis, and compliance checking using Snowflake Cortex.
"""

from .base import BaseAgent
from .data_collector import DataCollectorAgent
from .data_qa import DataQAAgent
from .business_analyst import BusinessAnalystAgent
from .compliance import ComplianceAgent
from .orchestrator import AgentOrchestrator

__all__ = [
    'BaseAgent',
    'DataCollectorAgent',
    'DataQAAgent',
    'BusinessAnalystAgent',
    'ComplianceAgent',
    'AgentOrchestrator'
]

__version__ = '1.0.0'
