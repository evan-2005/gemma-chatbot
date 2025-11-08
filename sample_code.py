import streamlit as st
import requests
import json
import chromadb
import datetime

# --- 1. App Configuration ---

# Set the page title and icon
st.set_page_config(page_title="Mario Chatbot", page_icon="🍄")

# Set the title of the chat interface
st.title("Chat with Mario! 🍄")
st.caption("Your personal plumber, powered by Ollama, ChromaDB, and Streamlit.")

# --- 2. Setup Ollama & ChromaDB ---

# Define constants
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "mario" # Your custom Ollama model
CHROMA_PATH = "./mario_memory_db" # Folder to store long-term memory

# Function to initialize ChromaDB (cached for performance)
@st.cache_resource
def get_chroma_collection():
    """
    Initializes a persistent ChromaDB client and returns the chat history collection.
    """
    try:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        collection = client.get_or_create_collection(name="chat_history")
        print("ChromaDB client initialized successfully.")
        return collection
    except Exception as e:
        st.error(f"Failed to initialize ChromaDB: {e}")
        return None

# Load the ChromaDB collection
collection = get_chroma_collection()

# --- 3. Initialize Chat History in Session State ---

# st.session_state is a dictionary that persists across script re-runs.
# We use it to store the messages that are displayed on the screen.
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 4. Display Past Chat Messages ---

# Loop through the stored messages and display them in the chat interface
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 5. Generator Function for Streaming Response ---

def stream_response(payload):
    """
    Yields tokens from the Ollama API stream and returns the full response.
    This function is used by st.write_stream.
    """
    full_response = ""
    try:
        response = requests.post(OLLAMA_URL, json=payload, stream=True)
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                data = json.loads(line)
                token = data['message']['content']
                full_response += token
                yield token # Yield each token for live streaming
                
                # Stop when the model signals it's done
                if data.get('done'):
                    break
                    
    except requests.exceptions.ConnectionError:
        yield f"Mamma mia! Could not connect to the server at {OLLAMA_URL}."
    except Exception as e:
        yield f"Mamma mia! An error occurred: {e}"
    
    # The 'st.write_stream' function will return this value
    return full_response

# --- 6. Handle User Input and Run the Chat ---

# st.chat_input creates a text box at the bottom of the screen
if prompt := st.chat_input("Ask Mario a question!"):
    
    # 1. Add user's message to session state (for display)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 2. Display user's message in the chat
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- 3. RAG: Retrieve Relevant Memories from ChromaDB ---
    
    api_messages = [] # This list will be sent to the API
    try:
        # Query ChromaDB for the 5 most relevant past messages
        results = collection.query(
            query_texts=[prompt],
            n_results=5
        )
        
        # Build the context for the API
        if results['documents']:
            # Zip documents, metadatas together to sort them
            zipped_results = list(zip(
                results['documents'][0],
                results['metadatas'][0]
            ))
            
            # Sort by timestamp to keep the conversation in order
            zipped_results.sort(key=lambda x: x[1].get('timestamp', 0))

            # Add the sorted, retrieved memories to our API context
            for doc, meta in zipped_results:
                api_messages.append({"role": meta['role'], "content": doc})
        
        # Add the user's *current* prompt to the list
        api_messages.append({"role": "user", "content": prompt})

    except Exception as e:
        st.error(f"Error querying ChromaDB: {e}")
        # Fallback: just send the current prompt without context
        api_messages = [{"role": "user", "content": prompt}]
        
    # --- 4. RAG: Generate Response from Ollama ---

    # Define the payload for the Ollama API
    payload = {
        "model": MODEL_NAME,
        "messages": api_messages,
        "stream": True 
    }

    # 5. Display the assistant's response (with streaming)
    with st.chat_message("assistant"):
        # st.write_stream streams the output of the generator function
        full_response = st.write_stream(stream_response(payload))

    # --- 6. Save to Session State (for display) & ChromaDB (for memory) ---

    # Add the assistant's full response to the session state (for display)
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    
    # Save both the prompt and response to ChromaDB for long-term memory
    try:
        user_ts = datetime.datetime.now().isoformat()
        asst_ts = (datetime.datetime.now() + datetime.timedelta(seconds=1)).isoformat()

        collection.add(
            documents=[prompt, full_response],
            metadatos=[
                {"role": "user", "timestamp": user_ts}, 
                {"role": "assistant", "timestamp": asst_ts}
            ],
            ids=[f"msg_{user_ts}_user", f"msg_{asst_ts}_asst"]
        )
    except Exception as e:
        st.error(f"Error saving message to ChromaDB: {e}")
