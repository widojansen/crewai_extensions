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
    if 'agents_yaml' not in st.session_state:
        st.session_state.agents_yaml = ""
    if 'agents_yaml_validated' not in st.session_state:
        st.session_state.agents_yaml_validated = False
    if 'agents_yaml_is_valid' not in st.session_state:
        st.session_state.agents_yaml_is_valid = True
    if 'agents_validation_error' not in st.session_state:
        st.session_state.agents_validation_error = None
    if 'agents_editor_content' not in st.session_state:
        st.session_state.agents_editor_content = ""

    # Load agents configuration if not already loaded
    if not st.session_state.agents_yaml:
        agents_yaml, error = load_yaml_to_string(app_instance.agents_config_path)
        if error:
            tab.warning(error)
            # Create a default template if file doesn't exist
            agents_yaml = """# Agent Configuration
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
        st.session_state.agents_yaml = agents_yaml
        st.session_state.agents_editor_content = agents_yaml

    # Show file path
    tab.caption(f"Configuration file: {app_instance.agents_config_path}")

    # Add a hint about YAML format
    with tab.expander("YAML Format Guidelines", expanded=False):
        tab.markdown("""
                ## Agent Configuration Format

                Each agent should have the following properties:

                - `role`: The agent's role in the crew (e.g., "Researcher")
                - `goal`: What the agent aims to accomplish
                - `backstory`: The agent's background and expertise
                - `verbose`: Set to true for detailed output
                - `allow_delegation`: Whether the agent can delegate tasks

                Example:
                ```yaml
                researcher:
                  role: "Research Agent"
                  goal: "Find accurate information on the topic."
                  backstory: "You are an expert researcher with years of experience."
                  verbose: true
                  allow_delegation: false
                ```
                """)

    # Define callback for when text area changes - just store the content
    def on_yaml_change():
        st.session_state.agents_editor_content = st.session_state.agents_yaml_editor
        # Reset validation state when content changes
        st.session_state.agents_yaml_validated = False

    # Edit YAML content with on_change callback
    yaml_editor = tab.text_area(
        "Edit Agents Configuration:",
        value=st.session_state.agents_editor_content,
        height=400,
        key="agents_yaml_editor",
        on_change=on_yaml_change
    )

    # Two column layout for the buttons
    col1, col2, col3 = tab.columns([1, 1, 1])

    # Validate button
    with col1:
        if tab.button("1. Validate YAML", use_container_width=True, key="validate_agents_btn"):
            # Get current content
            content = st.session_state.agents_editor_content

            # Validate it
            is_valid, error = validate_yaml(content)

            # Store validation results
            st.session_state.agents_yaml_is_valid = is_valid
            st.session_state.agents_validation_error = error
            st.session_state.agents_yaml_validated = True

            # Force a rerun to update the UI
            st.rerun()

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
            # Try to save the file
            success, error = save_yaml_file(app_instance.agents_config_path, st.session_state.agents_editor_content, app_instance)
            if success:
                st.session_state.agents_yaml = st.session_state.agents_editor_content
                tab.success(f"Configuration saved to {app_instance.agents_config_path}")
            else:
                tab.error(error)
                print(f"Error saving agents config: {error}")

    # Reload button
    with col3:
        if tab.button("Reload from File", use_container_width=True, key="reload_agents_btn"):
            agents_yaml, error = load_yaml_to_string(app_instance.agents_config_path)
            if error:
                tab.warning(error)
            else:
                st.session_state.agents_yaml = agents_yaml
                st.session_state.agents_editor_content = agents_yaml
                st.session_state.agents_yaml_validated = False
                tab.success("Reloaded configuration from file.")
                st.rerun()

    # Show validation results (after validate button is clicked)
    if st.session_state.agents_yaml_validated:
        if st.session_state.agents_yaml_is_valid:
            tab.success("✅ YAML is valid! You can now save the configuration.")
        else:
            tab.error(f"❌ Invalid YAML: {st.session_state.agents_validation_error}")

    # Preview structured data (only if validated and valid)
    if st.session_state.agents_yaml_validated and st.session_state.agents_yaml_is_valid:
        with tab.expander("Preview Parsed Configuration", expanded=True):
            try:
                agents_data = yaml.safe_load(st.session_state.agents_editor_content)
                tab.json(agents_data)
            except Exception as e:
                tab.error(f"Could not parse YAML: {str(e)}")


def create_tasks_tab(tab, app_instance):
    """Create the tasks configuration tab."""
    tab.subheader("📋 Task Configuration")

    # Initialize state variables if they don't exist
    if 'tasks_yaml' not in st.session_state:
        st.session_state.tasks_yaml = ""
    if 'tasks_yaml_validated' not in st.session_state:
        st.session_state.tasks_yaml_validated = False
    if 'tasks_yaml_is_valid' not in st.session_state:
        st.session_state.tasks_yaml_is_valid = True
    if 'tasks_validation_error' not in st.session_state:
        st.session_state.tasks_validation_error = None
    if 'tasks_editor_content' not in st.session_state:
        st.session_state.tasks_editor_content = ""

    # Load tasks configuration if not already loaded
    if not st.session_state.tasks_yaml:
        tasks_yaml, error = load_yaml_to_string(app_instance.tasks_config_path)
        if error:
            tab.warning(error)
            # Create a default template if file doesn't exist
            tasks_yaml = """# Task Configuration
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
        st.session_state.tasks_yaml = tasks_yaml
        st.session_state.tasks_editor_content = tasks_yaml

    # Show file path
    tab.caption(f"Configuration file: {app_instance.tasks_config_path}")

    # Add a hint about YAML format
    with tab.expander("YAML Format Guidelines", expanded=False):
        tab.markdown("""
                ## Task Configuration Format

                Each task should have the following properties:

                - `description`: What the task involves (can include placeholders like {topic})
                - `expected_output`: What the task should produce
                - `agent`: Which agent performs this task (must match an agent name)
                - `async_execution`: Whether the task runs asynchronously
                - `human_input`: Whether human input is required
                - `context`: List of tasks whose output this task depends on

                Example:
                ```yaml
                research_task:
                  description: "Research facts about {topic}"
                  expected_output: "A comprehensive report with key findings"
                  agent: "researcher"
                  async_execution: false
                  human_input: false
                ```
                """)

    # Define callback for when text area changes - just store the content
    def on_yaml_change():
        st.session_state.tasks_editor_content = st.session_state.tasks_yaml_editor
        # Reset validation state when content changes
        st.session_state.tasks_yaml_validated = False

    # Edit YAML content with on_change callback
    yaml_editor = tab.text_area(
        "Edit Tasks Configuration:",
        value=st.session_state.tasks_editor_content,
        height=400,
        key="tasks_yaml_editor",
        on_change=on_yaml_change
    )

    # Two column layout for the buttons
    col1, col2, col3 = tab.columns([1, 1, 1])

    # Validate button
    with col1:
        if tab.button("1. Validate YAML", use_container_width=True, key="validate_tasks_btn"):
            # Get current content
            content = st.session_state.tasks_editor_content

            # Validate it
            is_valid, error = validate_yaml(content)

            # Store validation results
            st.session_state.tasks_yaml_is_valid = is_valid
            st.session_state.tasks_validation_error = error
            st.session_state.tasks_yaml_validated = True

            # Force a rerun to update the UI
            st.rerun()

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
            # Try to save the file
            success, error = save_yaml_file(app_instance.tasks_config_path, st.session_state.tasks_editor_content, app_instance)
            if success:
                st.session_state.tasks_yaml = st.session_state.tasks_editor_content
                tab.success(f"Configuration saved to {app_instance.tasks_config_path}")
            else:
                tab.error(error)
                print(f"Error saving tasks config: {error}")

    # Reload button
    with col3:
        if tab.button("Reload from File", use_container_width=True, key="reload_tasks_btn"):
            tasks_yaml, error = load_yaml_to_string(app_instance.tasks_config_path)
            if error:
                tab.warning(error)
            else:
                st.session_state.tasks_yaml = tasks_yaml
                st.session_state.tasks_editor_content = tasks_yaml
                st.session_state.tasks_yaml_validated = False
                tab.success("Reloaded configuration from file.")
                st.rerun()

    # Show validation results (after validate button is clicked)
    if st.session_state.tasks_yaml_validated:
        if st.session_state.tasks_yaml_is_valid:
            tab.success("✅ YAML is valid! You can now save the configuration.")
        else:
            tab.error(f"❌ Invalid YAML: {st.session_state.tasks_validation_error}")

    # Preview structured data (only if validated and valid)
    if st.session_state.tasks_yaml_validated and st.session_state.tasks_yaml_is_valid:
        with tab.expander("Preview Parsed Configuration", expanded=True):
            try:
                tasks_data = yaml.safe_load(st.session_state.tasks_editor_content)
                tab.json(tasks_data)
            except Exception as e:
                tab.error(f"Could not parse YAML: {str(e)}")


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