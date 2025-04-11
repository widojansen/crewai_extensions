# Enhanced LLM Logging for CrewAI Extensions

This documentation explains how to use the enhanced LLM logging capabilities within the `crewai_extensions` library, which provides comprehensive logging of LLM requests and responses, including the raw HTTP traffic with Ollama and other LLM providers.

## Overview

The enhanced logging system provides:

1. **Complete Request/Response Logging**: Captures the full details of every request to the LLM API and the complete response received, including the raw HTTP traffic.

2. **LLM Parameter Tracking**: Logs all parameters passed to the LLM such as temperature, model name, and tokens.

3. **Token Usage Statistics**: Records detailed information about token usage for monitoring and cost optimization.

4. **HTTP Traffic Inspection**: Captures the raw HTTP requests and responses between your application and Ollama or other providers.

## How It Works

The implementation adds logging at three different levels:

1. **HTTP Layer Logging**: Intercepts all HTTP traffic to log raw requests and responses.
2. **LiteLLM Wrapper Logging**: Enhances the LiteLLM library's logging capabilities.
3. **LLM Class Logging**: Adds detailed logging to the high-level LLM class.

## Using Enhanced Logging

### Command Line Usage

To enable enhanced logging when running your CrewAI project from the command line:

```bash
python main.py run --topic "Artificial Intelligence" --verbose-logging
```

This will activate all enhanced logging features for this run.

### Programmatic Usage

You can enable enhanced logging in your code by:

1. When creating an LLM instance:

```python
from crewai_extensions import create_llm

llm = create_llm(
    model="llama3.1",
    verbose_logging=True  # Enable enhanced logging
)
```

2. At any point in your code:

```python
from crewai_extensions.logging_utils import enable_verbose_logging

# Enable enhanced logging
enable_verbose_logging()
```

### In Streamlit

If you're using the CrewAI Streamlit UI, you can modify your `app.py` to enable enhanced logging:

```python
from crewai_extensions.streamlit_ui import launch_streamlit_ui
import os

# Set environment variable to enable enhanced logging
os.environ["ENABLE_ENHANCED_LLM_LOGGING"] = "true"

if __name__ == "__main__":
    launch_streamlit_ui({
        "project_name": "Blog Post Creator",
        "page_title": "Blog Post Creator",
        "input_field_label": "Enter a blog topic:",
        "input_field_default": "Artificial Intelligence in Healthcare",
        "output_file_extension": "md",
        "main_module_path": "main.py"
    })
```

And check for it in your `main.py`:

```python
# Check if enhanced logging was requested by Streamlit
if os.environ.get("ENABLE_ENHANCED_LLM_LOGGING", "").lower() == "true":
    from crewai_extensions.logging_utils import enable_verbose_logging
    enable_verbose_logging()
```

## Log Output Examples

With enhanced logging enabled, your log files will contain entries like:

### HTTP Request

```
================================================================================
HTTP Request: POST http://localhost:11434/api/generate
================================================================================
Request headers: {"Accept": "application/json", "Content-Type": "application/json", "Host": "localhost:11434"}
Request body: {
  "model": "llama3.1",
  "prompt": "You are an expert content strategist. Plan a detailed structure for a blog post on Artificial Intelligence in Healthcare.",
  "stream": false,
  "options": {
    "temperature": 0.7
  }
}
```

### HTTP Response

```
================================================================================
HTTP Response: 200 from http://localhost:11434/api/generate (took 15.23s)
================================================================================
Response headers: {"Content-Type": "application/json", "Server": "Ollama"}
Response body: {
  "model": "llama3.1",
  "created_at": "2025-04-10T16:45:23.018362Z",
  "response": "# Artificial Intelligence in Healthcare: A Comprehensive Guide\n\n## Introduction (150 words)\n- Brief overview of AI's emergence in healthcare\n- Current state of healthcare challenges that AI aims to address\n- The goal of this blog post: to explore how AI is transforming healthcare\n\n## The Evolution of AI in Healthcare (300 words)\n- Historical perspective: early applications of AI in medicine\n- Major milestones and breakthroughs\n- The convergence of big data, cloud computing, and machine learning\n\n...",
  "done": true,
  "total_duration": 15215423927,
  "load_duration": 1452871,
  "prompt_eval_duration": 5693245,
  "eval_duration": 15208277811,
  "eval_count": 1024
}
```

### LiteLLM Request/Response

```
================================================================================
LITELLM REQUEST - MODEL: ollama/llama3.1
================================================================================
Messages (1):
  Message 1 (user):
You are a writing agent with the following details:
Role: Writing Agent
Goal: Write high-quality, engaging blog content following the provided structure.
...

================================================================================
LITELLM RESPONSE (took 42.67s)
================================================================================
Response content:
# Artificial Intelligence in Healthcare: Revolutionizing Patient Care and Medical Advancements

## Introduction

In recent years, the healthcare industry has witnessed a remarkable transformation with the integration of Artificial Intelligence (AI) technologies...

Usage statistics: {
  "prompt_tokens": 512,
  "completion_tokens": 1024,
  "total_tokens": 1536
}
```

## Configuration Options

For fine-grained control, you can adjust these logging settings:

1. **Log HTTP Traffic Only**: 
   ```python
   from crewai_extensions.logging_utils import setup_http_logging
   setup_http_logging()
   ```

2. **Enable LiteLLM Verbose Logging**:
   ```python
   import litellm
   litellm.set_verbose = True
   ```

3. **Adjust Log Level**:
   ```python
   import logging
   from crewai_extensions.logging_utils import logger
   logger.setLevel(logging.DEBUG)  # For even more verbose logging
   ```

## Log File Location

Log files are stored in the `logs` directory of your project with filenames based on the topic and timestamp:

```
logs/Artificial_Intelligence_in_Healthcare_20250410_164523.log
```

## Troubleshooting

If you encounter issues with enhanced logging:

1. Check that all required files in `crewai_extensions` have been properly updated
2. Verify that you have the necessary permissions to read/write log files
3. Ensure that any environment variables like `PYTHONPATH` are set correctly

For any errors, check your application logs for details about what might be failing during setup.