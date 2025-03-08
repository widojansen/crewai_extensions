# Integration Guide: Enhanced Logging for CrewAI Tasks and Agents

## Table of Contents
1. [Overview](#overview)
2. [Installation](#installation)
3. [Integration Options](#integration-options)
4. [Implementation Details](#implementation-details)
5. [Customizing the Logging](#customizing-the-logging)
6. [Troubleshooting](#troubleshooting)
7. [Log Output Examples](#log-output-examples)

This guide explains how to integrate the enhanced logging extensions for CrewAI's Task and Agent classes into your existing project.

## Overview

The extensions provide detailed logging for the lifecycle of CrewAI Tasks and Agents, including:

- Task inputs/starting parameters
- Task execution duration
- Task outputs/results
- Agent configuration
- Agent task execution
- Human interactions

These extensions build upon your existing logging infrastructure to provide a comprehensive view of the CrewAI workflow.

## Installation

1. Add the extension files to your project:
   - `agent_extensions.py`
   - `task_extensions.py`
   - `crew_extensions.py`

2. Update your imports to use the extended classes as needed.

3. If you're using the extension as part of your custom library:
   ```bash
   pip install -e .
   ```
   
4. Ensure your logging directory exists:
   ```python
   import os
   os.makedirs('logs', exist_ok=True)
   ```

## Integration Options

There are several ways to integrate these extensions, depending on your project's needs:

### Option 1: Direct Replacement (Simplest)

Replace your CrewAI imports with the extended versions:

```python
# Instead of
from crewai import Agent, Task, Crew

# Use
from crewai_extensions.agent_extensions import ExtendedAgent as Agent
from crewai_extensions.task_extensions import ExtendedTask as Task
from crewai_extensions.crew_extensions import CrewWithLogging, kickoff_with_logging
```

### Option 2: Wrapper Approach (Minimal Changes)

Keep your existing code and wrap the crew creation and execution:

```python
from crewai import Agent, Task, Crew
from crewai_extensions.crew_extensions import CrewWithLogging, kickoff_with_logging

# Create agents and tasks as normal
researcher = Agent(...)
research_task = Task(...)

# Wrap the crew creation
crew = CrewWithLogging.create(
    agents=[researcher],
    tasks=[research_task],
    process=Process.sequential
)

# Use enhanced kickoff
result = kickoff_with_logging(crew, inputs={"topic": "AI Ethics"})
```

### Option 3: Integration with BlogPostCreator

Modify your `crew.py` file to use the extended classes:

```python
# Add to imports
from crewai_extensions.agent_extensions import create_agent
from crewai_extensions.task_extensions import create_task  
from crewai_extensions.crew_extensions import CrewWithLogging, kickoff_with_logging

class BlogPostCreator():
    # ... existing code ...
    
    @agent
    def planner(self) -> Agent:
        # Create an extended agent
        return create_agent(
            config=self.agents_config['planner'],
            llm=self.llm,
            verbose=True
        )
    
    # Also update writer() and editor() methods similarly
    
    @task
    def planning_task(self) -> Task:
        # Create an extended task
        return create_task(
            config=self.tasks_config['planning_task']
        )
    
    # Also update writing_task() and editing_task() methods similarly
    
    # Update kickoff method
    def kickoff(self, inputs=None):
        # ... existing code ...
        
        # Create a crew using CrewWithLogging
        crew_instance = CrewWithLogging.create(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
        
        # Run with enhanced logging
        result = kickoff_with_logging(crew_instance, inputs=inputs)
        
        # Save the result to the specified file
        self.save_output_to_file(result, output_filename)
        
        return result
```

## Implementation Details

The extensions work by wrapping the core functionality of CrewAI's Task and Agent classes:

1. **ExtendedAgent**: Enhances the Agent class with detailed logging for:
   - Agent initialization
   - Task execution
   - Human interactions

2. **ExtendedTask**: Extends the Task class with logging for:
   - Task initialization
   - Execution start and end times
   - Input parameters
   - Results and durations

3. **CrewWithLogging**: A helper class that:
   - Converts standard Agents and Tasks to extended versions
   - Creates a Crew with enhanced logging capabilities
   - Logs crew creation and configuration

4. **kickoff_with_logging**: A wrapper function that:
   - Logs the start and end of crew execution
   - Records execution duration
   - Logs inputs and results

## Customizing the Logging

You can customize the logging behavior by modifying the extension files:

1. **Change log levels**: In each extension file, you can adjust log levels (INFO, DEBUG, etc.)

2. **Add custom log handlers**: Add specific handlers for different outputs:
   ```python
   # In agent_extensions.py or task_extensions.py
   handler = logging.FileHandler('detailed_task_logs.log')
   handler.setLevel(logging.DEBUG)
   logger.addHandler(handler)
   ```

3. **Add metadata to logs**: Modify the logged information:
   ```python
   # In task_extensions.py
   logger.info(f"Task inputs: {json.dumps({**filtered_kwargs, 'custom_field': 'value'}, indent=2)}")
   ```

## Troubleshooting

Common issues and solutions:

### Import Errors
If you encounter import errors, the extensions are designed to fall back to basic logging. You might see warnings like:

```
WARNING: Could not import logging_utils, using basic logging
```

Solution: Check the import paths in the extension files and adjust them to match your project structure.

### Type Errors
Type errors can occur when CrewAI changes its API:

```
TypeError: __init__() got an unexpected keyword argument 'xyz'
```

Solution: Update the extension classes to match the current CrewAI implementation.

### Duplicate Logging
If you see duplicate log entries:

Solution: Ensure you're not adding multiple handlers to the same logger. Check for existing handlers before adding new ones.

## Log Output Examples

Here are examples of the enhanced logs:

### Task Execution Logs
```
2025-03-07 10:15:23,456 - CrewAI - INFO - Initialized ExtendedTask: Research the topic thoroughly...
2025-03-07 10:15:23,789 - CrewAI - INFO - Task Configuration: {"description": "Research the topic thoroughly", "expected_output": "A comprehensive research report with key facts and insights", "has_callback": true}
2025-03-07 10:15:24,012 - CrewAI - INFO - Starting task execution: Research the topic thoroughly
2025-03-07 10:15:24,014 - CrewAI - INFO - Task execution start time: 2025-03-07T10:15:24.013212
2025-03-07 10:15:24,015 - CrewAI - INFO - Task inputs: {"topic": "AI Ethics"}
2025-03-07 10:16:35,678 - CrewAI - INFO - Task completed: Research the topic thoroughly
2025-03-07 10:16:35,679 - CrewAI - INFO - Task execution duration: 71.67 seconds
2025-03-07 10:16:35,680 - CrewAI - INFO - Task result preview: # Research Report: AI Ethics
...
```

### Agent Execution Logs
```
2025-03-07 10:15:22,345 - CrewAI - INFO - Initialized ExtendedAgent: Research Specialist
2025-03-07 10:15:22,346 - CrewAI - INFO - Agent Configuration: {"role": "Research Specialist", "goal": "Find accurate information about the topic", "backstory": "You are an experienced researcher with attention to detail", "verbose": true, "allow_delegation": false, "tools": []}
2025-03-07 10:15:24,016 - CrewAI - INFO - Agent Research Specialist starting task execution: ResearchTask
2025-03-07 10:15:24,017 - CrewAI - INFO - Task inputs: {"topic": "AI Ethics"}
2025-03-07 10:16:35,675 - CrewAI - INFO - Agent Research Specialist completed task: ResearchTask
2025-03-07 10:16:35,676 - CrewAI - INFO - Task result preview: # Research Report: AI Ethics...
```

### Crew Execution Logs
```
2025-03-07 10:15:20,123 - CrewAI - INFO - Created Crew with logging
2025-03-07 10:15:20,124 - CrewAI - INFO - Process: sequential
2025-03-07 10:15:20,124 - CrewAI - INFO - Agents: 3
2025-03-07 10:15:20,125 - CrewAI - INFO - Tasks: 3
2025-03-07 10:15:20,126 - CrewAI - INFO - Starting crew execution with inputs: {"topic": "AI Ethics"}
2025-03-07 10:15:20,127 - CrewAI - INFO - Start time: 2025-03-07T10:15:20.126789
2025-03-07 10:18:45,789 - CrewAI - INFO - Crew execution completed successfully
2025-03-07 10:18:45,790 - CrewAI - INFO - Duration: 205.66 seconds
2025-03-07 10:18:45,791 - CrewAI - INFO - Result preview: # AI Ethics: Navigating the Moral Landscape of Artificial Intelligence...
```

In your `main.py`, you might need a small change to use the enhanced kickoff:

```python
def run(topic, streamlit_mode=False):
    """Run the crew."""
    # Set the topic for log file naming and create a topic-specific logger
    set_current_topic(topic)
    log_file = create_topic_logger(topic)

    print(f"Running BlogPostCreator with topic: {topic}")
    logger.info(f"Running BlogPostCreator with topic: {topic}")
    logger.info(f"Log file: {log_file}")

    inputs = {
        'topic': topic
    }
    
    # Create the BlogPostCreator instance
    blog_creator = BlogPostCreator()
    
    # Option 1: Use the modified kickoff method
    blog_creator.kickoff(inputs=inputs)
    
    # Option 2: Or use a wrapper function that applies enhanced logging
    # run_with_enhanced_logging(blog_creator, topic)
```

### Option 4: Minimal Impact Integration

If you prefer not to modify your existing classes, you can create a wrapper function:

```python
def run_with_enhanced_logging(blog_creator, topic):
    """Run the BlogPostCreator with enhanced logging"""
    # Get the original crew
    crew_instance = blog_creator.crew()
    
    # Extract agents and tasks
    agents = crew_instance.agents
    tasks = crew_instance.tasks
    
    # Create an enhanced crew
    enhanced_crew = CrewWithLogging.create(
        agents=agents,
        tasks=tasks,
        process=crew_instance.process,
        verbose=crew_instance.verbose
    )
    
    # Generate the output filename
    output_filename = blog_creator.get_formatted_filename(topic)
    
    # Run with enhanced logging
    inputs = {"topic": topic}
    result = kickoff_with_logging(enhanced_crew, inputs=inputs)
    
    # Save the result to the specified file
    blog_creator.save_output_to_file(result, output_filename)
    
    return result
```