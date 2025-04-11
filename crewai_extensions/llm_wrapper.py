"""
Updated LLM wrapper module to make crewai_extensions compatible with CrewAI internals.
"""

import logging
import json
import traceback
from typing import Any, Dict, List, Optional, Union

from crewai_extensions.llm import LLM as CustomLLM
from crewai_extensions.logging_utils import logger, log_json, setup_http_logging
import litellm


class LLMWrapper:
    """
    An enhanced wrapper class that intercepts LiteLLM calls to ensure model name handling
    is done correctly.
    """

    def __init__(self, custom_llm: CustomLLM):
        """
        Initialize with an instance of your custom LLM class.

        Args:
            custom_llm: An instance of your custom LLM implementation
        """
        self.custom_llm = custom_llm

        # Must expose these properties for CrewAI
        self.model = custom_llm.model
        self.api_key = custom_llm.api_key
        self.api_base = custom_llm.api_base
        self.base_url = custom_llm.base_url

        # Save original litellm.completion
        self.original_litellm_completion = litellm.completion

        # Replace litellm.completion with our wrapped version
        litellm.completion = self._wrapped_litellm_completion

        # Initialize HTTP logging if not already done
        setup_http_logging()

    def _wrapped_litellm_completion(self, **kwargs):
        """
        Wrapped version of litellm.completion that handles object/string confusion
        and logs request/response details.
        """
        # Check if model is an LLMWrapper object and replace it with the model name
        if 'model' in kwargs and isinstance(kwargs['model'], LLMWrapper):
            kwargs['model'] = self.model

        # Also check for our wrapper class specifically
        if 'model' in kwargs and str(kwargs['model']).startswith('<crewai_extensions.llm_wrapper'):
            kwargs['model'] = self.model

        # Add model prefix for Ollama models
        if self.model.startswith('llama') and 'ollama/' not in self.model:
            kwargs['model'] = f"ollama/{self.model}"

        # Log the request details
        try:
            # Deep copy to avoid modifying the original
            kwargs_copy = json.loads(json.dumps(kwargs, default=str))

            # Clean sensitive information
            if 'api_key' in kwargs_copy:
                kwargs_copy['api_key'] = '[REDACTED]'

            # Add separators for better log readability
            logger.info("=" * 80)
            logger.info(f"LITELLM REQUEST - MODEL: {kwargs_copy.get('model', 'unknown')}")
            logger.info("=" * 80)

            # Log messages separately with special formatting
            if 'messages' in kwargs_copy:
                messages = kwargs_copy.pop('messages')
                logger.info(f"Messages ({len(messages)}):")
                for idx, msg in enumerate(messages):
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    if isinstance(content, str):
                        preview = content[:1000] + "..." if len(content) > 1000 else content
                        logger.info(f"  Message {idx + 1} ({role}):\n{preview}")
                    else:
                        logger.info(f"  Message {idx + 1} ({role}): {content}")

            # Log other parameters
            log_json(kwargs_copy, prefix="Other parameters: ")
        except Exception as e:
            logger.error(f"Error logging LiteLLM request: {e}")

        # Measure time
        import time
        start_time = time.time()

        try:
            # Call the original method
            response = self.original_litellm_completion(**kwargs)

            # Log the response
            elapsed = time.time() - start_time

            # Add separators for better log readability
            logger.info("=" * 80)
            logger.info(f"LITELLM RESPONSE (took {elapsed:.2f}s)")
            logger.info("=" * 80)

            # Log response details
            try:
                # Extract and log content
                if hasattr(response, 'choices') and response.choices:
                    first_choice = response.choices[0]
                    if hasattr(first_choice, 'message'):
                        message = first_choice.message
                        if hasattr(message, 'content') and message.content:
                            content = message.content
                            preview = content[:1000] + "..." if len(content) > 1000 else content
                            logger.info(f"Response content:\n{preview}")

                # Log usage statistics
                if hasattr(response, 'usage') and response.usage:
                    usage_dict = response.usage.__dict__ if hasattr(response.usage, '__dict__') else response.usage
                    log_json(usage_dict, prefix="Usage statistics: ")

                # Log full response (with safe conversion to avoid errors)
                if hasattr(response, '__dict__'):
                    log_json(response.__dict__, prefix="Full response: ")
                else:
                    logger.info(f"Full response (string): {str(response)}")
            except Exception as e:
                logger.error(f"Error logging LiteLLM response: {e}")

            return response
        except Exception as e:
            # Log error with elapsed time
            elapsed = time.time() - start_time
            logger.error(f"LiteLLM completion error after {elapsed:.2f}s: {str(e)}")
            logger.error(f"Attempted with model: {kwargs.get('model', 'unknown')}")
            logger.error(traceback.format_exc())
            raise

    def call(self,
             messages: Union[str, List[Dict[str, str]]],
             tools: Optional[List[dict]] = None,
             callbacks: Optional[List[Any]] = None,
             available_functions: Optional[Dict[str, Any]] = None) -> Union[str, Any]:
        """
        Delegate the call to the custom LLM implementation.
        """
        try:
            return self.custom_llm.call(
                messages=messages,
                tools=tools,
                callbacks=callbacks,
                available_functions=available_functions
            )
        except Exception as e:
            logging.error(f"Error in LLMWrapper.call: {str(e)}")
            raise

    def supports_function_calling(self) -> bool:
        """Delegate to the custom LLM implementation."""
        return self.custom_llm.supports_function_calling()

    def supports_stop_words(self) -> bool:
        """Delegate to the custom LLM implementation."""
        return self.custom_llm.supports_stop_words()

    def get_context_window_size(self) -> int:
        """Delegate to the custom LLM implementation."""
        return self.custom_llm.get_context_window_size()

    def __del__(self):
        """Restore original litellm completion when wrapper is destroyed."""
        if hasattr(self, 'original_litellm_completion'):
            litellm.completion = self.original_litellm_completion


# Function to create a wrapped LLM instance
def create_llm(model: str, **kwargs) -> LLMWrapper:
    """
    Create a wrapped LLM instance that's compatible with CrewAI.

    Args:
        model: The model name to use
        **kwargs: Additional parameters to pass to the LLM constructor

    Returns:
        LLMWrapper: A wrapped LLM instance
    """
    # Enable verbose logging in LiteLLM if requested
    verbose_logging = kwargs.pop('verbose_logging', False)
    if verbose_logging:
        litellm.set_verbose = True
        logger.info("Enabled verbose logging for LiteLLM")

    # If Ollama model but missing prefix, add it
    if model.startswith('llama') and not model.startswith('ollama/'):
        original_model = model
        model = f"ollama/{model}"
        logging.info(f"Converted model name from {original_model} to {model}")

    custom_llm = CustomLLM(model=model, **kwargs)

    # Create the wrapper
    wrapper = LLMWrapper(custom_llm)

    # Log LLM initialization
    logger.info(f"Created LLM wrapper for model: {model}")

    return wrapper