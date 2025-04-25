import streamlit as st
import yaml
import os
import json
import traceback


def run(app_instance):
    """
    Display the Config page with Agents and Tasks tabs

    Args:
        app_instance: The CrewAIStreamlitUI instance with configuration
    """
    # Add the header
    st.title(f"{app_instance.project_name} - Configuration")

    # Create tabs for Agents and Tasks
    tab_names = []

    if app_instance.show_agents_tab:
        tab_names.append("Agents")

    if app_instance.show_tasks_tab:
        tab_names.append("Tasks")

    # Only create tabs if we have at least one
    if len(tab_names) > 0:
        tabs = st.tabs(tab_names)

        # Initialize tab index counter
        tab_idx = 0

        # Create the tabs content
        if app_instance.show_agents_tab:
            create_agents_tab(tabs[tab_idx], app_instance)
            tab_idx += 1

        if app_instance.show_tasks_tab:
            create_tasks_tab(tabs[tab_idx], app_instance)
    else:
        st.warning("No configuration tabs are enabled. Set show_agents_tab or show_tasks_tab to True.")


def create_agents_tab(tab, app_instance):
    """Create the agents configuration tab."""
    tab.subheader("🤖 Agent Configuration")

    # Initialize state variables if they don't exist
    if 'agents_data' not in st.session_state:
        st.session_state.agents_data = {}
    if 'agents_yaml_validated' not in st.session_state:
        st.session_state.agents_yaml_validated = False
    if 'agents_yaml_is_valid' not in st.session_state:
        st.session_state.agents_yaml_is_valid = True
    if 'agents_validation_error' not in st.session_state:
        st.session_state.agents_validation_error = None

    # Show file path
    tab.caption(f"Configuration file: {app_instance.agents_config_path}")

    # Load agents configuration if not already loaded
    if not st.session_state.agents_data:
        agents_yaml, error = load_yaml_to_string(app_instance.agents_config_path)
        if error:
            tab.warning(error)
            # Create a default template if file doesn't exist
            default_yaml = """# Agent Configuration
        # Define your CrewAI agents here

        planner:
          role: "Planning Agent"
          goal: "Create a detailed structure for the blog post with sections and content focus."
          backstory: "You are an expert content strategist with years of experience structuring high-quality blog posts."
          verbose: true
          allow_delegation: false

        writer:
          role: "Writing Agent"
          goal: "Write high-quality, engaging blog content following the provided structure."
          backstory: "You are a talented writer with expertise in creating engaging and informative content."
          verbose: true
          allow_delegation: false

        editor:
          role: "Editing Agent"
          goal: "Review and polish the blog content for clarity, accuracy, and engagement."
          backstory: "You are a meticulous editor with an eye for detail and a passion for quality content."
          verbose: true
          allow_delegation: false
        """
            try:
                st.session_state.agents_data = yaml.safe_load(default_yaml) or {}
            except Exception as e:
                tab.error(f"Error parsing default YAML: {str(e)}")
                st.session_state.agents_data = {}
        else:
            try:
                st.session_state.agents_data = yaml.safe_load(agents_yaml) or {}
            except Exception as e:
                tab.error(f"Error parsing YAML from file: {str(e)}")
                st.session_state.agents_data = {}
    
    # Add a hint about agent configuration
    with tab.expander("Agent Configuration Guidelines", expanded=False):
        tab.markdown("""
                ## Agent Configuration Format

                Each agent should have the following properties:

                - `role`: The agent's role in the crew (e.g., "Researcher")
                - `goal`: What the agent aims to accomplish
                - `backstory`: The agent's background and expertise
                - `verbose`: Set to true for detailed output
                - `allow_delegation`: Whether the agent can delegate tasks

                You can add multiple agents with different configurations.
                """)
    
    # Add new agent section
    with tab.expander("Add New Agent", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            new_agent_name = st.text_input("Agent Name", key="new_agent_name", placeholder="e.g., researcher")
        with col2:
            if st.button("Add Agent", use_container_width=True):
                if new_agent_name and new_agent_name not in st.session_state.agents_data:
                    st.session_state.agents_data[new_agent_name] = {
                        "role": "",
                        "goal": "",
                        "backstory": "",
                        "verbose": True,
                        "allow_delegation": False
                    }
                    st.rerun()
                elif new_agent_name in st.session_state.agents_data:
                    st.warning(f"Agent '{new_agent_name}' already exists.")
                else:
                    st.warning("Please enter an agent name.")
    
    # Display and edit each agent
    if st.session_state.agents_data:
        tab.subheader("Edit Agents")
        
        agents_to_delete = []
        
        for agent_name, agent_config in st.session_state.agents_data.items():
            with tab.expander(f"Agent: {agent_name}", expanded=True):
                # Two columns for the header - name and delete button
                header_col1, header_col2 = st.columns([3, 1])
                
                with header_col1:
                    st.subheader(agent_name)
                
                with header_col2:
                    if st.button("Delete Agent", key=f"delete_{agent_name}", use_container_width=True):
                        agents_to_delete.append(agent_name)
                
                # Create form fields for each agent property
                agent_config["role"] = st.text_input(
                    "Role",
                    value=agent_config.get("role", ""),
                    key=f"{agent_name}_role"
                )
                
                agent_config["goal"] = st.text_area(
                    "Goal",
                    value=agent_config.get("goal", ""),
                    key=f"{agent_name}_goal"
                )
                
                agent_config["backstory"] = st.text_area(
                    "Backstory",
                    value=agent_config.get("backstory", ""),
                    key=f"{agent_name}_backstory"
                )
                
                # Two columns for boolean values
                col1, col2 = st.columns(2)
                
                with col1:
                    agent_config["verbose"] = st.checkbox(
                        "Verbose",
                        value=agent_config.get("verbose", True),
                        key=f"{agent_name}_verbose"
                    )
                
                with col2:
                    agent_config["allow_delegation"] = st.checkbox(
                        "Allow Delegation",
                        value=agent_config.get("allow_delegation", False),
                        key=f"{agent_name}_allow_delegation"
                    )
                
                # Add any custom fields that might exist in the configuration
                custom_fields = [k for k in agent_config.keys() if k not in ["role", "goal", "backstory", "verbose", "allow_delegation"]]
                
                if custom_fields:
                    st.subheader("Additional Properties")
                    for field in custom_fields:
                        if isinstance(agent_config[field], bool):
                            agent_config[field] = st.checkbox(
                                field.capitalize(),
                                value=agent_config[field],
                                key=f"{agent_name}_{field}"
                            )
                        elif isinstance(agent_config[field], (int, float)):
                            agent_config[field] = st.number_input(
                                field.capitalize(),
                                value=agent_config[field],
                                key=f"{agent_name}_{field}"
                            )
                        else:
                            agent_config[field] = st.text_input(
                                field.capitalize(),
                                value=str(agent_config[field]),
                                key=f"{agent_name}_{field}"
                            )
        
        # Process any agent deletions
        for agent_name in agents_to_delete:
            if agent_name in st.session_state.agents_data:
                del st.session_state.agents_data[agent_name]
                st.rerun()
    else:
        tab.info("No agents configured. Add your first agent above.")
    
    # Preview YAML section
    with tab.expander("Preview YAML", expanded=False):
        # Convert the current configuration to YAML
        agents_yaml = yaml.dump(st.session_state.agents_data, default_flow_style=False, sort_keys=False)
        st.code(agents_yaml, language="yaml")
    
    # Buttons for actions
    col1, col2, col3 = tab.columns([1, 1, 1])
    
    # Validate button
    with col1:
        if tab.button("1. Validate Configuration", use_container_width=True, key="validate_agents_btn"):
            try:
                # Convert to YAML for validation
                agents_yaml = yaml.dump(st.session_state.agents_data, default_flow_style=False, sort_keys=False)
                
                # Validate it (just checks for valid YAML)
                is_valid, error = validate_yaml(agents_yaml)
                
                # Store validation results
                st.session_state.agents_yaml_is_valid = is_valid
                st.session_state.agents_validation_error = error
                st.session_state.agents_yaml_validated = True
                
                # Force a rerun to update the UI
                st.rerun()
            except Exception as e:
                tab.error(f"Error during validation: {str(e)}")
    
    # Save button (only enabled after validation)
    with col2:
        save_button = tab.button(
            "2. Save Configuration",
            use_container_width=True,
            type="primary",
            key="save_agents_btn",
            disabled=not (st.session_state.agents_yaml_validated and st.session_state.agents_yaml_is_valid)
        )
        
        # Process save button click
        if save_button:
            try:
                # Convert to YAML for saving
                agents_yaml = yaml.dump(st.session_state.agents_data, default_flow_style=False, sort_keys=False)
                
                # Try to save the file
                success, error = save_yaml_file(app_instance.agents_config_path, agents_yaml, app_instance)
                if success:
                    tab.success(f"Configuration saved to {app_instance.agents_config_path}")
                else:
                    tab.error(error)
                    print(f"Error saving agents config: {error}")
            except Exception as e:
                tab.error(f"Error preparing data for save: {str(e)}")
    
    # Reload button
    with col3:
        if tab.button("Reload from File", use_container_width=True, key="reload_agents_btn"):
            agents_yaml, error = load_yaml_to_string(app_instance.agents_config_path)
            if error:
                tab.warning(error)
            else:
                try:
                    st.session_state.agents_data = yaml.safe_load(agents_yaml) or {}
                    st.session_state.agents_yaml_validated = False
                    tab.success("Reloaded configuration from file.")
                    st.rerun()
                except Exception as e:
                    tab.error(f"Error parsing YAML from file: {str(e)}")
    
    # Show validation results (after validate button is clicked)
    if st.session_state.agents_yaml_validated:
        if st.session_state.agents_yaml_is_valid:
            tab.success("✅ Configuration is valid! You can now save it.")
        else:
            tab.error(f"❌ Invalid configuration: {st.session_state.agents_validation_error}")


def create_tasks_tab(tab, app_instance):
    """Create the tasks configuration tab."""
    tab.subheader("📋 Task Configuration")

    # Initialize state variables if they don't exist
    if 'tasks_data' not in st.session_state:
        st.session_state.tasks_data = {}
    if 'tasks_yaml_validated' not in st.session_state:
        st.session_state.tasks_yaml_validated = False
    if 'tasks_yaml_is_valid' not in st.session_state:
        st.session_state.tasks_yaml_is_valid = True
    if 'tasks_validation_error' not in st.session_state:
        st.session_state.tasks_validation_error = None

    # Show file path
    tab.caption(f"Configuration file: {app_instance.tasks_config_path}")

    # Load tasks configuration if not already loaded
    if not st.session_state.tasks_data:
        tasks_yaml, error = load_yaml_to_string(app_instance.tasks_config_path)
        if error:
            tab.warning(error)
            # Create a default template if file doesn't exist
            default_yaml = """# Task Configuration
        # Define your CrewAI tasks here

        planning_task:
          description: "Create a comprehensive plan for a blog post on {topic}."
          expected_output: "A detailed blog post plan with sections, key points for each section, and a compelling title."
          agent: "planner"
          async_execution: false
          human_input: false

        writing_task:
          description: "Write a comprehensive blog post about {topic} following the provided plan."
          expected_output: "A comprehensive, engaging, and factually accurate blog post with proper sections and formatting."
          agent: "writer"
          async_execution: false
          human_input: false
          context: ["planning_task"]

        editing_task:
          description: "Review and improve the blog post for clarity, coherence, grammar, and engaging style."
          expected_output: "A polished, error-free, and highly engaging final blog post that maintains accuracy while being enjoyable to read."
          agent: "editor"
          async_execution: false
          human_input: false
          context: ["writing_task"]
        """
            try:
                st.session_state.tasks_data = yaml.safe_load(default_yaml) or {}
            except Exception as e:
                tab.error(f"Error parsing default YAML: {str(e)}")
                st.session_state.tasks_data = {}
        else:
            try:
                st.session_state.tasks_data = yaml.safe_load(tasks_yaml) or {}
            except Exception as e:
                tab.error(f"Error parsing YAML from file: {str(e)}")
                st.session_state.tasks_data = {}
    
    # Add a hint about task configuration
    with tab.expander("Task Configuration Guidelines", expanded=False):
        tab.markdown("""
                ## Task Configuration Format

                Each task should have the following properties:

                - `description`: What the task involves (can include placeholders like {topic})
                - `expected_output`: What the task should produce
                - `agent`: Which agent performs this task (must match an agent name)
                - `async_execution`: Whether the task runs asynchronously
                - `human_input`: Whether human input is required
                - `context`: List of tasks whose output this task depends on

                You can add multiple tasks with different configurations.
                """)
    
    # Get available agent names from the agents configuration
    agent_options = [""] + list(st.session_state.get('agents_data', {}).keys())
    
    # Add new task section
    with tab.expander("Add New Task", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            new_task_name = st.text_input("Task Name", key="new_task_name", placeholder="e.g., research_task")
        with col2:
            if st.button("Add Task", use_container_width=True):
                if new_task_name and new_task_name not in st.session_state.tasks_data:
                    st.session_state.tasks_data[new_task_name] = {
                        "description": "",
                        "expected_output": "",
                        "agent": "",
                        "async_execution": False,
                        "human_input": False,
                        "context": []
                    }
                    st.rerun()
                elif new_task_name in st.session_state.tasks_data:
                    st.warning(f"Task '{new_task_name}' already exists.")
                else:
                    st.warning("Please enter a task name.")
    
    # Display and edit each task
    if st.session_state.tasks_data:
        tab.subheader("Edit Tasks")
        
        # Get list of all task names for context selection
        task_names = list(st.session_state.tasks_data.keys())
        
        tasks_to_delete = []
        
        for task_name, task_config in st.session_state.tasks_data.items():
            with tab.expander(f"Task: {task_name}", expanded=True):
                # Two columns for the header - name and delete button
                header_col1, header_col2 = st.columns([3, 1])
                
                with header_col1:
                    st.subheader(task_name)
                
                with header_col2:
                    if st.button("Delete Task", key=f"delete_{task_name}", use_container_width=True):
                        tasks_to_delete.append(task_name)
                
                # Create form fields for each task property
                task_config["description"] = st.text_area(
                    "Description",
                    value=task_config.get("description", ""),
                    key=f"{task_name}_description"
                )
                
                task_config["expected_output"] = st.text_area(
                    "Expected Output",
                    value=task_config.get("expected_output", ""),
                    key=f"{task_name}_expected_output"
                )
                
                # Use a dropdown selector for agents instead of text input
                current_agent = task_config.get("agent", "")
                
                # Display warning if the current agent doesn't exist in agent options
                if current_agent and current_agent not in agent_options:
                    st.warning(f"Agent '{current_agent}' is not defined in the Agents configuration.")
                
                task_config["agent"] = st.selectbox(
                    "Agent",
                    options=agent_options,
                    index=agent_options.index(current_agent) if current_agent in agent_options else 0,
                    key=f"{task_name}_agent"
                )
                
                # Two columns for boolean values
                col1, col2 = st.columns(2)
                
                with col1:
                    task_config["async_execution"] = st.checkbox(
                        "Async Execution",
                        value=task_config.get("async_execution", False),
                        key=f"{task_name}_async_execution"
                    )
                
                with col2:
                    task_config["human_input"] = st.checkbox(
                        "Human Input",
                        value=task_config.get("human_input", False),
                        key=f"{task_name}_human_input"
                    )
                
                # Context field - use multiselect for task dependencies
                context_value = task_config.get("context", [])
                
                # Filter out the current task from the context options to prevent self-reference
                context_options = [t for t in task_names if t != task_name]
                
                # Build multiselect for context selection
                task_config["context"] = st.multiselect(
                    "Context (tasks this task depends on)",
                    options=context_options,
                    default=[ctx for ctx in context_value if ctx in context_options],
                    key=f"{task_name}_context_select"
                )
                
                # Add any custom fields that might exist in the configuration
                custom_fields = [k for k in task_config.keys() if k not in ["description", "expected_output", "agent", "async_execution", "human_input", "context"]]
                
                if custom_fields:
                    st.subheader("Additional Properties")
                    for field in custom_fields:
                        if isinstance(task_config[field], bool):
                            task_config[field] = st.checkbox(
                                field.capitalize(),
                                value=task_config[field],
                                key=f"{task_name}_{field}"
                            )
                        elif isinstance(task_config[field], (int, float)):
                            task_config[field] = st.number_input(
                                field.capitalize(),
                                value=task_config[field],
                                key=f"{task_name}_{field}"
                            )
                        else:
                            task_config[field] = st.text_input(
                                field.capitalize(),
                                value=str(task_config[field]),
                                key=f"{task_name}_{field}"
                            )
        
        # Process any task deletions
        for task_name in tasks_to_delete:
            if task_name in st.session_state.tasks_data:
                del st.session_state.tasks_data[task_name]
                
                # Also remove this task from any other task's context
                for other_task, config in st.session_state.tasks_data.items():
                    if "context" in config and task_name in config["context"]:
                        config["context"].remove(task_name)
                
                st.rerun()
    else:
        tab.info("No tasks configured. Add your first task above.")
    
    # Preview YAML section
    with tab.expander("Preview YAML", expanded=False):
        # Convert the current configuration to YAML
        tasks_yaml = yaml.dump(st.session_state.tasks_data, default_flow_style=False, sort_keys=False)
        st.code(tasks_yaml, language="yaml")
    
    # Buttons for actions
    col1, col2, col3 = tab.columns([1, 1, 1])
    
    # Validate button
    with col1:
        if tab.button("1. Validate Configuration", use_container_width=True, key="validate_tasks_btn"):
            try:
                # Convert to YAML for validation
                tasks_yaml = yaml.dump(st.session_state.tasks_data, default_flow_style=False, sort_keys=False)
                
                # Validate it (just checks for valid YAML)
                is_valid, error = validate_yaml(tasks_yaml)
                
                # Store validation results
                st.session_state.tasks_yaml_is_valid = is_valid
                st.session_state.tasks_validation_error = error
                st.session_state.tasks_yaml_validated = True
                
                # Force a rerun to update the UI
                st.rerun()
            except Exception as e:
                tab.error(f"Error during validation: {str(e)}")
    
    # Save button (only enabled after validation)
    with col2:
        save_button = tab.button(
            "2. Save Configuration",
            use_container_width=True,
            type="primary",
            key="save_tasks_btn",
            disabled=not (st.session_state.tasks_yaml_validated and st.session_state.tasks_yaml_is_valid)
        )
        
        # Process save button click
        if save_button:
            try:
                # Convert to YAML for saving
                tasks_yaml = yaml.dump(st.session_state.tasks_data, default_flow_style=False, sort_keys=False)
                
                # Try to save the file
                success, error = save_yaml_file(app_instance.tasks_config_path, tasks_yaml, app_instance)
                if success:
                    tab.success(f"Configuration saved to {app_instance.tasks_config_path}")
                else:
                    tab.error(error)
                    print(f"Error saving tasks config: {error}")
            except Exception as e:
                tab.error(f"Error preparing data for save: {str(e)}")
    
    # Reload button
    with col3:
        if tab.button("Reload from File", use_container_width=True, key="reload_tasks_btn"):
            tasks_yaml, error = load_yaml_to_string(app_instance.tasks_config_path)
            if error:
                tab.warning(error)
            else:
                try:
                    st.session_state.tasks_data = yaml.safe_load(tasks_yaml) or {}
                    st.session_state.tasks_yaml_validated = False
                    tab.success("Reloaded configuration from file.")
                    st.rerun()
                except Exception as e:
                    tab.error(f"Error parsing YAML from file: {str(e)}")
    
    # Show validation results (after validate button is clicked)
    if st.session_state.tasks_yaml_validated:
        if st.session_state.tasks_yaml_is_valid:
            tab.success("✅ Configuration is valid! You can now save it.")
        else:
            tab.error(f"❌ Invalid configuration: {st.session_state.tasks_validation_error}")


def load_yaml_file(file_path):
    """Load and parse a YAML file"""
    """Load a YAML file and return its content."""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                content = yaml.safe_load(file)
                return content, None
        else:
            return {}, f"File not found: {file_path}"
    except Exception as e:
        return {}, f"Error loading YAML file: {str(e)}"


def save_yaml_file(file_path, content, app_instance):
    """Save content to a YAML file with improved debugging and error handling."""
    print(f"Try to save YAML file: {file_path}")
    try:
        # Print debug info
        print(f"Attempting to save YAML to: {file_path}")

        # Get absolute file path if relative
        project_root = app_instance.get_project_root()
        if not os.path.isabs(file_path):
            absolute_path = os.path.join(project_root, file_path)
        else:
            absolute_path = file_path

        print(f"Absolute file path: {absolute_path}")

        # Ensure the directory exists
        directory = os.path.dirname(absolute_path)
        if not os.path.exists(directory):
            print(f"Creating directory: {directory}")
            os.makedirs(directory, exist_ok=True)

        # If content is a string, try to parse it as YAML first to validate
        if isinstance(content, str):
            try:
                yaml_content = yaml.safe_load(content)
                print(f"Successfully parsed YAML string")

                # Write the raw string content - this preserves formatting
                with open(absolute_path, 'w') as file:
                    file.write(content)
                    print(f"File saved with raw string content: {absolute_path}")

                return True, None
            except Exception as yaml_error:
                error_msg = f"Error parsing YAML content: {str(yaml_error)}"
                print(error_msg)
                return False, error_msg
        else:
            # If content is already a Python object, dump it directly
            with open(absolute_path, 'w') as file:
                yaml.dump(content, file, default_flow_style=False, sort_keys=False)
                print(f"File saved: {absolute_path}")

            return True, None
    except Exception as e:
        error_msg = f"Error saving YAML file: {str(e)}"
        print(error_msg)
        traceback_str = traceback.format_exc()
        print(f"Traceback: {traceback_str}")
        return False, error_msg


def validate_yaml(yaml_str):
    """
    Validate YAML string to ensure it's properly formatted.

    Args:
        yaml_str (str): The YAML string to validate

    Returns:
        tuple: (bool, str) - (True, None) if valid, (False, error_message) if invalid
    """
    try:
        yaml.safe_load(yaml_str)
        return True, None
    except Exception as e:
        return False, f"Invalid YAML: {str(e)}"

def load_yaml_to_string(file_path):
    """Load a YAML file and return its content as a string."""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                return file.read(), None
        else:
            return "", f"File not found: {file_path}"
    except Exception as e:
        return "", f"Error loading YAML file: {str(e)}"

# Add any other helper methods needed