# Agent Services API

This section details the core components responsible for the AI Agent's lifecycle, orchestration, and execution.

Location: `backend/app/services/agent/`

---

## Agent Orchestrator

**File**: [`agent_orchestrator.py`](https://github.com/ramblinghermit0403/agent_bridge/blob/main/backend/app/services/agent/agent_orchestrator.py)



The **Agent Orchestrator** is the brain of the application. It uses [LangGraph](https://langchain-ai.github.io/langgraph/) to define a cyclic state graph that manages the conversation flow between the User, the LLM, and the Tools.

### `create_graph_agent`

```python
def create_graph_agent(
    llm: BaseChatModel, 
    tools: List[StructuredTool], 
    prompt: ChatPromptTemplate, 
    model_provider: str = "gemini"
) -> StateGraph
```

Constructs the uncompiled state machine for the agent.

**Logic Flow:**
1.  **Agent Node**: Calls the LLM with the current conversation state and bound tools.
2.  **Route Tools**: Uses `route_tools` to check the LLM's output.
    - If **no tools** are called -> Ends turn.
    - If **tools** are called -> Checks permissions.
        - If **approval required** -> Routes to `human_review`.
        - If **auto-approved** -> Routes to `tools`.
3.  **Human Review Node**: Pauses execution (via LangGraph interrupt) if user permission is needed. Waiting for distinct "Approved" or "Denied" signals.
4.  **Tools Node**: Executes approved tools and feeds output back to the Agent Node.

### `GraphAgentExecutor`

A compatibility wrapper that makes the LangGraph executable look like a standard LangChain `AgentExecutor`. This allows the rest of the FastAPI application (streaming endpoints, etc.) to interact with the new graph system without refactoring.

---

## Agent Factory

**File**: [`agent_factory.py`](https://github.com/ramblinghermit0403/agent_bridge/blob/main/backend/app/services/agent/agent_factory.py)



Responsible for assembling a unique agent instance for every request, tailored to the specific user's context (connected tools, permissions, etc.).

### `create_final_agent_pipeline`

```python
async def create_final_agent_pipeline(
    user_mcp_servers: Dict[str, Any], 
    user_id: str = None, 
    model_provider: str = "gemini", 
    model_name: str = "gemini-2.5-flash"
) -> GraphAgentExecutor
```

**Key Responsibilities:**
1.  **LLM Selection**: Calls `llm_factory` to get the correct model (e.g., Gemini, OpenAI).
2.  **Tool Construction**: Iterates through `user_mcp_servers` to build executable tools using `tools.py`.
3.  **Registry Init**: Registers these tools into a local `ToolRegistry` so the agent can "search" for them if needed.
4.  **Graph Compilation**: Compiles the `StateGraph` with a `MemorySaver` checkpointer for conversation state persistence.

---

## Dynamic Tools

**File**: [`tools.py`](https://github.com/ramblinghermit0403/agent_bridge/blob/main/backend/app/services/agent/tools.py)



This module handles the complex logic of converting remote MCP tool definitions (JSON schemas) into executable Python functions (LangChain `StructuredTool` objects).

### `build_tools_from_servers`

```python
async def build_tools_from_servers(
    user_mcp_servers: Dict, 
    user_id: str = None, 
    blocking: bool = True
) -> List[StructuredTool]
```

**Process:**
1.  **Connect**: Initializes an `MCPConnector` for each server.
2.  **Discover**: Fetches the list of tools (using cache if available).
3.  **Permission Filter**: Removes any tools internally disabled by `ToolPermission` records.
4.  **Wrap**: Converts each tool into a `StructuredTool` using `create_tool_func`.

### `create_tool_func`

Wraps the raw MCP `connector.run_tool` call with **Safety & Robustness** layers:
-   **Retry Logic**: Uses `tenacity` exponential backoff for transient network errors.
-   **Permission Check**: Before execution, checks `PendingApproval` tables. If the tool is "sensitive" and not approved, it **blocks** execution until the user approves via the UI.

---

## LLM Factory

**File**: [`llm_factory.py`](https://github.com/ramblinghermit0403/agent_bridge/blob/main/backend/app/services/agent/llm_factory.py)



### `get_llm`

```python
@lru_cache(maxsize=16)
def get_llm(
    model_provider: str, 
    model_name: str
) -> BaseChatModel
```

**Why it matters**: LLM Clients (like `ChatGoogleGenerativeAI` or `ChatOpenAI`) can be expensive to instantiate repeatedly. This factory uses Python's `@lru_cache` to keep a singleton instance for each model configuration, significantly reducing latency per request.
