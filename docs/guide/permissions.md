# Tool Permissions & Approvals

Agent Bridge includes a powerful permission system that gives you control over what tools the AI agent can use.

## Overview

There are two layers of permission control:

1. **Tool Permissions** - Enable or disable specific tools from an MCP server
2. **Tool Approvals** - Control whether the agent needs your approval before executing a tool

## 1. Tool Permissions (Enable/Disable)

You can selectively enable or disable individual tools from any connected MCP server.

### How It Works
*   Navigate to **Settings** > **Connections**
*   Click on an MCP server to expand its tools
*   Toggle each tool on or off

### Use Cases
*   Disable dangerous tools (e.g., `delete_file`) while keeping others active
*   Limit agent capabilities for specific use cases
*   Test specific tool integrations in isolation

### API Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/mcp/settings/{server_id}/tools` | GET | List all tools with enabled status |
| `/api/mcp/settings/{server_id}/tools/{tool_name}` | PATCH | Toggle a tool's enabled state |

## 2. Tool Approvals (Human-in-the-Loop)

Before the agent executes certain tools, it can pause and ask for your approval. This is the "Human-in-the-Loop" feature.

### Approval Types

| Type | Behavior |
|------|----------|
| **`always`** | Tool runs automatically without asking |
| **`once`** | Ask once, then auto-approve for 1 hour |
| **`never`** | Always ask before running this tool |

### How It Works
1.  The agent decides to call a tool (e.g., `create_github_issue`)
2.  The system checks your approval preferences for that tool
3.  If approval is required, the agent **pauses** and sends you a prompt
4.  You approve or deny the action
5.  The agent resumes (or reports the denial)

### Setting Approvals
In the chat interface, when the agent asks for permission, you can choose:
*   **Allow Once** - Approve this specific call
*   **Always Allow** - Never ask again for this tool
*   **Deny** - Reject this action

### API Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/tool-approvals` | GET | List all your approval preferences |
| `/api/tool-approvals` | POST | Create or update an approval preference |
| `/api/tool-approvals/{tool_name}` | DELETE | Remove an approval preference |

## Architecture

The permission system is implemented in the LangGraph agent orchestrator:

```
Agent decides to call tool
        ↓
[route_tools] checks approval status
        ↓
   ┌────┴────┐
   ↓         ↓
Approved   Needs Review
   ↓         ↓
Execute   [human_review_node] → Pause Graph
   ↓         ↓
Resume ←──────┘
```

**Key Files:**
*   `server/app/routes/tool_permissions.py` - API endpoints
*   `server/app/services/agent/agent_orchestrator.py` - Graph logic
*   `server/app/services/security/permissions.py` - Approval checking logic
