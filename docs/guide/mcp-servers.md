# Connecting MCP Servers

## What is MCP?

The **Model Context Protocol (MCP)** is an open standard that enables AI models to interact with external data and tools. Instead of building custom integrations for every tool (GitHub, Slack, Notion) into every AI model, MCP provides a universal language for connection.

In **Agent Bridge**, the server acts as an **MCP Client**. It connects to one or more **MCP Servers**, discovers their tools, and exposes them to the AI Agent.

## Adding a New MCP Server (Frontend)

### Step 1: Open Settings
1.  Click on **Settings** in the sidebar
2.  Navigate to the **Connections** tab

### Step 2: Choose a Preset (Optional)
Use the **Load Preset** dropdown to autofill settings for popular providers:
*   **Notion** - Official Notion MCP Server
*   **GitHub** - Official GitHub MCP Server

Selecting a preset will automatically fill in the Server Name, URL, and OAuth requirements.

### Step 3: Fill in Server Details
| Field | Description | Required |
|-------|-------------|----------|
| **Server Name** | A friendly name for this connection (e.g., "My GitHub") | Yes |
| **Server URL** | The HTTP(S) endpoint for the MCP server | Yes |
| **Description** | Notes about this server or its purpose | No |

### Step 4: Configure OAuth (If Required)
If the server requires authentication, toggle **Requires OAuth?** and fill in:

| Field | Description |
|-------|-------------|
| **Client ID** | Your OAuth application's Client ID |
| **Client Secret** | Your OAuth application's Client Secret |
| **Scope** | Permission scopes (e.g., `read:user`) |

> **Need credentials?** Refer to the official documentation for [Notion](https://developers.notion.com/docs/authorization) or [GitHub](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-an-oauth-app).


**Advanced Options** (toggle to reveal):
*   **Authorization URL** - Manual OAuth authorize endpoint
*   **Token URL** - Manual OAuth token endpoint

> Agent Bridge will attempt to discover these automatically from the Server URL.

### Step 5: Save
*   **Without OAuth**: Click **Test Connection** to verify, then **Save Connection**
*   **With OAuth**: Click **Authenticate & Connect** to open the OAuth popup

## Managing Existing Servers

From the **Connections** tab, you can:
*   **Configure** - View and manage individual tools (enable/disable)
*   **Reconnect** - Refresh tokens and verify connection
*   **Delete** - Remove the server configuration
*   **Toggle** - Enable/disable the server without deleting

---

## Connection Types (Technical)

### 1. Remote Servers (SSE/HTTP)
Remote servers run as independent web services. This is the **primary and recommended** method for connecting to all MCP servers.

**Example Preset (from `servers.json`):**
```json
{
  "presets": {
    "Notion": {
      "server_url": "https://mcp.notion.com/mcp",
      "description": "Official Notion MCP Server.",
      "requires_oauth": true
    }
  }
}
```

### 2. Local Servers (via HTTP Proxy)

> **Why HTTP, not Stdio?**  
> Agent Bridge is designed for **full containerization**. Running stdio-based MCP servers as subprocesses would break in Docker/Kubernetes environments. Instead, expose local MCP servers as HTTP endpoints.

**How It Works:**
1.  Run your local MCP server with an HTTP/SSE wrapper
2.  Expose it on a local port (e.g., `http://localhost:8002/sse`)
3.  Add it to Agent Bridge like any remote server

**Example: Exposing a Filesystem MCP Server**
```bash
npx @anthropic-ai/mcp-server-sse-adapter -- npx @modelcontextprotocol/server-filesystem /path/to/directory
```

Then add via the UI with URL: `http://localhost:8002/sse`

**Benefits:**
*   Container-friendly (Docker/Kubernetes)
*   Decoupled architecture
*   Consistent HTTP/SSE interface

---

## Pre-configured Server Presets

| Server | URL | OAuth Required |
|--------|-----|----------------|
| **Notion** | `https://mcp.notion.com/mcp` | Yes |
| **GitHub** | `https://api.githubcopilot.com/mcp/` | Yes |

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/mcp/settings/` | GET | List all configured servers |
| `/api/mcp/settings/` | POST | Add a new server |
| `/api/mcp/settings/{id}` | PATCH | Update a server |
| `/api/mcp/settings/{id}` | DELETE | Delete a server |
| `/api/mcp/settings/{id}/reconnect` | POST | Reconnect/refresh tokens |
| `/api/mcp/presets` | GET | Get available presets |
| `/api/mcp/test-connection` | POST | Test a server URL |

## Inspecting Servers

Use the CLI tool to debug connections:
```bash
python server/inspect_mcp.py <SERVER_URL>
```
