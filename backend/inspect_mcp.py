import requests
import json
import sys

def inspect(url):
    print(f"--- Inspecting {url} ---")
    try:
        resp = requests.post("http://localhost:8001/api/mcp/inspect", json={"server_url": url})
        if resp.status_code == 200:
            print(json.dumps(resp.json(), indent=2))
        else:
            print(f"Error: {resp.status_code}")
            print(resp.text)
    except Exception as e:
        print(f"Failed: {e}")

urls = [
    "https://mcp.notion.com/mcp",
    "https://mcp.figma.com/mcp",
    "https://api.githubcopilot.com/mcp/"
]

for u in urls:
    inspect(u)
