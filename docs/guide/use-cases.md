# Open Source Use Cases

Agent Bridge is designed to be more than just an application—it's a modular platform that can be adopted in many ways.

## 1. Full Platform Deployment

**Who**: Engineering teams, startups, enterprises  
**Why**: Own your AI infrastructure without vendor lock-in

| Scenario | Value |
|----------|-------|
| **Internal DevOps Assistant** | Engineers chat with an agent that can create GitHub issues, check CI status, query logs |
| **Customer Support Copilot** | Support team uses agent connected to CRM, ticketing, and knowledge base MCP servers |
| **Self-Hosted Alternative** | Replace SaaS tools like ChatGPT Teams with on-prem solution for data privacy |

---

## 2. Learning & Education

**Who**: Developers learning agentic AI, bootcamp students, educators  
**Why**: Real-world, production-grade reference implementation

| What to Learn | Where in Codebase |
|---------------|-------------------|
| **LangGraph State Machines** | `agent_orchestrator.py` - StateGraph with conditional edges |
| **Human-in-the-Loop Patterns** | `human_review_node` - Graph interrupts and resumption |
| **Tool Calling with MCP** | `tools.py` - Dynamic tool generation from MCP servers |
| **SSE Streaming** | `streaming.py` - FastAPI EventSourceResponse patterns |
| **OAuth 2.0 + PKCE** | `mcp/auth.py` - Full OAuth flow with token refresh |

---

## 3. Modular Extraction

**Who**: Developers building their own AI products  
**Why**: Don't reinvent the wheel—extract battle-tested components

| Module | Can Be Used For |
|--------|-----------------|
| **`llm_factory.py`** | Drop-in multi-provider LLM client for any Python project |
| **`MCPConnector`** | Reusable MCP client for any agent framework (CrewAI, AutoGen) |
| **`GraphAgentExecutor`** | Wrapper pattern for LangGraph → legacy AgentExecutor migration |
| **Tool Permission System** | Portable human-in-the-loop approval logic |
| **Vue SSE Components** | Frontend patterns for streaming AI responses |

---

## 4. MCP Server Development & Testing

**Who**: MCP server authors, tool builders  
**Why**: Need a reference client to test against

| Use Case | How |
|----------|-----|
| **Validate Tool Discovery** | Connect your MCP server, check if tools appear correctly |
| **Test OAuth Flow** | Debug authorization URLs, callback handling, token exchange |
| **Verify Tool Execution** | Execute tools through the agent, check request/response format |
| **Performance Benchmarking** | Measure latency of tool calls under real agent workloads |

---

## 5. Enterprise Customization

**Who**: Enterprises with specific compliance/security needs  
**Why**: Fork and customize for internal requirements

| Customization | Example |
|---------------|---------|
| **Add Enterprise SSO** | Integrate SAML/OIDC for corporate login |
| **Audit Logging** | Add comprehensive logging for compliance |
| **Custom LLM Providers** | Add Azure OpenAI, AWS Bedrock, private models |
| **Role-Based Access** | Extend permission system for team hierarchies |
| **On-Prem Vector DB** | Swap Pinecone for self-hosted Milvus/Weaviate |

---

## 6. Research & Experimentation

**Who**: AI researchers, prompt engineers, agent architects  
**Why**: Modifiable sandbox for agent behavior research

| Experiment | Approach |
|------------|----------|
| **Prompt Engineering** | Modify `prompts.py` to test different personas/instructions |
| **Tool Selection Strategies** | Experiment with tool routing in `route_tools` |
| **Memory Architectures** | Swap checkpointers to test persistence strategies |
| **Multi-Agent Patterns** | Extend graph to include sub-agents |

---

## Getting Started by Use Case

| Your Goal | Start Here |
|-----------|------------|
| Deploy the full platform | [Getting Started](./getting-started.md) |
| Learn agent architecture | [Architecture](../dev/architecture.md) |
| Extract a module | [Agent Core](../dev/agent-core.md) |
| Test your MCP server | [Connecting MCP Servers](./mcp-servers.md) |
| Customize for enterprise | [Extending the Platform](../dev/expansion.md) |
