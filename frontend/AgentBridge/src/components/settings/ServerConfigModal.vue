<template>
  <div v-if="isOpen" class="modal-overlay" @click.self="closeModal">
    <div class="config-modal">
      <!-- Header -->
      <div class="modal-header">
        <h2>Configure {{ serverName }}</h2>
        <button @click="closeModal" class="close-btn">&times;</button>
      </div>

      <!-- Server Info -->
      <div class="server-info">
        <div class="info-row">
          <span class="label">URL:</span>
          <span class="value">{{ serverUrl }}</span>
        </div>
        <div class="info-row">
          <span class="label">Status:</span>
          <span :class="['status-badge', isActive ? 'active' : 'inactive']">
            {{ isActive ? 'Active' : 'Inactive' }}
          </span>
        </div>
      </div>

      <!-- Tools Section -->
      <div class="tools-section">
        <h3>Available Tools ({{ tools.length }})</h3>
        
        <div v-if="loading" class="loading-state">
          <div class="spinner"></div>
          <p>Loading tools...</p>
        </div>

        <div v-else-if="error" class="error-state">
          <p>{{ error }}</p>
          <button @click="loadTools" class="retry-btn">Retry</button>
        </div>

        <div v-else-if="tools.length === 0" class="empty-state">
          <p>No tools available for this server.</p>
        </div>

        <div v-else class="tool-list">
          <div v-for="tool in tools" :key="tool.name" class="tool-item">
            <div class="tool-info">
              <strong class="tool-name">{{ tool.name }}</strong>
              <p class="tool-description">{{ tool.description || 'No description available' }}</p>
            </div>
            <label class="toggle-switch">
              <input 
                type="checkbox" 
                :checked="tool.is_enabled"
                @change="toggleTool(tool)"
              >
              <span class="slider"></span>
            </label>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="modal-footer">
        <button @click="closeModal" class="footer-btn secondary">Close</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import { useToast } from 'vue-toastification';

const props = defineProps({
  isOpen: Boolean,
  serverId: Number,
  serverName: String,
  serverUrl: String,
  isActive: Boolean
});

const emit = defineEmits(['close']);

const toast = useToast();
const tools = ref([]);
const loading = ref(false);
const error = ref(null);

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';

const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  if (!token) {
    toast.error('Authentication required');
    return null;
  }
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  };
};

const loadTools = async () => {
  if (!props.serverId) return;
  
  loading.value = true;
  error.value = null;
  
  const headers = getAuthHeaders();
  if (!headers) {
    loading.value = false;
    return;
  }

  try {
    const response = await fetch(`${API_URL}/api/mcp/settings/${props.serverId}/tools`, {
      headers
    });

    if (!response.ok) {
      throw new Error('Failed to load tools');
    }

    const data = await response.json();
    tools.value = Array.isArray(data) ? data : (data.tools || []);
  } catch (err) {
    error.value = err.message;
    toast.error(`Error loading tools: ${err.message}`);
  } finally {
    loading.value = false;
  }
};

const toggleTool = async (tool) => {
  const newState = !tool.is_enabled;
  const headers = getAuthHeaders();
  if (!headers) return;

  try {
    const response = await fetch(
      `${API_URL}/api/mcp/settings/${props.serverId}/tools/${tool.name}`,
      {
        method: 'PATCH',
        headers,
        body: JSON.stringify({ is_enabled: newState })
      }
    );

    if (!response.ok) {
      throw new Error('Failed to update tool');
    }

    // Update local state
    tool.is_enabled = newState;
    toast.success(`Tool ${tool.name} ${newState ? 'enabled' : 'disabled'}`);
  } catch (err) {
    toast.error(`Error updating tool: ${err.message}`);
    // Revert on error
    tool.is_enabled = !newState;
  }
};

const closeModal = () => {
  emit('close');
};

// Load tools when modal opens
watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    loadTools();
  }
});
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.config-modal {
  background-color: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-primary);
}

.close-btn {
  background: none;
  border: none;
  font-size: 2rem;
  color: var(--text-secondary);
  cursor: pointer;
  line-height: 1;
  padding: 0;
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s;
}

.close-btn:hover {
  color: var(--text-primary);
}

.server-info {
  padding: 1.5rem;
  border-bottom: 1px solid var(--border-color);
  background-color: var(--bg-secondary);
}

.info-row {
  display: flex;
  align-items: center;
  margin-bottom: 0.5rem;
}

.info-row:last-child {
  margin-bottom: 0;
}

.label {
  font-weight: 500;
  color: var(--text-secondary);
  min-width: 60px;
}

.value {
  color: var(--text-primary);
  font-family: 'Courier New', monospace;
  font-size: 0.9rem;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 4px;
  font-size: 0.875rem;
  font-weight: 500;
}

.status-badge.active {
  background-color: var(--text-primary);
  color: var(--bg-primary);
}

.status-badge.inactive {
  background-color: var(--bg-secondary);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

.tools-section {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
}

.tools-section h3 {
  margin: 0 0 1rem 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-primary);
}

.loading-state,
.error-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  color: var(--text-secondary);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border-color);
  border-top-color: var(--text-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.retry-btn {
  margin-top: 1rem;
  padding: 0.5rem 1rem;
  background-color: var(--text-primary);
  color: var(--bg-primary);
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
}

.retry-btn:hover {
  opacity: 0.9;
}

.tool-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.tool-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 1rem;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  transition: border-color 0.2s;
}

.tool-item:hover {
  border-color: var(--text-primary);
}

.tool-info {
  flex: 1;
  margin-right: 1rem;
}

.tool-name {
  display: block;
  font-size: 1rem;
  color: var(--text-primary);
  margin-bottom: 0.25rem;
}

.tool-description {
  margin: 0;
  font-size: 0.875rem;
  color: var(--text-secondary);
  line-height: 1.4;
}

/* Toggle Switch */
.toggle-switch {
  position: relative;
  display: inline-block;
  width: 48px;
  height: 24px;
  flex-shrink: 0;
}

.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--border-color);
  transition: 0.3s;
  border-radius: 24px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: var(--bg-primary);
  transition: 0.3s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: var(--text-primary);
}

input:checked + .slider:before {
  transform: translateX(24px);
}

.modal-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--border-color);
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.footer-btn {
  padding: 0.5rem 1.25rem;
  border-radius: 4px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.footer-btn.secondary {
  background-color: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-primary);
}

.footer-btn.secondary:hover {
  background-color: var(--hover-bg);
}
</style>
