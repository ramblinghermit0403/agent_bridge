---
layout: home

hero:
  name: "Agent Bridge"
  text: "The Agent Architecture"
  tagline: "Scalable. Dynamic. Safe. Built on the Model Context Protocol."
  actions:
    - theme: brand
      text: Start Learning
      link: /dev/learning/index
    - theme: alt
      text: Documentation
      link: /guide/getting-started
    - theme: alt
      text: GitHub
      link: https://github.com/ramblinghermit0403/agent_bridge

features:
  - title: Tool Agnostic
    details: Decoupling reasoning from capabilities. Agents discover tools at runtime using dynamic registry and factory patterns.
    link: /dev/learning/01_paradigm

  - title: Model Context Protocol
    details: Native support for MCP. Connect GitHub, Notion, Linear, and local environments without custom adapters.
    link: /guide/mcp-servers

  - title: Human-in-the-Loop
    details: Granular permission control. Intercept, review, and approve tool execution in real-time.
    link: /dev/learning/04_safety

  - title: LangGraph Orchestration
    details: State-machine based architecture for complex, cyclic reasoning loops and reliable persistence.
    link: /dev/learning/02_orchestrator

---

<div class="minimal-footer" style="padding: 4rem 0; text-align: center; border-top: 1px solid var(--vp-c-divider);">
  <h2 style="font-weight: 600; margin-bottom: 1rem; border: none;">Engineered for Production</h2>
  <p style="max-width: 600px; margin: 0 auto; color: var(--vp-c-text-2);">
    Agent Bridge provides the foundational layer for building enterprise-grade AI agents. 
    Focus on your tools and prompts while we handle state, security, and orchestration.
  </p>
</div>
