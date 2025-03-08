"""
Extensions for CrewAI's core Crew class with improved logging.
This module provides a way to easily use the extended Task and Agent classes.
"""

import json
import traceback
import logging
from typing import Any, Dict, List, Optional, Union, Callable
import os
import datetime

# Import the original Crew to use with our extensions
try:
    from crewai import Crew, Process
except ImportError:
    # Fallback to dynamic import
    from crewai_extensions.compatibility import import_original_class

    Crew = import_original_class('crewai', 'Crew')
    Process = import_original_class('crewai', 'Process')

# Import our extended classes
try:
    from agent_extensions import ExtendedAgent, create_agent
except ImportError:
    try:
        from .agent_extensions import ExtendedAgent, create_agent
    except ImportError:
        print("WARNING: Could not import agent_extensions")


        # Create dummy functions if import fails
        def create_agent(*args, **kwargs):
            from crewai import Agent
            return Agent(*args, **kwargs)


        # Define a class just for type hints
        class ExtendedAgent:
            pass

try:
    from task_extensions import ExtendedTask, create_task
except ImportError:
    try:
        from .task_extensions import ExtendedTask, create_task
    except ImportError:
        print("WARNING: Could not import task_extensions")


        # Create dummy functions if import fails
        def create_task(*args, **kwargs):
            from crewai import Task
            return Task(*args, **kwargs)


        # Define a class just for type hints
        class ExtendedTask:
            pass

# Import logging utilities
try:
    # Try absolute import
    from src.blog_post_creator.logging_utils import logger, log_crew_execution, debug_trace
except ImportError:
    try:
        # Try relative import
        from .logging_utils import logger, log_crew_execution, debug_trace
    except ImportError:
        try:
            # Try import from current directory
            from logging_utils import logger, log_crew_execution, debug_trace
        except ImportError:
            # Create basic logging if all imports fail
            print("WARNING: Could not import logging_utils, using basic logging")
            logging.basicConfig(level=logging.INFO)
            logger = logging.getLogger('CrewAI')


            def log_crew_execution(func):
                return func


            def debug_trace(message):
                print(f"DEBUG: {message}")
                return True


class CrewWithLogging:
    """
    A utility class to create a Crew with extended Agents and Tasks for enhanced logging.
    This is an alternative to subclassing the Crew directly, which might be more complex
    due to initialization differences.
    """

    @staticmethod
    def create(
            agents: List[Union[ExtendedAgent, Any]],
            tasks: List[Union[ExtendedTask, Any]],
            process: Process = Process.sequential,
            verbose: bool = False,
            config: Optional[Dict[str, Any]] = None,
            manager_llm: Optional[Any] = None,
            **kwargs
    ) -> Crew:
        """
        Create a Crew with logging enabled for all tasks and agents.

        Args:
            agents: List of agents (will be converted to ExtendedAgent if not already)
            tasks: List of tasks (will be converted to ExtendedTask if not already)
            process: The process to use (sequential, parallel, hierarchical)
            verbose: Whether to enable verbose output
            config: Additional configuration
            manager_llm: LLM to use for managing the crew
            **kwargs: Additional arguments for Crew initialization

        Returns:
            Crew: A standard CrewAI Crew object with enhanced logging agents and tasks
        """
        # Convert any standard agents to ExtendedAgent
        extended_agents = []
        for agent in agents:
            if not isinstance(agent, ExtendedAgent):
                # Extract agent configuration
                agent_config = {
                    "role": getattr(agent, "role", "Unknown"),
                    "goal": getattr(agent, "goal", "Unknown"),
                    "backstory": getattr(agent, "backstory", ""),
                    "verbose": getattr(agent, "verbose", verbose),
                    "allow_delegation": getattr(agent, "allow_delegation", False),
                    "tools": getattr(agent, "tools", []),
                    "llm": getattr(agent, "llm", None)
                }
                # Create a new ExtendedAgent with the same configuration
                extended_agent = create_agent(**agent_config)
                extended_agents.append(extended_agent)
            else:
                extended_agents.append(agent)

        # Convert any standard tasks to ExtendedTask
        extended_tasks = []
        for task in tasks:
            if not isinstance(task, ExtendedTask):
                # Extract task configuration
                task_config = {
                    "description": getattr(task, "description", "Unknown"),
                    "expected_output": getattr(task, "expected_output", None),
                    "output": getattr(task, "output", None),
                    "context": getattr(task, "context", []),
                    "callback": getattr(task, "callback", None),
                    "tools": getattr(task, "tools", []),
                    "agent": getattr(task, "agent", None)
                }
                # Create a new ExtendedTask with the same configuration
                extended_task = create_task(**task_config)
                extended_tasks.append(extended_task)
            else:
                extended_tasks.append(task)

        # Create the Crew with our extended components
        crew = Crew(
            agents=extended_agents,
            tasks=extended_tasks,
            process=process,
            verbose=verbose,
            config=config,
            manager_llm=manager_llm,
            **kwargs
        )

        # Log crew creation
        logger.info(f"Created Crew with logging")
        logger.info(f"Process: {process.name if hasattr(process, 'name') else str(process)}")
        logger.info(f"Agents: {len(extended_agents)}")
        logger.info(f"Tasks: {len(extended_tasks)}")

        return crew


@log_crew_execution
def kickoff_with_logging(crew: Crew, inputs: Dict[str, Any]) -> Any:
    """
    Wrapper for crew.kickoff that adds additional logging.

    Args:
        crew: The Crew instance
        inputs: Inputs for the crew

    Returns:
        Any: The crew execution result
    """
    start_time = datetime.datetime.now()
    logger.info(f"Starting crew execution with inputs: {json.dumps(inputs, default=str)}")
    logger.info(f"Start time: {start_time.isoformat()}")

    try:
        result = crew.kickoff(inputs=inputs)

        end_time = datetime.datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Crew execution completed successfully")
        logger.info(f"Duration: {duration:.2f} seconds")

        # Log result preview
        if hasattr(result, 'raw_output') and result.raw_output:
            result_preview = result.raw_output[:500] + "..." if len(result.raw_output) > 500 else result.raw_output
            logger.info(f"Result preview: {result_preview}")
        elif hasattr(result, 'result') and result.result:
            result_preview = result.result[:500] + "..." if len(result.result) > 500 else result.result
            logger.info(f"Result preview: {result_preview}")
        elif hasattr(result, '__str__'):
            result_str = str(result)
            result_preview = result_str[:500] + "..." if len(result_str) > 500 else result_str
            logger.info(f"Result preview: {result_preview}")

        return result

    except Exception as e:
        error_msg = f"Error during crew execution: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        raise