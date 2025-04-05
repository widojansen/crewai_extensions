import logging
import json
from datetime import datetime
from functools import wraps
import os
import traceback
import sys
import io
import re
import atexit

# Print immediately to help with debugging
print(f"Loading logging_utils.py - Start at {datetime.now().isoformat()}")

# Module initialization lock file
LOCK_FILE = os.path.join(os.getcwd(), '.logging_lock')

# Global variables
streamlit_log_queue = None  # Queue for Streamlit integration
current_topic = "blog"  # Default topic
log_file = None  # Current log file path
logger = None  # Logger instance
_initialized = False  # Initialization flag
_initialization_time = None  # When was logging initialized


# Function to create a process-specific lock file
def _create_lock_file():
    """Create a lock file to prevent multiple initializations"""
    # Use PID to make it unique per process
    pid = os.getpid()
    lock_content = f"{pid}:{datetime.now().isoformat()}"

    try:
        with open(LOCK_FILE, 'w') as f:
            f.write(lock_content)

        # Register cleanup
        atexit.register(lambda: os.remove(LOCK_FILE) if os.path.exists(LOCK_FILE) else None)

        print(f"Created logging lock file for PID {pid}")
        return True
    except Exception as e:
        print(f"Warning: Failed to create lock file: {e}")
        return False


# Function to check if we're already initialized in this process
def _check_lock_file():
    """Check if lock file exists and is for current process"""
    if not os.path.exists(LOCK_FILE):
        return False

    try:
        with open(LOCK_FILE, 'r') as f:
            content = f.read().strip()

        if ':' in content:
            pid_str = content.split(':', 1)[0]
            try:
                pid = int(pid_str)
                return pid == os.getpid()  # Only initialized if lock is for current process
            except ValueError:
                return False

        return False
    except Exception:
        return False


# Try to get the topic from environment if set
if "BLOG_TOPIC" in os.environ:
    current_topic = os.environ["BLOG_TOPIC"]
    print(f"Using topic from environment: {current_topic}")
else:
    # Try to get the topic from command line arguments
    if len(sys.argv) > 2 and sys.argv[1] == "run" and "--topic" in sys.argv:
        try:
            topic_index = sys.argv.index("--topic") + 1
            if topic_index < len(sys.argv):
                topic = sys.argv[topic_index]
                # Clean and truncate the topic
                clean_topic = re.sub(r'[^\w\s]', '', topic)  # Remove special characters
                clean_topic = clean_topic.replace(" ", "_")  # Replace spaces with underscores
                current_topic = clean_topic[:40] if len(clean_topic) > 40 else clean_topic
                print(f"Using topic from command line: {current_topic}")
        except Exception as e:
            print(f"Error getting topic from command line: {e}")
            # Continue with default topic


# Function to get logger name
def get_log_filename():
    """Get the log filename based on current topic"""
    return f'logs/{current_topic}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'


def set_streamlit_queue(queue):
    """Set the queue for Streamlit integration"""
    global streamlit_log_queue
    streamlit_log_queue = queue
    print("Streamlit log queue configured")


def set_current_topic(topic):
    """Set the current topic for log file naming"""
    global current_topic
    old_topic = current_topic # Store old topic for comparison

    if topic:
        # Clean and truncate the topic - replace spaces with underscores and limit to 40 chars
        clean_topic = re.sub(r'[^\w\s]', '', topic)  # Remove special characters
        clean_topic = clean_topic.replace(" ", "_")  # Replace spaces with underscores
        current_topic = clean_topic[:40] if len(clean_topic) > 40 else clean_topic
        print(f"Set current topic for logging to: {current_topic}")

        # If topic actually changed, create new log file immediately
        if old_topic != current_topic:
            return create_topic_logger()  # This will create a new log file

    return current_topic


# Custom formatter for logging
class CustomFormatter(logging.Formatter):
    def format(self, record):
        formatted_message = super().format(record)
        # If we're in Streamlit mode, also add to the Streamlit queue
        if streamlit_log_queue is not None:
            try:
                streamlit_log_queue.put(formatted_message)
            except:
                pass  # Ignore errors with the queue
        return formatted_message


# Initialize logging system - ensuring this only happens once per process
def initialize_logging():
    """Set up the logging system - only runs once per process"""
    global logger, log_file, _initialized, _initialization_time

    # Check if already initialized in this process
    if _initialized or _check_lock_file():
        print(f"Logging already initialized at {_initialization_time}")

        # Ensure we have a logger even if initialized elsewhere
        if logger is None:
            logger = logging.getLogger('CrewAI')

        return logger

    # Create lock file to prevent others from initializing
    _create_lock_file()

    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
        print("Created logs directory")

    # Make sure topic is truncated before creating log file
    global current_topic
    if len(current_topic) > 40:
        current_topic = current_topic[:40]
        print(f"Truncating initial topic to: {current_topic}")

    # Generate a log filename based on the current topic
    log_file = get_log_filename()
    print(f"Setting up logging to file: {log_file}")

    try:
        # Create formatter
        formatter = CustomFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)

        # Configure root logger
        logging.basicConfig(
            level=logging.INFO,
            handlers=[file_handler, console_handler]
        )

        # Get the logger
        logger = logging.getLogger('CrewAI')

        # Mark as initialized
        _initialized = True
        _initialization_time = datetime.now().isoformat()

        logger.info(f"Logging initialized at {_initialization_time}")
        print(f"Logging configured successfully to {log_file}")

        return logger
    except Exception as e:
        print(f"Error configuring logging: {e}")
        # Set up a bare minimum logger
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger('CrewAI')
        return logger


# Initialize logging once when this module is imported
logger = initialize_logging()


# Custom stream handler to capture stdout and stderr
class StdoutCaptureHandler(logging.Handler):
    def __init__(self, level=logging.INFO):
        super().__init__(level)
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

    def emit(self, record):
        pass  # We don't need to do anything here

    def start_capture(self):
        """Start capturing stdout and stderr"""
        sys.stdout = StdoutRedirector(self.original_stdout, logger)
        sys.stderr = StdoutRedirector(self.original_stderr, logger, is_error=True)

    def stop_capture(self):
        """Restore original stdout and stderr"""
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr


class StdoutRedirector:
    """Redirects stdout/stderr to both console and logger"""

    def __init__(self, original_stream, logger, is_error=False):
        self.original_stream = original_stream
        self.logger = logger
        self.is_error = is_error
        self.buffer = io.StringIO()

    def write(self, message):
        # Write to the original stream (console)
        self.original_stream.write(message)

        # Store in buffer until we get a complete line
        self.buffer.write(message)

        # If message ends with newline, log the complete line
        if message.endswith('\n'):
            line = self.buffer.getvalue().rstrip('\n')
            if line:  # Only log non-empty lines
                if self.is_error:
                    self.logger.error(f"STDERR: {line}")
                else:
                    self.logger.info(f"STDOUT: {line}")
            self.buffer = io.StringIO()

    def flush(self):
        # Flush any remaining content in the buffer
        line = self.buffer.getvalue()
        if line:
            if self.is_error:
                self.logger.error(f"STDERR: {line}")
            else:
                self.logger.info(f"STDOUT: {line}")
            self.buffer = io.StringIO()

        # Flush the original stream
        self.original_stream.flush()


# Create and start the stdout/stderr capture
stdout_capture = StdoutCaptureHandler()
stdout_capture.start_capture()


def log_task_execution(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        task_name = self.__class__.__name__

        # Print for debug - will show in console
        print(f"Starting task: {task_name}")

        try:
            # Get agent info safely
            agent_info = {}
            if hasattr(self, 'agent'):
                if hasattr(self.agent, 'role'):
                    agent_info["role"] = self.agent.role
                if hasattr(self.agent, 'goal'):
                    agent_info["goal"] = self.agent.goal
                if hasattr(self.agent, 'backstory'):
                    agent_info["backstory"] = self.agent.backstory

            # Log task start
            logger.info(f"Starting task: {task_name}")
            logger.info(f"Agent Info: {json.dumps(agent_info, indent=2)}")

            # Log input parameters
            input_params = kwargs.get('inputs', {})
            logger.info(f"Task inputs: {json.dumps(input_params, indent=2)}")

            # Execute the task
            result = func(self, *args, **kwargs)

            # Log successful completion
            logger.info(f"Task completed: {task_name}")
            logger.info(f"Task result: {str(result)[:500]}...")  # Log only first 500 chars
            print(f"Task completed: {task_name}")

            return result

        except Exception as e:
            # Log any errors
            error_msg = f"Task failed: {task_name}, Error: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            print(f"ERROR: {error_msg}")

            # Re-raise the exception to be handled upstream
            raise

    return wrapper


def log_llm_interaction(prompt, response):
    """Log LLM requests and responses."""
    try:
        # Format prompt and response for better readability
        if isinstance(prompt, list):
            prompt_text = "\n".join([str(p) for p in prompt])
        else:
            prompt_text = str(prompt)

        if hasattr(response, 'content'):
            response_text = response.content
        elif hasattr(response, 'text'):
            response_text = response.text
        else:
            response_text = str(response)

        # Create a structured log entry
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "llm_interaction",
            "llm_request": prompt_text[:500] + ("..." if len(prompt_text) > 500 else ""),
            "llm_response": response_text[:500] + ("..." if len(response_text) > 500 else "")
        }

        # Log as JSON for structured logging
        logger.info(f"LLM Interaction: {json.dumps(log_entry, indent=2)}")

        # Add to streamlit queue if available
        if streamlit_log_queue:
            streamlit_log_queue.put(log_entry)
    except Exception as e:
        logger.error(f"Error in log_llm_interaction: {e}")
        logger.error(traceback.format_exc())


def log_crew_execution(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        crew_name = self.__class__.__name__

        # Print for debug - will show in console
        print(f"Starting crew execution: {crew_name}")

        # Log crew start
        logger.info(f"Starting crew execution: {crew_name}")

        try:
            # Execute the crew
            result = func(self, *args, **kwargs)

            # Log successful completion
            logger.info(f"Crew execution completed: {crew_name}")
            print(f"Crew execution completed: {crew_name}")

            return result

        except Exception as e:
            # Log any errors
            error_msg = f"Crew execution failed: {crew_name}, Error: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            print(f"ERROR: {error_msg}")

            # Re-raise the exception to be handled upstream
            raise

    return wrapper


# Add a debug function that can be called from other files
def debug_trace(message):
    """Helper function to print debug info and log a stack trace"""
    print(f"DEBUG: {message}")
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")

    logger.debug(message)
    logger.debug(f"Stack trace: \n{traceback.format_stack()}")

    return True


# Function to create a new logger with the current topic
def create_topic_logger(topic=None):
    """
    Set the topic and ensure we're logging to the right file.
    If the topic has changed, it creates a new log file.
    Returns the log file path or None if no new file was created.
    """
    global current_topic, log_file, logger

    # This ensures we have a logger, even if somehow initialize_logging wasn't called
    if logger is None:
        logger = initialize_logging()

    # Store the old topic for comparison
    old_topic = current_topic

    # Update current topic if a new one is provided
    if topic:
        set_current_topic(topic)

    # If topic has changed, create a new log file
    if old_topic != current_topic:
        print(f"Topic changed from {old_topic} to {current_topic}, creating new log file")

        # Get all handlers of type FileHandler from the logger
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]

        # Close and remove all file handlers
        for handler in file_handlers:
            print(f"Closing log file: {handler.baseFilename}")
            handler.close()
            logger.removeHandler(handler)

        # Create the new log file name
        log_file = get_log_filename()
        print(f"Creating new log file: {log_file}")

        try:
            # Add new file handler
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(CustomFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            logger.addHandler(file_handler)

            logger.info(f"Logging redirected to new topic-based file: {log_file}")
            return log_file
        except Exception as e:
            print(f"Error creating topic logger: {e}")
            logger.error(f"Error creating topic logger: {e}")
            return None

    return None


print(f"Loaded logging_utils.py - End at {datetime.now().isoformat()} (log file: {log_file})")