# AgentBridge Backend 🧠

A powerful, agentic AI backend tailored for the **Model Context Protocol (MCP)**. This system orchestrates LangChain agents, manages tool permissions, streams real-time responses, and bridges specific LLMs (Gemini, etc.) with external data sources like GitHub, Notion, and local files.

## 🚀 Key Features

*   **langGraph Orchestration**: Uses advanced state graphs for agent loops, allowing for robust reasoning, tool usage, and human-in-the-loop workflows.
*   **Dynamic Agent Caching**: Agents are built on-the-fly based on user configuration and cached for performance. The cache automatically invalidates when configuration (models, tools, permissions) changes.
*   **Model Context Protocol (MCP) Support**: seamless integration with any MCP-compliant server.
    *   Native support for **GitHub**, **Notion**, **Filesystem**, and others.
    *   OAuth 2.0 flow handling for secure remote server connections.
*   **Granular Tool Permissions**:
    *   **Allow Once**: Approve a sensitive action for a single run.
    *   **Always Allow**: Whitelist specific tools (e.g., "search queries") for auto-execution.
    *   **Deny**: Block specific tool calls.
    *   **Enable/Disable**: Toggle entire tools on/off via settings.
*   **Real-time Streaming**: Server-Sent Events (SSE) for token-by-token streaming of agent thoughts and tool outputs.
*   **Session Management**: Redis-backed persistent conversation history.
*   **PostgreSQL Database**: Robust storage for user profiles, server settings, and permission records.

## 🏗️ Architecture

The backend is built with **FastAPI** for high performance and **LangChain/LangGraph** for cognitive architecture.

```mermaid
graph TD
    Client[Frontend Client] <-->|SSE Stream| API[FastAPI Gateway]
    API <-->|Auth & State| DB[(PostgreSQL)]
    API <-->|History| Cache[(Redis)]
    
    API --> Agent[Agent Orchestrator]
    Agent -->|LangGraph| Graph[State Graph]
    
    Graph -->|Loop| LLM[LLM Interface (Gemini/Bedrock)]
    Graph -->|Tool Calls| MCP[MCP Connector]
    
    MCP <--> GitHub[GitHub MCP Server]
    MCP <--> Notion[Notion MCP Server]
    MCP <--> Local[Local Tools]
    
    subgraph Security Layer
    Permissions[Permission Manager]
    OAuth[OAuth Handler]
    end
    
    Agent -.-> Permissions
```

## � Architecture Decisions: Why SSE?

You might notice that this backend primarily supports **Server-Sent Events (SSE)** over HTTP, rather than the standard `stdio` transport used by many local MCP servers.

**Why?**
*   **Containerization**: Running the backend in Docker/Cloud Run makes spawning arbitrary child processes (stdio) difficult or insecure.
*   **Decoupling**: The agent backend can be hosted on a powerful cloud GPU instance while connecting to "local" tools running on your laptop or another edge device.
*   **Scalability**: HTTP services are easier to load balance and manage than long-lived subprocess pipes.

**How to use Stdio servers (e.g., `server-filesystem`)?**
To use standard stdio-based MCP servers, you need to run them behind a **Stdio-to-SSE Bridge**.
We recommend using a simple wrapper or proxy that exposes the stdio process as an SSE endpoint (e.g., `http://localhost:8000/sse`).

## �🛠️ Project Structure

```text
backend/
├── app/
│   ├── api/                # API dependencies
│   ├── auth/               # OAuth2 & JWT handling
│   ├── core/               # App config & constants
│   ├── database/           # DB connection & base models
│   ├── models/             # SQLAlchemy ORM models (User, ToolPermission, etc.)
│   ├── routes/             # API Route handlers
│   │   ├── agent.py        # Main chat/stream endpoints
│   │   ├── tool_permissions.py # Permission management
│   │   └── ...
│   ├── services/           # Business Logic
│   │   ├── agent/          # LangGraph & Agent Factory
│   │   ├── mcp/            # MCP Protocol implementation
│   │   ├── security/       # Permission enforcement logic
│   │   └── streaming.py    # SSE Stream generator
│   └── main.py             # App Entrypoint
├── tests/                  # Pytest suite
├── .env.example            # Environment variable template
└── requirements.txt        # Dependencies
```

## ⚡ Setup & Installation

### Prerequisites
*   Python 3.11+
*   PostgreSQL
*   Redis (accessible URL)

### 1. Clone & Environment
```bash
git clone <repo_url>
cd backend
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\activate on Windows
```

### 2. Install Dependencies
We recommend using `uv` for fast installation, or standard pip:
```bash
# Using uv (Recommended)
pip install uv
uv pip install -r requirements.txt

# Or using pip
pip install -r requirements.txt
```

### 3. Configuration (.env)
Copy the example env file and fill in your secrets:
```bash
cp .env.example .env
```

**Critical Variables:**
*   `DATABASE_URL`: PostgreSQL connection string
*   `REDIS_URL_MEMORY`: Redis connection string
*   `GOOGLE_API_KEY`: For Gemini LLM
*   `SECRET_KEY`: For JWT tokens
*   `GITHUB_CLIENT_ID` / `NOTION_CLIENT_ID`: For MCP OAuth (optional)

### 4. Database Migration
Initialize the database tables:
```bash
# We use Alembic or sync on startup (check main.py lifespans)
# Currently, app.main handles startup table creation via SQLAlchemy
python bootstrap_servers.py  # Optional: Loads default local servers
```

### 5. Run Server
```bash
uv run uvicorn app.main:app --reload --port 8001
```
Visit `http://localhost:8001/docs` for the interactive Swagger UI.

## 🔑 key API Endpoints

### Agent Interaction
*   `GET /ask/stream`: Main SSE endpoint for chatting with the agent.
    *   Params: `prompt`, `session_id`, `model`, `resume` (for approval flow).

### MCP Integration
*   `GET /api/mcp/settings/`: List configured MCP servers.
*   `POST /api/mcp/settings/`: Add a new standard MCP server URL.
*   `POST /api/mcp/oauth/callback`: Callback handler for connecting GitHub/Notion.

### Tool Control
*   `GET /api/mcp/settings/{id}/tools`: List tools for a specific server (with enabled status).
*   `PATCH /api/mcp/settings/{id}/tools/{name}`: Enable/Disable a specific tool.
*   `GET /api/tool-approvals`: View "Always Allow" preferences.
*   `DELETE /api/tool-approvals/{name}`: Revoke an auto-approval.

## 🛡️ Security & Permissions

The backend implements a **Human-in-the-loop** security model for tool execution.

1.  **Check**: Before executing any tool, the `human_review_node` checks the database.
2.  **Verify**:
    *   If **Always Allowed**: Execute immediately.
    *   If **Denied**: Skip and inform agent.
    *   If **Unknown**: Pause execution, interrupt the graph, and notify frontend.
3.  **Resume**: User clicks "Allow" -> Frontend calls API -> Backend updates state -> Graph resumes.

## 🧪 Testing

Run output tests to verify agent behavior:
```bash
pytest tests/
```

## 🤝 Contributing

1.  Fork the repo
2.  Create feature branch (`git checkout -b feature/amazing-feature`)
3.  Commit changes
4.  Push and open PR

## License
MIT License
