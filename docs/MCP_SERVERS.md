# Supported MCP Servers

This agent supports the Model Context Protocol (MCP) to connect with various tools and data sources.

## Pre-Approved Servers
The platform comes with built-in configurations for the following servers.

### Remote Servers (OAuth Required)
These servers require OAuth authentication. The agent handles the auth flow (discovery, PKCE, token exchange) automatically.

| Server | Description | Auth Type |
| :--- | :--- | :--- |
| **Figma** | Read design files and comments. | OAuth 2.0 (PKCE) |
| **GitHub** | Repository access via Copilot MCP. | OAuth 2.0 (Device/Web) |
| **Notion** | Access pages and databases. | OAuth 2.0 |

### Local / Utility Servers
These run alongside the agent or are built-in for basic tasks.

| Server | Description | URL |
| :--- | :--- | :--- |
| **Basic Math** | Arithmetic and Factorial tools. | `http://localhost:8000/sse` |
| **File & Data** | Read/Write local files. | `http://localhost:8000/sse` |
| **System** | Shell commands & env vars. | `http://localhost:8000/sse` |
| **Weather** | Example weather tools. | `http://localhost:8000/sse` |

## Adding Custom Servers
You can add custom MCP servers dynamically via the API or by editing `backend/app/core/preapproved_servers.py`.

### Configuration Structure
```python
{
    "server_name": "My Custom Server",
    "server_url": "https://mcp.api.com/sse",
    "type": "remote",
    "requires_auth": True,
    "oauth_config": { ... }
}
```

## 🔐 Remote Server Registration (OAuth)

Remote MCP servers typically leverage OAuth 2.0 to securely access user data (e.g., your Figma files or Notion pages). This requires your Agent Bridge instance to be registered as an authorized "Application" with the provider.

### How to Obtain a Client ID

There are two main ways to register your application:

#### 1. Dynamic Client Registration (Recommended for Open Source)
Some MCP providers (like Figma and Notion) support RFC 7591 "Dynamic Client Registration". This allows you to programmatically register your local instance and receive a unique `Client ID` and `Secret` instantly.

We provide script examples for this:
1.  Navigate to `backend/examples/`.
2.  Run the registration script for your desired service:
    ```bash
    python backend/examples/register_figma_client.py
    ```
3.  The script will output `FIGMA_CLIENT_ID` and `FIGMA_CLIENT_SECRET`.
4.  Add these to your `backend/.env` file.

#### 2. Manual Registration (Developer Portal)
If dynamic registration fails or isn't supported (e.g., GitHub), you must register manually:

1.  Go to the **Developer Settings** of the service (e.g., GitHub Developer Settings).
2.  Create a **New OAuth App**.
3.  Set the **Redirect URI** to:
    ```
    http://localhost:8001/api/mcp/oauth/callback
    ```
4.  Copy the generated **Client ID** and **Client Secret**.
5.  Add them to your `backend/.env`.

### Use Case
Once configured, when a user tries to use a tool from that server (e.g., "Read Figma File"), the Agent Bridge will automatically:
1.  Detect that Auth is required.
2.  Redirect the user to the provider's login page using your `Client ID`.
3.  Exchange the returned code for an Access Token.
4.  Store the token securely for future requests.

