# How to Obtain OAuth Credentials (Client ID & Secret)

To connect Agent Bridge to a secure MCP server (like Notion, Figma, or a custom enterprise server), you need a **Client ID** and **Client Secret**. These credentials identify your Agent Bridge instance to the server.

There are two main ways to obtain them:

## 1. Manual Registration (Most Common)
For major SaaS platforms (Notion, GitHub, Figma, Google), you must register an "App" in their Developer Portal.

### Steps:
1.  **Go to the Developer Portal** of the service you want to connect.
    *   **Notion**: [Notion My Integrations](https://www.notion.so/my-integrations)
    *   **GitHub**: [GitHub OAuth Apps](https://github.com/settings/applications/new)
    *   **Figma**: [Figma My Apps](https://www.figma.com/developers/apps)
2.  **Create a New App/Integration**.
    *   Name: "Agent Bridge (Your Name)"
    *   Logo: (Optional)
3.  **Configure Redirect URI** (Critical).
    *   You must enter the callback URL of your Agent Bridge instance.
    *   **Local Development**: `http://localhost:8001/api/mcp/oauth/callback`
    *   **Production/Remote**: `https://<your-domain>/api/mcp/oauth/callback`
4.  **Copy Credentials**.
    *   Copy the **Client ID** and **Client Secret** and paste them into Agent Bridge.

---

## 2. Dynamic Client Registration (Advanced / Enterprise)
Some modern MCP servers and OAuth providers support **Dynamic Client Registration** (RFC 7591). This allows you to programmatically "ask" for a Client ID without visiting a website.

### How to Discover & Register:
1.  **Find the Discovery Endpoint**:
    *   Check `{server_url}/.well-known/oauth-authorization-server` 
    *   OR `{server_url}/.well-known/openid-configuration`
    
2.  **Check for `registration_endpoint`**:
    *   Look at the JSON response. If you see `"registration_endpoint": "https://..."`, the server supports dynamic registration.

3.  **Register your Client**:
    *   Send a POST request to the registration endpoint.
    *   **Example (cURL)**:
        ```bash
        curl -X POST https://api.myserver.com/register \
          -H "Content-Type: application/json" \
          -d '{
            "client_name": "Agent Bridge",
            "redirect_uris": ["http://localhost:8001/api/mcp/oauth/callback"],
            "grant_types": ["authorization_code", "refresh_token"],
            "scope": "read write" 
          }'
        ```
    *   **Response**:
        ```json
        {
           "client_id": "auto-generated-id",
           "client_secret": "auto-generated-secret",
           ...
        }
        ```
    *   Use these returned credentials in Agent Bridge.
