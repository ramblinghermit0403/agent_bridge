# Agent Core

This guide explains the internal "brain" of the agent, focusing on how it thinks (Prompts) and how it remembers (Memory).

## 1. Prompts & Personality

The behavior of the agent is primarily defined by its system prompt. This prompt gives the LLM its role, rules, and context before any user messages are added.

### Location
All prompt definitions are located in:  
**`server/app/services/agent/prompts.py`**

### System Prompts

We use a modular approach to prompts.

#### LangGraph Prompt (Default)
Used by the main agent loop (`agent_factory.py`).

**Current Logic:**
*   **Role**: Expert Assistant.
*   **Priority**: Tool Usage > Internal Knowledge.
*   **Permissions**: Instructions on how to handle "Access Denied" errors (i.e., ask the user for permission).

**Code Reference:**
```python
def build_langgraph_prompt():
    system_prompt = (
        "You are an expert assistant with access to specialized tools..."
        # ...
    )
    return ChatPromptTemplate.from_messages(...)
```

### Customizing the Persona
To change the agent into a specialist (e.g., a "Senior DevOps Engineer"), you simply modify the string in `build_langgraph_prompt`.

**Example:**
```python
def build_langgraph_prompt():
    system_prompt = (
        "You are a Senior DevOps Engineer. You speak efficiently and focus on code.\n"
        "RULES:\n"
        "1. Always check existing file contents before writing new code..."
    )
    # ...
```

## 2. Memory & Persistence

The agent's memory is decoupled from the logic, allowing you to swap backends depending on your deployment needs (Local Dev vs. Production).

### Types of Memory

#### A. Conversation History (Chat Log)
This stores the raw list of Human/AI messages.
*   **Default**: Redis (`RedisChatMessageHistory`).
*   **Location**: `server/app/services/agent/memory.py`.
*   **Swapping**: You can replace `RedisChatMessageHistory` with `PostgresChatMessageHistory` or `FileChatMessageHistory` by changing the `get_session_memory` function.

```python
# server/app/services/agent/memory.py
def get_session_memory(session_id: str):
    # Swap this line to change backends
    return RedisChatMessageHistory(session_id=session_id, url=os.getenv("REDIS_URL"))
```

#### B. Graph State (Checkpointers)
This stores the **internal state** of the agent (variables, current step, tool outputs). This is what enables "Human-in-the-loop" features like pausing execution and resuming later.
*   **Default**: In-Memory (`MemorySaver`). *State is lost on restart.*
*   **Production**: Postgres (`PostgresSaver`) or SQLite (`AsyncSqliteSaver`).
*   **Location**: `server/app/services/agent/agent_factory.py`.

**Swapping to Persistent Storage:**
To enable persistence across restarts, look for the `create_final_agent_pipeline` function and swap the checkpointer.

```python
# server/app/services/agent/agent_factory.py
from langgraph.checkpoint.postgres import PostgresSaver

# ... inside create_final_agent_pipeline ...

# OLD (Dev):
# checkpointer = MemorySaver()

# NEW (Prod):
async with PostgresSaver.from_conn_string("postgresql://...") as checkpointer:
    app = graph.compile(checkpointer=checkpointer)
```

### Best Practices
*   **Development**: Use `MemorySaver` (fast, no setup) and local Redis.
*   **Production**: Use `PostgresSaver` for the graph and a managed Redis/Postgres for chat history to ensure no data is lost during deployments.
