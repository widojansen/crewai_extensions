"""
CrewAI Extensions - Enhanced functionality for CrewAI with better logging
"""

from crewai_extensions.llm import LLM
from crewai_extensions.llm_wrapper import create_llm, LLMWrapper
from .agent_extensions import ExtendedAgent, create_agent
from .task_extensions import ExtendedTask, create_task
from .crew_extensions import CrewWithLogging, kickoff_with_logging

__version__ = "0.2.0"

