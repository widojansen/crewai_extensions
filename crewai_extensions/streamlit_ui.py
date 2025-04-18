import streamlit as st
import subprocess
import os
import time
import threading
import queue
import glob
import base64
from datetime import datetime
import re
import traceback
import warnings
import logging
import sys
import psutil
import yaml


class CrewAIStreamlitUI:
    """
    A reusable Streamlit UI for CrewAI projects.

    This class provides a configurable web interface to manage CrewAI projects,
    displaying logs, outputs, and files in a user-friendly way.
    """

    def __init__(
            self,
            project_name="CrewAI Project",
            page_title="CrewAI Project",
            page_icon="📝",
            input_field_label="Enter topic:",
            input_field_default="Artificial Intelligence",
            input_field_placeholder="e.g., Machine Learning",
            input_field_help="Enter the topic for processing",
            output_dir="output",
            logs_dir="logs",
            config_dir="config",
            agents_config_file="agents.yaml",
            tasks_config_file="tasks.yaml",
            output_file_extension="md",
            main_module_path=None,
            process_action="run",
            process_param_name="--topic",
            stream_logs=True,
            show_log_tab=True,
            show_output_tab=True,
            show_files_tab=True,
            show_agents_tab=True,
            show_tasks_tab=True,
            max_monitor_time=1800,  # 30 minutes timeout for subprocess
            topic_clean_func=None
    ):
        """
        Initialize the Streamlit UI with configurable parameters.

        Args:
            project_name (str): Name shown in the UI header
            page_title (str): Browser tab title
            page_icon (str): Icon for the browser tab
            input_field_label (str): Label for the main input field
            input_field_default (str): Default value for the input field
            input_field_placeholder (str): Placeholder text for the input field
            input_field_help (str): Help text for the input field
            output_dir (str): Directory where output files are stored
            logs_dir (str): Directory where log files are stored
            config_dir (str): Directory where configuration files are stored
            agents_config_file (str): Filename for agents configuration
            tasks_config_file (str): Filename for tasks configuration
            output_file_extension (str): File extension for output files (without dot)
            main_module_path (str): Path to the main.py module to execute
            process_action (str): Action parameter for the subprocess command (e.g., "run")
            process_param_name (str): Parameter name for the input value (e.g., "--topic")
            stream_logs (bool): Whether to stream logs in real-time
            show_log_tab (bool): Whether to show the log tab
            show_output_tab (bool): Whether to show the output preview tab
            show_files_tab (bool): Whether to show the files tab
            show_agents_tab (bool): Whether to show the agents configuration tab
            show_tasks_tab (bool): Whether to show the tasks configuration tab
            max_monitor_time (int): Maximum time to monitor a process before timeout
            topic_clean_func (callable): Optional function to clean the topic value
        """
        # Set environment variables to control warnings
        os.environ['PYTHONWARNINGS'] = 'ignore::UserWarning'

        # Store configuration
        self.project_name = project_name
        self.page_title = page_title
        self.page_icon = page_icon
        self.input_field_label = input_field_label
        self.input_field_default = input_field_default
        self.input_field_placeholder = input_field_placeholder
        self.input_field_help = input_field_help
        self.output_dir = output_dir
        self.logs_dir = logs_dir
        self.config_dir = config_dir
        self.agents_config_file = agents_config_file
        self.tasks_config_file = tasks_config_file
        self.output_file_extension = output_file_extension
        self.main_module_path = main_module_path
        self.process_action = process_action
        self.process_param_name = process_param_name
        self.stream_logs = stream_logs
        self.show_log_tab = show_log_tab
        self.show_output_tab = show_output_tab
        self.show_files_tab = show_files_tab
        self.show_agents_tab = show_agents_tab
        self.show_tasks_tab = show_tasks_tab
        self.max_monitor_time = max_monitor_time
        self.topic_clean_func = topic_clean_func or self._default_topic_clean

        # Config file paths
        self.agents_config_path = os.path.join(self.config_dir, self.agents_config_file)
        self.tasks_config_path = os.path.join(self.config_dir, self.tasks_config_file)

        # Initialize the log queue for thread-safe logging
        self.log_queue = queue.Queue()

        # Create directories if they don't exist
        self._ensure_directories()

        # Update the paths based on actual project structure
        self._update_config_paths()


    def _ensure_directories(self):
        """Create necessary directories if they don't exist."""
        project_root = self.get_project_root()
        os.makedirs(os.path.join(project_root, self.logs_dir), exist_ok=True)
        os.makedirs(os.path.join(project_root, self.output_dir), exist_ok=True)
        os.makedirs(os.path.join(project_root, self.config_dir), exist_ok=True)

    def _update_config_paths(self):
        """
        Update configuration file paths to target the specific location:
        <CrewAI project root>/src/<CrewAI project name>/config
        """
        project_root = self.get_project_root()
        print(f"Project root: {project_root}")

        # Get the project name from the root directory
        project_name = os.path.basename(project_root)
        print(f"Project name: {project_name}")

        # Target the specific location based on the project structure
        target_config_dir = os.path.join(project_root, "src", project_name, "config")
        print(f"Target config directory: {target_config_dir} (exists: {os.path.exists(target_config_dir)})")

        # If the target directory exists, use it
        if os.path.exists(target_config_dir):
            # Set the config_dir relative to project root for consistent reference
            self.config_dir = os.path.join("src", project_name, "config")
            print(f"Using config directory: {self.config_dir}")

            # Update the config file paths
            self.agents_config_path = os.path.join(self.config_dir, self.agents_config_file)
            self.tasks_config_path = os.path.join(self.config_dir, self.tasks_config_file)

            print(f"Agents config path: {self.agents_config_path}")
            print(f"Tasks config path: {self.tasks_config_path}")

            # Check if the actual files exist
            agents_full_path = os.path.join(project_root, self.agents_config_path)
            tasks_full_path = os.path.join(project_root, self.tasks_config_path)

            print(f"Checking agents file: {agents_full_path} (exists: {os.path.exists(agents_full_path)})")
            print(f"Checking tasks file: {tasks_full_path} (exists: {os.path.exists(tasks_full_path)})")
        else:
            # If the target directory doesn't exist, create it
            os.makedirs(target_config_dir, exist_ok=True)
            print(f"Created target config directory: {target_config_dir}")

            # Set the config_dir to the target location
            self.config_dir = os.path.join("src", project_name, "config")
            self.agents_config_path = os.path.join(self.config_dir, self.agents_config_file)
            self.tasks_config_path = os.path.join(self.config_dir, self.tasks_config_file)

            print(f"Will use agents config path: {self.agents_config_path}")
            print(f"Will use tasks config path: {self.tasks_config_path}")

    def get_project_root(self):
        """Find the project root directory from the current directory."""
        return os.getcwd()

    def _default_topic_clean(self, topic):
        """Default function to clean a topic string for use in filenames."""
        clean_topic = re.sub(r'[^\w\s]', '', topic)
        clean_topic = clean_topic.replace(" ", "_")
        return clean_topic[:40] if len(clean_topic) > 40 else clean_topic

    def _initialize_session_state(self):
        """Initialize Streamlit session state variables."""
        if 'process_running' not in st.session_state:
            st.session_state.process_running = False
        if 'current_log_file' not in st.session_state:
            st.session_state.current_log_file = None
        if 'current_output_file' not in st.session_state:
            st.session_state.current_output_file = None
        if 'log_content' not in st.session_state:
            st.session_state.log_content = ""
        if 'last_log_position' not in st.session_state:
            st.session_state.last_log_position = 0
        if 'process' not in st.session_state:
            st.session_state.process = None
        if 'show_completion_notification' not in st.session_state:
            st.session_state.show_completion_notification = False
        if 'needs_final_refresh' not in st.session_state:
            st.session_state.needs_final_refresh = False

        # YAML state variables
        if 'agents_yaml' not in st.session_state:
            st.session_state.agents_yaml = ""
        if 'tasks_yaml' not in st.session_state:
            st.session_state.tasks_yaml = ""

        # Flags to track the state of save operations
        if 'agents_save_clicked' not in st.session_state:
            st.session_state.agents_save_clicked = False
        if 'tasks_save_clicked' not in st.session_state:
            st.session_state.tasks_save_clicked = False

        # Editor content backup for persistence
        if 'agents_yaml_editor_content' not in st.session_state:
            st.session_state.agents_yaml_editor_content = ""
        if 'tasks_yaml_editor_content' not in st.session_state:
            st.session_state.tasks_yaml_editor_content = ""

    def _silence_warnings(self):
        """Suppress unnecessary warnings."""

        # Completely suppress Streamlit warnings by redirecting stderr
        class StreamlitWarningFilter:
            def __init__(self, original_stderr):
                self.original_stderr = original_stderr

            def write(self, text):
                # Filter out Streamlit warning about missing ScriptRunContext
                if "missing ScriptRunContext" not in text:
                    self.original_stderr.write(text)

            def flush(self):
                self.original_stderr.flush()

        # Install the filter
        sys.stderr = StreamlitWarningFilter(sys.stderr)

        # Also try to silence Streamlit logging
        logging.getLogger("streamlit").setLevel(logging.ERROR)
        warnings.filterwarnings("ignore", category=UserWarning)

    def add_log_message(self, message):
        """Add a message to the log queue."""
        self.log_queue.put(("add_log", message))

    def find_main_py(self):
        """Find the main.py script by looking in various locations."""
        # If a specific path was provided, use that
        if self.main_module_path:
            if os.path.exists(self.main_module_path):
                return self.main_module_path, self.get_project_root()

        # Get the project root
        project_root = self.get_project_root()
        self.add_log_message(f"Project root: {project_root}\n")

        # Check if main.py is in the current directory
        main_py_path = os.path.join(project_root, "main.py")
        if os.path.exists(main_py_path):
            return main_py_path, project_root

        # Check if main.py is in src/<project_name>
        for src_dir in ["src", "source", "app"]:
            if os.path.exists(os.path.join(project_root, src_dir)):
                for subdir in os.listdir(os.path.join(project_root, src_dir)):
                    src_path = os.path.join(project_root, src_dir, subdir, "main.py")
                    if os.path.exists(src_path):
                        self.add_log_message(f"Found main.py in {src_dir}/{subdir}\n")
                        return src_path, project_root

        # If not found anywhere, return None
        return None, project_root

    def start_process(self, input_value):
        """Start the CrewAI process with the given input value."""
        # Clear previous state
        st.session_state.process_running = True
        st.session_state.log_content = ""
        st.session_state.last_log_position = 0
        st.session_state.current_log_file = None
        st.session_state.current_output_file = None

        # Store the input value in session state for later use
        st.session_state.input_value = input_value

        # Clean input value for filename
        clean_value = self.topic_clean_func(input_value)

        # Record the timestamp when the process is started for later comparison
        st.session_state.process_start_time = time.time()

        # Add debugging info
        self.add_log_message(f"Starting process for: {input_value}\n")
        self.add_log_message(f"Cleaned value: {clean_value}\n")

        # Find main.py
        main_py_path, work_dir = self.find_main_py()

        if main_py_path:
            self.add_log_message(f"Found main.py at {main_py_path}\n")
            self.add_log_message(f"Working directory will be: {work_dir}\n")
        else:
            # If main.py is not found, try running as a module
            self.add_log_message("Trying alternative approach with Python module import...\n")

            # Check if src/<project> exists and is a Python package
            for src_dir in ["src", "source", "app"]:
                if os.path.exists(os.path.join(work_dir, src_dir, "__init__.py")):
                    for subdir in os.listdir(os.path.join(work_dir, src_dir)):
                        subdir_path = os.path.join(work_dir, src_dir, subdir)
                        if os.path.isdir(subdir_path) and os.path.exists(os.path.join(subdir_path, "__init__.py")):
                            self.add_log_message(f"Found {src_dir}.{subdir} package structure\n")
                            work_dir = work_dir
                            main_py_path = f"{src_dir}.{subdir}.main"
                            break

            if not isinstance(main_py_path, str) or not main_py_path:
                error_msg = "ERROR: main.py not found in any expected location\n"
                self.add_log_message(error_msg)
                st.session_state.process_running = False
                return False

        # Run the process
        try:
            # Create environment variables for the process
            env = os.environ.copy()

            # Set environment variable to prevent duplicate log file creation
            env["CREW_INPUT_VALUE"] = clean_value

            # Prepare command based on whether we have a file path or module path
            if isinstance(main_py_path, str) and main_py_path.endswith(".py"):
                # We're using a file path
                cmd = ["python", main_py_path, self.process_action, self.process_param_name, input_value]
            else:
                # We're using a module path
                cmd = ["python", "-m", main_py_path, self.process_action, self.process_param_name, input_value]

            self.add_log_message(f"Running command: {' '.join(cmd)}\n")

            # Start the process with the modified environment
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                cwd=work_dir,
                env=env
            )

            # Store process in session state
            st.session_state.process = process

            self.add_log_message(f"Process started with PID: {process.pid}\n")

            # Start a thread to monitor the process output
            threading.Thread(
                target=self._monitor_process,
                args=(process, clean_value),
                daemon=True
            ).start()

            return True
        except Exception as e:
            error_traceback = traceback.format_exc()
            error_msg = f"Error starting process: {str(e)}\n{error_traceback}"
            self.add_log_message(f"ERROR: {error_msg}\n")
            st.session_state.process_running = False
            return False

    def _read_process_output(self, process):
        """Read output from a subprocess."""
        try:
            self.add_log_message("Starting to read process output\n")
            for line in iter(process.stdout.readline, ''):
                if line:
                    self.add_log_message(line)
                else:
                    break
            self.add_log_message("Process output ended\n")
        except Exception as e:
            error_traceback = traceback.format_exc()
            self.add_log_message(f"ERROR reading process output: {str(e)}\n{error_traceback}\n")

    def _monitor_log_file(self, log_file, process_pid=None):
        """Monitor a log file for changes using polling with improved reliability."""
        print(f"Starting to monitor log file: {log_file}")

        # Add creation time information for debugging
        create_time = os.path.getctime(log_file)
        modified_time = os.path.getmtime(log_file)

        self.add_log_message(f"Starting to monitor log file: {log_file}\n")
        self.add_log_message(
            f"File creation time: {datetime.fromtimestamp(create_time).strftime('%Y-%m-%d %H:%M:%S.%f')}\n")
        self.add_log_message(
            f"File last modified: {datetime.fromtimestamp(modified_time).strftime('%Y-%m-%d %H:%M:%S.%f')}\n")

        if not os.path.exists(log_file):
            error_msg = f"ERROR: Log file does not exist: {log_file}"
            print(error_msg)
            self.add_log_message(f"{error_msg}\n")
            return

        # Initial file size and modification time
        try:
            last_size = os.path.getsize(log_file)
            last_modified = os.path.getmtime(log_file)
        except Exception as e:
            error_msg = f"ERROR: Could not get file stats: {str(e)}"
            print(error_msg)
            self.add_log_message(f"{error_msg}\n")
            return

        self.add_log_message(f"Initial file size: {last_size} bytes\n")

        # Set monitoring parameters
        start_time = time.time()
        max_monitor_time = 3600  # 1 hour
        check_interval = 0.2
        last_heartbeat = time.time()
        heartbeat_interval = 10  # Send heartbeat every 10 seconds
        last_activity = time.time()
        inactivity_threshold = 15  # Wait 15 seconds after process ends before stopping monitoring

        try:
            while time.time() - start_time < max_monitor_time:
                # Send periodic heartbeat
                if time.time() - last_heartbeat > heartbeat_interval:
                    self.add_log_message(
                        f"Still monitoring log file... (runtime: {int(time.time() - start_time)} seconds)\n")
                    last_heartbeat = time.time()

                # Check if file still exists
                if not os.path.exists(log_file):
                    self.add_log_message(f"Log file no longer exists: {log_file}\n")
                    break

                # Check for file changes
                try:
                    current_size = os.path.getsize(log_file)
                    current_modified = os.path.getmtime(log_file)
                except Exception as e:
                    error_msg = f"ERROR: Could not get current file stats: {str(e)}"
                    print(error_msg)
                    self.add_log_message(f"{error_msg}\n")
                    break

                # If file has grown or been modified
                if current_size > last_size or current_modified > last_modified:
                    last_activity = time.time()  # Update last activity time

                    try:
                        with open(log_file, 'r') as f:
                            # Seek to where we were before
                            f.seek(last_size)

                            # Read the new content
                            new_content = f.read()

                            if new_content:
                                # Send the new content line by line
                                for line in new_content.splitlines(True):  # keepends=True
                                    self.add_log_message(line)

                        # Update our position trackers
                        last_size = current_size
                        last_modified = current_modified
                        print(f"Read {current_size - last_size} new bytes from log file")

                    except Exception as e:
                        error_msg = f"ERROR reading log file: {str(e)}"
                        print(error_msg)
                        self.add_log_message(f"{error_msg}\n")
                        break

                # Check if process has exited
                process_ended = False
                if process_pid:
                    try:
                        # Try using psutil first
                        process_ended = not psutil.pid_exists(process_pid)
                    except:
                        # Fallback: check if process.poll() is not None
                        if hasattr(st.session_state, 'process') and st.session_state.process:
                            process_ended = st.session_state.process.poll() is not None

                    if process_ended and time.time() - last_activity < 2:  # Only log this once
                        self.add_log_message(f"Process with PID {process_pid} no longer exists\n")
                        # Signal that the process has completed
                        self.log_queue.put(("set_process_running", False))

                # Only stop monitoring if process has ended AND we've had no activity for a while
                if process_ended and time.time() - last_activity > inactivity_threshold:
                    # Double-check for any final content
                    try:
                        final_current_size = os.path.getsize(log_file)
                        if final_current_size > last_size:
                            with open(log_file, 'r') as f:
                                f.seek(last_size)
                                final_content = f.read()
                                if final_content:
                                    self.add_log_message("Reading final log content...\n")
                                    for line in final_content.splitlines(True):
                                        self.add_log_message(line)
                            last_size = final_current_size
                    except Exception as e:
                        print(f"Error reading final content: {str(e)}")

                    self.add_log_message(
                        f"Process has ended and no activity for {inactivity_threshold} seconds, stopping log monitoring\n")
                    break

                # Wait before checking again
                time.sleep(check_interval)

            # Report monitoring end
            if time.time() - start_time >= max_monitor_time:
                self.add_log_message(f"Maximum monitoring time reached for {log_file}\n")
            else:
                self.add_log_message(f"Finished monitoring log file: {log_file}\n")

        except Exception as e:
            error_traceback = traceback.format_exc()
            error_msg = f"ERROR in log monitor: {str(e)}\n{error_traceback}"
            print(error_msg)
            self.add_log_message(f"{error_msg}\n")

    def _monitor_process(self, process, clean_value):
        """Monitor the entire process execution."""
        try:
            self.add_log_message("Monitor process thread started\n")

            # Get the process PID to pass to the log monitoring function
            process_pid = process.pid

            # Start a thread to read process output
            stdout_thread = threading.Thread(
                target=self._read_process_output,
                args=(process,),
                daemon=True
            )
            stdout_thread.start()

            # Create a timestamp of when the process started
            process_start_time = time.time()
            self.add_log_message(
                f"Process start time: {datetime.fromtimestamp(process_start_time).strftime('%Y-%m-%d %H:%M:%S.%f')}\n")

            # Store the process start time in session state for later file comparisons
            st.session_state.process_start_time = process_start_time

            # Wait for the log file to be created (with timeout)
            max_wait = 90  # seconds
            start_time = time.time()
            log_file_found = False
            log_monitoring_threads = []

            while time.time() - start_time < max_wait:
                # Find the most recent log file for this input value
                log_pattern = f"{self.logs_dir}/{clean_value}_*.log"
                log_files = glob.glob(log_pattern)

                # Filter files by creation time - only look at files created after process started
                # Use a small buffer to account for possible clock differences
                new_log_files = [f for f in log_files if os.path.getctime(f) > (process_start_time - 1)]

                if new_log_files:
                    # Sort by creation time (newest first)
                    new_log_files.sort(key=os.path.getmtime, reverse=True)

                    # Check all recent log files, not just the newest one
                    for idx, current_log_file in enumerate(new_log_files[:3]):  # Consider up to 3 newest files
                        self.add_log_message(
                            f"Found new log file {idx + 1} created after process start: {current_log_file}\n")

                        # Verify this is truly a new file by checking creation time
                        create_time = os.path.getctime(current_log_file)
                        self.add_log_message(
                            f"Log file creation time: {datetime.fromtimestamp(create_time).strftime('%Y-%m-%d %H:%M:%S.%f')}\n")

                        # Start monitoring this log file
                        if idx == 0:  # Only set the primary log file for the first (newest) one
                            # Send the log file path to the main thread
                            self.log_queue.put(("set_log_file", current_log_file))

                        # Start monitoring the log file in a separate thread
                        log_thread = threading.Thread(
                            target=self._monitor_log_file,
                            args=(current_log_file, process_pid),
                            daemon=True
                        )
                        log_thread.start()
                        log_monitoring_threads.append(log_thread)

                    log_file_found = True
                    break

                # Log the search attempt every 5 sec
                elapsed = time.time() - start_time
                if elapsed % 5 < 0.1:  # Log approx every 5 seconds
                    self.add_log_message(
                        f"Searching for new log file... (pattern: {log_pattern}), found {len(log_files)} files but none created after process start.\n")

                # Wait before trying again
                time.sleep(0.5)

            if not log_file_found:
                self.add_log_message(f"WARNING: No log file found after {max_wait} seconds\n")

            # Wait for process to complete (with timeout)
            completed_normally = False
            try:
                # Wait up to the configured timeout
                return_code = process.wait(timeout=self.max_monitor_time)
                self.add_log_message(f"Process completed with return code: {return_code}\n")
                completed_normally = True
            except subprocess.TimeoutExpired:
                self.add_log_message(
                    f"WARNING: Process timed out after {self.max_monitor_time} seconds, killing process\n")
                process.kill()
                return_code = process.wait()
                self.add_log_message(f"Process killed, return code: {return_code}\n")
            except KeyboardInterrupt:
                # Handle keyboard interrupts explicitly
                self.add_log_message("Process terminated by user (KeyboardInterrupt)\n")
                try:
                    process.kill()
                    return_code = process.wait(timeout=5)
                    self.add_log_message(f"Process killed, return code: {return_code}\n")
                except Exception as e:
                    self.add_log_message(f"Error while killing process: {str(e)}\n")
            except Exception as e:
                # Handle other exceptions during process monitoring
                self.add_log_message(f"Exception while monitoring process: {str(e)}\n")
                try:
                    # Check if process is still running
                    if process.poll() is None:
                        process.kill()
                        self.add_log_message("Process killed after exception\n")
                except Exception as inner_e:
                    self.add_log_message(f"Additional error killing process: {str(inner_e)}\n")

            # Always check for the output file at the end
            time.sleep(3)  # Allow time for file creation to complete

            # Find the output file (should be created at the end)
            output_pattern = f"{self.output_dir}/{clean_value}_*.{self.output_file_extension}"
            output_files = glob.glob(output_pattern)

            if output_files:
                # Sort by creation time (newest first)
                output_files.sort(key=os.path.getmtime, reverse=True)
                current_output_file = output_files[0]
                self.add_log_message(f"Found output file: {current_output_file}\n")

                # Send the output file path to the main thread
                self.log_queue.put(("set_output_file", current_output_file))
            else:
                self.add_log_message(f"WARNING: No output file found matching pattern: {output_pattern}\n")

            # Wait a bit longer for log writing to complete
            time.sleep(2)

        except Exception as e:
            error_traceback = traceback.format_exc()
            self.add_log_message(f"ERROR in monitor_process: {str(e)}\n{error_traceback}\n")
        finally:
            # Signal that the process has completed - do this regardless of how we exit
            self.log_queue.put(("set_process_running", False))
            self.add_log_message("Process monitoring completed\n")

    def _ensure_refresh(self):
        """Check if we need to refresh the UI and do so if needed."""
        if st.session_state.process_running:
            # Verify process is still running
            previous_state = st.session_state.process_running
            st.session_state.process_running = self._verify_process_running()

            # If state just changed to not running, set needs_final_refresh
            if previous_state and not st.session_state.process_running:
                st.session_state.needs_final_refresh = True
                print("Process detected as completed in ensure_refresh()")

            # Process new messages from queue
            self._update_log_display()

            # Regular checks and updates
            current_time = time.time()
            if not hasattr(st.session_state, 'last_verify_check'):
                st.session_state.last_verify_check = current_time

            if current_time - st.session_state.last_verify_check > 3:
                st.session_state.last_verify_check = current_time
                self._verify_log_file()

            # Periodically check if we need to reload the full log
            if not hasattr(st.session_state, 'last_full_log_check'):
                st.session_state.last_full_log_check = current_time

            if current_time - st.session_state.last_full_log_check > 7:
                st.session_state.last_full_log_check = current_time

                if st.session_state.current_log_file and os.path.exists(st.session_state.current_log_file):
                    file_size = os.path.getsize(st.session_state.current_log_file)
                    content_size = len(st.session_state.log_content.encode('utf-8'))

                    if file_size > content_size * 1.2:
                        print(f"Log file size ({file_size}) larger than content ({content_size}), reloading...")
                        st.session_state.log_content = self._read_full_log_file(st.session_state.current_log_file)

            # Schedule next refresh
            time.sleep(0.5)
            st.rerun()
        elif hasattr(st.session_state, 'needs_final_refresh') and st.session_state.needs_final_refresh:
            # Handle the case where process just completed
            st.session_state.needs_final_refresh = False
            print("Performing final refresh after process completion")

            # Make one last check for output file
            if 'input_value' in st.session_state:
                clean_value = self.topic_clean_func(st.session_state.input_value)

                # Look for output file one last time
                output_pattern = f"{self.output_dir}/{clean_value}_*.{self.output_file_extension}"
                output_files = glob.glob(output_pattern)
                if output_files and (not st.session_state.current_output_file or not os.path.exists(
                        st.session_state.current_output_file)):
                    output_files.sort(key=os.path.getmtime, reverse=True)
                    st.session_state.current_output_file = output_files[0]
                    print(f"Final refresh found output file: {output_files[0]}")

            time.sleep(0.5)
            st.rerun()

    def _verify_process_running(self):
        """Verify if the process is still running."""
        if st.session_state.process_running and hasattr(st.session_state, 'process'):
            process = st.session_state.process

            # Multiple ways to check if process has exited
            process_ended = False

            # Method 1: Check process.poll()
            if process and process.poll() is not None:
                return_code = process.poll()
                self.add_log_message(f"Detected process completion via poll(), return code: {return_code}\n")
                process_ended = True

            # Method 2: Try psutil
            if not process_ended and process:
                try:
                    process_ended = not psutil.pid_exists(process.pid)
                    if process_ended:
                        self.add_log_message(
                            f"Detected process completion via psutil, PID {process.pid} no longer exists\n")
                except Exception as e:
                    print(f"Error checking process with psutil: {e}")

            # If process has ended by any method, signal completion
            if process_ended:
                self.log_queue.put(("set_process_running", False))
                return False

        return st.session_state.process_running

    def _verify_log_file(self):
        """Verify that we're monitoring the correct (newest) log file."""
        if not st.session_state.process_running or not hasattr(st.session_state, 'input_value'):
            return

        # Clean input value for filename matching
        clean_value = self.topic_clean_func(st.session_state.input_value)

        # Get process start time if available
        start_time = getattr(st.session_state, 'process_start_time', None)

        # Find the newest log file
        log_pattern = f"{self.logs_dir}/{clean_value}_*.log"
        log_files = glob.glob(log_pattern)

        if log_files:
            # Filter by creation time if start time is available
            if start_time is not None:
                new_log_files = [f for f in log_files if os.path.getctime(f) > (start_time - 1)]
                if new_log_files:
                    log_files = new_log_files

            # Sort by modification time (newest first)
            log_files.sort(key=os.path.getmtime, reverse=True)
            newest_log = log_files[0]

            current_log_mtime = 0
            if st.session_state.current_log_file and os.path.exists(st.session_state.current_log_file):
                current_log_mtime = os.path.getmtime(st.session_state.current_log_file)

            newest_log_mtime = os.path.getmtime(newest_log)

            # Switch if we found a newer file or if current file doesn't exist
            if not st.session_state.current_log_file or \
                    newest_log != st.session_state.current_log_file or \
                    newest_log_mtime > current_log_mtime:

                # We found a newer log file than what we're currently monitoring
                self.add_log_message(f"Switching to newer log file: {newest_log}\n")

                # Update the current log file
                st.session_state.current_log_file = newest_log

                # Read the new log file content
                try:
                    st.session_state.log_content = self._read_full_log_file(newest_log)

                    # Start a new monitoring thread for this file if process is still running
                    if hasattr(st.session_state, 'process') and st.session_state.process:
                        pid = st.session_state.process.pid

                        # Start monitoring the log file
                        log_thread = threading.Thread(
                            target=self._monitor_log_file,
                            args=(newest_log, pid),
                            daemon=True
                        )
                        log_thread.start()

                        self.add_log_message(f"Started monitoring new log file: {newest_log}\n")

                except Exception as e:
                    self.add_log_message(f"Error switching to new log file: {str(e)}\n")

    def _read_full_log_file(self, log_file_path):
        """Read the entire log file content with improved error handling."""
        if not log_file_path or not os.path.exists(log_file_path):
            return "No log file available or file not found."

        try:
            # Try with explicit encoding
            with open(log_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"Successfully read {len(content)} chars from log file")
                return content
        except UnicodeDecodeError:
            # Try with a different encoding if UTF-8 fails
            try:
                with open(log_file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
                    print(f"Successfully read {len(content)} chars from log file (using latin-1 encoding)")
                    return content
            except Exception as e:
                return f"Error reading log file with alternate encoding: {e}"
        except Exception as e:
            return f"Error reading log file: {e}"

    def _get_output_content(self):
        """Read the content of the current output file."""
        if st.session_state.current_output_file and os.path.exists(st.session_state.current_output_file):
            try:
                with open(st.session_state.current_output_file, 'r') as f:
                    content = f.read()
                    return content
            except Exception as e:
                return f"Error reading output file: {e}"

        # Check if we can find any output files for this input value
        if 'input_value' in st.session_state:
            clean_value = self.topic_clean_func(st.session_state.input_value)

            # Try to find the most recent output file matching the pattern
            output_pattern = f"{self.output_dir}/{clean_value}_*.{self.output_file_extension}"
            output_files = glob.glob(output_pattern)

            if output_files:
                # Sort by creation time (newest first)
                output_files.sort(key=os.path.getmtime, reverse=True)
                newest_file = output_files[0]
                st.session_state.current_output_file = newest_file

                try:
                    with open(newest_file, 'r') as f:
                        content = f.read()
                        return content
                except Exception as e:
                    return f"Error reading output file: {e}"

        return f"No output file available yet. The {self.output_file_extension.upper()} file will appear here when it's ready."

    def _get_download_link(self, file_path, link_text):
        """Generate a download link for a file."""
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            b64 = base64.b64encode(data).decode()
            filename = os.path.basename(file_path)
            mime_type = "text/markdown" if file_path.endswith('.md') else "text/plain"
            href = f'<a href="data:{mime_type};base64,{b64}" download="{filename}">{link_text}</a>'
            return href
        except Exception as e:
            return f"Error creating download link: {e}"

    def _update_log_display(self):
        """Update the log display with new content from the queue."""
        # Process all items in the queue
        new_content = []
        processed_count = 0
        needs_final_refresh = False

        try:
            # Process everything currently in the queue (non-blocking)
            while True:
                try:
                    message = self.log_queue.get(block=False)
                    processed_count += 1

                    # Handle different message types
                    if isinstance(message, tuple) and len(message) == 2:
                        message_type, message_content = message

                        if message_type == "add_log":
                            new_content.append(message_content)
                        elif message_type == "set_log_file":
                            st.session_state.current_log_file = message_content
                            print(f"Setting current_log_file to: {message_content}")

                            # When a new log file is set, read it completely
                            try:
                                st.session_state.log_content = self._read_full_log_file(message_content)
                                print(f"Loaded complete log file: {len(st.session_state.log_content)} chars")
                            except Exception as e:
                                print(f"Error loading complete log file: {e}")
                        elif message_type == "set_output_file":
                            st.session_state.current_output_file = message_content
                            print(f"Setting current_output_file to: {message_content}")
                        elif message_type == "set_process_running":
                            old_state = st.session_state.process_running
                            st.session_state.process_running = message_content
                            print(f"Setting process_running to: {message_content}")

                            # If transitioning from running to not running, set completion notification
                            if old_state and not message_content:
                                self._on_process_complete()
                                needs_final_refresh = True

                    self.log_queue.task_done()
                except queue.Empty:
                    break
        except Exception as e:
            print(f"Error processing log queue: {str(e)}")

        # Update the log content with new lines
        if new_content:
            content_to_add = "".join(new_content)
            st.session_state.log_content += content_to_add

            # Double-check if there's a file size mismatch and reload if needed
            if st.session_state.current_log_file and os.path.exists(st.session_state.current_log_file):
                file_size = os.path.getsize(st.session_state.current_log_file)
                content_size = len(st.session_state.log_content.encode('utf-8'))

                # If the file is significantly larger, just reload it entirely
                if file_size > content_size * 1.5:
                    print(f"Major log size mismatch detected: file={file_size}, content={content_size}")
                    try:
                        st.session_state.log_content = self._read_full_log_file(st.session_state.current_log_file)
                        print(f"Force-reloaded log file: {len(st.session_state.log_content)} chars")
                    except Exception as e:
                        print(f"Error force-reloading log file: {e}")

        return processed_count > 0

    def _on_process_complete(self):
        """Run final verification steps when a process completes."""
        # Set start time for this function
        start_time = time.time()
        max_search_time = 5  # seconds

        # Find output file if it wasn't found during the process
        if not st.session_state.current_output_file and 'input_value' in st.session_state:
            clean_value = self.topic_clean_func(st.session_state.input_value)

            # Keep trying until we find a file or timeout
            while time.time() - start_time < max_search_time:
                # Try to find the most recent output file matching the pattern
                output_pattern = f"{self.output_dir}/{clean_value}_*.{self.output_file_extension}"
                output_files = glob.glob(output_pattern)

                if output_files:
                    # Sort by creation time (newest first)
                    output_files.sort(key=os.path.getmtime, reverse=True)
                    st.session_state.current_output_file = output_files[0]
                    self.add_log_message(f"Found output file after process completion: {output_files[0]}\n")
                    break

                # Wait briefly before checking again
                time.sleep(0.5)

        # Set flag to show notification in next UI refresh
        st.session_state.show_completion_notification = True

    # YAML Configuration File Handling

    def _load_yaml_file(self, file_path):
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

    def _save_yaml_file(self, file_path, content):
        """Save content to a YAML file with improved debugging and error handling."""
        print(f"Try to save YAML file: {file_path}")
        try:
            # Print debug info
            print(f"Attempting to save YAML to: {file_path}")

            # Get absolute file path if relative
            project_root = self.get_project_root()
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

    def _load_yaml_to_string(self, file_path):
        """Load a YAML file and return its content as a string."""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as file:
                    return file.read(), None
            else:
                return "", f"File not found: {file_path}"
        except Exception as e:
            return "", f"Error loading YAML file: {str(e)}"

    def _validate_yaml(self, yaml_str):
        """Validate YAML string to ensure it's properly formatted."""
        try:
            yaml.safe_load(yaml_str)
            return True, None
        except Exception as e:
            return False, f"Invalid YAML: {str(e)}"

    def _create_agents_tab(self, tab):
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
            agents_yaml, error = self._load_yaml_to_string(self.agents_config_path)
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
        tab.caption(f"Configuration file: {self.agents_config_path}")

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
                is_valid, error = self._validate_yaml(content)

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
                success, error = self._save_yaml_file(self.agents_config_path, st.session_state.agents_editor_content)
                if success:
                    st.session_state.agents_yaml = st.session_state.agents_editor_content
                    tab.success(f"Configuration saved to {self.agents_config_path}")
                else:
                    tab.error(error)
                    print(f"Error saving agents config: {error}")

        # Reload button
        with col3:
            if tab.button("Reload from File", use_container_width=True, key="reload_agents_btn"):
                agents_yaml, error = self._load_yaml_to_string(self.agents_config_path)
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

    def _create_tasks_tab(self, tab):
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
            tasks_yaml, error = self._load_yaml_to_string(self.tasks_config_path)
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
        tab.caption(f"Configuration file: {self.tasks_config_path}")

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
                is_valid, error = self._validate_yaml(content)

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
                success, error = self._save_yaml_file(self.tasks_config_path, st.session_state.tasks_editor_content)
                if success:
                    st.session_state.tasks_yaml = st.session_state.tasks_editor_content
                    tab.success(f"Configuration saved to {self.tasks_config_path}")
                else:
                    tab.error(error)
                    print(f"Error saving tasks config: {error}")

        # Reload button
        with col3:
            if tab.button("Reload from File", use_container_width=True, key="reload_tasks_btn"):
                tasks_yaml, error = self._load_yaml_to_string(self.tasks_config_path)
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

    def _create_output_tab(self, tab):
        """Create the output preview tab."""
        # Add a refresh button at the top of this tab
        if tab.button("Refresh Output View", type="primary", key="refresh_output_view_btn"):
            # Clear the output content cache to force a reload
            if 'current_output_file' in st.session_state:
                # We don't delete the value, just refresh the view
                st.rerun()

        # Get output content
        output_content = self._get_output_content()

        if st.session_state.current_output_file and os.path.exists(st.session_state.current_output_file):
            # Add a download button for the current output
            col1, col2 = tab.columns([3, 1])
            with col1:
                tab.subheader("Generated Output")
                # Show the filename
                tab.caption(f"File: {os.path.basename(st.session_state.current_output_file)}")
            with col2:
                tab.download_button(
                    label="Download Output",
                    data=output_content,
                    file_name=os.path.basename(st.session_state.current_output_file),
                    mime=f"text/{self.output_file_extension}",
                    use_container_width=True,
                    key="output_file_btn"
                )

            # Display the content
            tab.markdown(output_content)

            # Also add a text area for copying
            with tab.expander("View as raw text (for copying)"):
                tab.text_area("Raw Text", output_content, height=300)

        else:
            # Show waiting message
            tab.markdown("""
            <style>
            .waiting-container {
                text-align: center;
                padding: 5rem 1rem;
                background-color: #F9FAFB;
                border-radius: 0.5rem;
                border: 1px dashed #D1D5DB;
                margin: 2rem 0;
            }
            .waiting-icon {
                font-size: 4rem;
                margin-bottom: 1rem;
                color: #9CA3AF;
            }
            .waiting-text {
                font-size: 1.5rem;
                color: #4B5563;
            }
            </style>
            <div class="waiting-container">
                <div class="waiting-icon">📝</div>
                <div class="waiting-text">Your output will appear here when it's ready</div>
                <p>Start the generation process by entering input and clicking the "Generate" button</p>
            </div>
            """, unsafe_allow_html=True)

    def _create_log_tab(self, tab):
        """Create the log tab."""
        # Add refresh button
        if tab.button("🔄 Force Refresh Logs", use_container_width=True, type="primary", key="force_refresh_logs_btn"):
            if st.session_state.current_log_file and os.path.exists(st.session_state.current_log_file):
                try:
                    st.session_state.log_content = self._read_full_log_file(st.session_state.current_log_file)
                    tab.success(f"Refreshed logs from {os.path.basename(st.session_state.current_log_file)}")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    tab.error(f"Error refreshing logs: {e}")

        # Debug section
        with tab.expander("Debug Information", expanded=False):
            if st.session_state.current_log_file:
                tab.write(f"Current log file: {st.session_state.current_log_file}")

                if os.path.exists(st.session_state.current_log_file):
                    create_time = os.path.getctime(st.session_state.current_log_file)
                    tab.write(f"Creation time: {datetime.fromtimestamp(create_time).strftime('%Y-%m-%d %H:%M:%S.%f')}")

                    if hasattr(st.session_state, 'process_start_time'):
                        tab.write(
                            f"Process start time: {datetime.fromtimestamp(st.session_state.process_start_time).strftime('%Y-%m-%d %H:%M:%S.%f')}")
                        tab.write(
                            f"File created after process start: {create_time > st.session_state.process_start_time}")
                else:
                    tab.write("Log file does not exist on disk")
            else:
                tab.write("No log file selected")

        # Add log controls
        col1, col2 = tab.columns([1, 1])
        with col1:
            if tab.button("Clear Logs", use_container_width=True, key="clear_logs_btn"):
                st.session_state.log_content = ""
                st.rerun()

        with col2:
            if tab.button("Load Full Log", use_container_width=True, key="load_logs_btn"):
                if st.session_state.current_log_file and os.path.exists(st.session_state.current_log_file):
                    try:
                        st.session_state.log_content = self._read_full_log_file(st.session_state.current_log_file)
                        st.rerun()
                    except Exception as e:
                        tab.error(f"Error loading log file: {e}")

        # Show log file status
        if st.session_state.current_log_file:
            if os.path.exists(st.session_state.current_log_file):
                log_size = os.path.getsize(st.session_state.current_log_file) / 1024  # KB
                last_modified = datetime.fromtimestamp(os.path.getmtime(st.session_state.current_log_file))
                time_str = last_modified.strftime("%H:%M:%S")
                tab.info(
                    f"Log file: {os.path.basename(st.session_state.current_log_file)} ({log_size:.1f} KB, last modified: {time_str})")
            else:
                tab.warning("Selected log file not found on disk")
        else:
            tab.info("No log file selected")

        # Custom styling for the log display
        tab.markdown("""
        <style>
        .log-container {
            background-color: #1E1E1E;
            color: #DCDCDC;
            font-family: monospace;
            padding: 1rem;
            border-radius: 0.5rem;
            height: 500px;
            overflow-y: auto;
            white-space: pre-wrap;
            line-height: 1.5;
        }
        </style>
        """, unsafe_allow_html=True)

        # Format the log content with color highlights
        formatted_log = st.session_state.log_content
        formatted_log = formatted_log.replace("ERROR", "<span style='color: #FF5252;'>ERROR</span>")
        formatted_log = formatted_log.replace("WARNING", "<span style='color: #FFC107;'>WARNING</span>")
        formatted_log = formatted_log.replace("INFO", "<span style='color: #4FC3F7;'>INFO</span>")
        formatted_log = formatted_log.replace("DEBUG", "<span style='color: #9CCC65;'>DEBUG</span>")

        # Add container header
        tab.markdown(f"<p>Log content ({len(st.session_state.log_content)} chars):</p>", unsafe_allow_html=True)

        # Add auto-scroll feature
        auto_scroll = tab.checkbox("Auto-scroll to newest logs", value=True)

        # Display log content
        log_container = tab.container()
        with log_container:
            tab.markdown(f"<div class='log-container' id='log-container'>{formatted_log}</div>", unsafe_allow_html=True)

        # Add JavaScript for auto-scrolling if enabled
        if auto_scroll:
            tab.markdown("""
            <script>
                // Auto-scroll the log container to the bottom
                const logContainer = document.querySelector('.log-container');
                if (logContainer) {
                    logContainer.scrollTop = logContainer.scrollHeight;
                }
            </script>
            """, unsafe_allow_html=True)

    def _create_files_tab(self, tab):
        """Create the files tab."""
        # Add custom styling for the files tab
        tab.markdown("""
        <style>
        .file-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem;
            margin-bottom: 0.5rem;
            background-color: white;
            border-radius: 0.25rem;
            border: 1px solid #E5E7EB;
        }
        .file-name {
            font-weight: 500;
        }
        .file-time {
            color: #6B7280;
            font-size: 0.875rem;
        }
        </style>
        """, unsafe_allow_html=True)

        col1, col2 = tab.columns(2)

        # Log files column
        with col1:
            tab.subheader("📋 Log Files")
            log_files = glob.glob(os.path.join(self.logs_dir, "*.log"))
            log_files.sort(key=os.path.getmtime, reverse=True)

            with tab.container():
                tab.markdown("<div class='file-container'>", unsafe_allow_html=True)

                if log_files:
                    for log_file in log_files[:20]:  # Show the 20 most recent
                        filename = os.path.basename(log_file)
                        # Get file creation time
                        create_time = datetime.fromtimestamp(os.path.getmtime(log_file))
                        time_str = create_time.strftime("%Y-%m-%d %H:%M:%S")
                        file_size = os.path.getsize(log_file) / 1024  # Size in KB

                        tab.markdown(
                            f"""
                            <div class='file-row'>
                                <div>
                                    <div class='file-name'>{filename}</div>
                                    <div class='file-time'>{time_str} ({file_size:.1f} KB)</div>
                                </div>
                                <div>
                                    {self._get_download_link(log_file, '⬇️ Download')}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                else:
                    tab.markdown(
                        """
                        <div style='text-align: center; padding: 2rem;'>
                            <p>No log files found.</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                tab.markdown("</div>", unsafe_allow_html=True)

        # Output files column
        with col2:
            tab.subheader(f"📄 Output Files")
            output_files = glob.glob(os.path.join(self.output_dir, f"*.{self.output_file_extension}"))
            output_files.sort(key=os.path.getmtime, reverse=True)

            with tab.container():
                tab.markdown("<div class='file-container'>", unsafe_allow_html=True)

                if output_files:
                    for output_file in output_files[:20]:  # Show the 20 most recent
                        filename = os.path.basename(output_file)
                        # Get file creation time
                        create_time = datetime.fromtimestamp(os.path.getmtime(output_file))
                        time_str = create_time.strftime("%Y-%m-%d %H:%M:%S")

                        # Extract input value from filename (if it follows our pattern)
                        clean_value_match = re.match(r'(.+)_\d{8}_\d{6}\.' + self.output_file_extension, filename)
                        display_name = clean_value_match.group(1).replace('_',
                                                                          ' ').title() if clean_value_match else filename

                        # Get file size
                        file_size = os.path.getsize(output_file) / 1024  # Size in KB

                        tab.markdown(
                            f"""
                            <div class='file-row'>
                                <div>
                                    <div class='file-name'>{display_name}</div>
                                    <div class='file-time'>{time_str} ({file_size:.1f} KB)</div>
                                </div>
                                <div>
                                    {self._get_download_link(output_file, '⬇️ Download')}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                else:
                    tab.markdown(
                        """
                        <div style='text-align: center; padding: 2rem;'>
                            <p>No output files found.</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                tab.markdown("</div>", unsafe_allow_html=True)

    def run(self):
        """
        Run the Streamlit UI
        """
        # Set page config to wide mode
        st.set_page_config(
            page_title=self.page_title,
            page_icon=self.page_icon,
            layout="wide",
            initial_sidebar_state="auto"
        )

        # Initialize session state for menu selection if it doesn't exist
        if 'menu_selection' not in st.session_state:
            st.session_state.menu_selection = "Run Crew"

        # Create a sidebar menu
        st.sidebar.title("Navigation")

        # Add CSS styling for the menu
        st.sidebar.markdown("""
        <style>
        .sidebar-menu {
            padding: 10px;
            background-color: #f0f2f6;
            border-radius: 5px;
            margin-bottom: 10px;
            font-weight: bold;
            text-align: center;
            cursor: pointer;
        }
        .sidebar-menu:hover {
            background-color: #e0e2e6;
        }
        .selected {
            background-color: #4e8cff;
            color: white;
        }
        </style>
        """, unsafe_allow_html=True)

        # Menu items
        menu_items = ["Run Crew", "Config", "Ollama Interface", "Dashboard"]

        # Generate menu buttons
        for item in menu_items:
            selected_class = "selected" if st.session_state.menu_selection == item else ""
            if st.sidebar.button(item, key=f"menu_{item}",
                                 use_container_width=True,
                                 type="primary" if st.session_state.menu_selection == item else "secondary"):
                st.session_state.menu_selection = item
                st.rerun()

        # Display the selected page content
        if st.session_state.menu_selection == "Run Crew":
            self._display_run_crew_page()
        elif st.session_state.menu_selection == "Dashboard":
            self._display_dashboard_page()
        elif st.session_state.menu_selection == "Config":
            self._display_config_page()
        elif st.session_state.menu_selection == "Ollama Interface":  # Add this condition
            self._display_ollama_interface_page()

    def _display_ollama_interface_page(self):
        """Display the Ollama LLM interface page."""
        try:
            # Import the ollama_interface module from the pages directory
            from .pages import ollama_interface

            # Call the run function
            ollama_interface.run()
        except ImportError as e:
            st.error(f"Error loading Ollama interface: {str(e)}")
            st.info("Make sure the ollama_interface.py file exists in the pages directory.")
        except Exception as e:
            st.error(f"Error displaying Ollama interface: {str(e)}")

    def _display_run_crew_page(self):
        """
        Display the Run Crew page with all the original functionality
        """
        # Add the header
        st.title(f"{self.project_name} - Run Crew")

        # Initialize the session state
        self._initialize_session_state()

        # Silence specific Streamlit warnings
        self._silence_warnings()

        col1, col2 = st.columns([3, 1])

        # Add the input field to the first column
        with col1:
            if self.input_field_label:
                user_input = st.text_area(
                    label=self.input_field_label,
                    value=self.input_field_default,
                    placeholder=self.input_field_placeholder,
                    help=self.input_field_help,
                    key="user_input"
                )
        with col2:
            # Create a container to vertically center the button
            container = st.container()
            # Add some vertical space to roughly align with the text area
            st.write("")
            st.write("")
            run_button = st.button("Run", type="primary", use_container_width=True)

            # Handle the button click
            if run_button:
                if "process_running" in st.session_state and st.session_state.process_running:
                    st.warning("A process is already running. Please wait for it to complete.")
                else:
                    # Get the user input value
                    topic = st.session_state.user_input if "user_input" in st.session_state else ""

                    # Clean the topic if a function is provided
                    if self.topic_clean_func and topic:
                        topic = self.topic_clean_func(topic)

                    # Start the process
                    self.start_process(input_value=topic)

        # Add a separator between input/button and tabs
        st.markdown("---")

        # Create tabs
        tab_names = []

        if self.show_output_tab:
            tab_names.append("Log")

        if self.show_log_tab:
            tab_names.append("Output")

        if self.show_files_tab:
            tab_names.append("Files")

        # Only create tabs if we have more than one
        if len(tab_names) > 1:
            tabs = st.tabs(tab_names)
        else:
            # For a single tab, we'll just use the main area
            tabs = [st]

        # Initialize tab index counter
        tab_idx = 0

        # Create the tabs content
        if self.show_output_tab:
            with tabs[tab_idx]:
                self._create_log_tab(tabs[tab_idx])
            tab_idx += 1

        if self.show_log_tab:
            with tabs[tab_idx]:
                self._create_output_tab(tabs[tab_idx])
            tab_idx += 1

        if self.show_files_tab:
            with tabs[tab_idx]:
                self._create_files_tab(tabs[tab_idx])

        # Check and update the process status
        self._ensure_refresh()

    def _display_config_page(self):
        """
        Display the Config page with Agents and Tasks tabs
        """
        # Add the header
        st.title(f"{self.project_name} - Configuration")

        # Initialize the session state
        self._initialize_session_state()

        # Create tabs for Agents and Tasks
        tab_names = []

        if self.show_agents_tab:
            tab_names.append("Agents")

        if self.show_tasks_tab:
            tab_names.append("Tasks")

        # Only create tabs if we have at least one
        if len(tab_names) > 0:
            tabs = st.tabs(tab_names)

            # Initialize tab index counter
            tab_idx = 0

            # Create the tabs content
            if self.show_agents_tab:
                self._create_agents_tab(tabs[tab_idx])
                tab_idx += 1

            if self.show_tasks_tab:
                self._create_tasks_tab(tabs[tab_idx])
        else:
            st.warning("No configuration tabs are enabled. Set show_agents_tab or show_tasks_tab to True.")

    def _display_dashboard_page(self):
        """
        Display the Dashboard page (currently empty)
        """
        st.title("Dashboard")
        st.write("Welcome to the Dashboard! This page is currently under development.")

        # Add a placeholder for future dashboard content
        st.info("Dashboard features coming soon...")

        # Add a sample chart as a placeholder
        import numpy as np

        # Sample data for demonstration
        chart_data = np.random.randn(20, 3)

        st.subheader("Sample Visualization")
        st.line_chart(chart_data)

        # Add some placeholder widgets
        st.subheader("Settings")

        col1, col2 = st.columns(2)

        with col1:
            st.checkbox("Enable advanced features", key="dashboard_advanced")
            st.slider("Sample parameter", 0, 100, 50, key="dashboard_slider")

        with col2:
            st.selectbox("View mode", ["Standard", "Detailed", "Compact"], key="dashboard_view")
            st.number_input("Update frequency (seconds)", min_value=1, max_value=60, value=5, key="dashboard_frequency")

        st.button("Refresh Dashboard", key="dashboard_refresh")


def launch_streamlit_ui(config=None):
    """
    Launch a Streamlit UI for a CrewAI project.

    Args:
        config (dict, optional): Configuration options for the UI.
            See CrewAIStreamlitUI constructor for available options.

    Returns:
        None: This function runs the Streamlit app and doesn't return.
    """
    if config is None:
        config = {}

    # Create and run the UI
    ui = CrewAIStreamlitUI(**config)
    ui.run()

