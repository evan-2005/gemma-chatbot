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
