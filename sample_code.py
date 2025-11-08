import streamlit as st
import ollama

# Set the page title
st.title("🤖 My Ollama Chatbot")

# Define the model to use
OLLAMA_MODEL = "llama3" # Or "llama3", "codellama", etc.

# --- Session State Initialization ---
# This is the most important part.
# We initialize a "messages" list in st.session_state to store the chat history.
# This list persists across script re-runs.
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Display Chat History ---
# Loop through the messages stored in session state
# and display them using st.chat_message.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Handle New User Input ---
# st.chat_input creates a text input field at the bottom of the page.
# The 'if prompt := ...' syntax assigns the user's input to the 'prompt'
# variable and runs the code block *only if* the user submitted a message.
if prompt := st.chat_input("What is up?"):
    
    # 1. Add the user's message to session state
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 2. Display the user's message in the chat
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 3. Display the assistant's response (with streaming)
    with st.chat_message("assistant"):
        try:
            # This is where you call the Ollama API
            # We pass the entire message history from session state
            response_stream = ollama.chat(
                model=OLLAMA_MODEL,
                messages=st.session_state.messages,
                stream=True  # This is key for streaming
            )
            
            # Create a generator function to yield content chunks
            def stream_generator():
                for chunk in response_stream:
                    # Yield just the content part of the chunk
                    if 'content' in chunk['message']:
                        yield chunk['message']['content']
            
            # Use st.write_stream to display the response as it comes in
            # This function returns the full, concatenated response once complete
            full_response = st.write_stream(stream_generator())
            
            # 4. Add the full assistant response to session state
            st.session_state.messages.append(
                {"role": "assistant", "content": full_response}
            )

        except ollama.ResponseError as e:
            st.error(f"Ollama API Error: {e.error}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
