"""
CrewAI Extensions - Enhanced functionality for CrewAI
"""

from crewai_extensions.llm import LLM
from crewai_extensions.llm_wrapper import create_llm, LLMWrapper
from crewai_extensions.logging_utils import (
    logger, log_crew_execution, log_task_execution,
    log_llm_interaction, set_current_topic, create_topic_logger,
    debug_trace, set_streamlit_queue
)
from crewai_extensions.llm_logging import LLMLoggingHandler
from crewai_extensions.streamlit_ui import CrewAIStreamlitUI, launch_streamlit_ui

__version__ = "0.4.3.4"

