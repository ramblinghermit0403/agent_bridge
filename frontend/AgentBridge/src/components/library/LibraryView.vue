<template>
  <div class="library-view">
    <div class="library-header">
      <h1 class="library-title">Server Library</h1>
      <p class="library-description">
        Explore pre-built MCP servers and their source code on GitHub. To build your own server—like the weather server
        in the official MCP quickstart—follow the guide below.
      </p>
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
  // {
  //   name: "Weather Server (Quickstart)",
  //   description: "Official MCP quickstart: exposes tools `get_forecast` and `get_alerts` for weather data.",
  //   githubUrl: "https://github.com/modelcontextprotocol/quickstart-resources/tree/main/weather-server-python",
  // },
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