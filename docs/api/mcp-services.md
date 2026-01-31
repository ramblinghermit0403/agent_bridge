# MCP Services API

This module implements the client-side logic for the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction), allowing the AI Agent to connect to, discover, and execute tools on remote servers (like Notion, GitHub, or local dev tools).

Location: `backend/app/services/mcp/`

---

## MCP Connector

**File**: [`connector.py`](https://github.com/ramblinghermit0403/agent_bridge/blob/main/backend/app/services/mcp/connector.py)



The `MCPConnector` class is the heavy lifter. It manages the persistent connection lifecycle, handling the complexities of SSE (Server-Sent Events) or HTTP streams, and ensuring authentication remains valid.

### Class: `MCPConnector`

```python
class MCPConnector:
    def __init__(
        self, 
        server_url: str, 
        credentials: Optional[str] = None,
        oauth_config: Optional[Dict] = None,
        ...
    )
```

**Key Responsibilities:**
1.  **Session Management**: Maintains a persistent `ClientSession` using `mcp.client`. It automatically detects whether to use SSE or HTTP transport.
2.  **Header Injection**: Inject auth tokens (e.g., `Authorization: Bearer <token>`, `X-Figma-Token`) based on the server domain.
3.  **Automatic Retries**: Wraps operations in `_execute_with_retry` to handle network blips.

### Core Methods

#### `run_tool`
```python
async def run_tool(self, tool_name: str, parameters: dict) -> Any
```
Executes a specific tool on the remote server.
- **Retry Policy**: If execution fails with a 401 (Unauthorized), it automatically attempts to refresh the OAuth token and retry the execution *once*.
- **Timeout**: Enforces a 60-second timeout to prevent the agent from hanging indefinitely on slow tools.

#### `list_tools`
```python
async def list_tools(self) -> List[Dict[str, Any]]
```
Fetches the `tools/list` from the server.
- **Caching**: Implements a module-level `_TOOLS_CACHE` to avoid repeated network calls for tool definitions during the same server lifecycle.

---

## Token Manager

**File**: [`token_manager.py`](https://github.com/ramblinghermit0403/agent_bridge/blob/main/backend/app/services/mcp/token_manager.py)



A specialized utility for handling OAuth2 token lifecycles. It ensures the agent never fails mid-task due to an expired access token.

### `refresh_oauth_token`

```python
async def refresh_oauth_token(
    server_name: str, 
    credentials: dict, 
    oauth_config: dict
) -> Optional[dict]
```

Performs a standard `refresh_token` grant exchange:
1.  Extracts the `refresh_token` from current credentials.
2.  POSTs to the provider's `token_url`.
3.  Calculates the new `expires_at` timestamp based on `expires_in` response (defaulting to 1 hour if unspecified).

### `is_token_expired`

```python
def is_token_expired(
    credentials: dict, 
    buffer_seconds: int = 300
) -> bool
```

**Logic**: Returns `True` if `now >= (expires_at - 300)`.
- **Why the buffer?** We proactively treat a token as "expired" 5 minutes early. This prevents race conditions where a token might be valid *now* but expires 2 seconds later while the request is in flight.

---

## Authentication

**File**: [`auth.py`](https://github.com/ramblinghermit0403/agent_bridge/blob/main/backend/app/services/mcp/auth.py)



Handles the "Calibration Phase" - the initial handshake when a user adds a new MCP server.
- **`exchange_code_for_token`**: Swaps the temporary OAuth authorization code for the initial Access/Refresh token pair.
- **`init_connection`**: Verifies the connection works immediately after setup by attempting a "ping" or listing tools.
