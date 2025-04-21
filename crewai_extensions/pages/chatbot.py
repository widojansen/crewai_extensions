import streamlit as st
import requests
import json
import os
from datetime import datetime

# Constants
OLLAMA_URL = 'http://localhost:11434/api/generate'
MODEL = 'llama3.1'
LOGS_FOLDER = 'chat_logs'
LOG_FILE = os.path.join(LOGS_FOLDER, 'chat_log.txt')
CONTEXT_FILE = os.path.join(LOGS_FOLDER, 'context.json')
REQUESTS_RESPONSES_LOG = os.path.join(LOGS_FOLDER, 'chat_requests_responses.log')


# Utils
def ensure_logs_folder_exists():
    """Ensure the chat logs folder exists, creating it if necessary."""
    if not os.path.exists(LOGS_FOLDER):
        os.makedirs(LOGS_FOLDER)


def load_context():
    ensure_logs_folder_exists()
    if os.path.exists(CONTEXT_FILE):
        with open(CONTEXT_FILE, 'r') as f:
            return json.load(f)
    return None


def save_context(context):
    ensure_logs_folder_exists()
    with open(CONTEXT_FILE, 'w') as f:
        json.dump(context, f)


def log_chat(user, bot):
    ensure_logs_folder_exists()
    with open(LOG_FILE, 'a') as f:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"[{timestamp}] You: {user}\n")
        f.write(f"[{timestamp}] Bot: {bot}\n\n")


def log_request_response(content):
    """Log detailed request/response information to a dedicated log file."""
    ensure_logs_folder_exists()
    with open(REQUESTS_RESPONSES_LOG, 'a') as f:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"[{timestamp}] {content}\n")


def ask_ollama(prompt, system_context="", model_context=None):
    """
    Send a prompt to Ollama with optional system context and model context
    
    Args:
        prompt: The user's message
        system_context: System instructions to prepend to the message
        model_context: The Ollama context for conversation history
    """
    # Prepare the full prompt with system context if provided
    full_prompt = prompt
    if system_context:
        full_prompt = f"### System:\n{system_context}\n\n### User:\n{prompt}"
    
    payload = {
        'model': MODEL,
        'prompt': full_prompt,
        'stream': False,
        'options': {
            'temperature': st.session_state.temperature,
            'stop': st.session_state.stop_sequences
        }
    }
    
    if model_context:
        payload['context'] = model_context

    # Log the request payload to the log file
    log_request_response(
        "================================================================================\n"
        "REQUEST PAYLOAD:\n"
        "================================================================================\n"
        f"{json.dumps(payload, indent=2)}\n"
        "================================================================================\n"
    )

    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()  # Catch HTTP errors
        data = response.json()

        # Log the complete response to the log file
        log_request_response(
            "================================================================================\n"
            "COMPLETE RESPONSE:\n"
            "================================================================================\n"
            f"{json.dumps(data, indent=2)}\n"
            "================================================================================\n"
        )

        if 'response' not in data:
            raise ValueError(f"Ollama returned unexpected response: {data}")

        return data['response'], data.get('context')

    except Exception as e:
        st.error(f"Error communicating with Ollama: {e}")
        # Log the error to the log file as well
        log_request_response(
            "================================================================================\n"
            "ERROR COMMUNICATING WITH OLLAMA:\n"
            "================================================================================\n"
            f"{str(e)}\n"
            "================================================================================\n"
        )
        return "⚠️ There was an error contacting the model.", model_context


def run():
    # Add custom CSS for ChatGPT-like styling with reduced spacing
    st.markdown("""
    <style>
        /* Reduce space between elements */
        .block-container {
            padding-top: 1rem;
            padding-bottom: 0;
            max-width: 95%;
        }

        /* Remove extra padding from Streamlit containers */
        .stContainer, .element-container, div.stMarkdown {
            padding-top: 0.2rem;
            padding-bottom: 0.2rem;
            margin-bottom: 0.2rem;
        }

        /* Styling for chat messages */
        .chat-message {
            padding: 0.8rem;
            border-radius: 0.5rem;
            margin-bottom: 0.5rem;
            display: flex;
            flex-direction: column;
        }
        .chat-message.user {
            background-color: #f0f2f6;
        }
        .chat-message.bot {
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
        }
        .chat-message.system {
            background-color: #f0f8ff;
            border: 1px dashed #b0c4de;
        }

        /* Chat container with reduced height */
        .chat-container {
            display: flex;
            flex-direction: column;
            max-height: 60vh;
            height: auto;
            overflow-y: auto;
            padding: 0.5rem;
            margin-top: 0.5rem;
            margin-bottom: 0.5rem;
        }

        .message-header {
            font-weight: bold;
            margin-bottom: 0.3rem;
        }

        /* Title spacing */
        h1 {
            margin-bottom: 0.2rem !important;
        }

        /* Subtitle spacing */
        p {
            margin-bottom: 0.5rem !important;
        }
        
        /* Context area styling */
        .context-area {
            background-color: #f8f9fa;
            border: 1px solid #e0e0e0;
            border-radius: 0.5rem;
            padding: 0.8rem;
            margin-bottom: 1rem;
        }
        
        /* Settings expander styling */
        .settings-expander {
            margin-bottom: 0.5rem;
        }
        
       /* Temperature box styling */
       .temperature-box {
           background-color: #f8f9fa;
           border: 1px solid #e0e0e0;
           border-radius: 0.5rem;
           padding: 0.8rem;
           margin-top: 0.5rem;
           margin-bottom: 0.5rem;
       }
    </style>
    """, unsafe_allow_html=True)

    # Ensure the logs folder exists when the app starts
    ensure_logs_folder_exists()

    # Compact header
    st.markdown("<h1 style='font-size:1.5rem;margin-bottom:0.2rem;'>💬 Chatbot (Ollama)</h1>", unsafe_allow_html=True)
    st.markdown("<p style='margin-top:0;'>Talk to a local LLM and track the conversation with persistent memory.</p>",
                unsafe_allow_html=True)

    # Initialize session state
    if "model_context" not in st.session_state:
        st.session_state.model_context = load_context()

    if "messages" not in st.session_state:
        st.session_state.messages = []
        
    # Add system context to the session state if not present
    if "system_context" not in st.session_state:
        st.session_state.system_context = "You are a helpful AI assistant. Be concise and clear in your answers."
        
    # Initialize temperature in the session state if not present
    if "temperature" not in st.session_state:
        st.session_state.temperature = 0.7
        
    # Initialize stop sequences in the session state if not present
    if "stop_sequences" not in st.session_state:
        st.session_state.stop_sequences = ["Observation:"]
        
    # Initialize user_input in session_state if not present
    if "user_input" not in st.session_state:
        st.session_state.user_input = ""
    
    # Store the current message to process
    if "current_message" not in st.session_state:
        st.session_state.current_message = ""
        
    # Flag to track if we should update system context
    if "update_context" not in st.session_state:
        st.session_state.update_context = False
        
    # Flag to track if we should update stop sequences
    if "update_stop_sequences" not in st.session_state:
        st.session_state.update_stop_sequences = False

    # Function to handle message submission - modified for single-click
    def submit_message():
        # Get the input directly from the widget key we're using
        user_input = st.session_state[input_key].strip()
        
        if user_input:  # Only process non-empty messages
            # Store message and process immediately
            st.session_state.current_message = user_input
            
            # Add a user message to the history
            st.session_state.messages.append({"role": "You", "content": user_input})
            
            # Get the bot response using the system context
            with st.spinner("Thinking..."):
                response, new_context = ask_ollama(
                    prompt=user_input,
                    system_context=st.session_state.system_context,
                    model_context=st.session_state.model_context
                )
                st.session_state.model_context = new_context
                save_context(new_context)
                log_chat(user_input, response)
            
            # Add bot response to history
            st.session_state.messages.append({"role": "Bot", "content": response.strip()})
            
            # Clear the input field by incrementing the key counter
            st.session_state.input_counter += 1
            
            # Trigger UI refresh
            st.rerun()
    
    # Function to update system context
    def update_system_context():
        st.session_state.system_context = st.session_state.context_input
        st.session_state.update_context = True
    
    # Function to update stop sequences
    def update_stop_sequences():
        stop_text = st.session_state.stop_sequences_input.strip()
        if stop_text:
            # Split by line and remove any empty lines
            sequences = [seq.strip() for seq in stop_text.split('\n') if seq.strip()]
            st.session_state.stop_sequences = sequences
        else:
            # If the input is empty, set an empty list
            st.session_state.stop_sequences = []
        st.session_state.update_stop_sequences = True
        
    # Function to handle chat clearing
    def clear_chat():
        st.session_state.messages = []
        st.session_state.current_message = ""
        # Reset the model context but not the system context
        st.session_state.model_context = None
        save_context(None)
        st.rerun()
    
    # Context area for setting system instructions and temperature
    with st.container():
        # First expander: System Context
        with st.expander("📝 System Context (instructions for the AI)", expanded=False):
            st.text_area(
                "Set context or instructions for the AI that apply to all messages:",
                value=st.session_state.system_context,
                height=100,
                key="context_input",
                help="These instructions will guide how the AI responds to your messages."
            )
            
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("Update Context", use_container_width=True):
                    update_system_context()
            
            # Show a preview of the current context
            if st.session_state.system_context:
                st.caption("Current system context:")
                st.markdown(f"""
                <div class="chat-message system">
                    <div class="message-header">🔧 System</div>
                    <div>{st.session_state.system_context}</div>
                </div>
                """, unsafe_allow_html=True)
                
        # Second expander: Temperature Control
        with st.expander("🌡️ Temperature Control", expanded=False):
            st.slider(
                "Adjust randomness of responses:",
                min_value=0.0,
                max_value=2.0,
                value=st.session_state.temperature,
                step=0.1,
                format="%.1f",
                key="temperature",
                help="Higher values (towards 2.0) make responses more random and creative. Lower values (towards 0.0) make responses more focused and deterministic."
            )
            
        # Third expander: Stop Sequences
        with st.expander("🛑 Stop Sequences", expanded=False):
            # Create the text area with current stop sequences as initial value
            current_stop_sequences = "\n".join(st.session_state.stop_sequences)
            st.text_area(
                "Set stop sequences (one per line):",
                value=current_stop_sequences,
                height=80,
                key="stop_sequences_input",
                help="The model will stop generating text when it encounters any of these sequences."
            )
            
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("Update Stop Sequences", use_container_width=True):
                    update_stop_sequences()
            
            # Show a preview of the current stop sequences
            if st.session_state.stop_sequences:
                st.caption("Current stop sequences:")
                for i, sequence in enumerate(st.session_state.stop_sequences):
                    st.code(f"{i+1}. \"{sequence}\"")
    
    # If context was updated, rerun to reflect changes
    if st.session_state.update_context:
        st.session_state.update_context = False
        st.rerun()
        
    # If stop sequences were updated, rerun to reflect changes
    if st.session_state.update_stop_sequences:
        st.session_state.update_stop_sequences = False
        st.rerun()
    
    # Chat display area
    chat_container = st.container()
    with chat_container:
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)

        if not st.session_state.messages:
            st.markdown(
                "<div style='text-align:center;color:#808080;padding:10px;'>Start a conversation by typing a message below.</div>",
                unsafe_allow_html=True)

        for message in st.session_state.messages:
            role = message["role"]
            content = message["content"]

            # Apply different styling based on the role
            if role == "You":
                st.markdown(f'''
                <div class="chat-message user">
                    <div class="message-header">👤 {role}</div>
                    <div>{content}</div>
                </div>
                ''', unsafe_allow_html=True)
            else:
                st.markdown(f'''
                <div class="chat-message bot">
                    <div class="message-header">🤖 {role}</div>
                    <div>{content}</div>
                </div>
                ''', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)
    
    # Input area with improved input handling
    input_container = st.container()
    with input_container:
        # Setup counter for dynamic key generation if it doesn't exist
        if "input_counter" not in st.session_state:
            st.session_state.input_counter = 0
            
        # Create a dynamic key that includes the counter
        input_key = f"user_input_{st.session_state.input_counter}"
        
        # Create the input form with auto-submission
        with st.form(key="message_form", clear_on_submit=True):
            col1, col2, col3 = st.columns([6, 1, 1])
            
            with col1:
                st.text_input(
                    "", 
                    placeholder="Ask anything...",
                    key=input_key,
                    label_visibility="collapsed"
                )
                
            # Add submit buttons to the form
            with col2:
                submit_button = st.form_submit_button("Send", use_container_width=True)
                
            with col3:
                clear_button = st.form_submit_button("Clear", use_container_width=True)
        
        # Process form submissions
        if submit_button:
            submit_message()
            
        if clear_button:
            clear_chat()