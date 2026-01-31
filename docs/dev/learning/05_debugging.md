# Module 5: Debugging & Tracing (The X-Ray)

## 1. Introduction: Becoming a Mind Reader

When a normal Python script fails, it throws a clear error: `IndexError: list index out of range`.
When an Agent fails, it sits quietly, smiles, and says: *"I'm sorry, I can't do that."*

Debugging an Agent is less like fixing a car and more like psychoanalysis. You need to ask:
*   "What did you *think* the user meant?"
*   "What tools *did you think* you had?"
*   "Why did you *decide* to stop?"

This module is your **X-Ray machine**. It teaches you how to see inside the black box.

## 2. The Log Stream: Reading Thoughts

The Agent Orchestrator prints its internal monologue to your terminal.
To be an effective Agent Engineer, you must learn to read this stream like the Matrix.

### Scenario: The Case of the Missing Tool
**User says**: "Restart the server."
**Agent says**: "I don't know how to do that."

**Let's look at the logs:**

```text
INFO: agent_node: Entering with 5 messages
INFO: agent_node: Binding 1 tools to LLM...
INFO: agent_node: Tool calls: 0
```

**The Clue**: `Binding 1 tools`.
**The Deduction**: The Agent only had 1 tool available (likely `search_tools`). It *should* have searched for "restart", but for some reason, it decided not to.
**The Fix**: Check if the System Prompt encourages searching.

### Scenario: The Infinite Loop
**User says**: "Fix bug."
**Agent**: *Spins forever.*

**The Logs:**
```text
INFO: agent_node: Tool calls details: ['read_file']
INFO: tools: Executing read_file...
INFO: agent_node: Tool calls details: ['read_file']
INFO: tools: Executing read_file...
```
**The Clue**: It's calling `read_file` on the same file over and over.
**The Deduction**: The Agent is confused by the file content. It thinks it needs to read it again to "understand" it.
**The Fix**: Prompt Engineering. Tell the agent: "If you have read the file once, do not read it again unless it changed."

## 3. The Brain Scan: Inspecting Redis

Sometimes logs aren't enough. The Agent is "stuck" in a state you can't understand.
It's time to open the brain interactively.

We use **Redis** to store the agent's memory.
If you have `redis-cli` installed, you can dump the current thoughts of a frozen thread.

```bash
# List all active conversations
redis-cli keys "checkpoint:*"

# See the latest snapshot for thread 123
redis-cli hget "checkpoint:123" "channel:values"
```

**What you will see:**
A giant JSON blob containing the `messages` list.
*   Look for the **Last Message**.
*   Does it have `tool_calls`?
*   Does it have an `error` property?

## 4. Common Diseases & Cures

### The "Context Window" Overflow
*   **Symptom**: The Agent works for 10 minutes, then crashes with a 400 error.
*   **Diagnosis**: The `messages` list grew too long.
*   **Cure**: We need a "Memory Manager" (not yet implemented in V1) to summarize old messages, or simply restart the thread.

### The "Hallucinated Tool"
*   **Symptom**: The Agent tries to call `github_search(query='foo')`.
*   **Rubber Duck**: "But wait, the tool is named `search_github_issues`!"
*   **Diagnosis**: The LLM *guessed* the tool name instead of reading the definition.
*   **Cure**: Improve the tool description in the MCP server or the `tool_registry`.

## 5. Final Exam

To verify you have mastered the Agent Bridge, try this:
1.  Run the backend.
2.  Ask the Agent to "Find a file named `secret.txt`."
3.  Watch the logs.
    *   Do you see the `search_tools` call?
    *   Do you see the Factory loading the `file_system` tools?
    *   Do you see the `human_review` node blocking the `read_file` action?

If you can trace that path, **you are ready to build.**
