"""
Compatibility utilities for handling version differences in CrewAI.
"""

import importlib
import pkg_resources
import warnings

def get_crewai_version():
    """
    Get the installed version of CrewAI.
    
    Returns:
        str: CrewAI version string
    """
    try:
        return pkg_resources.get_distribution("crewai").version
    except pkg_resources.DistributionNotFound:
        return None

def check_compatibility():
    """
    Check if this extension package is compatible with the installed CrewAI version.
    
    Raises:
        Warning: If compatibility issues are detected
    """
    crewai_version = get_crewai_version()
    
    if crewai_version is None:
        warnings.warn(
            "CrewAI package not found. Please install it: pip install crewai"
        )
        return
    
    # Add compatibility checks as needed
    # For example:
    major, minor, patch = map(int, crewai_version.split('.'))
    
    if major > 1:
        warnings.warn(
            f"This extension package was designed for CrewAI v0.x.x or v1.x.x, "
            f"but CrewAI v{crewai_version} is installed. "
            f"Some functionality may not work correctly."
        )

def import_original_class(module_path, class_name):
    """
    Import a class from CrewAI to extend or modify it.
    
    Args:
        module_path (str): The module path (e.g., 'crewai.llm')
        class_name (str): The class name (e.g., 'LLM')
        
    Returns:
        class: The original class to extend
    """
    module = importlib.import_module(module_path)
    return getattr(module, class_name)

# Run compatibility check on import
check_compatibility()

