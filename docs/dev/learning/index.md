# Agent Architecture Learning Curriculum

Welcome to the deep dive into the **Tool-Agnostic Agent Architecture**. This documentation is designed to take you from a conceptual understanding of our agent design to a line-by-line code comprehension.

## Curriculum Overview

This course is split into 4 logical modules. It is recommended to read them in order.

### [Module 1: The Tool-Agnostic Paradigm](./01_paradigm.md)
*   **Concept**: What does "tool agnostic" mean?
*   **Why**: The business case for decoupling reasoning from capabilities.
*   **Technology**: The Model Context Protocol (MCP).

### [Module 2: The Orchestrator (The Brain)](./02_orchestrator.md)
*   **Architecture**: Deep dive into `agent_orchestrator.py`.
*   **Logic**: Understanding the "Think -> Act -> Observe" loop.
*   **Code**: `StateGraph`, `route_tools`, and `sub_agent_node`.

### [Module 3: Dynamic Tooling (The Body)](./03_factory.md)
*   **Mechanism**: How agents are assembled on-the-fly.
*   **Discovery**: The Role of `tool_registry.py` and semantic search.
*   **Factory**: Inside `create_final_agent_pipeline`.

### [Module 4: Safety & Persistence (The Conscience)](./04_safety.md)
*   **Safety**: Implementing Human-in-the-Loop with `human_review_node`.
*   **Persistence**: How `RedisSaver` enables long-running tasks.
*   **Permissions**: The `check_tool_approval` logic.

### [Module 5: Debugging & Tracing](./05_debugging.md)
*   **Logs**: How to read the `uvicorn` output.
*   **Common Errors**: Context windows and stuck states.
*   **Redis**: Inspecting the agent's memory.

## Where do I start in the code?

If you want to follow the flow of a request:

1.  **Start Here**: `backend/app/routes/agent.py` -> `chat()` function.
    *   This is where the API request lands.
2.  **Next**: `backend/app/services/agent/agent_factory.py` -> `create_final_agent_pipeline`.
    *   This is where the agent is built.
3.  **Then**: `backend/app/services/agent/agent_orchestrator.py` -> `GraphAgentExecutor.invoke`.
    *   This is where the thinking happens.

## Recommended Prerequisites

Before diving in, you should be familiar with:
*   **Python 3.10+** (AsyncIO)
*   **LangGraph**: Our state machine framework.
*   **LangChain**: The underlying cognitive architecture.
*   **MCP**: [Model Context Protocol](https://modelcontextprotocol.io/) basics.
