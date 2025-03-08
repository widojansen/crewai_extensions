"""
Extended Agent module for CrewAI with additional logging capabilities.
This extends the core Agent class with enhanced logging.
"""

import json
import traceback
import logging
from typing import Any, Dict, List, Optional, Union

# Import the original Agent to extend
try:
    from crewai import Agent as CrewAIAgent
except ImportError:
    # Fallback to dynamic import
    from crewai_extensions.compatibility import import_original_class

    CrewAIAgent = import_original_class('crewai', 'Agent')

# Import logging utilities
try:
    # Try absolute import
    from src.blog_post_creator.logging_utils import logger, debug_trace
except ImportError:
    try:
        # Try relative import
        from .logging_utils import logger, debug_trace
    except ImportError:
        try:
            # Try import from current directory
            from logging_utils import logger, debug_trace
        except ImportError:
            # Create basic logging if all imports fail
            print("WARNING: Could not import logging_utils, using basic logging")
            logging.basicConfig(level=logging.INFO)
            logger = logging.getLogger('CrewAI')


            def debug_trace(message):
                print(f"DEBUG: {message}")
                return True


class ExtendedAgent(CrewAIAgent):
    """
    Extended Agent class with enhanced logging capabilities.
    """

    def __init__(self, *args, **kwargs):
        """Initialize the extended agent with the same parameters as the original."""
        super().__init__(*args, **kwargs)
        logger.info(f"Initialized ExtendedAgent: {self.role}")

        # Log the agent configuration
        config = {
            "role": self.role,
            "goal": self.goal,
            "backstory": getattr(self, 'backstory', 'N/A'),
            "verbose": getattr(self, 'verbose', False),
            "allow_delegation": getattr(self, 'allow_delegation', False),
            "tools": [tool.__name__ if hasattr(tool, '__name__') else str(tool)
                      for tool in getattr(self, 'tools', [])]
        }

        logger.info(f"Agent Configuration: {json.dumps(config, indent=2)}")

    def execute_task(self, task: Any, *args, **kwargs) -> str:
        """
        Override the execute_task method to add logging.
        """
        logger.info(f"Agent {self.role} starting task execution: {task.__class__.__name__}")

        # Log the task inputs
        task_inputs = kwargs.get("context", {}) or {}
        logger.info(f"Task inputs: {json.dumps(task_inputs, indent=2)}")

        try:
            # Execute the original method
            result = super().execute_task(task, *args, **kwargs)

            # Log the result
            result_preview = result[:500] + "..." if len(result) > 500 else result
            logger.info(f"Agent {self.role} completed task: {task.__class__.__name__}")
            logger.info(f"Task result preview: {result_preview}")

            return result

        except Exception as e:
            error_msg = f"Error in agent {self.role} executing task {task.__class__.__name__}: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            raise

    def human_input(self, message: str) -> str:
        """Override to add logging for human interactions."""
        logger.info(f"Agent {self.role} requesting human input: {message}")
        response = super().human_input(message)
        logger.info(f"Human response received (length: {len(response)})")
        return response


# Function to create an extended agent
def create_agent(*args, **kwargs) -> ExtendedAgent:
    """
    Create an extended agent with enhanced logging capabilities.

    Args:
        Same parameters as crewai.Agent

    Returns:
        ExtendedAgent: An agent with enhanced logging
    """
    return ExtendedAgent(*args, **kwargs)