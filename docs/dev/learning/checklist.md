# 🎓 Agent Architecture Learning Checklist

Use this list to track your progress in understanding the codebase.

## 🟢 Module 1: The Foundation (Philosophy)
- [ ] **Concept**: Read "The Tool-Agnostic Paradigm" in `docs/dev/agent_curriculum.md`.
- [ ] **Concept**: Understand why we use MCP (Model Context Protocol).
- [ ] **Self-Check**: Explain to yourself (or a rubber duck) why we simply don't hardcode tool API calls in the prompt.

## 🧠 Module 2: Orchestration (The Brain)
- [ ] **Read**: "The Nervous System" in the curriculum.
- [ ] **Code Action**: Open `backend/app/services/agent/agent_orchestrator.py`.
- [ ] **Code Action**: Locate the `StateGraph` definition (~line 300).
- [ ] **Code Action**: Find the `route_tools` function and see how it checks for `requires_approval`.
- [ ] **Self-Check**: Which node runs first? `agent` or `tools`?

## 🛠️ Module 3: Dynamic Tooling (The Body)
- [ ] **Read**: "The Body" (Dynamic Assembly) in the curriculum.
- [ ] **Code Action**: Open `backend/app/services/agent/agent_factory.py`.
- [ ] **Code Action**: Find `create_final_agent_pipeline`.
- [ ] **Code Action**: Open `backend/app/services/agent/tool_registry.py` and see the `BM25Okapi` usage.
- [ ] **Self-Check**: How does the agent "know" about a new tool you just added to an MCP server?

## 🛡️ Module 4: Safety & Persistence (The Conscience)
- [ ] **Read**: "The Conscience" in the curriculum.
- [ ] **Code Action**: Look at `human_review_node` in `agent_orchestrator.py`.
- [ ] **Code Action**: Find where `PendingApproval` calls happen.
- [ ] **Self-Check**: If the server crashes while waiting for user approval, where is the state saved? (Hint: Redis Checkpointer).

## 🏁 Final Verification
- [ ] **Interactive**: Run the agent in the UI.
- [ ] **Trace**: Follow the logs in your terminal as the agent thinks and acts.
- [ ] **Complete**: Mark this checklist as done!
