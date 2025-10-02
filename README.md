# Agent Bridge

Agent Bridge acts as an intelligent orchestrator. It interprets your request, selects the right tool from your connected MCP Servers, and uses the tool's output to generate a final, comprehensive answer.

You → Agent Bridge (LLM) → Your MCP Server

## Powerful Use Cases

Automated BI
"Generate a sales report for Q2 and email it to the management team."

DevOps & Admin
"Check the status of all production servers and restart any that are offline."

Support Automation
"Find Jane Doe's latest order and issue a refund for the 'Pro Plan'."





---

## Project Structure

```
fastapi-mcp-langflow/
├── app/
│   ├── main.py
│   ├── mcp_connector.py
│   ├── langchain_agent.py
│   ├── config.py
│   └── auth/
│       └── oauth2.py
├── langflow_project/      # Mount your Langflow project here
├── requirements.txt
├── README.md
└── frontend/
    └── AgentBridge/
        └── src/
            └── components/
                └── agent/
                    └── AIagent.vue
```

---

## Features

- **FastAPI Backend**: Async API with JWT authentication, PostgreSQL (asyncpg), and modular structure.
- **Vue 3 Frontend**: Built with Vite, supports environment variables via `.env` and `import.meta.env`.
- **Langflow Integration**: Easily mount and use Langflow projects.
- **OAuth2/JWT Auth**: Secure endpoints using JWT tokens.
- **Pinecone & Google API**: Ready for vector DB and Google integrations.

---

## Setup

### 1. Backend

#### Install dependencies

```sh
cd backend
python -m venv venv
venv\Scripts\activate  # On Windows
pip install -r requirements.txt
```

#### Configure environment

Create a `.env` file in `backend/`:

```
DATABASE_URL="postgresql+asyncpg://<user>:<password>@<host>/<db>"
GOOGLE_API_KEY="your-google-api-key"
PINECONE_API_KEY="your-pinecone-api-key"
PINECONE_ENVIRONMENT="your-pinecone-env"
PINECONE_INDEX_NAME="your-index"
FORCE_REINDEX="false"
```

#### Run FastAPI server

```sh
uvicorn app.main:app --reload
```

---

### 2. Frontend

#### Install dependencies

```sh
cd frontend/AgentBridge
npm install
```

#### Configure environment

Create a `.env` file in `frontend/AgentBridge/`:

```
VITE_API_URL=http://localhost:8000
```

#### Run Vite dev server

```sh
npm run dev
```

---

## Usage

- Access the frontend at [http://localhost:5173](http://localhost:5173) (default Vite port).
- Backend API runs at [http://localhost:8000](http://localhost:8000).
- Authenticate via `/login` endpoint to receive a JWT token.
- Use the `/user` endpoint to get current user info (requires Bearer token).

---

## Security

- **Never commit secrets or API keys.**
- Use environment variables for all credentials.
- Change the `SECRET_KEY` in production.

---

## License

MIT License

---

## Credits

- [FastAPI](https://fastapi.tiangolo.com/)
- [Vue.js](https://vuejs.org/)
- [Langflow](https://github.com/langflow-ai/langflow)
- [Pinecone](https://www.pinecone.io/)
