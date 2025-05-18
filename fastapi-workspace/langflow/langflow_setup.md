# Langflow + LangChain Agent: Setup & Simple Flow

---

## 1. Set up a dedicated virtual-environment for Langflow

```bash
# go to your project root
cd /path/to/your/project

# create and activate a brand-new env (keep existing venv untouched)
python -m venv langflow-venv
# ── macOS / Linux
source langflow-venv/bin/activate
# ── Windows (PowerShell)
# .\langflow-venv\Scripts\Activate.ps1
```

## 2. Install prerequisites

```bash
pip install uv          # faster drop-in replacement for pip
uv pip install langflow # install Langflow itself
```

## 3. Run Langflow

```bash
uv run langflow run
```

Langflow prints a URL (typically `http://127.0.0.1:7860`).
Open it in your browser to reach the UI.

---

## 4. Build a simple flow

### 4.1 Create a blank canvas

1. Click **New Flow** → **Blank**.

### 4.2 Add blocks

| Step | Block                             | Purpose                        |
| ---- | --------------------------------- | ------------------------------ |
| a    | **Chat Input**                    | Accept user text.              |
| b    | **Custom Component** (code below) | Calls the LangChain agent API. |
| c    | **Chat Output**                   | Displays the agent’s answer.   |

### 4.3 Custom component code

Create a new component in Langflow → **Custom → + New Component**, paste:

```python
from langflow.custom import Component
from langflow.io import MessageTextInput, Output
from langflow.schema import Data
import requests
from urllib.parse import quote


class CustomComponent(Component):
    display_name = "Ask API"
    description = "Returns only the `output` field from the LangChain agent’s JSON response."
    icon = "globe"
    name = "AskAPI"

    # ── Inputs ───────────────────────────────
    inputs = [
        MessageTextInput(
            name="input_value",
            display_name="Input Value",
            info="Prompt sent to the agent.",
            value="add 2 and 3",
            tool_mode=True,
        ),
    ]

    # ── Outputs ──────────────────────────────
    outputs = [
        Output(
            display_name="API Response",
            name="output",
            method="build_output",
        ),
    ]

    # ── Logic ────────────────────────────────
    def build_output(self) -> Data:
        try:
            encoded = quote(self.input_value)
            # 🔁 Change port if your agent runs elsewhere
            url = f"http://127.0.0.1:8001/ask?prompt={encoded}"
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()

            data = resp.json()
            return data.get("response", {}).get("output", "No output found")

        except Exception as e:
            return Data(value=f"Error: {e}")
```

> **Important :** If your LangChain agent listens on a port other than **8001**, update the URL in the code.

### 4.4 Wire the flow

1. Connect **Chat Input → Ask API (input\_value)**.
2. Connect **Ask API (output) → Chat Output**.

Save, click **Run**, and test with a prompt—for example, **“add 2 and 3”**. The agent’s answer should appear in the chat output.

---
