# Getting Started

Welcome to **Agent Bridge**, a powerful platform for building, managing, and observing AI agents that can connect to your local and remote tools via the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/).

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

## First Run & Authentication

1.  **Create your first user**:
    When you first open the app, you will be prompted to log in. Since there are no users yet, you may need to use the registration endpoint or seed script (if available).
    *   *Default Dev User*: `admin@example.com` / `password` (check `server/scripts` if applicable).

2.  **Connect a Provider**:
    Go to **Settings** -> **AI Providers** and ensure you have at least one LLM provider configured (Gemini or OpenAI).

3.  **Start Chatting**:
    Navigate to the **Chat** page and select an agent to start a new conversation!
