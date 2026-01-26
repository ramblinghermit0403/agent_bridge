# System Expansion Guide

This guide explains how to extend the Agent Bridge platform with new capabilities.

## 1. Adding New MCP Servers
To add a new MCP server (e.g., SQLite, Slack, Gmail):

1.  **Define Configuration**:
    Add your server to `backend/app/core/preapproved_servers.py`:
    ```python
    {
        "server_name": "My New Server",
        "server_url": "http://localhost:8002/sse",
        "description": "Connects to X service.",
        "type": "remote" # or "local"
    }
    ```

2.  **Add Auth (If needed)**:
    If the server uses OAuth, add the `oauth_config` block:
    ```python
    "requires_auth": True,
    "oauth_config": {
        "client_id": os.environ.get("MY_SERVER_CLIENT_ID"),
        "authorization_url": "...",
        "token_url": "...",
        # ...
    }
    ```

3.  **Environment Variables**:
    Add any required Client IDs/Secrets to `backend/.env`.

---

## 2. Adding New LLM Providers
The system uses a factory pattern for LLM instantiation.

1.  **Create Provider Implementation**:
    Duplicate `backend/app/services/Agent/providers/openai.py` (or similar) into a new file, e.g., `my_provider.py`.
    Implement the `get_llm(model_name)` function.

2.  **Register Provider**:
    Edit `backend/app/services/Agent/llm_factory.py`:
    ```python
    # Import your new provider
    from .providers import my_provider

    PROVIDER_MAP = {
        # ... existing ...
        "my_provider": my_provider.get_llm
    }
    ```

3.  **Use It**:
    Update your agent configuration or `.env` to select the new provider.

---

## 3. Extending the Frontend
The frontend is a Vue.js 3 application.

*   **New Views**: Add `.vue` files in `frontend/src/view/`.
*   **Routes**: Register new paths in `frontend/src/router.js`.
*   **API Calls**: Use the global `axios` instance (configured with interceptors) to call backend endpoints.

## 4. Database Schema Changes
1.  **Modify Models**: Edit files in `backend/app/models/`.
2.  **Migrations**:
    We currently use `FastAPI` startup events to `create_all` tables.
    For production changes, rely on `alembic` (not currently configured, but recommended for future growth).
