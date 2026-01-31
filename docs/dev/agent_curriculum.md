# Learning Curriculum: Building a Tool-Agnostic Agent

This curriculum is designed to guide you through the architecture of a tool-agnostic agent, explaining the *what*, *why*, and *how* of each component in our codebase.

## Module 1: The Foundation (Philosophy)
**Goal**: Understand why we decouple reasoning from capabilities.

*   **Lesson 1.1: What is "Tool Agnostic"?**
    *   *Concept*: The agent doesn't "know" tools at compile time. It "discovers" them at runtime.
    *   *Why we do this*:
        *   **Scalability**: We can add 1000 tools without retraining the model.
        *   **Context Limit**: We can't stuff every API definition into the system prompt.
        *   **User Specificity**: User A sees GitHub tools; User B sees Jira tools. The agent code remains identical.
*   **Lesson 1.2: The Universal Interface (MCP)**
    *   *Concept*: Model Context Protocol acting as a standard driver for any service.
    *   *Why we do this*: To avoid writing custom wrappers for every single API.

## Module 2: The Nervous System (Orchestration)
**Goal**: Learn how the agent "thinks" and decides next steps.

*   **Lesson 2.1: The Brain (`agent_orchestrator.py`)**
    *   *Code Reference*: `backend/app/services/agent/agent_orchestrator.py`
    *   *Key Component*: `StateGraph` (LangGraph).
    *   *Why this component?*:
        *   Standard chains (linear) break when you need loops (Think → Act → Fail → Retry → Success).
        *   We need a stateful object to hold the conversation history across these loops.
*   **Lesson 2.2: The Decision Loop (Routing)**
    *   *Code Reference*: `route_tools` function.
    *   *Why this component?*: The agent might want to talk to the user OR call a tool. We need logic to distinguish these intents and route to the correct node (`agent` vs `tools` vs `human_review`).

## Module 3: The Body (Dynamic Assembly)
**Goal**: Understand how an agent is "born" for a single request.

*   **Lesson 3.1: The Builder (`agent_factory.py`)**
    *   *Code Reference*: `backend/app/services/agent/agent_factory.py`
    *   *Why this component?*:
        *   Agents are ephemeral. We build a fresh graph for every session to inject the specific user's permissions and available tools.
        *   It merges the generic "Brain" with the specific "Tools".
*   **Lesson 3.2: The Knowledge (`tool_registry.py`)**
    *   *Code Reference*: `backend/app/services/agent/tool_registry.py`
    *   *Key Mechanism*: BM25 / Keyword Search.
    *   *Why this component?*:
        *   **"Paging"**: We can only fit ~50 tool definitions in the prompt. If we have 500, we use the registry to "search" for relevant ones and dynamically bind them.

## Module 4: The Conscience (Safety & Persistence)
**Goal**: Ensuring the agent is safe and remembers context.

*   **Lesson 4.1: The Gatekeeper (`human_review_node`)**
    *   *Code Reference*: `backend/app/services/agent/agent_orchestrator.py` -> `human_review_node`
    *   *Why this component?*:
        *   **Trust**: A tool-agnostic agent is powerful. It might try to "Delete Database".
        *   We need an interrupt layer that pauses execution *before* a dangerous tool runs, asks the human, and *resumes* only if approved.
*   **Lesson 4.2: The Memory (`checkpointer`)**
    *   *Code Reference*: `backend/app/services/agent/redis_checkpointer.py`
    *   *Why this component?*:
        *   The web is stateless. If the agent asks for permission, the server might restart while waiting.
        *   Redis stores the exact "program counter" of the agent so it can resume days later.

## Final Review
*   **Checklist**:
    *   [ ] Can you trace a request from `POST /chat` to `agent_factory`?
    *   [ ] Do you understand why `tools=[search_tool]` is often the *only* initial tool?
    *   [ ] Can you explain why `check_tool_approval` is separate from the `ToolNode`?
