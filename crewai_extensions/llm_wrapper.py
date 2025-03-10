"""
Updated LLM wrapper module to make crewai_extensions compatible with CrewAI internals.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from crewai_extensions.llm import LLM as CustomLLM
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

    def _wrapped_litellm_completion(self, **kwargs):
        """
        Wrapped version of litellm.completion that handles object/string confusion.
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

        try:
            return self.original_litellm_completion(**kwargs)
        except Exception as e:
            logging.error(f"LiteLLM completion error: {str(e)}")
            logging.error(f"Attempted with model: {kwargs.get('model', 'unknown')}")
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
    # If Ollama model but missing prefix, add it
    if model.startswith('llama') and not model.startswith('ollama/'):
        original_model = model
        model = f"ollama/{model}"
        logging.info(f"Converted model name from {original_model} to {model}")

    custom_llm = CustomLLM(model=model, **kwargs)
    return LLMWrapper(custom_llm)