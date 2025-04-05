from langchain.callbacks.base import BaseCallbackHandler
import logging
import traceback
import os

# Print debug information
print(f"Loading llm_logging.py")
print(f"Current directory: {os.getcwd()}")

# Try to import logging_utils with different approaches
try:
    # Try absolute import
    from src.blog_post_creator.logging_utils import logger, log_llm_interaction

    print("Successfully imported logging_utils with absolute import in llm_logging.py")
except ImportError:
    try:
        # Try relative import
        from .logging_utils import logger, log_llm_interaction

        print("Successfully imported logging_utils with relative import in llm_logging.py")
    except ImportError:
        try:
            # Try import from current directory
            from logging_utils import logger, log_llm_interaction

            print("Successfully imported logging_utils from current directory in llm_logging.py")
        except ImportError:
            # Create basic logging if all imports fail
            print("WARNING: Could not import logging_utils in llm_logging.py, using basic logging")
            logging.basicConfig(level=logging.INFO)
            logger = logging.getLogger('CrewAI_LLM')


            # Create dummy function
            def log_llm_interaction(prompt, response):
                logger.info(f"LLM Request: {prompt}")
                logger.info(f"LLM Response: {response}")


class LLMLoggingHandler(BaseCallbackHandler):
    """Callback handler for logging LLM interactions."""

    def on_llm_start(self, serialized, prompts, **kwargs):
        """Log when LLM starts generating."""
        try:
            logger.info(f"Starting LLM call")
            # Log only first 200 chars of the first prompt to avoid excessive logging
            if prompts and len(prompts) > 0:
                prompt_preview = prompts[0][:200] + "..." if len(prompts[0]) > 200 else prompts[0]
                logger.info(f"Prompt preview: {prompt_preview}")
        except Exception as e:
            logger.error(f"Error in on_llm_start: {e}")
            logger.error(traceback.format_exc())

    def on_llm_end(self, response, **kwargs):
        """Log when LLM completes generating."""
        try:
            logger.info(f"Completed LLM call")

            # Extract content based on response type
            response_text = ""
            if hasattr(response, 'generations'):
                for gen_list in response.generations:
                    for gen in gen_list:
                        if hasattr(gen, 'text'):
                            response_text += gen.text + "\n"
                        elif hasattr(gen, 'message') and hasattr(gen.message, 'content'):
                            response_text += gen.message.content + "\n"
            elif hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)

            # Log response preview
            response_preview = response_text[:200] + "..." if len(response_text) > 200 else response_text
            logger.info(f"Response preview: {response_preview}")

            # Get prompt from kwargs
            prompts = kwargs.get('prompts', ["Unknown prompt"])
            prompt = prompts[0] if prompts else "Unknown prompt"

            # Use the log_llm_interaction function
            log_llm_interaction(prompt, response_text)
        except Exception as e:
            logger.error(f"Error in on_llm_end: {e}")
            logger.error(traceback.format_exc())

    def on_llm_error(self, error, **kwargs):
        """Log when LLM encounters an error."""
        logger.error(f"LLM Error: {error}")