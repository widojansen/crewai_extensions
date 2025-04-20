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

def ask_ollama(prompt, context=None):
    payload = {
        'model': MODEL,
        'prompt': prompt,
        'stream': False,
        'options': {
            'temperature': 0.7,
            'stop': ["Observation:"]
        }
    }
    if context:
        payload['context'] = context

    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()  # Catch HTTP errors
        data = response.json()

        if 'response' not in data:
            raise ValueError(f"Ollama returned unexpected response: {data}")

        return data['response'], data.get('context')

    except Exception as e:
        st.error(f"Error communicating with Ollama: {e}")
        return "⚠️ There was an error contacting the model.", context


def run():
    st.title("💬 Chatbot (Ollama)")
    st.markdown("Talk to a local LLM and track the conversation with persistent memory.")

    if "context" not in st.session_state:
        st.session_state.context = load_context()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("Your message", placeholder="Ask anything...")
        submitted = st.form_submit_button("Send")

    if submitted and user_input:
        response, new_context = ask_ollama(user_input, st.session_state.context)
        st.session_state.context = new_context
        save_context(new_context)
        log_chat(user_input, response)

        st.session_state.messages.append(("You", user_input))
        st.session_state.messages.append(("Bot", response.strip()))

    for role, msg in st.session_state.messages:
        st.markdown(f"**{role}**: {msg}")