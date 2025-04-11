from langchain.callbacks.base import BaseCallbackHandler
import logging
import traceback
import os
import json
import time
from datetime import datetime

# Print debug information
print(f"Loading llm_logging.py")
print(f"Current directory: {os.getcwd()}")

# Try to import logging_utils with different approaches
try:
    # Try absolute import
    from src.blog_post_creator.logging_utils import logger, log_llm_interaction, log_json

    print("Successfully imported logging_utils with absolute import in llm_logging.py")
except ImportError:
    try:
        # Try relative import
        from .logging_utils import logger, log_llm_interaction, log_json

        print("Successfully imported logging_utils with relative import in llm_logging.py")
    except ImportError:
        try:
            # Try import from current directory
            from logging_utils import logger, log_llm_interaction, log_json

            print("Successfully imported logging_utils from current directory in llm_logging.py")
        except ImportError:
            # Create basic logging if all imports fail
            print("WARNING: Could not import logging_utils in llm_logging.py, using basic logging")
            logging.basicConfig(level=logging.INFO)
            logger = logging.getLogger('CrewAI_LLM')


            # Create dummy functions
            def log_llm_interaction(prompt, response):
                logger.info(f"LLM Request: {prompt}")
                logger.info(f"LLM Response: {response}")


            def log_json(obj, prefix="", max_length=10000):
                try:
                    json_str = json.dumps(obj, default=str, indent=2)
                    if len(json_str) > max_length:
                        json_str = json_str[:max_length] + "... [truncated]"
                    logger.info(f"{prefix}{json_str}")
                except Exception as e:
                    logger.info(f"{prefix}{str(obj)} (couldn't convert to JSON: {e})")


class LLMLoggingHandler(BaseCallbackHandler):
    """Callback handler for logging LLM interactions."""

    def on_llm_start(self, serialized, prompts, **kwargs):
        """Log when LLM starts generating."""
        try:
            # Add a timestamp for timing calculations
            self.start_time = time.time()

            # Add separators for better readability
            logger.info("=" * 80)
            logger.info(f"LLM CALL STARTED: {datetime.now().isoformat()}")
            logger.info("=" * 80)

            # Log serialized info
            if serialized:
                logger.info(f"LLM: {serialized.get('name', 'unknown')}")

                # Log any configuration details
                if 'kwargs' in serialized:
                    logger.info("LLM Configuration:")
                    log_json(serialized['kwargs'], prefix="  ")

            # Log the prompts
            if prompts and len(prompts) > 0:
                logger.info(f"Prompts ({len(prompts)}):")
                for i, prompt in enumerate(prompts):
                    # Truncate very long prompts
                    if len(prompt) > 1000:
                        prompt_preview = prompt[:1000] + "... [truncated]"
                    else:
                        prompt_preview = prompt
                    logger.info(f"  Prompt {i + 1}:\n{prompt_preview}")

            # Log additional kwargs
            if kwargs:
                filtered_kwargs = {k: v for k, v in kwargs.items()
                                   if k not in ['run_id', 'parent_run_id', 'tags', 'metadata']}
                if filtered_kwargs:
                    logger.info("Additional parameters:")
                    log_json(filtered_kwargs, prefix="  ")

        except Exception as e:
            logger.error(f"Error in on_llm_start: {e}")
            logger.error(traceback.format_exc())

    def on_llm_end(self, response, **kwargs):
        """Log when LLM completes generating."""
        try:
            # Calculate elapsed time
            elapsed = time.time() - getattr(self, 'start_time', time.time())

            # Add separators for better readability
            logger.info("=" * 80)
            logger.info(f"LLM CALL COMPLETED (took {elapsed:.2f}s): {datetime.now().isoformat()}")
            logger.info("=" * 80)

            # Extract content based on response type
            response_text = ""
            if hasattr(response, 'generations'):
                logger.info(f"Response generations: {len(response.generations)}")
                for i, gen_list in enumerate(response.generations):
                    logger.info(f"  Generation group {i + 1}:")
                    for j, gen in enumerate(gen_list):
                        if hasattr(gen, 'text'):
                            gen_text = gen.text
                            response_text += gen_text + "\n"
                            logger.info(f"    Generation {j + 1} text: {gen_text[:500]}...")
                        elif hasattr(gen, 'message') and hasattr(gen.message, 'content'):
                            gen_text = gen.message.content
                            response_text += gen_text + "\n"
                            logger.info(f"    Generation {j + 1} message content: {gen_text[:500]}...")

                        # Log any additional attributes
                        for attr_name in ['generation_info', 'type', 'role']:
                            if hasattr(gen, attr_name) and getattr(gen, attr_name) is not None:
                                logger.info(f"    Generation {j + 1} {attr_name}: {getattr(gen, attr_name)}")
            elif hasattr(response, 'content'):
                response_text = response.content
                logger.info(f"Response content: {response_text[:1000]}...")
            else:
                response_text = str(response)
                logger.info(f"Response (string): {response_text[:1000]}...")

            # Log usage information if available
            if hasattr(response, 'llm_output') and response.llm_output:
                logger.info("LLM output metadata:")
                log_json(response.llm_output, prefix="  ")

            # Log usage statistics if available
            if hasattr(response, 'usage') and response.usage:
                logger.info("Usage statistics:")
                usage_dict = response.usage.__dict__ if hasattr(response.usage, '__dict__') else response.usage
                log_json(usage_dict, prefix="  ")

            # Get prompt from kwargs
            prompts = kwargs.get('prompts', ["Unknown prompt"])
            prompt = prompts[0] if prompts else "Unknown prompt"

            # Use the log_llm_interaction function to record the full interaction
            log_llm_interaction(prompt, response_text)

        except Exception as e:
            logger.error(f"Error in on_llm_end: {e}")
            logger.error(traceback.format_exc())

    def on_llm_error(self, error, **kwargs):
        """Log when LLM encounters an error."""
        try:
            # Calculate elapsed time if start_time exists
            elapsed = time.time() - getattr(self, 'start_time', time.time())

            logger.error(f"LLM Error after {elapsed:.2f}s: {error}")

            # Log additional error details if available
            if hasattr(error, '__dict__'):
                logger.error("Error details:")
                log_json(error.__dict__, prefix="  ")

            # Log traceback if available
            if hasattr(error, '__traceback__'):
                logger.error(f"Error traceback: {traceback.format_tb(error.__traceback__)}")

            # Log any additional context from kwargs
            if kwargs:
                filtered_kwargs = {k: v for k, v in kwargs.items()
                                   if k not in ['run_id', 'parent_run_id', 'tags', 'metadata']}
                if filtered_kwargs:
                    logger.error("Error context:")
                    log_json(filtered_kwargs, prefix="  ")

        except Exception as e:
            logger.error(f"Error in on_llm_error handler: {e}")
            logger.error(traceback.format_exc())