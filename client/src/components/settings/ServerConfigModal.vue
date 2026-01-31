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
          <span :class="['status-badge', statusClass]">
            {{ statusLabel }}
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
              <div class="tool-desc-wrapper">
                <p 
                    class="tool-description" 
                    :class="{ 'expanded': tool._expanded }"
                >
                    {{ tool.description || 'No description available' }}
                </p>
                <button 
                    v-if="(tool.description || '').length > 60" 
                    @click="tool._expanded = !tool._expanded" 
                    class="expand-btn"
                >
                    <svg 
                        :class="{ 'rotated': tool._expanded }"
                        xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                    >
                        <polyline points="6 9 12 15 18 9"></polyline>
                    </svg>
                </button>
              </div>
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

      <!-- Tool Approvals Section -->
      <div class="approvals-section">
        <h3>Auto-Approved Tools</h3>
        <p class="section-description">Tools with "Always Allow" will execute without asking for permission.</p>
        
        <div v-if="serverApprovals.length > 0" class="approval-list">
          <div v-for="approval in serverApprovals" :key="approval.id" class="approval-item">
            <div class="approval-info">
              <strong class="approval-name">{{ approval.tool_name }}</strong>
              <span class="approval-badge">{{ approval.approval_type }}</span>
            </div>
            <button @click="revokeApproval(approval.tool_name)" class="revoke-btn">
              Revoke
            </button>
          </div>
        </div>
        <p v-else class="empty-approvals">No auto-approved tools for this server.</p>
      </div>


    </div>
    
    <ConfirmationModal
      :isOpen="showConfirm"
      :title="'Confirm Revocation'"
      :message="confirmMessage"
      @cancel="cancelRevoke"
      @confirm="executeRevoke"
    />
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue';
import { useToast } from 'vue-toastification';
import ConfirmationModal from './ConfirmationModal.vue';

const props = defineProps({
  isOpen: Boolean,
  serverId: Number,
  serverName: String,
  serverUrl: String,
  isActive: Boolean
});

const emit = defineEmits(['close', 'reauth-needed']);

const toast = useToast();
const tools = ref([]);
const serverApprovals = ref([]);
const loading = ref(false);
const error = ref(null);

// Computed Status
const statusClass = computed(() => {
  if (!props.isActive) return 'disabled';
  if (loading.value) return 'checking';
  if (error.value) return 'offline';
  return 'online';
});

const statusLabel = computed(() => {
  if (!props.isActive) return 'Disabled';
  if (loading.value) return 'Connecting...';
  if (error.value) return 'Offline';
  return 'Online';
});

// Confirmation State
const showConfirm = ref(false);
const confirmMessage = ref('');
const pendingRevokeTool = ref(null);

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

    if (response.status === 401) {
      const data = await response.json();
      if (data.code === 'auth_required') {
        toast.error(`Session expired: ${data.detail}`);
        emit('reauth-needed', props.serverId);
        // We stop loading but leave the modal open (or let parent close it)
        loading.value = false;
        error.value = "Authentication required. Please check the login prompt.";
        return;
      }
    }

    if (!response.ok) {
      throw new Error('Failed to load tools');
    }

    const data = await response.json();
    const loadedTools = Array.isArray(data) ? data : (data.tools || []);
    // Initialize expanded state for UI
    tools.value = loadedTools.map(t => ({ ...t, _expanded: false }));
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

const fetchApprovals = async () => {
  const headers = getAuthHeaders();
  if (!headers) return;

  try {
    const response = await fetch(`${API_URL}/api/tool-approvals`, { headers });
    if (response.ok) {
      const allApprovals = await response.json();
      
      // Filter logic:
      // 1. Match by stored server_name (if correct)
      // 2. OR match if approval tool name starts with "ServerName_" (unique name format)
      // 3. OR match if approval tool name ends with "_ToolName" (looser check)
      
      const serverPrefix = props.serverName.replace(/ /g, '') + '_';
      
      serverApprovals.value = allApprovals.filter(a => {
        // Direct match
        if (a.server_name === props.serverName) return true;
        
        // Prefix match (e.g. GitHub_search_repositories)
        if (a.tool_name.startsWith(serverPrefix)) return true;
        
        // Tool name suffix match (check against loaded tools)
        // This handles cases where unique name formatting might be complex
        return tools.value.some(t => {
             // Check if approval tool name implies this raw tool
             // e.g. "GitHub_search" ends with "_search" (or is just "search")
             return a.tool_name === t.name || a.tool_name.endsWith('_' + t.name);
        });
      });
    }
  } catch (err) {
    console.error("Failed to fetch approvals:", err);
  }
};

const revokeApproval = (toolName) => {
  pendingRevokeTool.value = toolName;
  confirmMessage.value = `Revoke "Always Allow" for ${toolName}?`;
  showConfirm.value = true;
};

const cancelRevoke = () => {
  showConfirm.value = false;
  pendingRevokeTool.value = null;
};

const executeRevoke = async () => {
  if (!pendingRevokeTool.value) return;
  const toolName = pendingRevokeTool.value;
  showConfirm.value = false;

  const headers = getAuthHeaders();
  if (!headers) return;

  try {
    const res = await fetch(`${API_URL}/api/tool-approvals/${encodeURIComponent(toolName)}`, { 
      method: 'DELETE', 
      headers 
    });
    
    if (res.ok) {
      toast.success(`Approval revoked for ${toolName}`);
      serverApprovals.value = serverApprovals.value.filter(a => a.tool_name !== toolName);
    } else {
      const e = await res.json();
      toast.error(`Revoke failed: ${e.detail}`);
    }
  } catch (err) {
    toast.error(`Error: ${err.message}`);
  } finally {
    pendingRevokeTool.value = null;
  }
};

const closeModal = () => {
  emit('close');
};

// Load tools and approvals when modal opens
watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    loadTools();
    fetchApprovals();
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
  max-width: 500px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h2 {
  margin: 0;
  font-size: 1.125rem;
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
  padding: 1rem 1.5rem;
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
  font-size: 0.85rem;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.status-badge.online {
  color: var(--text-primary);
}

.status-badge.online::before {
  content: '';
  display: block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #10b981; /* Green-500 */
  box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2);
}

.status-badge.offline {
  color: #ef4444;
}

.status-badge.checking {
  color: var(--text-secondary);
  font-style: italic;
  font-weight: 400;
}

.status-badge.disabled {
  color: var(--text-secondary);
}

.tools-section {
  flex: 1;
  overflow-y: auto;
  padding: 1rem 1.5rem;
}

.tools-section h3 {
  margin: 0 0 0.75rem 0;
  font-size: 1rem;
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
  padding: 0.75rem;
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
  font-size: 0.9rem;
  color: var(--text-primary);
  margin-bottom: 0.2rem;
}

.tool-desc-wrapper {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
}

.tool-description {
  margin: 0;
  font-size: 0.8rem;
  color: var(--text-secondary);
  line-height: 1.4;
  
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-word; /* Handle long words/urls */
}

.tool-description.expanded {
  -webkit-line-clamp: unset;
  overflow: visible;
}

.expand-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px;
  transition: color 0.2s;
}

.expand-btn:hover {
  color: var(--text-primary);
}

.expand-btn svg {
  transition: transform 0.2s ease;
}

.expand-btn svg.rotated {
  transform: rotate(180deg);
}

/* Approvals Section */
.approvals-section {
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--border-color);
}

.approvals-section h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.section-description {
  margin: 0 0 1rem 0;
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.approval-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.approval-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
}

.approval-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.approval-name {
  font-size: 0.95rem;
  color: var(--text-primary);
}

.approval-badge {
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
  background-color: var(--accent-color);
  color: white;
  text-transform: uppercase;
}

.revoke-btn {
  padding: 0.375rem 0.75rem;
  background-color: transparent;
  border: 1px solid #ef4444;
  color: #ef4444;
  border-radius: 4px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.revoke-btn:hover {
  background-color: #ef4444;
  color: white;
}

.empty-approvals {
  text-align: center;
  color: var(--text-secondary);
  font-style: italic;
  padding: 1rem;
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
