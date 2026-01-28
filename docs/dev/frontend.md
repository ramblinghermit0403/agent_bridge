# Frontend Development Guide

The client is a modern Single Page Application (SPA) built with **Vue 3** and **Vite**.

## Tech Stack
*   **Framework**: Vue 3 (Composition API, `<script setup>`)
*   **Build Tool**: Vite
*   **Styling**: Custom CSS + Element Plus (for complex components)
*   **State**: Pinia
*   **Router**: Vue Router

## Project Structure

```
client/
├── src/
│   ├── components/        # Reusable UI components
│   │   ├── agent/         # Agent-specific (Chat, Thoughts)
│   │   ├── settings/      # Settings forms
│   │   ├── login/         # Authentication components
│   │   └── library/       # Library/History components
│   ├── view/              # Main page views (Home, Chat, Settings)
│   ├── assets/            # Static assets (CSS, images)
│   ├── main.js            # Vue app entry point
│   └── router.js          # Route definitions
```

## Key Concepts

### 1. Server-Sent Events (SSE)
We use SSE for real-time streaming of the agent's reasoning and responses.
*   **Endpoint**: `GET /api/agent/ask` with query parameters.
*   **Events**:
    *   `token` - Text chunk from the LLM.
    *   `tool_start` - Agent starting a tool call.
    *   `tool_end` - Tool call completed.
    *   `error` - An error occurred.
*   **Store**: Pinia stores accumulate these events to reconstruct the message history.

### 2. Authentication
Auth is handled via Bearer tokens.
*   **Store**: User session is managed in a Pinia store.
*   **Token Attachment**: Tokens are passed as query parameters to SSE endpoints, and as headers to REST endpoints.

### 3. Theming
Styles are defined in `src/assets/`. To customize the theme, edit the CSS files directly.

## Common Tasks

### Adding a New Page
1.  Create `src/view/NewPage.vue`.
2.  Add a route in `src/router.js`.
3.  Add a navigation link in the Sidebar component.

### Adding a New API Call
1.  Define the function in the appropriate service file or component.
2.  Call it from your component or store action.

---

## Core Components

The application is built from several key reusable components located in `client/src/components`.

### 1. AIagent (`agent/AIagent.vue`)
The primary chat interface. It handles the entire lifecycle of a conversation session.

*   **Key Responsibilities**:
    *   **SSE streaming**: Connects to `/ask/stream` to receive real-time tokens and tool events.
    *   **Message Rendering**: Displays user inputs, agent responses (Markdown), and scratchpad thoughts.
    *   **State Management**: Tracks `isAgentProcessing`, `isTyping`, and current `sessionId`.
    *   **Model Selection**: Fetches and allows switching between available LLM providers.

### 2. ToolPermissionMessage (`agent/ToolPermissionMessage.vue`)
A specialized interactive bubble that appears when the Agent requests permission to execute a sensitive tool.

*   **Props**:
    *   `toolName` (String): Name of the tool (e.g., `github_create_issue`).
    *   `serverName` (String): Origin server.
    *   `payload` (Object): The arguments the agent wants to pass to the tool.
    *   `approvalId` (String): Unique ID for the approval request.
*   **Events**:
    *   `@approve`: Emitted when user clicks "Allow Once" or "Always Allow".
    *   `@deny`: Emitted when user clicks "Deny".

### 3. ServerConfigModal (`settings/ServerConfigModal.vue`)
A configuration dialog for managing specific MCP servers.

*   **Props**:
    *   `isOpen` (Boolean): Controls visibility.
    *   `serverId` (Number): ID of the server setting to configure.
*   **Features**:
    *   **Tool Toggles**: Enable/Disable specific tools for a server.
    *   **Approval Management**: View and revoke "Always Allow" permissions.
    *   **Status Indicators**: Shows connection status and tool count.
