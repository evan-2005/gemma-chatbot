# 🤖 Dina & Dyno Multi-Persona Chatbot

A Streamlit-based chatbot application featuring two distinct AI personas (Dina and Dyno) with persistent memory using ChromaDB and local LLM inference via Ollama.

## ✨ Features

- **Multiple Personas**: Switch between Dina and Dyno, each with their own personality and memory
- **Persistent Memory**: Each persona remembers previous conversations using ChromaDB vector database
- **RAG (Retrieval-Augmented Generation)**: Contextual responses based on conversation history
- **Real-time Streaming**: Watch responses generate token-by-token
- **Isolated Chat Histories**: Each persona maintains separate conversation threads
- **Memory Management**: Clear individual persona memories independently
- **Connection Monitoring**: Real-time status of Ollama service
- **Adjustable Context**: Configure how much conversation history to consider

## 📋 Prerequisites

- Python 3.8+
- [Ollama](https://ollama.ai/) installed and running locally
- Custom Ollama models named `dina` and `dyno` (see setup instructions below)

## 🚀 Installation

### 1. Clone or Download the Repository

```bash
# If using git
git clone <your-repo-url>
cd chatbot-app

# Or simply download the files to a folder
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

**requirements.txt:**
```
streamlit>=1.28.0
requests>=2.31.0
chromadb>=0.4.15
```

### 3. Set Up Ollama Models

First, ensure Ollama is installed:

```bash
# macOS/Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Or download from https://ollama.ai/download
```

Create your custom models (Dina and Dyno):

#### Option A: Create from Existing Models

```bash
# Create Dina (e.g., based on llama2)
ollama create dina -f Modelfile-dina

# Create Dyno (e.g., based on mistral)
ollama create dyno -f Modelfile-dyno
```

**Example Modelfile-dina:**
```
FROM llama2:latest

PARAMETER temperature 0.8
PARAMETER top_p 0.9

SYSTEM """
You are Dina, a friendly and empathetic AI assistant. You are warm, patient, 
and always eager to help. You speak in a conversational, approachable tone 
and enjoy building rapport with users. You remember past conversations and 
use that context to provide personalized assistance.
"""
```

**Example Modelfile-dyno:**
```
FROM mistral:latest

PARAMETER temperature 0.7
PARAMETER top_p 0.85

SYSTEM """
You are Dyno, a dynamic and energetic AI assistant. You are quick-witted,
efficient, and love solving problems. You communicate in a clear, direct manner
and bring enthusiasm to every interaction. You remember past conversations
and use that knowledge to provide better assistance.
"""
```

#### Option B: Use Existing Models

If you want to skip custom models, modify `app.py` to use existing Ollama models:

```python
# In the sidebar section, change:
selected_persona = st.sidebar.radio(
    "Choose a model:",
    ["llama2", "mistral", "codellama"],  # Use any installed models
    key="selected_persona"
)
```

### 4. Start Ollama Service

```bash
ollama serve
```

Keep this terminal window open while using the app.

## 🎮 Usage

### Starting the Application

```bash
streamlit run app.py
```

The app will open in your default browser at `http://localhost:8501`

### Using the Chatbot

1. **Select a Persona**: Use the sidebar radio buttons to choose between Dina or Dyno
2. **Start Chatting**: Type your message in the chat input at the bottom
3. **View Responses**: Watch as the AI generates responses in real-time
4. **Switch Personas**: Change personas anytime - each maintains separate memory
5. **Adjust Context**: Use the slider to control how much conversation history influences responses
6. **Clear Memory**: Use the "Clear Memory" button to reset a persona's conversation history

### Understanding the Interface

**Sidebar Features:**
- ✅ **Connection Status**: Shows if Ollama is running
- 🎭 **Persona Selection**: Choose your AI assistant
- ⚙️ **Memory Context Size**: Adjust conversation context (3-15 messages)
- 🗑️ **Clear Memory**: Reset the selected persona's memory
- 📊 **Statistics**: View total messages stored for current persona

**Main Chat Area:**
- 💬 **Chat History**: Scrollable conversation history
- ⌨️ **Input Box**: Type and send messages
- 🤖 **Streaming Responses**: Real-time token generation

## 🏗️ Architecture

### Components

1. **Streamlit Frontend**: Web-based UI for chat interface
2. **Ollama Backend**: Local LLM inference engine
3. **ChromaDB**: Vector database for persistent memory storage
4. **RAG Pipeline**: Retrieves relevant context before generating responses

### Data Flow

```
User Input → ChromaDB Query (retrieve context) → 
Ollama API (generate response) → ChromaDB Store → Display to User
```

### File Structure

```
chatbot-app/
├── app.py                    # Main application
├── requirements.txt          # Python dependencies
├── README.md                # This file
├── Modelfile-dina           # Dina persona definition (optional)
├── Modelfile-dyno           # Dyno persona definition (optional)
└── multi_persona_db/        # ChromaDB storage (auto-created)
    ├── dina_chat_history/   # Dina's memories
    └── dyno_chat_history/   # Dyno's memories
```

## 🔧 Configuration

### Customizing Constants

Edit these values in `app.py`:

```python
OLLAMA_URL = "http://localhost:11434/api/chat"  # Ollama API endpoint
CHROMA_PATH = "./multi_persona_db"              # Database location
MAX_CONTEXT_MESSAGES = 10                       # Max context limit
```

### Adding New Personas

1. Create a new Ollama model: `ollama create newpersona -f Modelfile-newpersona`
2. Add to the radio button options in `app.py`:
   ```python
   selected_persona = st.sidebar.radio(
       "Choose a persona:",
       ["Dina", "Dyno", "NewPersona"],  # Add your persona here
       key="selected_persona"
   )
   ```
3. Initialize session state for the new persona:
   ```python
   if "newpersona_messages" not in st.session_state:
       st.session_state.newpersona_messages = []
   ```

## 🐛 Troubleshooting

### "Ollama is not running" error

**Solution**: 
```bash
# Start Ollama service
ollama serve
```

### "Model not found" error

**Solution**: 
```bash
# List available models
ollama list

# Pull a base model if needed
ollama pull llama2

# Create your personas
ollama create dina -f Modelfile-dina
ollama create dyno -f Modelfile-dyno
```

### ChromaDB connection errors

**Solution**: 
- Ensure the app has write permissions in the directory
- Delete `multi_persona_db/` folder and restart the app
- Check disk space availability

### Slow response times

**Solution**:
- Reduce the memory context size slider
- Use smaller/faster models (e.g., `tinyllama`)
- Ensure your system meets Ollama's requirements
- Check system resources (CPU/RAM usage)

### Port already in use

**Solution**:
```bash
# Use a different port
streamlit run app.py --server.port 8502
```

## 🔒 Privacy & Data

- **All data stays local**: No external API calls or data transmission
- **Persistent storage**: Conversations are saved in `./multi_persona_db/`
- **Data deletion**: Use "Clear Memory" or delete the database folder
- **No telemetry**: The app doesn't collect usage statistics

## 📝 Key Improvements from Original Code

1. ✅ **Fixed typo**: `metadatos` → `metadatas` in ChromaDB add call
2. ✅ **Connection checking**: Added Ollama connectivity verification
3. ✅ **Error handling**: Improved error messages and exception handling
4. ✅ **Type hints**: Added type annotations for better code clarity
5. ✅ **Settings control**: Adjustable memory context size
6. ✅ **Statistics display**: Show message count per persona
7. ✅ **Better UI**: Enhanced sidebar layout and visual feedback
8. ✅ **Code organization**: Separated concerns into helper functions
9. ✅ **Documentation**: Comprehensive docstrings and comments
10. ✅ **Timeout handling**: Added request timeout protection

## 🤝 Contributing

Feel free to fork, modify, and enhance this chatbot! Some ideas:

- Add more personas with unique characteristics
- Implement conversation export/import
- Add support for file uploads
- Create conversation summaries
- Add voice input/output
- Implement multi-language support

## 📄 License

This project is open source. Feel free to use and modify as needed.

## 🙏 Acknowledgments

- [Streamlit](https://streamlit.io/) - Web framework
- [Ollama](https://ollama.ai/) - Local LLM inference
- [ChromaDB](https://www.trychroma.com/) - Vector database
- Community contributors and testers

---

**Need help?** Open an issue or check the troubleshooting section above!

**Happy chatting with Dina & Dyno! 🎉**
