import streamlit as st
import requests
import json
import os
from datetime import datetime

# Constants
OLLAMA_URL = 'http://localhost:11434/api/generate'
MODEL = 'llama3.1'
LOG_FILE = 'chat_log.txt'
CONTEXT_FILE = 'context.json'


# Utils
def load_context():
    if os.path.exists(CONTEXT_FILE):
        with open(CONTEXT_FILE, 'r') as f:
            return json.load(f)
    return None


def save_context(context):
    with open(CONTEXT_FILE, 'w') as f:
        json.dump(context, f)


def log_chat(user, bot):
    with open(LOG_FILE, 'a') as f:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"[{timestamp}] You: {user}\n")
        f.write(f"[{timestamp}] Bot: {bot}\n\n")


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
            'temperature': 0.7,
            'stop': ["Observation:"]
        }
    }
    
    if model_context:
        payload['context'] = model_context

    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()  # Catch HTTP errors
        data = response.json()

        if 'response' not in data:
            raise ValueError(f"Ollama returned unexpected response: {data}")

        return data['response'], data.get('context')

    except Exception as e:
        st.error(f"Error communicating with Ollama: {e}")
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
    </style>
    """, unsafe_allow_html=True)

    # Compact header
    st.markdown("<h1 style='font-size:1.5rem;margin-bottom:0.2rem;'>💬 Chatbot (Ollama)</h1>", unsafe_allow_html=True)
    st.markdown("<p style='margin-top:0;'>Talk to a local LLM and track the conversation with persistent memory.</p>",
                unsafe_allow_html=True)

    # Initialize session state
    if "model_context" not in st.session_state:
        st.session_state.model_context = load_context()

    if "messages" not in st.session_state:
        st.session_state.messages = []
        
    # Add system context to session state if not present
    if "system_context" not in st.session_state:
        st.session_state.system_context = "You are a helpful AI assistant. Be concise and clear in your answers."
        
    # Flag to track if we should process a new message
    if "should_process" not in st.session_state:
        st.session_state.should_process = False
    
    # Flag to track if we should update system context
    if "update_context" not in st.session_state:
        st.session_state.update_context = False

    # Layout structure with reduced spacing - add a context area at the top
    context_area, chat_area, input_area = st.container(), st.container(), st.container()
    
    # Function to handle message submission
    def submit_message():
        if st.session_state.user_input.strip():  # Only process non-empty messages
            # Store current message for processing
            st.session_state.current_message = st.session_state.user_input
            st.session_state.should_process = True
    
    # Function to update system context
    def update_system_context():
        st.session_state.system_context = st.session_state.context_input
        st.session_state.update_context = True
            
    # Function to handle chat clearing
    def clear_chat():
        st.session_state.messages = []
        st.session_state.current_message = ""
        st.session_state.should_process = False
        # Reset the model context but not the system context
        st.session_state.model_context = None
        save_context(None)
    
    # Context area for setting system instructions
    with context_area:
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
    
    # Process the message first if needed
    if st.session_state.should_process:
        # Get the content of the message to process
        user_input = st.session_state.current_message
        
        # Add user message to history
        st.session_state.messages.append({"role": "You", "content": user_input})
        
        # Get bot response, using the system context
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
        
        # Reset processing flags
        st.session_state.should_process = False
        st.session_state.current_message = ""
        
        # Ensure we rerun once to reset the input field
        st.rerun()
    
    # If context was updated, rerun to reflect changes
    if st.session_state.update_context:
        st.session_state.update_context = False
        st.rerun()
    
    # Input area with clear input logic
    with input_area:
        col1, col2, col3 = st.columns([6, 1, 1])
        
        # Use a key that changes when we want to clear the input
        input_key = f"user_input_{len(st.session_state.messages)}"
        
        with col1:
            user_input = st.text_input(
                "", 
                placeholder="Ask anything...",
                key=input_key,
                label_visibility="collapsed"
            )
            
            # Store input value in session state
            if user_input:
                st.session_state.user_input = user_input

        with col2:
            if st.button("Send", use_container_width=True):
                submit_message()

        with col3:
            if st.button("Clear", use_container_width=True):
                clear_chat()
                st.rerun()
    
    # Chat display area
    with chat_area:
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