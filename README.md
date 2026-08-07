<div align="center">
  <img src="client/public/favicon.ico" alt="Agent Bridge Logo" width="120" style="filter: brightness(0) invert(1);" />
  <h1>Agent Bridge</h1>
  <p><strong>A modular AI agent platform connecting LangChain & FastAPI with Model Context Protocol (MCP) servers.</strong></p>

  <p>
    <a href="https://github.com/punkpeye/awesome-mcp-clients/pull/140">
      <img src="https://img.shields.io/badge/Awesome-MCP_Clients-5865F2?style=for-the-badge&logo=awesome-lists" alt="Awesome MCP Clients" />
    </a>
    <a href="https://opensource.org/licenses/MIT">
      <img src="https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge" alt="License: MIT" />
    </a>
    <a href="https://www.python.org/">
      <img src="https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.12+" />
    </a>
    <a href="https://vuejs.org/">
      <img src="https://img.shields.io/badge/Vue.js-3.x-4FC08D?style=for-the-badge&logo=vuedotjs&logoColor=white" alt="Vue 3" />
    </a>
    <a href="https://fastapi.tiangolo.com/">
      <img src="https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
    </a>
    <a href="https://ramblinghermit0403.github.io/agent_bridge/">
      <img src="https://img.shields.io/badge/Docs-VitePress-646CFF?style=for-the-badge&logo=vite&logoColor=white" alt="Documentation" />
    </a>
  </p>
</div>

<br/>

---

## 🌟 Featured in Awesome MCP Clients

Agent Bridge is officially added to the **[Awesome MCP Clients](https://github.com/punkpeye/awesome-mcp-clients/pull/140)** repository!

[Model Context Protocol (MCP)](https://modelcontextprotocol.io/) enables seamless interoperability between AI models and external tools & data sources. Agent Bridge provides an end-to-end, production-ready platform to manage, authenticate, and execute tools across multiple MCP servers.

---

## 🎬 Video Preview

[<video src="client/src/assets/tutorial.mp4" controls width="100%"></video>](https://github.com/user-attachments/assets/dced0bda-c6f0-4a26-803f-a7f8b818c59f)

---

## 🚀 Key Features

- 🤖 **AI Agent Orchestration**: LangChain & LangGraph state machine integration on top of a robust FastAPI backend.
- 🔌 **Multi-Server MCP Support**: Seamlessly register, manage, and execute tools across various Model Context Protocol servers.
- 🔐 **Authentication & Security**: Secure JWT user management, bcrypt password hashing, and OAuth 2.0 with PKCE (Figma, Notion, GitHub).
- 🛡️ **Human-in-the-Loop Permissions**: Fine-grained tool execution controls and permission requests.
- 🎨 **Modern Web Interface**: Responsive Vue 3 frontend using Vite, Tailwind CSS, and Element Plus components.
- ⚡ **Live Real-time Streaming**: SSE (Server-Sent Events) and WebSocket pipelines for agent interaction streaming.
- 🗄️ **Flexible Database Layer**: PostgreSQL database powered by SQLAlchemy ORM with SQLite local dev support.

---

## 📚 Documentation

🌐 **Official Documentation**: [https://ramblinghermit0403.github.io/agent_bridge/](https://ramblinghermit0403.github.io/agent_bridge/)

| Resource | Description |
| :--- | :--- |
| 🔌 [**Supported MCP Servers**](docs/guide/mcp-servers.md) | Setup guide for Figma, GitHub, Notion, and custom servers |
| 🤖 [**LLM Providers**](docs/guide/llm-providers.md) | Configuration for Gemini, OpenAI, Pinecone, and AWS Bedrock |
| 🏗️ [**Architecture Guide**](docs/dev/architecture.md) | In-depth breakdown of system design and agent flows |
| 🧩 [**Platform Expansion**](docs/dev/expansion.md) | Step-by-step guide to adding new servers and providers |
| 🧠 [**Prompts & Agent Core**](docs/dev/agent-core.md) | Customizing agent behavior, persona, and memory system |

---

## 📁 Project Structure

```text
agent_bridge/
├── backend/                # FastAPI backend server
│   ├── app/
│   │   ├── routes/         # API routes & endpoints
│   │   ├── services/       # Core business logic & agent services
│   │   ├── models/         # Database models (SQLAlchemy)
│   │   ├── schemas/        # Data schemas (Pydantic)
│   │   ├── auth/           # Authentication & JWT services
│   │   ├── database/       # DB configuration & connections
│   │   └── core/           # Utility modules & helpers
│   ├── pyproject.toml      # UV dependency management
│   └── requirements.txt    # Standard pip requirements
│
├── client/                 # Vue.js 3 frontend application
│   ├── src/
│   │   ├── view/           # Vue page views
│   │   ├── components/     # Reusable UI components
│   │   ├── router.js       # Vue Router configuration
│   │   └── main.js         # Frontend entry point
│   └── package.json        # Node.js dependencies
│
├── docs/                   # VitePress documentation site
├── docker-compose.yml      # Multi-container deployment config
├── LICENSE                 # MIT License
└── CONTRIBUTING.md         # Contribution guidelines
```

---

## ⚙️ Prerequisites

Ensure you have the following installed prior to setup:

- 🐍 **Python 3.12+**
- 📦 **Node.js 20+**
- 🐳 **Docker & Docker Compose** *(Optional, recommended for quick deployment)*

---

## ⚡ Quick Start (Docker)

Launch the entire stack with a single command using Docker Compose:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/ramblinghermit0403/agent_bridge.git
   cd agent_bridge
   ```

2. **Configure Environment Variables**:
   Create a `.env` file inside `backend/` (or `server/` depending on setup):
   ```bash
   cp backend/.env.example backend/.env
   ```
   Add your API credentials (e.g., `GOOGLE_API_KEY`, `OPENAI_API_KEY`).

3. **Spin up services**:
   ```bash
   docker-compose up --build
   ```
   - **Frontend UI**: `http://localhost:80`
   - **Backend API**: `http://localhost:8001`
   - **PostgreSQL**: `localhost:5432`

---

## 🛠️ Manual Installation (Development)

### 1. Backend Setup

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate.ps1
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8001
```
> The backend API will be available at `http://localhost:8001`.

### 2. Frontend Setup

```powershell
cd client
npm install
npm run dev
```
> The web interface will be accessible at `http://localhost:5173`.

### 3. Documentation Setup

```powershell
cd docs
npm install
npm run docs:dev
```
> The local docs server will run at `http://localhost:5173` (or next available port).

---

## 🔧 Configuration

### MCP Server Registration
To connect your custom MCP servers, update `backend/servers.json` and run the bootstrap script:
```bash
python bootstrap_servers.py your-email@example.com
```

### Database Migrations
Database tables auto-generate upon backend startup. Use SQLAlchemy migrations for custom schema alterations.

---

## 💡 Open Source Use Cases

Agent Bridge is built as a flexible, modular platform suitable for multiple usage patterns:

### 1. Full Platform Deployment
*Target: Engineering Teams, Startups, Enterprises*

| Scenario | Value Proposition |
| :--- | :--- |
| **Internal DevOps Assistant** | Autonomous agent that interacts with GitHub issues, CI pipelines, and log tools |
| **Customer Support Copilot** | Connected to CRM, ticketing systems, and knowledge base MCP servers |
| **Self-Hosted Workflows** | Complete data privacy with zero SaaS vendor lock-in |

### 2. Learning & Education
*Target: Developers learning Agentic AI & MCP*

| Concept | Location in Codebase |
| :--- | :--- |
| **LangGraph State Machines** | `agent_orchestrator.py` — StateGraph edge routing |
| **Human-in-the-Loop** | `human_review_node` — Approval interrupt logic |
| **Dynamic Tooling** | `tools.py` — Dynamic MCP tool factory |
| **SSE Response Streaming** | `streaming.py` — FastAPI EventSourceResponse pipelines |

### 3. Modular Extraction
*Target: Product Developers*

| Module | Purpose |
| :--- | :--- |
| `llm_factory.py` | Universal multi-provider LLM client wrapper |
| `MCPConnector` | Standalone MCP client integration for any Python framework |
| `Tool Permission System` | Portable approval flow logic |

### 4. MCP Server Testing & Sandbox
*Target: Tool Developers & Authors*

| Task | Workflow |
| :--- | :--- |
| **Tool Discovery** | Validate schema parsing and UI rendering |
| **OAuth Debugging** | Test authentication callbacks and token refresh handling |
| **Benchmark Tooling** | Measure real agent invocation latency under load |

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend Framework** | FastAPI, Python 3.12+, Pydantic |
| **Agent Core** | LangChain, LangGraph, Model Context Protocol (MCP) SDK |
| **Database & Cache** | PostgreSQL, SQLAlchemy ORM, Redis |
| **Frontend Framework** | Vue.js 3, Vite, Tailwind CSS, Element Plus |
| **Auth & Security** | JWT, bcrypt, OAuth 2.0 + PKCE |

---

## 🔐 Security & Governance

- Encrypted JWT session tokens and secure password hashing.
- CORS isolation and environment configuration controls.
- Role-based tool authorization and real-time execution approval requests.

---

## 🤝 Contributing

Contributions are welcomed! Check out [CONTRIBUTING.md](CONTRIBUTING.md) to learn how to get started with bug fixes, feature requests, or documentation improvements.

---

## 📄 License

This project is open-source software licensed under the [MIT License](LICENSE).

---

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/) & [LangChain](https://www.langchain.com/)
- Model Context Protocol standard by [Anthropic MCP](https://modelcontextprotocol.io/)
- Listed in [Awesome MCP Clients](https://github.com/punkpeye/awesome-mcp-clients/pull/140)

---

<p align="center">
  <sub>Built with ❤️ for the AI & Open Source Community.</sub>
</p>

