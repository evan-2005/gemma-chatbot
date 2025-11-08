import streamlit as st
import requests
import json
import chromadb
import datetime
"""
Streamlit Local AI Assistant — Dyno/Dyna Edition (with safe PDF import)

Features:
- Local chatbot with gender toggle (Dyno/Dyna)
- Themed UI and mascot image
- Combined tab: Assistant Tools (Notes, To‑Do, Reminders, Meetings)
- New tab: New Page (custom content area)
- File upload (txt/csv/pdf)

Run: streamlit run streamlit_ai_chatbot.py
"""

import os
import sqlite3
from datetime import datetime

import streamlit as st
import pandas as pd
import dateparser

# Try importing PyPDF2 safely
try:
    import PyPDF2
    def extract_text_from_pdf(file_buffer):
        try:
            reader = PyPDF2.PdfReader(file_buffer)
            return "\n".join([page.extract_text() or "" for page in reader.pages])
        except Exception as e:
            return f"[PDF parsing error] {e}"
except ImportError:
    PyPDF2 = None
    def extract_text_from_pdf(file_buffer):
        return "[PyPDF2 not installed — PDF preview disabled]"

# --------- Configuration ---------
DB_PATH = "assistant_data.db"
DYNO_IMG = "Dyno.png"
DYNA_IMG = "Gemini_Generated_Image_svnqrmsvnqrmsvnq.png"

# --------- Database helpers ---------
def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, content TEXT, created_at TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS todos (id INTEGER PRIMARY KEY AUTOINCREMENT, task TEXT, done INTEGER DEFAULT 0, created_at TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS reminders (id INTEGER PRIMARY KEY AUTOINCREMENT, text TEXT, remind_at TEXT, created_at TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS meetings (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, start_time TEXT, end_time TEXT, attendees TEXT, notes TEXT, created_at TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS pages (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, content TEXT, created_at TEXT)")
    conn.commit()
    return conn

conn = init_db()

# --------- Utility functions ---------
def add_item(table, data):
    placeholders = ', '.join(['?'] * len(data))
    conn.execute(f"INSERT INTO {table} VALUES (NULL, {placeholders})", data)
    conn.commit()

def list_items(table):
    return conn.execute(f"SELECT * FROM {table} ORDER BY id DESC").fetchall()

def toggle_todo(todo_id, done):
    conn.execute("UPDATE todos SET done=? WHERE id=?", (1 if done else 0, todo_id))
    conn.commit()

# --------- App ---------
st.set_page_config(page_title="Dyno/Dyna Local Assistant", layout="wide")

# Gender toggle
st.sidebar.header("User Preferences")
gender = st.sidebar.radio("Select your gender:", ["Male", "Female"])

if gender == "Male":
    theme_color = "#4da6ff"
    assistant_name = "Dyno"
    logo_path = DYNO_IMG
else:
    theme_color = "#ff99cc"
    assistant_name = "Dyna"
    logo_path = DYNA_IMG

st.markdown(f"""
    <style>
    .reportview-container {{ background-color: {theme_color}10; }}
    .sidebar .sidebar-content {{ background-color: {theme_color}30; }}
    .stButton>button {{ background-color: {theme_color}; color: white; border-radius: 10px; }}
    h1, h2, h3, h4, h5, h6 {{ color: {theme_color}; }}
    </style>
""", unsafe_allow_html=True)

col_logo, col_title = st.columns([1, 4])
with col_logo:
    st.image(logo_path, width=120)
with col_title:
    st.title(f"{assistant_name}: Your Local AI Assistant")

# Tabs
main_tabs = st.tabs(["Chat", "Assistant Tools", "New Page", "Files"])

# Chat tab
with main_tabs[0]:
    st.header(f"Chat with {assistant_name}")
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    for role, text in st.session_state.chat_history:
        st.markdown(f"**{'You' if role=='user' else assistant_name}:** {text}")
    msg = st.text_input(f"Type your message to {assistant_name}")
    if st.button("Send"):
        if msg.strip():
            st.session_state.chat_history.append(('user', msg))
            reply = f"Hi! I'm {assistant_name}. You said: '{msg}'. (Local AI mode active)"
            st.session_state.chat_history.append(('assistant', reply))
            st.experimental_rerun()

# Assistant Tools tab
with main_tabs[1]:
    st.header("Assistant Tools")
    sub_tabs = st.tabs(["Notes", "To‑Do", "Reminders", "Meetings"])

    # Notes
    with sub_tabs[0]:
        title = st.text_input("Note title")
        content = st.text_area("Note content")
        if st.button("Save Note"):
            add_item('notes', (title, content, datetime.utcnow().isoformat()))
            st.success("Note saved.")
        for n in list_items('notes'):
            st.markdown(f"**{n[1]}** — {n[3][:19]}\n\n{n[2]}")

    # To‑Do
    with sub_tabs[1]:
        task = st.text_input("New task")
        if st.button("Add Task"):
            add_item('todos', (task, 0, datetime.utcnow().isoformat()))
            st.success("Task added.")
        for tid, t, done, *_ in list_items('todos'):
            c1, c2 = st.columns([0.8, 0.2])
            with c1:
                st.write(t)
            with c2:
                checked = st.checkbox("Done", bool(done), key=f"todo_{tid}")
                if checked != bool(done):
                    toggle_todo(tid, checked)
                    st.experimental_rerun()

    # Reminders
    with sub_tabs[2]:
        text = st.text_input("Reminder text")
        when = st.text_input("When? (e.g., 'tomorrow 9am')")
        if st.button("Add Reminder"):
            remind_at = dateparser.parse(when).isoformat() if when else datetime.utcnow().isoformat()
            add_item('reminders', (text, remind_at, datetime.utcnow().isoformat()))
            st.success("Reminder added.")
        for r in list_items('reminders'):
            st.write(f"{r[2][:19]} — {r[1]}")

    # Meetings
    with sub_tabs[3]:
        title = st.text_input("Meeting title")
        start = st.text_input("Start (e.g., '2025-11-09 14:00')")
        end = st.text_input("End (optional)")
        attendees = st.text_input("Attendees (comma separated)")
        notes = st.text_area("Meeting notes")
        if st.button("Save Meeting"):
            add_item('meetings', (title, start, end, attendees, notes, datetime.utcnow().isoformat()))
            st.success("Meeting saved.")
        for m in list_items('meetings'):
            st.write(f"{m[2][:19]} — {m[1]} ({m[4]})")

# New Page tab
with main_tabs[2]:
    st.header("New Page")
    new_title = st.text_input("Page title")
    new_content = st.text_area("Page content")
    if st.button("Save Page"):
        add_item('pages', (new_title, new_content, datetime.utcnow().isoformat()))
        st.success("Page saved.")
    st.subheader("Saved Pages")
    for p in list_items('pages'):
        st.markdown(f"**{p[1]}** — {p[3][:19]}\n\n{p[2]}")

# Files tab
with main_tabs[3]:
    st.header("Upload Files")
    uploaded_files = st.file_uploader("Upload txt/csv/pdf", type=['txt', 'csv', 'pdf'], accept_multiple_files=True)
    if uploaded_files:
        for f in uploaded_files:
            st.markdown(f"**File:** {f.name}")
            if f.name.endswith('.pdf'):
                st.text(extract_text_from_pdf(f)[:1000])
            elif f.name.endswith('.csv'):
                st.dataframe(pd.read_csv(f))
            else:
                st.text(f.getvalue().decode('utf-8')[:1000])

st.sidebar.markdown(f"---\n**Local Mode:** No API calls — {assistant_name} runs entirely offline.")


########################################################################
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