# API Reference

The Agent Bridge exposes a RESTful API built with FastAPI.

## Interactive Documentation
When the server is running locally, you can access the interactive Swagger UI:

**`http://localhost:8001/docs`**


## Authentication
Most endpoints require a Bearer Token.
*   **Header**: `Authorization: Bearer <token>`
*   **Login**: `POST /api/auth/token` returns the token.

## Key Endpoints

### Agent Interactions

#### `GET /api/agent/ask` (SSE Stream)
Triggers a new agent run and streams the response via Server-Sent Events.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `token` | string | Yes | Bearer authentication token |
| `session_id` | string | No | Conversation ID (auto-generated if omitted) |
| `prompt` | string | Yes | The user's message |
| `provider` | string | No | LLM provider (`gemini`, `openai`). Default: `gemini` |
| `model` | string | No | Model name. Default: `gemini-2.5-flash` |
| `resume` | boolean | No | Resume an interrupted session |

**SSE Event Types:**
*   `token` - Text chunk from the LLM
*   `tool_start` - Agent starting a tool call
*   `tool_end` - Tool call completed
*   `error` - An error occurred

---

#### `GET /api/agent/chats`
Returns a list of all conversations for the current user.

#### `GET /api/agent/chat/{chat_id}/messages`
Returns all messages in a specific conversation.

#### `DELETE /api/agent/chat/{chat_id}`
Deletes a conversation.

### MCP Management

#### `GET /api/mcp/settings`
Returns a list of all configured MCP servers and their connection status.

#### `POST /api/mcp/settings`
Adds a new MCP server configuration.

#### `POST /api/mcp/settings/{setting_id}/reconnect`
Forces a reconnection to a specific MCP server.

### Settings & Providers

#### `GET /api/providers/`
List available LLM providers and their supported models.

#### `GET /api/user/me`
Returns the current user's profile information.
