import streamlit as st
import requests
import json
import chromadb
import datetime
from typing import Generator, Tuple, Optional

"""
Streamlit Local AI Assistant — Dina/Dyno Edition (Enhanced)

Features:
- Local chatbot with persona toggle (Dina/Dyno)
- Persistent memory using ChromaDB
- RAG-powered context retrieval
- Real-time streaming responses
- Connection monitoring
- Adjustable memory context

Run: streamlit run dinov3.py
"""

# --- 1. App Configuration ---

st.set_page_config(
    page_title="Dina & Dyno Chatbot",
    page_icon="🤖",
    layout="wide"
)

# --- 2. Constants ---

OLLAMA_URL = "http://localhost:11434/api/chat"
CHROMA_PATH = "./multi_persona_db"
MAX_CONTEXT_MESSAGES = 10  # Limit context to prevent token overflow

# --- 3. ChromaDB Connection ---

@st.cache_resource
def get_chroma_collection(collection_name: str) -> Tuple[Optional[chromadb.Client], Optional[chromadb.Collection]]:
    """
    Initializes a persistent ChromaDB client for a specific collection.
    
    Args:
        collection_name: Name of the collection to create/retrieve
        
    Returns:
        Tuple of (client, collection) or (None, None) on error
    """
    try:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        collection = client.get_or_create_collection(name=collection_name)
        return client, collection
    except Exception as e:
        st.error(f"Failed to initialize ChromaDB: {e}")
        return None, None

# --- 4. Helper Functions ---

def check_ollama_connection() -> bool:
    """Check if Ollama server is running and accessible."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        return response.status_code == 200
    except:
        return False

def stream_response(payload: dict) -> Generator[str, None, str]:
    """
    Yields tokens from the Ollama API stream.
    
    Args:
        payload: Request payload for Ollama API
        
    Yields:
        Individual tokens from the response stream
        
    Returns:
        Complete response text
    """
    full_response = ""
    try:
        response = requests.post(OLLAMA_URL, json=payload, stream=True, timeout=60)
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                data = json.loads(line)
                token = data['message']['content']
                full_response += token
                yield token
                
                if data.get('done'):
                    break
                    
    except requests.exceptions.ConnectionError:
        error_msg = f"❌ Could not connect to Ollama at {OLLAMA_URL}. Make sure Ollama is running."
        yield error_msg
        full_response = error_msg
    except requests.exceptions.Timeout:
        error_msg = "⏱️ Request timed out. The model might be taking too long to respond."
        yield error_msg
        full_response = error_msg
    except Exception as e:
        error_msg = f"❌ An error occurred: {str(e)}"
        yield error_msg
        full_response = error_msg
    
    return full_response

def clear_persona_memory(client: chromadb.Client, collection_name: str, messages_key: str) -> bool:
    """
    Clears a persona's memory from ChromaDB and session state.
    
    Args:
        client: ChromaDB client instance
        collection_name: Name of the collection to clear
        messages_key: Session state key for messages
        
    Returns:
        True if successful, False otherwise
    """
    try:
        client.delete_collection(name=collection_name)
        st.session_state[messages_key] = []
        # Recreate the collection
        client.get_or_create_collection(name=collection_name)
        return True
    except Exception as e:
        st.error(f"Error clearing memory: {e}")
        return False

# --- 5. Sidebar Configuration ---

st.sidebar.title("🤖 Persona Controls")
st.sidebar.markdown("Choose who you want to talk to. Their chat history and memory are separate.")

# Check Ollama connection
if check_ollama_connection():
    st.sidebar.success("✅ Ollama is connected")
else:
    st.sidebar.error("❌ Ollama is not running")
    st.sidebar.info("Start Ollama with: `ollama serve`")

# Persona selection
selected_persona = st.sidebar.radio(
    "Choose a persona:",
    ["Dina", "Dyno"],
    key="selected_persona"
)

model_name = selected_persona.lower()
collection_name = f"{model_name}_chat_history"
current_messages_key = f"{model_name}_messages"

# Get ChromaDB collection
client, collection = get_chroma_collection(collection_name)

# Settings
st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Settings")
max_memories = st.sidebar.slider(
    "Memory context size",
    min_value=3,
    max_value=15,
    value=5,
    help="Number of past messages to consider for context"
)

# Clear memory button
st.sidebar.markdown("---")
if st.sidebar.button(f"🗑️ Clear {selected_persona}'s Memory", type="secondary"):
    if client and collection:
        if clear_persona_memory(client, collection_name, current_messages_key):
            st.sidebar.success(f"✅ {selected_persona}'s memory cleared!")
            st.rerun()
    else:
        st.sidebar.error("ChromaDB not initialized.")

# Statistics
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Statistics")
if collection:
    try:
        count = collection.count()
        st.sidebar.metric("Total messages stored", count)
    except:
        st.sidebar.metric("Total messages stored", "N/A")

# --- 6. Initialize Session State ---

if "dina_messages" not in st.session_state:
    st.session_state.dina_messages = []

if "dyno_messages" not in st.session_state:
    st.session_state.dyno_messages = []

# --- 7. Main Chat Interface ---

st.title(f"💬 Chat with {selected_persona}!")
st.caption(f"This is a persistent chat. {selected_persona} will remember your conversation history.")

# Display chat history
for message in st.session_state[current_messages_key]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 8. Handle User Input ---

if prompt := st.chat_input(f"Ask {selected_persona} a question..."):
    
    if not check_ollama_connection():
        st.error("❌ Cannot send message: Ollama is not running. Please start Ollama and try again.")
        st.stop()
    
    # Add user message to session state
    st.session_state[current_messages_key].append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- RAG: Retrieve relevant context ---
    api_messages = []
    
    if collection:
        try:
            # Query ChromaDB for relevant past messages
            results = collection.query(
                query_texts=[prompt],
                n_results=max_memories
            )
            
            if results['documents'] and results['documents'][0]:
                # Sort by timestamp to maintain conversation order
                zipped_results = list(zip(
                    results['documents'][0],
                    results['metadatas'][0]
                ))
                zipped_results.sort(key=lambda x: x[1].get('timestamp', ''))
                
                # Add retrieved messages as context
                for doc, meta in zipped_results:
                    api_messages.append({
                        "role": meta['role'],
                        "content": doc
                    })
        
        except Exception as e:
            st.warning(f"⚠️ Could not retrieve context: {e}")
    
    # Add current prompt
    api_messages.append({"role": "user", "content": prompt})
    
    # --- Generate response ---
    payload = {
        "model": model_name,
        "messages": api_messages,
        "stream": True
    }

    # Display assistant response
    with st.chat_message("assistant"):
        full_response = st.write_stream(stream_response(payload))

    # Save to session state
    st.session_state[current_messages_key].append({
        "role": "assistant",
        "content": full_response
    })
    
    # --- Save to ChromaDB ---
    if collection and not full_response.startswith("❌") and not full_response.startswith("⏱️"):
        try:
            user_ts = datetime.datetime.now().isoformat()
            asst_ts = (datetime.datetime.now() + datetime.timedelta(milliseconds=100)).isoformat()

            collection.add(
                documents=[prompt, full_response],
                metadatas=[  # Fixed typo: was "metadatos"
                    {"role": "user", "timestamp": user_ts},
                    {"role": "assistant", "timestamp": asst_ts}
                ],
                ids=[f"msg_{user_ts}_user", f"msg_{asst_ts}_asst"]
            )
        except Exception as e:
            st.error(f"⚠️ Error saving to memory: {e}")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "Built with Streamlit, Ollama & ChromaDB | "
    f"Currently chatting with: <b>{selected_persona}</b>"
    "</div>",
    unsafe_allow_html=True
)
