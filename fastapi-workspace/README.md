# FastAPI Workspace

This project is a **FastAPI** application that integrates with multiple MCP **MCP** servers and **LangChain** agents.

## Project Structure

```text
app/
├─ main.py            # FastAPI entry point
├─ mcp_connector.py   # Handles connections to the MCP service
├─ langchain_agent.py # Integrates LangChain functionality
└─ config.py          # Configuration settings (urls of the mcp servers)

langflow/             # Mount your Langflow project here

requirements.txt      # Python dependencies
```

## Setup Instructions

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd fastapi-workspace
   ```

2. **Create and activate a virtual environment inside `venv/`(create venv folder if not present)**

   ```bash
   python -m venv venv        # create
   # macOS / Linux
   source venv/bin/activate   # activate

   # Windows (PowerShell)
   # .\venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**

   ```bash
   uvicorn app.main:app --reload
   ```

## Usage

With the server running, visit **`http://localhost:8000`** to access the interactive API docs and endpoints.

Make sure the mcp servers are running on a different port.

## License

This project is licensed under the **MIT License**. See the `LICENSE` file for full details.
