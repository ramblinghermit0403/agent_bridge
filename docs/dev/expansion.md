# System Expansion Guide

This guide explains how to extend the Agent Bridge platform with new capabilities.

## 1. Adding New MCP Servers
To add a new MCP server (e.g., SQLite, Slack, Gmail):

1.  **Define Configuration**:
    Add your server to `server/servers.json`:
    ```json
    {
      "presets": {
        "My New Server": {
            "server_url": "http://localhost:8002/sse",
            "description": "Connects to X service.",
            "requires_oauth": false,
            "show_advanced": true
        }
      }
    }
    ```

2.  **Add Auth (If needed)**:
    If the server uses OAuth, set `requires_oauth: true` and fill in the fields.
    ```json
    "My Secure Server": {
        "server_url": "...",
        "requires_oauth": true,
        "authorization_url": "https://provider.com/oauth/authorize",
        "token_url": "https://provider.com/oauth/token",
        "client_id": "YOUR_CLIENT_ID" 
    }
    ```

3.  **Environment Variables**:
    Add any required Client IDs/Secrets to `server/.env`.

---

## 2. Adding New LLM Providers
The system uses a factory pattern for LLM instantiation.

1.  **Create Provider Implementation**:
    Duplicate `server/app/services/Agent/providers/openai.py` (or similar) into a new file, e.g., `my_provider.py`.
    Implement the `get_llm(model_name)` function.

2.  **Register Provider**:
    Edit `server/app/services/Agent/llm_factory.py`:
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

*   **New Views**: Add `.vue` files in `client/src/view/`.
*   **Routes**: Register new paths in `client/src/router.js`.
*   **API Calls**: Use the global `axios` instance (configured with interceptors) to call backend endpoints.

## 4. Database Schema Changes
1.  **Modify Models**: Edit files in `server/app/models/`.
2.  **Migrations**:
    We currently use `FastAPI` startup events to `create_all` tables.
    For production changes, rely on `alembic` (not currently configured, but recommended for future growth).
