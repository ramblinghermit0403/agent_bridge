<template>
  <div class="permission-message">
    <!-- Header -->
    <div class="message-header">
      <div class="header-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-6 h-6"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
      </div>
      <div class="header-text">
        <h3>Permission Required</h3>
        <p>The agent needs your approval to execute this tool.</p>
      </div>
    </div>

    <!-- Tool Details -->
    <div class="tool-info">
      <div class="info-row">
        <span class="label">Tool:</span>
        <span class="value">{{ toolName }}</span>
      </div>
      <div class="info-row">
        <span class="label">Server:</span>
        <span class="value">{{ serverName }}</span>
      </div>
    </div>

    <!-- Payload Preview (Collapsible) -->
    <div class="payload-preview">
      <details>
        <summary>View Input Parameters</summary>
        <pre class="json-code">{{ formattedPayload }}</pre>
      </details>
    </div>

    <!-- Actions -->
    <div class="message-actions">
      <button @click="deny" class="btn deny-btn">
        Deny
      </button>
      <div class="allow-group">
        <button @click="allowOnce" class="btn allow-btn">
          Allow Once
        </button>
        <button @click="allowAlways" class="btn allow-always-btn">
          Always Allow
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  toolName: String,
  serverName: String,
  payload: Object,
  approvalId: String
});

const emit = defineEmits(['approve', 'deny']);

const formattedPayload = computed(() => {
  if (!props.payload) return '{}';
  return JSON.stringify(props.payload, null, 2);
});

const deny = () => {
  emit('deny', { approvalId: props.approvalId });
};

const allowOnce = () => {
  emit('approve', {
    approvalId: props.approvalId,
    approvalType: 'once',
    toolName: props.toolName,
    serverName: props.serverName
  });
};

const allowAlways = () => {
  emit('approve', {
    approvalId: props.approvalId,
    approvalType: 'always',
    toolName: props.toolName,
    serverName: props.serverName
  });
};
</script>

<style scoped>
.permission-message {
  width: 100%;
  max-width: 48rem; /* Match user/agent bubble width constraint if needed, or full with */
  border: 1px solid var(--border-color);
  background-color: var(--bg-secondary);
  border-radius: 8px;
  overflow: hidden;
  margin-top: 0.5rem;
  margin-bottom: 0.5rem;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(5px); }
  to { opacity: 1; transform: translateY(0); }
}

.message-header {
  display: flex;
  gap: 0.75rem;
  padding: 1rem;
  background-color: #fefce8; /* Light yellow background for warning feel? Use var if strictly monochrome */
  border-bottom: 1px solid var(--border-color);
}
/* Allow overriding colors for dark mode compatibility if vars exist */
@media (prefers-color-scheme: dark) {
    .message-header {
        background-color: rgba(253, 224, 71, 0.1); /* transparent yellow */
    }
}

.header-icon {
  flex-shrink: 0;
  color: #F59E0B; /* Amber 500 */
}

.header-text h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: #92400E; /* Amber 800 */
  line-height: 1.4;
}

.header-text p {
  margin: 0.25rem 0 0 0;
  font-size: 0.875rem;
  color: #B45309; /* Amber 700 */
}

/* Dark Theme Overrides */
/* Assuming usage of .dark-theme class or media query. Using media query for robustness if class not present on body */
@media (prefers-color-scheme: dark) {
  .permission-message {
    background-color: #1e1e1e; /* Darker card background */
    border-color: #333;
  }
}

:global(.dark-theme) .message-header,
@media (prefers-color-scheme: dark) {
    .message-header {
        background-color: rgba(245, 158, 11, 0.15); /* Dark Amber Tint */
        border-bottom: 1px solid rgba(245, 158, 11, 0.3);
    }
    .header-icon {
        color: #FBBF24; /* Amber 400 */
    }
    .header-text h3 {
        color: #FEF3C7; /* Amber 100 - High Contrast on Dark */
    }
    .header-text p {
        color: #FDE68A; /* Amber 200 */
    }
}

.tool-info {
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  font-size: 0.95rem;
  border-bottom: 1px solid var(--border-color);
}

.info-row {
  display: flex;
  gap: 0.75rem;
  align-items: baseline;
}

.label {
  font-weight: 600;
  color: var(--text-secondary);
  min-width: 60px;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.value {
  color: var(--text-primary);
  font-family: 'SF Mono', SFMono-Regular, Consolas, 'Liberation Mono', Menlo, monospace;
  background: var(--bg-primary);
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
  border: 1px solid var(--border-color);
  font-size: 0.9rem;
}

.payload-preview {
  padding: 0 1.25rem 1.25rem 1.25rem;
}

.payload-preview details summary {
  cursor: pointer;
  color: var(--text-secondary);
  font-size: 0.85rem;
  font-weight: 500;
  margin: 1rem 0 0.5rem 0;
  user-select: none;
  transition: color 0.2s;
}

.payload-preview details summary:hover {
  color: var(--text-primary);
}

.json-code {
  background-color: var(--bg-primary);
  padding: 1rem;
  border-radius: 6px;
  font-size: 0.85rem;
  color: var(--text-primary);
  overflow-x: auto;
  margin: 0;
  border: 1px solid var(--border-color);
  font-family: 'SF Mono', SFMono-Regular, Consolas, monospace;
}

.message-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.25rem;
  background-color: var(--bg-primary); 
  border-top: 1px solid var(--border-color);
}

.allow-group {
    display: flex;
    gap: 0.75rem;
}

.btn {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  height: 2.25rem;
}

.deny-btn {
  background-color: transparent;
  border-color: var(--border-color);
  color: var(--text-secondary);
}

.deny-btn:hover {
  background-color: #FEF2F2; /* Red 50 */
  color: #DC2626; /* Red 600 */
  border-color: #FECACA; /* Red 200 */
}
:global(.dark-theme) .deny-btn:hover,
@media (prefers-color-scheme: dark) {
    .deny-btn:hover {
        background-color: rgba(220, 38, 38, 0.15);
        border-color: rgba(220, 38, 38, 0.3);
        color: #F87171;
    }
}


.allow-btn {
  background-color: var(--text-primary);
  color: var(--bg-primary);
  border: 1px solid var(--text-primary);
}

.allow-btn:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

.allow-always-btn {
  background-color: transparent;
  border-color: var(--text-primary);
  color: var(--text-primary);
}

.allow-always-btn:hover {
  background-color: var(--bg-secondary);
}
</style>
