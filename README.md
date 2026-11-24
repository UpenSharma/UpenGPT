# UpenGPT

A ChatGPT-style AI assistant built with **FastAPI**, **LangGraph** and **Google Gemini**.
It streams answers in real time, remembers past conversations, answers questions about documents you upload, and can search the web.

## Features

- **Streaming chat**: answers appear token by token, like ChatGPT.
- **Conversation history**: every chat is saved and can be reopened from the sidebar.
- **Chat with your documents**: upload PDF, DOCX, TXT, MD, PY or CSV files and ask questions about them (RAG with Chroma).
- **Web search**: uses Tavily for current events, prices, releases and other time-sensitive questions.
- **Memory**: ask it to "remember" a fact and it can recall it later, across conversations.
- **Calculator**: a safe math tool for arithmetic and common functions (`sqrt`, `log`, `sin`, …).
- **Model picker**: switch between Gemini models from the UI.

## Tech stack

| Layer | Technology |
|---|---|
| Web server | FastAPI, Uvicorn, Jinja2 |
| Agent | LangGraph, LangChain |
| LLM and embeddings | Google Gemini (`gemini-3.5-flash-lite`, `gemini-embedding-001`) |
| Vector store | Chroma |
| Web search | Tavily |
| Database | SQLite via SQLAlchemy, plus LangGraph SQLite checkpoints |

## Project structure

```
UpenGPT/
├── app.py              # FastAPI app: routes for chat streaming, upload, history
├── agent.py            # LangGraph agent, Gemini model selection, system prompt
├── tools.py            # Agent tools: document search, memory, calculator, web search
├── rag.py              # Document loading, chunking and Chroma vector search
├── database.py         # SQLAlchemy models for conversations, messages and memories
├── templates/
│   └── index.html      # Chat UI
├── requirements.txt
└── .env                # Your API keys (not committed)
```

Runtime data is created automatically on first run and is not committed:
`data/` (SQLite databases), `chroma_db/` (vector store) and `uploads/` (uploaded files).

## Getting started

### Prerequisites

- Python 3.11, installed through [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or another method
- A [Google AI Studio](https://aistudio.google.com/) API key for Gemini
- A [Tavily](https://tavily.com/) API key (optional, for web search)

### 1. Clone the repository

```bash
git clone https://github.com/UpenSharma/UpenGPT.git
cd UpenGPT
```

### 2. Create and activate an environment

```bash
conda create -n UpenGPT python=3.11 -y
conda activate UpenGPT
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your API keys

Create a file named `.env` in the project root:

```env
GOOGLE_API_KEY=your-google-api-key

# Optional: enables web search
TAVILY_API_KEY=your-tavily-api-key

# Optional: default model (defaults to gemini-3.5-flash-lite)
GEMINI_MODEL=gemini-3.5-flash-lite

# Optional: LangSmith tracing
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=your-langsmith-api-key
LANGSMITH_PROJECT=UpenGPT
```

Never commit `.env`. It is already listed in `.gitignore`.

### 5. Run the app

```bash
python app.py
```

Open **http://localhost:8080** in your browser.
The server reloads automatically when you change a file.

## Supported models

The model picker offers these Gemini models:

| Model | Notes |
|---|---|
| `gemini-3.5-flash-lite` | Default. Fast and low cost; good for testing. |
| `gemini-3.5-flash` | More capable general model. |
| `gemini-3.1-flash-lite` | Lightweight alternative. |

Older models such as `gemini-2.5-flash` are no longer available to new API keys.
To change the list, edit `ALLOWED_MODELS` in `agent.py` and the `<select>` options in `templates/index.html`.

## API endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Chat UI |
| `POST` | `/chat/stream` | Send a message; streams the reply as Server-Sent Events. Body: `{"message", "thread_id", "model"}` |
| `POST` | `/upload` | Upload a document for a conversation (form fields: `file`, `thread_id`) |
| `GET` | `/conversations` | List saved conversations |
| `GET` | `/history/{thread_id}` | Messages in one conversation |

## Deploying to Azure App Service

The app runs on Azure App Service (Linux, Python 3.11).

1. Create a Linux web app with the **Python 3.11** runtime. Use B1 or higher; the dependencies are too heavy for the Free tier.
2. In **Configuration → Application settings**, add your keys from `.env` (`GOOGLE_API_KEY`, `TAVILY_API_KEY`, …) and set `SCM_DO_BUILD_DURING_DEPLOYMENT=true`.
3. Set the startup command:
   ```
   python -m uvicorn app:app --host 0.0.0.0 --port 8000
   ```
4. Zip the code (`*.py`, `requirements.txt`, `templates/`) and deploy it:
   ```bash
   az webapp deploy -g <resource-group> -n <app-name> --src-path upengpt.zip --type zip
   ```
   The first deployment takes about 10 minutes while Azure installs the dependencies.

> **Note:** On Azure, only files under `/home` survive a restart. Chat history, memories and uploaded documents are stored in the app folder, so they are reset whenever the app restarts or is redeployed.

## License

This project is licensed under the terms of the [LICENSE](LICENSE) file.
