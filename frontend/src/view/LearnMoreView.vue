<template>
  <div class="learn-more">
    <!-- Hero Section -->
    <section class="hero">
      <!-- <div class="hero-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" fill="none" stroke="currentColor" stroke-width="2"
          stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 22V8" />
          <path d="M5 12H2a10 10 0 0 0 20 0h-3" />
          <path d="M5 12a10 10 0 0 1 14 0" />
        </svg>
      </div> -->
      <h1>Understanding Agent Bridge</h1>
      <p>
        Discover how Agent Bridge uses the <strong>Model Context Protocol (MCP)</strong> to connect powerful language
        models with your real-world tools and data.
      </p>
    </section>

    <!-- How It Works -->
    <section class="section">
      <h2>A High-Level View</h2>
      <p class="section-subtitle">
        Agent Bridge acts as an intelligent orchestrator. It interprets your request, selects the right tool from your
        connected MCP Servers, and uses the tool's output to generate a final, comprehensive answer.
      </p>
      <div class="diagram">
        <div class="diagram-item">You</div>
        <div class="arrow">→</div>
        <div class="diagram-item core">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" stroke="currentColor"
            stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z" />
            <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
            <line x1="12" y1="19" x2="12" y2="22" />
          </svg>
          <span>Agent Bridge (LLM)</span>
        </div>
        <div class="arrow">→</div>
        <div class="diagram-item">Your MCP Server</div>
      </div>
    </section>

    <!-- Use Cases -->
    <section class="section">
      <h2>Powerful Use Cases</h2>
      <div class="grid">
        <div class="card">
          <h3>Automated BI</h3>
          <p>"Generate a sales report for Q2 and email it to the management team."</p>
        </div>
        <div class="card">
          <h3>DevOps & Admin</h3>
          <p>"Check the status of all production servers and restart any that are offline."</p>
        </div>
        <div class="card">
          <h3>Support Automation</h3>
          <p>"Find Jane Doe's latest order and issue a refund for the 'Pro Plan'."</p>
        </div>
      </div>
    </section>

    <!-- CTA -->
    <section class="section cta">
      <h2>Ready to Build?</h2>
      <p class="section-subtitle">Connect your first MCP server in the settings. Use our open-source library to wrap your existing APIs into an
        MCP-compliant server and unlock the power of your tools.</p>
      <button @click="$router.push('/settings')">Go to Connections Settings</button>
    </section>
  </div>
</template>
<style scoped>
:root {
  --text-primary: #1e1e2f;
  --text-secondary: #5c5f6e;

  --bg-primary: #ffffff;
  --bg-secondary: #f5f7fa;

  --accent-color: #4a6ef5;
  --accent-hover: #3e5bdd;

  --gradient-start: #4a6ef5;
  --gradient-end: #8b5cf6;

  --border-color: #e0e3eb;
}

.learn-more {
  padding: 2rem;
  max-width: 960px;
  padding-bottom: 70px;
  margin: 0 auto;
  color: var(--text-primary);
  background: var(--bg-primary);
  
  /* --- ADDED FOR SCROLLING --- */
  height: 100vh; /* Set a fixed height to enable internal scrolling */
  overflow-y: auto; /* Show scrollbar when content overflows */
  box-sizing: border-box; /* Include padding in height calculation */
  
  /* --- Custom Scrollbar Styling (For Firefox) --- */
  scrollbar-width: thin;
  scrollbar-color: var(--text-secondary) var(--bg-primary);
}

/* --- Base Section Styling --- */
/* Unified styling for all major content blocks for consistency */
.section,
.hero {
  background: var(--bg-secondary);
  padding: 2.5rem;
  margin-bottom: 2rem;
  border-radius: 16px;
  border: 1px solid var(--border-color);
  transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
  text-align: center;
}

.section:hover,
.hero:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 30px -10px rgba(74, 110, 245, 0.1);
}

/* --- Typography --- */
h1 {
  font-size: 2.25rem;
  font-weight: 700;
  margin-bottom: 1rem;
  background: linear-gradient(90deg, var(--text-primary), color-mix(in srgb, var(--text-primary) 60%, white));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

h2 {
  font-size: 1.75rem;
  margin-bottom: 0.75rem;
  font-weight: 700;
  color: var(--text-primary);
}

.hero p, .section-subtitle {
  max-width: 600px;
  margin: 0 auto 1.5rem auto;
  color: var(--text-secondary);
  font-size: 1.1rem;
  line-height: 1.6;
}

/* --- Hero Section Specifics --- */
.hero {
  padding: 3.5rem 2.5rem;
}

.hero-icon {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 72px;
  height: 72px;
  margin: 0 auto 1.5rem;
  border-radius: 50%;
  background: white;
  border: 1px solid var(--border-color);
  color: var(--accent-color);
  box-shadow: 0 4px 10px -4px rgba(0,0,0,0.05);
}

/* --- Diagram --- */
.diagram {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 1rem;
  margin-top: 2rem;
}

.diagram-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem 1.5rem;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  font-weight: 500;
  color: var(--text-primary);
  transition: transform 0.2s ease;
}
.diagram-item:hover {
  transform: translateY(-3px);
}

.diagram-item.core {
  background: var(--accent-color);
  border-color: var(--accent-color);
  color: white;
  transform: scale(1.05);
  box-shadow: 0 4px 20px -5px color-mix(in srgb, var(--accent-color) 40%, transparent);
}
.diagram-item.core:hover {
  transform: scale(1.05) translateY(-3px);
}

.arrow {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-secondary);
}

/* --- Use Case Cards --- */
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1.5rem;
  margin-top: 2rem;
  text-align: left;
}
.card {
  background: var(--bg-primary);
  border-radius: 12px;
  padding: 1.5rem;
  border: 1px solid var(--border-color);
  position: relative;
  transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}

.card:hover {
  transform: translateY(-6px);
  border-color: color-mix(in srgb, var(--accent-color) 30%, var(--border-color));
  box-shadow: 0 8px 25px -8px rgba(0,0,0,0.08);
}

.card h3 {
  font-size: 1.125rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
  color: var(--text-primary);
}

.card p {
  font-size: 0.95rem;
  color: var(--text-secondary);
  line-height: 1.5;
}

/* --- Call to Action --- */
.cta button {
  margin-top: 1rem;
  padding: 0.8rem 2rem;
  font-size: 1rem;
  font-weight: 600;
  color: white;
  background-color: var(--accent-color);
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease-in-out;
}

.cta button:hover {
  background-color: var(--accent-hover);
  transform: translateY(-2px);
  box-shadow: 0 4px 15px color-mix(in srgb, var(--accent-color) 25%, transparent);
}

@media (max-width: 600px) {
  .learn-more {
    padding: 1rem;
  }
  .section, .hero {
    padding: 2rem 1.5rem;
  }
  h1 {
    font-size: 1.75rem;
  }
  h2 {
    font-size: 1.5rem;
  }
}

/* --- NEW: Custom Scrollbar Styling (For Webkit) --- */
.learn-more::-webkit-scrollbar {
  width: 10px;
}

.learn-more::-webkit-scrollbar-track {
  background: var(--bg-primary);
}

.learn-more::-webkit-scrollbar-thumb {
  background-color: var(--text-secondary);
  border-radius: 10px;
  border: 3px solid var(--bg-primary); /* Creates a "padded" effect */
}

.learn-more::-webkit-scrollbar-thumb:hover {
  background-color: var(--text-primary);
}

</style>