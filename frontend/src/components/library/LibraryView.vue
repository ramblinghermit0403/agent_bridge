<template>
  <div class="library-view">
    <div class="library-header">
      <h1 class="library-title">Server Library</h1>
      <p class="library-description">
        Manage your connected MCP servers and explore pre-built examples
      </p>
    </div>

    <!-- Remote Servers Section -->
    <div class="connected-servers-section">
      <h2 class="section-title">Remote Servers</h2>
      <p class="section-description">Connect to remote MCP servers</p>
      
      <div class="connected-servers-grid">
        <router-link 
          v-for="server in remoteServers"
          :key="server.type"
          to="/settings"
          class="connected-server-card"
        >
          <div class="server-icon" :class="`${server.type}-icon`">
            <!-- GitHub Icon -->
            <svg v-if="server.type === 'github'" xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
            </svg>
            <!-- Notion Icon -->
            <svg v-else-if="server.type === 'notion'" xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
              <path d="M4.459 4.208c.746.606 1.026.56 2.428.466l13.215-.793c.28 0 .047-.28-.046-.326L17.86 1.968c-.42-.326-.981-.7-2.055-.607L3.01 2.295c-.466.046-.56.28-.374.466zm.793 3.08v13.904c0 .747.373 1.027 1.214.98l14.523-.84c.841-.046.935-.56.935-1.167V6.354c0-.606-.233-.933-.748-.887l-15.177.887c-.56.047-.747.327-.747.933zm14.337.745c.093.42 0 .84-.42.888l-.7.14v10.264c-.608.327-1.168.514-1.635.514-.748 0-.935-.234-1.495-.933l-4.577-7.186v6.952L12.21 19s0 .84-1.168.84l-3.222.186c-.093-.186 0-.653.327-.746l.84-.233V9.854L7.822 9.76c-.094-.42.14-1.026.793-1.073l3.456-.233 4.764 7.279v-6.44l-1.215-.139c-.093-.514.28-.887.747-.933zM1.936 1.035l13.31-.98c1.634-.14 2.055-.047 3.082.7l4.249 2.986c.7.513.934.653.934 1.213v16.378c0 1.026-.373 1.634-1.68 1.726l-15.458.934c-.98.047-1.448-.093-1.962-.747l-3.129-4.06c-.56-.747-.793-1.306-.793-1.96V2.667c0-.839.374-1.54 1.447-1.632z"/>
            </svg>
          </div>
          <div class="server-info">
            <h3 class="server-name">{{ server.name }}</h3>
            <p class="server-description">{{ server.description }}</p>
          </div>
          <div class="server-arrow">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="9 18 15 12 9 6"></polyline>
            </svg>
          </div>
        </router-link>
      </div>
    </div>

    <hr />

    <!-- Example Servers Section -->
    <div class="example-servers-section">
      <h2 class="section-title">Example Servers</h2>
      <p class="section-description">Explore pre-built MCP servers and their source code</p>
    </div>

    <div class="server-cards-container">
      <a
        v-for="server in servers"
        :key="server.name"
        :href="server.githubUrl"
        target="_blank"
        class="server-card"
      >
        <h2 class="card-title">{{ server.name }}</h2>
        <p class="card-description">{{ server.description }}</p>
        <div class="card-footer">
          <span class="github-link">View on GitHub</span>
          <!-- external link icon -->
        </div>
      </a>
    </div>

    <hr />

    <div class="quick-start-guide">
      <h2 class="guide-title">How to Build an MCP Weather Server</h2>
      <p class="guide-intro">
        In the official MCP quickstart, you’ll create a simple weather-focused server that exposes two tools—<code>get_alerts</code>
        and <code>get_forecast</code>—which can then be connected to an MCP client such as Claude for Desktop :contentReference[oaicite:1]{index=1}.
      </p>

      <h3>Quick Start (Python)</h3>
      <ol>
        <li>
          Install the MCP Python SDK:
          <pre><code>uv init weather
cd weather

# Create virtual environment and activate it
uv venv
source .venv/bin/activate

# Install dependencies
uv add "mcp[cli]" httpx

# Create our server file
touch weather.py</code></pre>
        </li>
        <li>
          Create the server file (e.g., <code>weather_mcp_server.py</code>):
          <pre><code>
from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("weather")

# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"

async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string."""
    props = feature["properties"]
    return f"""
Event: {props.get('event', 'Unknown')}
Area: {props.get('areaDesc', 'Unknown')}
Severity: {props.get('severity', 'Unknown')}
Description: {props.get('description', 'No description available')}
Instructions: {props.get('instruction', 'No specific instructions provided')}

@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. CA, NY)
    """
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    if not data or "features" not in data:
        return "Unable to fetch alerts or no alerts found."

    if not data["features"]:
        return "No active alerts for this state."

    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n---\n".join(alerts)

@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    # First get the forecast grid endpoint
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data:
        return "Unable to fetch forecast data for this location."

    # Get the forecast URL from the points response
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)

    if not forecast_data:
        return "Unable to fetch detailed forecast."

    # Format the periods into a readable forecast
    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:5]:  # Only show next 5 periods
        forecast = f"""
{period['name']}:
Temperature: {period['temperature']}°{period['temperatureUnit']}
Wind: {period['windSpeed']} {period['windDirection']}
Forecast: {period['detailedForecast']}
"""
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='sse')
          </code></pre>
        </li>
        <li>
          Run your server:
          <pre><code>python weather_mcp_server.py</code></pre>
          The server will start and expose the two tools via MCP.
        </li>
        <li>
          Connect to the server from Claude for Desktop (or another MCP client):
          Then invoke `get_forecast` or `get_alerts` directly from your chat—MCP tools will show up for you to call.
        </li>
      </ol>

      <p>
        This mirrors the official quickstart, where the weather server exposes these two tools and integrates with an MCP host like Claude :contentReference[oaicite:2]{index=2}.
      </p>

      <div class="guide-link-container">
        <a
          href="https://modelcontextprotocol.io/quickstart/server"
          class="guide-link"
          target="_blank"
        >
          View the Official MCP “Build an MCP Server” Guide
        </a>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";

const servers = ref([
  {
    name: "Basic Math Server",
    description: "A simple MCP server with tools for basic arithmetic and factorial calculations.",
    githubUrl: "https://github.com/ramblinghermit0403/mcp_server_sse/tree/main/math",
  },
  {
    name: "File and Data Server",
    description: "Tools for reading, writing, and manipulating local files (JSON, CSV).",
    githubUrl: "https://github.com/ramblinghermit0403/mcp_server_sse/tree/main/file_data_server",
  },
  {
    name: "System Automation Server",
    description: "Execute shell commands and manage environment variables.",
    githubUrl: "https://github.com/ramblinghermit0403/mcp_server_sse/tree/main/system_automation_server",
  },
]);

const remoteServers = ref([
  {
    name: 'GitHub',
    type: 'github',
    description: 'Access GitHub repositories and code'
  },
  {
    name: 'Notion',
    type: 'notion',
    description: 'Manage Notion pages and databases'
  }
]);
</script>

<style scoped>
/* Scoped styles for the LibraryView component */
.library-view {
  padding: 2rem;
  max-width: 1200px;
  height: 100vh;
  margin: 0 auto;
  font-family: Arial, sans-serif;
  color: #333;
  overflow-y: auto;
  padding-bottom: 110px ;
  /* Enable scrolling if content overflows */
}

.library-view::-webkit-scrollbar {
  width: 8px;
}

.library-view::-webkit-scrollbar-track {
  background: transparent;
}

.library-view::-webkit-scrollbar-thumb {
  background-color: var(--text-secondary);
  border-radius: 10px;
  border: 2px solid var(--bg-primary);
}

.library-view::-webkit-scrollbar-thumb:hover {
  background-color: var(--text-primary);
}

.library-header {
  margin-bottom: 2rem;
  text-align: center;
}

.library-title {
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--text-primary);
}

.library-description {
  font-size: 1.125rem;
  color: var(--text-secondary);
}

/* Connected Servers Section */
.connected-servers-section {
  margin-bottom: 3rem;
}

.section-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}

.section-description {
  font-size: 1rem;
  color: var(--text-secondary);
  margin-bottom: 1.5rem;
}

.connected-servers-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
}

.connected-server-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 1.25rem;
  text-decoration: none;
  color: inherit;
  transition: transform 0.2s, box-shadow 0.2s, background-color 0.2s;
  cursor: pointer;
}

.connected-server-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  background-color: var(--bg-primary);
}

.server-icon {
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.github-icon {
  background-color: #24292e;
  color: white;
}

.notion-icon {
  background-color: white;
  color: black;
  border: 1px solid var(--border-color);
}

.server-info {
  flex-grow: 1;
}

.server-name {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.25rem 0;
}

.server-description {
  font-size: 0.875rem;
  margin: 0;
  color: var(--text-secondary);
}

.server-arrow {
  flex-shrink: 0;
  color: var(--text-secondary);
}

.no-servers-message {
  grid-column: 1 / -1;
  text-align: center;
  padding: 3rem 2rem;
  background-color: var(--bg-secondary);
  border: 1px dashed var(--border-color);
  border-radius: 12px;
}

.no-servers-message p {
  color: var(--text-secondary);
  margin-bottom: 1rem;
  font-size: 1rem;
}

.connect-button {
  display: inline-block;
  padding: 0.75rem 1.5rem;
  background-color: var(--accent-color);
  color: white;
  text-decoration: none;
  border-radius: 8px;
  font-weight: 600;
  transition: background-color 0.2s;
}

.connect-button:hover {
  background-color: #0056b3;
}

/* Example Servers Section */
.example-servers-section {
  margin-bottom: 1.5rem;
}

.server-cards-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

.server-card {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 1.5rem;
  text-decoration: none;
  color: inherit;
  transition: transform 0.2s, box-shadow 0.2s, background-color 0.2s;
}

.server-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
  background-color: var(--bg-primary);
}

.card-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}

.card-description {
  font-size: 1rem;
  color: var(--text-secondary);
  flex-grow: 1;
}

.card-footer {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 1rem;
  font-weight: 500;
  color: var(--accent-color);
}

.card-footer svg {
  color: var(--accent-color);
}

.quick-start-guide {
  margin-top: 3rem;
  padding: 2rem;
  background-color: var(--bg-secondary);
  border-radius: 12px;
  border: 1px solid #e0e0e0;
}

.guide-title {
  font-size: 2rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 1rem;
}

.guide-intro {
  font-size: 1rem;
  line-height: 1.5;
  color: var(--text-secondary);
}

.quick-start-guide h3 {
  font-size: 1.5rem;
  font-weight: 600;
  margin-top: 2rem;
  margin-bottom: 1rem;
  color: var(--text-primary);
}

.quick-start-guide ol {
  padding-left: 1.5rem;
  list-style-type: decimal;
}

.quick-start-guide li {
  margin-bottom: 1rem;
  font-size: 1rem;
  color: var(--text-secondary);
}

.quick-start-guide pre {
  background-color: var(--bg-primary);
  border-radius: 8px;
  padding: 1rem;
  overflow-x: auto;
  margin-top: 0.5rem;
}

.quick-start-guide p {
  margin-top: 1rem;
  font-size: 1rem;
  color: var(--text-secondary);
}


.quick-start-guide code {
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.guide-link-container {
  margin-top: 2rem;
  text-align: center;
}

.guide-link {
  display: inline-block;
  background-color: var(--accent-color);
  color: #fff;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  text-decoration: none;
  font-weight: 600;
  transition: background-color 0.2s;
}

.guide-link:hover {
  background-color: #0056b3;
}

hr {
  border: 0;
  height: 1px;
  background: #e0e0e0;
  margin: 2rem 0;
}
</style>