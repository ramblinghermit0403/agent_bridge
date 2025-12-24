<template>
  <div class="permission-message">
    <!-- Header -->
    <div class="message-header">
      <div class="header-icon">⚠️</div>
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
  font-size: 1.5rem;
}

.header-text h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.header-text p {
  margin: 0.25rem 0 0 0;
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.tool-info {
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  font-size: 0.9rem;
}

.info-row {
  display: flex;
  gap: 0.5rem;
}

.label {
  font-weight: 600;
  color: var(--text-secondary);
  min-width: 60px;
}

.value {
  color: var(--text-primary);
  font-family: monospace;
}

.payload-preview {
  padding: 0 1rem 1rem 1rem;
}

.payload-preview details summary {
  cursor: pointer;
  color: var(--text-secondary);
  font-size: 0.85rem;
  font-weight: 500;
  margin-bottom: 0.5rem;
}

.payload-preview details summary:hover {
  color: var(--text-primary);
}

.json-code {
  background-color: var(--bg-primary);
  padding: 0.75rem;
  border-radius: 4px;
  font-size: 0.8rem;
  color: var(--text-secondary);
  overflow-x: auto;
  margin: 0;
  border: 1px solid var(--border-color);
}

.message-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-top: 1px solid var(--border-color);
  background-color: var(--bg-primary); /* Slightly distinct from body? */
}

.allow-group {
    display: flex;
    gap: 0.5rem;
}

.btn {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.2s;
}

.deny-btn {
  background-color: transparent;
  border-color: var(--border-color);
  color: var(--text-secondary);
}

.deny-btn:hover {
  background-color: #fee2e2; /* Light red */
  color: #991b1b;
  border-color: #fecaca;
}

.allow-btn {
  background-color: var(--text-primary);
  color: var(--bg-primary);
}

.allow-btn:hover {
  opacity: 0.9;
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
