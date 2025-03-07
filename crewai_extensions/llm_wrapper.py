"""
LLM wrapper module to make crewai_extensions compatible with CrewAI internals.
This module creates a compatibility layer between your custom LLM class and CrewAI.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from crewai_extensions.llm import LLM as CustomLLM


class LLMWrapper:
    """
    A wrapper class that adapts your custom LLM class to work with CrewAI.

    The main issue is that CrewAI sometimes passes the entire LLM object
    as the model parameter to LiteLLM instead of just the model name.
    This wrapper fixes that behavior by properly handling the delegation.
    """

    def __init__(self, custom_llm: CustomLLM):
        """
        Initialize with an instance of your custom LLM class.

        Args:
            custom_llm: An instance of your custom LLM implementation
        """
        self.custom_llm = custom_llm
        # Directly expose necessary attributes that CrewAI might access
        self.model = custom_llm.model
        self.api_key = custom_llm.api_key
        self.api_base = custom_llm.api_base
        self.base_url = custom_llm.base_url

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
    custom_llm = CustomLLM(model=model, **kwargs)
    return LLMWrapper(custom_llm)