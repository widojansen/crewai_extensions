"""
Extended Task module for CrewAI with additional logging capabilities.
This extends the core Task class with enhanced logging.
"""

import json
import traceback
import logging
from typing import Any, Dict, List, Optional, Union, Callable
from functools import wraps
import inspect
import datetime

# Import the original Task to extend
try:
    from crewai import Task as CrewAITask
except ImportError:
    # Fallback to dynamic import
    from crewai_extensions.compatibility import import_original_class

    CrewAITask = import_original_class('crewai', 'Task')

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


class ExtendedTask(CrewAITask):
    """
    Extended Task class with enhanced logging capabilities.
    """

    def __init__(self, *args, **kwargs):
        """Initialize the extended task with the same parameters as the original."""
        super().__init__(*args, **kwargs)

        # Store original execute method to be wrapped
        self._original_execute = self.execute

        # Wrap the execute method with logging
        self.execute = self._wrap_execute(self.execute)

        # Log task initialization
        task_config = {
            "description": self.description,
            "expected_output": getattr(self, 'expected_output', 'N/A'),
            "has_callback": hasattr(self, 'callback') and self.callback is not None
        }

        logger.info(f"Initialized ExtendedTask: {task_config.get('description', 'No description')[:50]}...")
        logger.info(f"Task Configuration: {json.dumps(task_config, indent=2)}")

    def _wrap_execute(self, execute_method: Callable) -> Callable:
        """
        Wrap the execute method with logging.

        Args:
            execute_method: The original execute method

        Returns:
            Callable: The wrapped execute method
        """

        @wraps(execute_method)
        def wrapped_execute(*args, **kwargs):
            """Wrapped execute method with logging."""
            start_time = datetime.datetime.now()
            task_name = self.description[:50] + "..." if len(self.description) > 50 else self.description

            logger.info(f"Starting task execution: {task_name}")
            logger.info(f"Task execution start time: {start_time.isoformat()}")

            # Log input parameters
            filtered_kwargs = {k: v for k, v in kwargs.items()
                               if k not in ['llm', 'agent'] and not k.startswith('_')}

            if filtered_kwargs:
                try:
                    logger.info(f"Task inputs: {json.dumps(filtered_kwargs, indent=2, default=str)}")
                except Exception as e:
                    logger.info(f"Task inputs available but could not be serialized: {str(e)}")

            # Log the agent assigned to this task
            agent_info = {}
            if 'agent' in kwargs and kwargs['agent'] is not None:
                agent = kwargs['agent']
                if hasattr(agent, 'role'):
                    agent_info["role"] = agent.role
                if hasattr(agent, 'goal'):
                    agent_info["goal"] = agent.goal

                logger.info(f"Task assigned to agent: {json.dumps(agent_info, indent=2)}")

            try:
                # Execute the original method
                result = execute_method(*args, **kwargs)

                # Log the result
                end_time = datetime.datetime.now()
                duration = (end_time - start_time).total_seconds()

                logger.info(f"Task completed: {task_name}")
                logger.info(f"Task execution duration: {duration:.2f} seconds")

                # Log result preview (limiting length for large outputs)
                if isinstance(result, str):
                    result_preview = result[:500] + "..." if len(result) > 500 else result
                    logger.info(f"Task result preview: {result_preview}")
                else:
                    logger.info(f"Task result type: {type(result).__name__}")

                # Execute callback if it exists and isn't already called in the original method
                if hasattr(self, 'callback') and self.callback is not None:
                    try:
                        # Check if callback accepts the right arguments
                        callback_args = inspect.signature(self.callback).parameters
                        if 'task' in callback_args and 'result' in callback_args:
                            logger.info(f"Executing task callback")
                            self.callback(task=self, result=result)
                    except Exception as callback_error:
                        logger.error(f"Error in task callback: {str(callback_error)}")
                        logger.error(traceback.format_exc())

                return result

            except Exception as e:
                error_msg = f"Error executing task {task_name}: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                raise

        return wrapped_execute


# Function to create an extended task
def create_task(*args, **kwargs) -> ExtendedTask:
    """
    Create an extended task with enhanced logging capabilities.

    Args:
        Same parameters as crewai.Task

    Returns:
        ExtendedTask: A task with enhanced logging
    """
    return ExtendedTask(*args, **kwargs)