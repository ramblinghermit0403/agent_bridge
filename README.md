# Agent Bridge

**Agent Bridge** is a powerful AI agent platform that connects LangChain agents with MCP (Model Context Protocol) servers, enabling intelligent automation and tool execution through a modern web interface.

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

- [**Supported MCP Servers**](docs/MCP_SERVERS.md): Setup guide for Figma, GitHub, Notion, and custom servers.
- [**Supported Providers**](docs/PROVIDERS.md): Configuration for Gemini, Pinecone, and AWS Bedrock.
- [**Expansion Guide**](docs/EXPANSION.md): How to add new MCP servers, LLM providers, and features.
- [**Prompts & Persona**](docs/PROMPTS.md): Customizing the agent's behavior and system prompts.



## 🎥 Demo

[![Agent Bridge Walkthrough](http://img.youtube.com/vi/7w0LObDVEyA/0.jpg)](https://youtu.be/7w0LObDVEyA)

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

## 🚀 Getting Started

### Prerequisites

- **Python**: 3.12 or higher
- **Node.js**: 20.19.0 or 22.12.0+
- **PostgreSQL**: For database storage
- **Redis**: For caching and real-time features (optional)

### Backend Setup

1. **Navigate to the server directory**
   ```bash
   cd server
   ```

2. **Install dependencies using uv (recommended)**
   ```bash
   pip install uv
   uv sync
   ```
   
   Or using pip:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   
   Create a `.env` file in the `server` directory with the following:
   ```env
   # Database
   DATABASE_URL=postgresql://user:password@localhost:5432/agentbridge
   
   # JWT Authentication
   SECRET_KEY=your-secret-key-here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   
   # Redis (optional)
   REDIS_URL=redis://localhost:6379
   
   # LangChain / AI
   GOOGLE_API_KEY=your-google-api-key
   
   # OAuth (optional)
   FIGMA_CLIENT_ID=your-figma-client-id
   FIGMA_CLIENT_SECRET=your-figma-client-secret
   NOTION_CLIENT_ID=your-notion-client-id
   NOTION_CLIENT_SECRET=your-notion-client-secret
   ```

4. **Run the backend server**
   ```bash
   uv run uvicorn app.main:app --reload --port 8001
   ```
   
   The API will be available at `http://localhost:8001`
   
   Interactive API docs: `http://localhost:8001/docs`

### Frontend Setup

1. **Navigate to the client directory**
   ```bash
   cd client
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Run the development server**
   ```bash
   npm run dev
   ```
   
   The application will be available at `http://localhost:5173`

4. **Build for production**
   ```bash
   npm run build
   ```

### Run with Docker

1. **Ensure Docker and Docker Compose are installed.**

2. **Configure environment variables:**
   Copy `.env.example` to `.env` in both `server/` and `client/AgentBridge/` directories and update the values.

3. **Run the services:**
   ```bash
   docker-compose up --build
   ```

   The backend will be available at `http://localhost:8001` and the frontend at `http://localhost:80`.

## 🔧 Configuration

### MCP Server Configuration

To connect MCP servers, edit the `servers.json` file in the server directory. Then run the bootstrap script:
```bash
python bootstrap_servers.py your-email@example.com
```

This will automatically register or update all servers defined in the configuration file.

### Database Migrations

The application automatically creates database tables on startup. For manual migrations or schema updates, use SQLAlchemy migrations.

## 📖 Usage

### Authentication

1. **Sign Up**: Create a new account through the frontend UI
2. **Login**: Authenticate to receive a JWT token
3. **API Access**: Use the token in the `Authorization: Bearer <token>` header

### Agent Interaction

1. Navigate to the **Dashboard** after logging in
2. Configure your **Tool Permissions** in Settings
3. Interact with the AI agent through the chat interface
4. The agent can execute tools based on your permissions

### Tool Management

- **View Available Tools**: See all tools from connected MCP servers
- **Grant Permissions**: Control which tools the agent can use
- **Execute Tools**: Run tools manually or let the agent decide

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
