<template>
  <div v-if="isVisible" class="permission-overlay" @click.self="deny">
    <div class="permission-dialog">
      <!-- Header -->
      <div class="dialog-header">
        <div class="header-icon">⚠️</div>
        <h3>Tool Execution Request</h3>
      </div>

      <!-- Tool Details -->
      <div class="tool-details">
        <div class="detail-row">
          <span class="label">Tool:</span>
          <span class="value">{{ toolName }}</span>
        </div>
        <div class="detail-row">
          <span class="label">Server:</span>
          <span class="value">{{ serverName }}</span>
        </div>
      </div>

      <!-- Payload Section -->
      <div class="payload-section">
        <h4>Input Parameters:</h4>
        <pre class="json-payload">{{ formattedPayload }}</pre>
      </div>

      <!-- Action Buttons -->
      <div class="permission-actions">
        <button @click="deny" class="action-btn deny-btn">
          Deny
        </button>
        <button @click="allowOnce" class="action-btn allow-once-btn">
          Allow Once
        </button>
        <button @click="allowAlways" class="action-btn allow-always-btn">
          Always Allow
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';

const props = defineProps({
  isVisible: Boolean,
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

// Auto-focus on the dialog when it appears
watch(() => props.isVisible, (newVal) => {
  if (newVal) {
    // Could add focus management here
  }
});
</script>

<style scoped>
.permission-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.permission-dialog {
  background-color: var(--bg-primary);
  border: 2px solid var(--text-primary);
  border-radius: 8px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.dialog-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.5rem;
  border-bottom: 1px solid var(--border-color);
  background-color: var(--bg-secondary);
}

.header-icon {
  font-size: 2rem;
  line-height: 1;
}

.dialog-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
}

.tool-details {
  padding: 1.5rem;
  border-bottom: 1px solid var(--border-color);
}

.detail-row {
  display: flex;
  align-items: center;
  margin-bottom: 0.75rem;
}

.detail-row:last-child {
  margin-bottom: 0;
}

.label {
  font-weight: 600;
  color: var(--text-secondary);
  min-width: 80px;
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.value {
  color: var(--text-primary);
  font-family: 'Courier New', monospace;
  font-size: 0.95rem;
}

.payload-section {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
  background-color: var(--bg-secondary);
}

.payload-section h4 {
  margin: 0 0 1rem 0;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.json-payload {
  background-color: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  padding: 1rem;
  margin: 0;
  font-family: 'Courier New', monospace;
  font-size: 0.875rem;
  color: var(--text-primary);
  overflow-x: auto;
  line-height: 1.5;
}

.permission-actions {
  display: flex;
  gap: 0.75rem;
  padding: 1.5rem;
  border-top: 1px solid var(--border-color);
  justify-content: flex-end;
}

.action-btn {
  padding: 0.75rem 1.5rem;
  border-radius: 4px;
  font-weight: 600;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border: none;
}

.deny-btn {
  background-color: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-primary);
}

.deny-btn:hover {
  background-color: var(--hover-bg);
}

.allow-once-btn {
  background-color: var(--text-primary);
  color: var(--bg-primary);
  opacity: 0.7;
}

.allow-once-btn:hover {
  opacity: 0.85;
}

.allow-always-btn {
  background-color: var(--text-primary);
  color: var(--bg-primary);
}

.allow-always-btn:hover {
  opacity: 0.9;
}

/* Responsive */
@media (max-width: 640px) {
  .permission-dialog {
    width: 95%;
    max-height: 90vh;
  }

  .permission-actions {
    flex-direction: column;
  }

  .action-btn {
    width: 100%;
  }
}
</style>
