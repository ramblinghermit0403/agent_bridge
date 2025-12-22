import os
from dotenv import load_dotenv

load_dotenv()

preapproved_mcp_servers = [
    {
        "server_name": "Basic Math Server",
        "server_url": "http://localhost:8000/sse",
        "description": "A simple MCP server with tools for basic arithmetic and factorial calculations. (Run locally)",
        "type": "local"
    },
    {
        "server_name": "File and Data Server",
        "server_url": "http://localhost:8000/sse",
        "description": "Tools for reading, writing, and manipulating local files. (Run locally)",
        "type": "local"
    },
    {
        "server_name": "System Automation Server",
        "server_url": "http://localhost:8000/sse",
        "description": "Execute shell commands and manage environment variables. (Run locally)",
        "type": "local"
    },
    {
         "server_name": "Weather Server (Quickstart)",
         "server_url": "http://localhost:8000/sse",
         "description": "Official MCP quickstart weather server. (Run locally)",
         "type": "local"
    },
    {
        "server_name": "Figma",
        "server_url": "https://mcp.figma.com/mcp",
        "description": "Connect to Figma files to read design data.",
        "type": "remote",
        "requires_auth": True,
        "oauth_config": {
            "client_id": os.environ.get("FIGMA_CLIENT_ID"),
            "client_secret": os.environ.get("FIGMA_CLIENT_SECRET"),
            "authorization_url": "https://www.figma.com/oauth",
            "token_url": "https://api.figma.com/v1/oauth/token",
            "scope": "file_content:read,current_user:read",
            "redirect_uri": "http://localhost:8001/api/mcp/oauth/callback"
        }
    },
    {
        "server_name": "GitHub",
        "server_url": "https://api.githubcopilot.com/mcp/",
        "description": "Connect to GitHub Copilot MCP Server.",
        "type": "remote",
        "requires_auth": True,
        "oauth_config": {
            "client_id": os.environ.get("GITHUB_CLIENT_ID"),
            "client_secret": os.environ.get("GITHUB_CLIENT_SECRET"),
            "authorization_url": "https://github.com/login/oauth/authorize",
            "token_url": "https://github.com/login/oauth/access_token",
            "scope": "repo user",
            "redirect_uri": "http://localhost:8001/api/mcp/oauth/callback"
        }
    }
]
