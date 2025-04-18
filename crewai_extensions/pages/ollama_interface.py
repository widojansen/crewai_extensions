import streamlit as st
import requests
import json
from typing import Dict, Any


def run():
    st.title("Ollama LLM Interface")
    st.write("This page allows you to send requests to a local running Ollama LLM.")

    # API endpoint selection
    api_endpoint = st.selectbox(
        "Select API Endpoint",
        options=["http://localhost:11434/api/show", "http://localhost:11434/api/generate", "http://localhost:11434/api/embeddings"],
        index=1
    )

    # Headers section
    st.subheader("Request Headers")

    # Display the default headers in a form
    with st.form(key="headers_form"):
        headers = {}

        # Create two columns for key-value pairs
        cols = st.columns(2)
        default_headers = {
            "host": "localhost:11434",
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, zstd",
            "connection": "keep-alive",
            "user-agent": "litellm/1.60.2",
            "content-length": "1751"
        }

        # Display each header in the form
        header_fields = {}
        for i, (key, value) in enumerate(default_headers.items()):
            col = i % 2
            header_fields[key] = cols[col].text_input(f"Header {i + 1}: {key}", value=value, key=f"header_{key}")

        # Option to add a new header
        st.form_submit_button("Update Headers", type="primary")

    # Collect header values
    for key, field in header_fields.items():
        if field:  # Only add non-empty fields
            headers[key] = field

    # Request body section
    st.subheader("Request Body")

    if "api/show" in api_endpoint:
        # Simple form for /api/show endpoint
        with st.form(key="show_form"):
            model_name = st.text_input("Model Name", value="llama3.1")

            col1, col2 = st.columns([1, 4])
            with col1:
                submit_show = st.form_submit_button("Send Request")
            with col2:
                reset_show = st.form_submit_button("Reset")

        if submit_show:
            body = {"name": model_name}
            display_and_send_request(api_endpoint, headers, body)

        if reset_show:
            st.experimental_rerun()

    elif "api/generate" in api_endpoint:
        # More complex form for /api/generate endpoint
        with st.form(key="generate_form"):
            model_name = st.text_input("Model", value="llama3.1")

            # System prompt and user input
            system_prompt = st.text_area("System Prompt", value="You are a helpful AI assistant.")
            user_prompt = st.text_area("User Prompt", value="Tell me about artificial intelligence.")

            # Combine system and user prompts
            full_prompt = f"### System:\n{system_prompt}\n\n### User:\n{user_prompt}"

            # Advanced options in an expander
            with st.expander("Advanced Options"):
                col1, col2 = st.columns(2)
                with col1:
                    temperature = st.slider("Temperature", min_value=0.0, max_value=2.0, value=0.7, step=0.1)
                    stream = st.checkbox("Stream Output", value=False)
                with col2:
                    stop_sequences = st.text_area("Stop Sequences (one per line)", value="\nObservation:")

            # Convert stop sequences to list
            stop_list = [seq.strip() for seq in stop_sequences.split('\n') if seq.strip()]

            col1, col2 = st.columns([1, 4])
            with col1:
                submit_generate = st.form_submit_button("Send Request")
            with col2:
                reset_generate = st.form_submit_button("Reset")

        # Build the request body
        body = {
            "model": model_name,
            "prompt": full_prompt,
            "stream": stream,
            "options": {
                "temperature": temperature
            }
        }

        # Add stop sequences if provided
        if stop_list:
            body["options"]["stop"] = stop_list

        # Preview the request body
        with st.expander("Preview Request Body"):
            st.code(json.dumps(body, indent=2), language="json")

        if submit_generate:
            display_and_send_request(api_endpoint, headers, body)

        if reset_generate:
            st.experimental_rerun()
    elif "api/embeddings" in api_endpoint:
        with st.form(key="generate_form"):
            model_name = st.text_input("Model", value="llama3.1")

            # prompt
            prompt = st.text_area("Prompt", value="Tell me about artificial intelligence.")

            # Advanced options in an expander
            with st.expander("Advanced Options"):
                temperature = st.slider("Temperature", min_value=0.0, max_value=2.0, value=0.7, step=0.1)

            col1, col2 = st.columns([1, 4])
            with col1:
                submit_generate = st.form_submit_button("Send Request")
            with col2:
                reset_generate = st.form_submit_button("Reset")

        # Build the request body
        body = {
            "model": model_name,
            "prompt": prompt,
            "options": {
                "temperature": temperature
            }
        }


        # Preview the request body
        with st.expander("Preview Request Body"):
            st.code(json.dumps(body, indent=2), language="json")

        if submit_generate:
            display_and_send_request(api_endpoint, headers, body)

        if reset_generate:
            st.experimental_rerun()

def display_and_send_request(url: str, headers: Dict[str, str], body: Dict[str, Any]):
    """Display and send the request to the Ollama API"""

    st.subheader("Request Details")

    # Display the curl command
    curl_cmd = generate_curl_command(url, headers, body)
    st.code(curl_cmd, language="bash")

    # Send the actual request
    try:
        with st.spinner("Sending request..."):
            response = requests.post(url, headers=headers, json=body, timeout=60)

        st.subheader("Response")

        # Display response status
        st.write(f"Status Code: {response.status_code}")

        # Try to parse and display JSON response
        try:
            resp_json = response.json()

            # If this is a generate response, extract and display the response text
            if "response" in resp_json:
                st.markdown("### Response Text")
                st.markdown(resp_json["response"])

                # Display metadata in an expander
                with st.expander("Response Metadata"):
                    metadata = {k: v for k, v in resp_json.items() if k != "response"}
                    st.json(metadata)
            else:
                # For other responses, show the full JSON
                st.json(resp_json)

        except json.JSONDecodeError:
            # If not JSON, display as text
            st.text(response.text)

    except Exception as e:
        st.error(f"Error sending request: {str(e)}")


def generate_curl_command(url: str, headers: Dict[str, str], body: Dict[str, Any]) -> str:
    """Generate a curl command from the request parameters"""

    # Start with the basic curl command
    curl_cmd = ["curl", "-X", "POST", url]

    # Add headers
    for key, value in headers.items():
        curl_cmd.extend(["-H", f'"{key}: {value}"'])

    # Add the JSON body
    body_json = json.dumps(body)
    curl_cmd.extend(["-d", f"'{body_json}'"])

    # Join all parts with spaces
    return " ".join(curl_cmd)


if __name__ == "__main__":
    run()