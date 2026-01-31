# Agent Bridge

**Agent Bridge** is a powerful AI agent platform that connects LangChain agents with MCP (Model Context Protocol) servers, enabling intelligent automation and tool execution through a modern web interface.

[<video src="client/src/assets/tutorial.mp4" controls width="100%"></video>](https://github.com/user-attachments/assets/dced0bda-c6f0-4a26-803f-a7f8b818c59f)

## 🌟 Features

- **AI Agent Integration**: Built on FastAPI with LangChain for intelligent agent orchestration
- **MCP Server Support**: Connect and manage multiple MCP servers for extended functionality
- **User Authentication**: Secure JWT-based authentication with user management
- **Tool Permissions**: Fine-grained control over which tools agents can execute
- **Modern UI**: Beautiful Vue.js frontend with Tailwind CSS and Element Plus
- **Real-time Updates**: WebSocket support for live agent interactions
- **OAuth Integration**: Support for Figma and Notion API integrations
- **Database Support**: PostgreSQL with SQLAlchemy ORM

## 📚 Documentation

For detailed configuration guides, please see:

- [**Supported MCP Servers**](docs/guide/mcp-servers.md): Setup guide for Figma, GitHub, Notion, and custom servers.
- [**Supported Providers**](docs/guide/llm-providers.md): Configuration for Gemini, Pinecone, and AWS Bedrock.
- [**Expansion Guide**](docs/dev/expansion.md): How to add new MCP servers, LLM providers, and features.
- [**Prompts & Persona**](docs/dev/agent-core.md): Customizing the agent's behavior and system prompts.



## 🎥 Walkthrough





## 📁 Project Structure

```text
ai agent mcp/
├── server/                 # FastAPI backend server
│   ├── app/
│   │   ├── routes/         # API endpoints
│   │   ├── services/       # Business logic
│   │   ├── models/         # Database models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── auth/           # Authentication logic
│   │   ├── database/       # Database configuration
│   │   └── core/           # Core utilities
│   ├── pyproject.toml      # Python dependencies (uv)
│   └── requirements.txt    # Alternative pip dependencies
│
└── client/               # Vue.js frontend
    ├── src/
    │   ├── view/       # Vue pages
    │   ├── components/ # Reusable Vue components
    │   ├── router.js   # Vue Router configuration
    │   └── main.js     # App entry point
    └── package.json    # Node.js dependencies
├── docker-compose.yml   # Docker orchestration
├── LICENSE              # MIT License
└── CONTRIBUTING.md      # Contribution guidelines
```

## Prerequisites

Before you begin, ensure you have the following installed:

*   **Python 3.12+**: The server backend is built with FastAPI.
*   **Node.js 20+**: The client frontend uses Vue 3 and Vite.
*   **Docker (Optional)**: Recommended for the easiest setup experience.

## Quick Start (Docker)

If you have Docker installed, you can get the entire stack running in one command.

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/ramblinghermit0403/agent_bridge.git
    cd agent_bridge
    ```

2.  **Configure Environment Variables**:
    Before starting, create a `.env` file in the `server/` directory:
    ```bash
    cp server/.env.example server/.env
    ```
    Edit `server/.env` and add your `GOOGLE_API_KEY` or `OPENAI_API_KEY`.

3.  **Start the services**:
    ```bash
    docker-compose up --build
    ```
    *   **Client (Frontend)**: `http://localhost:80`
    *   **Server (Backend API)**: `http://localhost:8001`
    *   **Database (PostgreSQL)**: `localhost:5432`

4.  **Access the application**:
    Open your browser to [http://localhost](http://localhost).

## Manual Installation (Development)

For developers who want to modify the code, running the services manually is recommended.

### 1. Backend Setup (Server)

The server handles the agent logic, database, and tool execution.

1.  **Navigate to the server directory**:
    ```powershell
    cd server
    ```

2.  **Create a virtual environment**:
    We recommend using `uv` or `venv`.
    ```powershell
    uv venv
    # or
    python -m venv .venv
    ```

3.  **Activate the environment**:
    ```powershell
    .venv\Scripts\activate.ps1
    ```

4.  **Install dependencies**:
    ```powershell
    uv pip install -r requirements.txt
    # or
    pip install -r requirements.txt
    ```

5.  **Configure Environment Variables**:
    Create a `.env` file from the example:
    ```powershell
    cp .env.example .env
    ```
    Edit `.env` and configure the required keys:
    *   `GOOGLE_API_KEY` - For Gemini models.
    *   `OPENAI_API_KEY` - For OpenAI models (optional).
    *   `DATABASE_URL` - PostgreSQL connection string (optional, defaults to SQLite for local dev).
    *   `PINECONE_API_KEY` - For vector search (optional).

6.  **Run the Server**:
    ```powershell
    uv run uvicorn app.main:app --reload --port 8001
    ```
    The API will be available at `http://localhost:8001`.

### 2. Frontend Setup (Client)

The client provides the web interface for chatting and managing agents.

1.  **Navigate to the client directory**:
    ```powershell
    cd client
    ```

2.  **Install dependencies**:
    ```powershell
    npm install
    ```

3.  **Run the Development Server**:
    ```powershell
    npm run dev
    ```
    The application will be available at `http://localhost:5173`.

## 🔧 Configuration

### MCP Server Configuration

To connect MCP servers, edit the `servers.json` file in the server directory. Then run the bootstrap script:
```bash
python bootstrap_servers.py your-email@example.com
```

This will automatically register or update all servers defined in the configuration file.

### Database Migrations

The application automatically creates database tables on startup. For manual migrations or schema updates, use SQLAlchemy migrations.

## Usage

### First Run & Authentication

1.  **Create your first user**:
    When you first open the app, you will be prompted to log in. Since there are no users yet, you may need to use the registration endpoint or seed script (if available).
    *   *Default Dev User*: `admin@example.com` / `password` (check `server/scripts` if applicable).

2.  **Connect a Provider**:
    Go to **Settings** -> **AI Providers** and ensure you have at least one LLM provider configured (Gemini or OpenAI).

3.  **Start Chatting**:
    Navigate to the **Chat** page and select an agent to start a new conversation!

## 🛠️ Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **LangChain**: AI agent orchestration
- **SQLAlchemy**: ORM for database operations
- **PostgreSQL**: Primary database
- **Redis**: Caching and pub/sub
- **Modular Architecture**: Clean separation of concerns (Auth, Streaming, Agent Logic).
- **Documentation**:
  - [Supported MCP Servers](docs/MCP_SERVERS.md) (Figma, Notion, GitHub)
  - [Supported Providers](docs/PROVIDERS.md) (Gemini, Pinecone)
- **Pydantic**: Data validation
- **JWT**: Authentication tokens
- **MCP**: Model Context Protocol integration

### Frontend
- **Vue.js 3**: Progressive JavaScript framework
- **Vue Router**: Client-side routing
- **Tailwind CSS**: Utility-first CSS framework
- **Element Plus**: Vue 3 component library
- **Axios**: HTTP client
- **FontAwesome**: Icon library
- **Vite**: Build tool and dev server

## 🔐 Security

- JWT-based authentication with secure token handling
- Password hashing with bcrypt
- CORS middleware for cross-origin requests
- Environment-based configuration for sensitive data
- Tool permission system for controlled agent actions

## 🔌 Adding LLM Providers

1. Duplicate `backend/app/services/Agent/providers/openai.py`
2. Implement your provider logic
3. Register it in `backend/app/services/Agent/llm_factory.py` in the `PROVIDER_MAP` variable.

## 📝 API Endpoints

### Authentication
- `POST /auth/signup` - Create new user account
- `POST /auth/login` - Authenticate user
- `GET /auth/me` - Get current user info

### Agent
- `POST /agent/chat` - Send message to agent
- `GET /agent/history` - Get conversation history

### Settings
- `GET /settings` - Get user settings
- `PUT /settings` - Update settings
- `GET /settings/oauth-clients` - List OAuth integrations

### Tool Permissions
- `GET /tool-permissions` - List tool permissions
- `POST /tool-permissions` - Grant tool permission
- `DELETE /tool-permissions/{id}` - Revoke permission

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests to us.

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Powered by [LangChain](https://www.langchain.com/)
- UI components from [Element Plus](https://element-plus.org/)
- Styled with [Tailwind CSS](https://tailwindcss.com/)

## 📞 Support

For questions or issues, please open an issue on the repository or contact the development team.

---

**Happy Building! 🚀**
