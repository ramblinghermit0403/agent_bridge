# API & Architecture Overview

The Agent Bridge backend is built with **FastAPI** and follows a modular service-oriented architecture.

## Core Modules

| Module | Description |
| :--- | :--- |
| **Agent Services** | Handles the LLM orchestration, LangGraph workflows, and dynamic tool binding. |
| **MCP Services** | Manages connections to Model Context Protocol servers, including OAuth authentication and tool discovery. |
| **Database Models** | SQLAlchemy models for persistence (Users, Settings, Permissions). |
| **Auth** | JWT-based authentication and security utilities. |

## Data Flow

1. **User Request**: Client sends a chat message to `POST /chat`.
2. **Agent Initialization**: `agent_factory` builds a user-specific graph with tools relevant to the user's connected MCP servers.
3. **Graph Execution**: The LangGraph workflow (`agent_orchestrator`) executes.
   - **Agent Node**: LLM generates a response or tool call.
   - **Permissions Check**: If a tool is called, permissions are checked against `tool_permissions`.
   - **Human Review**: If required, execution pauses for user approval.
   - **Tool Execution**: Approved tools are executed via `MCPConnector`.
4. **Response**: Final answer is streamed back to the client.

## Directory Structure
```
backend/app/
├── services/
│   ├── agent/       # LLM & Graph Logic
│   └── mcp/         # MCP Server Connections
├── models/          # Database Schema
├── routes/          # API Endpoints
└── auth/            # Security & JWT
```
