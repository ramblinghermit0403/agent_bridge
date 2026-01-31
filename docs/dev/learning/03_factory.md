# Module 3: Dynamic Tooling (The Body)

## 1. Introduction: The Backpack Problem

Imagine you are going on a hike. You have a backpack (your **Context Window**).
You have a garage full of 5,000 tools (saws, hammocks, pots, ropes, axes...).

You cannot fit all 5,000 tools in your backpack. If you try, the backpack breaks (the LLM crashes or gets confused).
So, what do you do?

*   **Approach A (Static)**: You pack a saw and a rope. But what if you encounter a river and need a raft? You are stuck.
*   **Approach B (Dynamic)**: You carry a magical radio. When you see a river, you radio the garage: "Send me something for water." A drone drops a raft. You use it. Then you drop the raft and radio for a tent.

Our Agent uses **Approach B**.
In technical terms, the "Backpack" is the System Prompt. The "Garage" is our **Tool Registry**.

## 2. The Factory: Building a Custom Body

Because every user has a different "Garage" (User A has GitHub, User B has Notion), we cannot pre-build the agent. We must build it **Just-In-Time**.

This happens in `backend/app/services/agent/agent_factory.py`.

### The `create_final_agent_pipeline` Function
Think of this function as the **Assembly Line**.
Every time a user starts a chat (or resumes one), this function runs:

1.  **Scan User Config**: It checks which MCP servers the user has connected.
2.  **Fetch Tool Definitions**: It asks those servers for their tool lists.
    *   *Result*: A list of 500 potential tools.
3.  **Create Registry**: It indexes these 500 tools into a search engine (BM25).
4.  **Inject Initial Tools**: It picks a small set of "always available" tools (like `search_tools`) and puts them in the backpack.
5.  **Compile Graph**: It takes the generic Brain (from Module 2) and gives it this specific backpack.

**Result**: A unique Agent instance that exists only for this specific user session.

## 3. The Registry: The Search Engine

The file `backend/app/services/agent/tool_registry.py` is the librarian.
It doesn't "run" tools. It "knows about" tools.

We use an algorithm called **BM25** (Best Matching 25). It is a classic keyword search algorithm (similar to what Solr or Lucene use).

### How the Agent "Learns" a New Tool
Let's trace a concrete example.

**Scenario**: The user asks, "Restart the production database."
**Problem**: The Agent's backpack currently only has `search_tools`. It doesn't know how to restart a database.

**The Loop**:
1.  **Think**: The Agent analyzes the request. "I need to restart a database. I don't have a tool for that. I should search."
2.  **Act**: The Agent calls `search_tools(query="restart database")`.
3.  **System**: The Registry runs BM25 against the 500 descriptions in the Garage.
    *   *Found*: `aws_restart_db_instance` (Score: 0.95)
    *   *Found*: `azure_restart_sql` (Score: 0.92)
4.  **Observe**: The Agent receives these tool definitions.
    *   *Crucial Step*: The System **dynamically binds** these new tools to the LLM. They are now in the backpack.
5.  **Think**: "Aha! I see `aws_restart_db_instance`. I will call that."

## 4. What the Agent Actually Sees (JSON)

To demystify "Tool Definitions", here is exactly what we send to the LLM. It's just JSON.

When we say "we bind the tool", we are just appending this text to the System Prompt:

```json
{
  "name": "aws_restart_db_instance",
  "description": "Restarts a specific RDS database instance.",
  "parameters": {
    "type": "object",
    "properties": {
      "instance_id": {
        "type": "string",
        "description": "The AWS identifier for the database"
      }
    },
    "required": ["instance_id"]
  }
}
```

The LLM is trained to read this schema and output a formatted string like:
`Action: aws_restart_db_instance(instance_id="prod-db-1")`

## 5. Summary

*   **The Problem**: Context Windows are small. Tool Lists are huge.
*   **The Solution**: The **Factory** builds a `ToolRegistry` for every user.
*   **The Mechanism**: The Agent starts with an empty backpack and uses `search_tools` to find what it needs on the fly.

This is what makes the agent **Tool Agnostic**. It doesn't need to know AWS exists when we write the code. It discovers AWS at runtime.

But wait... if the Agent can find "Restart Database" and just run it... isn't that dangerous?
That brings us to **Module 4: Safety**.
