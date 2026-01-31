<template>
  <div class="settings-group">
    <h3>MCP Server Connections</h3>
    <p class="setting-description">Manage your stored Modern Context Protocol (MCP) server configurations. These are typically HTTP(S) endpoints for Server-Sent Events (SSE).</p>
    
    <div v-if="mcpServerSettings.length > 0" style="max-height: 300px; overflow-y: auto; border-radius: 8px; margin-bottom: 1.5rem;">
    <div v-for="setting in mcpServerSettings" :key="setting.id" class="setting-item connection-item" style="padding: 0.75rem; border-bottom: 1px solid var(--border-color);">
        <div class="setting-info">
        <label class="setting-label">{{ setting.server_name }}</label>
        <p class="setting-description">{{ setting.server_url }}</p>
        <p v-if="setting.description" class="setting-description small-text">{{ setting.description }}</p>
        </div>
        <div class="setting-control">
        <button @click="openConfigModal(setting)" class="form-button small-button">Configure</button>
        <button @click="reconnectServer(setting)" :disabled="reconnectingServerId === setting.id" class="form-button small-button secondary-button" style="margin-right: 0.5rem; display: inline-flex; align-items: center; justify-content: center; gap: 6px; min-width: 100px;" title="Verify connection & refresh tokens">
            <svg v-if="reconnectingServerId === setting.id" class="spin" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-6.219-8.56"></path></svg>
            <span v-else>Reconnect</span>
        </button>
        <button @click="deleteSetting(setting.id)" class="form-button small-button secondary-button">Delete</button>
        <label class="toggle-switch" style="margin-left: 0.5rem;"><input type="checkbox" v-model="setting.is_active" @change="toggleSettingActive(setting)"><span class="slider"></span></label>
        </div>
    </div>
    </div>
    <p v-else class="setting-description" style="margin-top: 1rem;">No MCP server connections saved yet.</p>
    <hr class="settings-divider">
    
    <h3>Add New MCP Server</h3>
    
    <!-- Presets Dropdown -->
    <div class="setting-item" style="border: 1px solid var(--border-color); border-radius: 6px; padding: 0.75rem 1rem; margin-bottom: 1rem;">
        <div class="setting-info" style="border:none;"><label class="setting-label" style="display:flex; align-items:center; gap:8px;"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg> Load Preset</label><p class="setting-description">Autofill settings for popular providers.</p></div>
        <div class="setting-control">
        <select @change="applyPreset($event.target.value)" class="form-input" style="cursor: pointer;">
            <option value="">Select a preset...</option>
            <option v-for="(config, name) in SERVER_PRESETS" :key="name" :value="name">{{ name }}</option>
        </select>
        </div>
    </div>

    <div class="setting-item" style="border-bottom: none; padding: 0.75rem 0;">
    <div class="setting-info"><label for="newServerName" class="setting-label">Server Name</label><p class="setting-description">A friendly, unique name for this connection (e.g., "My Dev MCP").</p></div>
    <div class="setting-control"><input type="text" id="newServerName" v-model="newMcpServer.server_name" class="form-input"></div>
    </div>
    <div class="setting-item" style="border-bottom: none; padding: 0.75rem 0;">
    <div class="setting-info"><label for="newMcpServerUrl" class="setting-label">MCP Server URL</label><p class="setting-description">The HTTP(S) endpoint for the Modern Context Protocol (SSE) server.</p></div>
    <div class="setting-control"><input type="text" id="newMcpServerUrl" v-model="newMcpServer.server_url" class="form-input"></div>
    </div>
    <div class="setting-item" style="border-bottom: none; padding: 0.75rem 0;">
    <div class="setting-info"><label for="newServerDescription" class="setting-label">Description (Optional)</label><p class="setting-description">Brief notes about this server or its purpose.</p></div>
    <div class="setting-control"><input type="text" id="newServerDescription" v-model="newMcpServer.description" class="form-input"></div>
    </div>
    
    <!-- Custom OAuth Options -->
    <div class="setting-item" style="border-bottom: none; padding: 0.75rem 0;">
    <div class="setting-info">
        <label class="setting-label">Requires OAuth?</label>
        <p class="setting-description">Enable if this server requires OAuth 2.0 authentication (e.g., custom remote servers).</p>
    </div>
    <div class="setting-control">
        <label class="toggle-switch">
        <input type="checkbox" v-model="newMcpServer.requires_oauth">
        <span class="slider"></span>
        </label>
    </div>
    </div>
    
    <div v-if="newMcpServer.requires_oauth" style="background: var(--bg-secondary); padding: 1rem; border-radius: 8px; margin-bottom: 1rem; border: 1px solid var(--border-color);">
    <h4 style="margin-top:0; margin-bottom: 1rem; font-size: 1rem;">OAuth Configuration</h4>
    <div class="setting-item" style="border:none; padding: 0.5rem 0;">
        <div class="setting-info"><label>Client ID</label></div>
        <div class="setting-control"><input type="text" v-model="newMcpServer.client_id" class="form-input" placeholder="Your Client ID"></div>
    </div>
    <div class="setting-item" style="border:none; padding: 0.5rem 0;">
        <div class="setting-info"><label>Client Secret</label></div>
        <div class="setting-control"><input type="password" v-model="newMcpServer.client_secret" class="form-input" placeholder="Your Client Secret"></div>
    </div>
    <div class="setting-item" style="border:none; padding: 0.5rem 0;">
        <div class="setting-info"><label>Scope (Optional)</label></div>
        <div class="setting-control"><input type="text" v-model="newMcpServer.scope" class="form-input" placeholder="e.g. read:user"></div>
    </div>

    <p class="setting-description small-text" style="margin-top: 5px; margin-bottom: 10px;">
        <router-link to="/client-registration" style="color: var(--primary-color); text-decoration: underline;">How to obtain these?</router-link>
    </p>
    
    <!-- Advanced Options Toggle -->
        <div class="setting-item" style="border:none; padding: 0.5rem 0; margin-top: 10px;">
        <div class="setting-info"><label>Advanced Options</label> <p class="setting-description small-text">Specify manual OAuth endpoints</p></div>
        <div class="setting-control">
            <label class="toggle-switch">
            <input type="checkbox" v-model="newMcpServer.show_advanced">
            <span class="slider"></span>
            </label>
        </div>
    </div>
    
    <div v-if="newMcpServer.show_advanced" style="border-left: 2px solid var(--border-color); padding-left: 1rem; margin-top: 0.5rem;">
            <div class="setting-item" style="border:none; padding: 0.5rem 0;">
            <div class="setting-info"><label>Authorization URL</label></div>
            <div class="setting-control"><input type="text" v-model="newMcpServer.authorization_url" class="form-input" placeholder="https://example.com/oauth/authorize"></div>
        </div>
            <div class="setting-item" style="border:none; padding: 0.5rem 0;">
            <div class="setting-info"><label>Token URL</label></div>
            <div class="setting-control"><input type="text" v-model="newMcpServer.token_url" class="form-input" placeholder="https://example.com/oauth/token"></div>
        </div>
    </div>
        <p class="setting-description small-text" style="margin-top: 1rem;">
        <strong>Note:</strong> We will attempt to discover authorization endpoints automatically from the Server URL.
    </p>
    </div>

    <div class="setting-item save-section">
    <button @click="saveNewConnection" :disabled="isTestingConnection" class="form-button primary-button" style="display: inline-flex; align-items: center; justify-content: center; gap: 6px; min-width: 140px;">
        <svg v-if="isTestingConnection" class="spin" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-6.219-8.56"></path></svg>
        <span v-else>{{ newMcpServer.requires_oauth ? 'Authenticate & Connect' : 'Test & Save Connection' }}</span>
    </button>
    </div>

    <!-- AUTH MODAL -->
    <div v-if="showAuthModal" class="modal-overlay">
        <div class="modal-content">
        <h3 class="modal-title">{{ authConfig.server?.id ? 'Reconnect to' : 'Connect to' }} {{ authConfig.server?.server_name }}</h3>
        <p class="setting-description" style="margin-bottom: 1rem;">
            {{ authConfig.server?.id 
                ? `Your session for ${authConfig.server?.server_name} has expired. Please re-authenticate to continue.`
                : `The app will open a popup to authenticate you with ${authConfig.server?.server_name}.` 
            }}
        </p>
        
        <div v-if="!authConfig.usingSharedId">
            <div v-if="authConfig.client_id && !authConfig.isEditingId" style="background: var(--bg-secondary); padding: 0.75rem; border-radius: 8px; margin-bottom: 1rem;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <span class="setting-label" style="display:block; font-size: 0.8em; color: var(--text-secondary);">Using Client ID</span>
                        <code style="font-size: 1em; color: var(--text-primary);">{{ authConfig.client_id }}</code>
                    </div>
                    <button @click="authConfig.isEditingId = true" class="footer-btn secondary" style="padding: 4px 8px; font-size: 0.8em;">Change</button>
                </div>
            </div>

            <div v-else>
                <div class="setting-item" style="border:none; padding: 0.5rem 0;">
                    <div class="setting-info" style="padding:0;"><label>Client ID</label></div>
                    <div class="setting-control" style="width: 100%;"><input type="text" v-model="authConfig.client_id" class="form-input" :placeholder="`Enter Client ID`"></div>
                </div>
                
                <p class="setting-description small-text" style="background: rgba(0,0,0,0.03); padding: 8px; border-radius: 4px;">
                    <strong>Why?</strong> Custom connections require your own Client ID from the provider's developer settings.
                </p>
            </div>
        </div>
        <div v-else>
                <p class="setting-description" style="background: rgba(0,255,0,0.05); padding: 0.75rem; border-radius: 8px; text-align: center;">
                <strong>Managed Authentication</strong><br>
                Server-provided ID active.
                </p>
        </div>
        
        <div class="modal-footer">
            <button @click="closeAuthModal" class="form-button secondary-button">Cancel</button>
            <button @click="startOAuthFlow" class="form-button primary-button">Authenticate & Connect</button>
        </div>
        </div>
    </div>

    <!-- Server Config Modal -->
    <ServerConfigModal
        :isOpen="showConfigModal"
        :serverId="configServer?.id"
        :serverName="configServer?.server_name"
        :serverUrl="configServer?.server_url"
        :isActive="configServer?.is_active"
        @close="closeConfigModal"
        @update-server="handleServerUpdate"
        @reauth-needed="handleReauthNeeded"
    />
    
    <ConfirmationModal
        :isOpen="showConfirm"
        :title="'Delete Connection'"
        :message="confirmMessage"
        :confirmText="'Delete'"
        :cancelText="'Cancel'"
        @cancel="cancelDelete"
        @confirm="executeDelete"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { useToast } from 'vue-toastification';
import ServerConfigModal from './ServerConfigModal.vue';
import ConfirmationModal from './ConfirmationModal.vue';

const BACKEND_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';
const toast = useToast();

const mcpServerSettings = ref([]);
const SERVER_PRESETS = ref({});
const preapprovedServers = ref([]); // Keeping for compatibility if needed
const isTestingConnection = ref(false);
const reconnectingServerId = ref(null);

const newMcpServer = reactive({
  server_name: '',
  server_url: '',
  description: '',
  is_active: true,
  requires_oauth: false,
  client_id: '',
  client_secret: '',
  scope: '',
  show_advanced: false,
  authorization_url: '',
  token_url: ''
});

// Auth Modal
const showAuthModal = ref(false);
const authConfig = reactive({
  server: null,
  client_id: '',
  client_secret: '',
  usingSharedId: false,
  isEditingId: false
});

// Config Modal
const showConfigModal = ref(false);
const configServer = ref(null);

// Confirm Modal
const showConfirm = ref(false);
const confirmMessage = ref('');
const pendingDeleteId = ref(null);

const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  if (!token) {
    toast.error('Authentication token not found. Please log in.'); return null;
  }
  return { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` };
};

const fetchMcpServerSettings = async () => {
  const headers = getAuthHeaders(); if (!headers) return;
  try {
    const response = await fetch(`${BACKEND_BASE_URL}/api/mcp/settings/`, { headers });
    if (response.ok) mcpServerSettings.value = await response.json();
    else { const e = await response.json(); toast.error(`Fetch failed: ${e.detail}`); }
  } catch (e) { toast.error(`Error: ${e.message}`); }
};

const fetchPreapprovedServers = async () => {
    try {
        const response = await fetch(`${BACKEND_BASE_URL}/api/mcp/presets`);
        if (response.ok) {
            const data = await response.json();
            SERVER_PRESETS.value = data;
             // Also store as array if needed for compatibility logic in openAuthModal
             preapprovedServers.value = Object.entries(data).map(([name, config]) => ({
                 server_name: name,
                 ...config
             }));
        } else {
             console.error("Failed to load presets");
        }
    } catch (e) {
        console.error("Error loading presets", e);
    }
};

const applyPreset = (presetName) => {
    if (!presetName || !SERVER_PRESETS.value[presetName]) return;
    const p = SERVER_PRESETS.value[presetName];
    Object.assign(newMcpServer, {
        server_name: presetName,
        server_url: p.server_url,
        description: p.description,
        requires_oauth: p.requires_oauth,
        authorization_url: p.authorization_url,
        token_url: p.token_url,
        scope: p.scope,
        show_advanced: p.show_advanced
    });
    toast.info(`Loaded preset for ${presetName}`);
};

const saveNewConnection = async () => {
  if (!newMcpServer.server_name || !newMcpServer.server_url) { toast.warning('Please provide a server name and URL.'); return; }
  
  try {
     new URL(newMcpServer.server_url);
  } catch (_) {
     toast.error("Please enter a valid URL (e.g., http://localhost:8000/sse)");
     return;
  }
  
  const isDuplicate = mcpServerSettings.value.some(s => 
      s.server_name === newMcpServer.server_name || 
      (s.server_url === newMcpServer.server_url && s.server_url !== '')
  );
  if (isDuplicate && !newMcpServer.requires_oauth) {
      toast.error("Duplicate Error: A server with this name or URL already exists.");
      return;
  }
  
  if (newMcpServer.requires_oauth) {
      if (!newMcpServer.client_id || !newMcpServer.client_secret) {
          toast.warning("Client ID and Secret are required for custom OAuth.");
          return;
      }
      
      const headers = getAuthHeaders();
      try {
           const initRes = await fetch(`${BACKEND_BASE_URL}/api/mcp/oauth/init`, {
             method: 'POST',
             headers,
             body: JSON.stringify({
                 server_name: newMcpServer.server_name,
                 server_url: newMcpServer.server_url,
                 client_id: newMcpServer.client_id,
                 client_secret: newMcpServer.client_secret,
                 scope: newMcpServer.scope,
                 redirect_uri: `${BACKEND_BASE_URL}/api/mcp/oauth/callback`,
                 authorization_url: newMcpServer.authorization_url,
                 token_url: newMcpServer.token_url
             })
           });
           
           if (!initRes.ok) {
                const err = await initRes.json();
                toast.error(`Error starting auth: ${err.detail}`);
                return;
           }
           
           const { auth_url } = await initRes.json();
           const popup = window.open(auth_url, 'OAuth', 'width=600,height=700');
           
           const messageHandler = async (event) => {
             if (event.data.type === 'oauth-callback') {
                 window.removeEventListener('message', messageHandler);
                 try {
                     const finalRes = await fetch(`${BACKEND_BASE_URL}/api/mcp/oauth/finalize?code=${event.data.code}&state=${event.data.state}`, {
                         method: 'POST',
                         headers
                     });
                     if (finalRes.ok) {
                         const saved = await finalRes.json();
                         toast.success("Connected & Saved successfully!");
                         mcpServerSettings.value.push(saved);
                         Object.assign(newMcpServer, { server_name: '', server_url: '', is_active: true, description: '', requires_oauth: false, client_id: '', client_secret: '', scope: '' });
                         fetchMcpServerSettings(); 
                     } else {
                         const err = await finalRes.json();
                         toast.error(`Finalization failed: ${err.detail}`);
                     }
                 } catch(e) {
                     toast.error("Error finalizing connection.");
                 }
             }
           };
           window.addEventListener('message', messageHandler);
           
      } catch (e) {
          toast.error(`Error initiating auth: ${e.message}`);
      }
      return;
  }

  const headers = getAuthHeaders(); if (!headers) return;
  
  isTestingConnection.value = true;
  try {
    const res = await fetch(`${BACKEND_BASE_URL}/api/mcp/settings/`, { method: 'POST', headers, body: JSON.stringify(newMcpServer) });
    if (res.ok) {
      const saved = await res.json();
      toast.success('Connection verified & saved!'); mcpServerSettings.value.push(saved);
      Object.assign(newMcpServer, { server_name: '', server_url: '', is_active: true, description: '', requires_oauth: false, client_id: '', client_secret: '', scope: '' });
    } else { const e = await res.json(); toast.error(`Save failed: ${e.detail}`); }
  } catch (e) { toast.error(`Error: ${e.message}`); }
  finally { isTestingConnection.value = false; }
};

const toggleSettingActive = async (setting) => {
  const headers = getAuthHeaders(); if (!headers) { setting.is_active = !setting.is_active; return; }
  try {
    const res = await fetch(`${BACKEND_BASE_URL}/api/mcp/settings/${setting.id}`, { method: 'PATCH', headers, body: JSON.stringify({ is_active: setting.is_active }) });
    if (!res.ok) { const e = await res.json(); toast.error(`Update failed: ${e.detail}`); setting.is_active = !setting.is_active; }
    else { toast.success(`Server ${setting.is_active ? 'enabled' : 'disabled'}`); }
  } catch (e) { toast.error(`Error: ${e.message}`); setting.is_active = !setting.is_active; }
};

const deleteSetting = (settingId) => {
  pendingDeleteId.value = settingId;
  confirmMessage.value = 'Are you sure you want to delete this connection?';
  showConfirm.value = true;
};

const cancelDelete = () => {
    showConfirm.value = false;
    pendingDeleteId.value = null;
};

const executeDelete = async () => {
  if (!pendingDeleteId.value) return;
  const settingId = pendingDeleteId.value;
  showConfirm.value = false;

  const headers = getAuthHeaders(); if (!headers) return;
  try {
    const res = await fetch(`${BACKEND_BASE_URL}/api/mcp/settings/${settingId}`, { method: 'DELETE', headers });
    if (res.ok) { toast.success('Connection deleted'); mcpServerSettings.value = mcpServerSettings.value.filter(s => s.id !== settingId); }
    else { const e = await res.json(); toast.error(`Delete failed: ${e.detail}`); }
  } catch (e) { toast.error(`Error: ${e.message}`); }
  finally {
      pendingDeleteId.value = null;
  }
};

const reconnectServer = async (setting) => {
  const headers = getAuthHeaders(); if (!headers) return;
  reconnectingServerId.value = setting.id;
  toast.info(`Reconnecting to ${setting.server_name}...`);
  try {
    const res = await fetch(`${BACKEND_BASE_URL}/api/mcp/settings/${setting.id}/reconnect`, { method: 'POST', headers });
    const data = await res.json();
    
    if (res.status === 401 && data.code === 'auth_required') {
        toast.error(`Session expired: ${data.detail}`);
        handleReauthNeeded(setting.id);
        return;
    }

    if (res.ok) {
        toast.success(data.message);
    } else {
        toast.error(`Reconnect failed: ${data.detail}`);
    }
  } catch (e) {
      toast.error(`Error: ${e.message}`);
  } finally {
      reconnectingServerId.value = null;
  }
};

const openConfigModal = (server) => {
  configServer.value = server;
  showConfigModal.value = true;
};

const closeConfigModal = () => {
  showConfigModal.value = false;
  configServer.value = null;
};

const handleServerUpdate = () => {
  fetchMcpServerSettings();
};

const handleReauthNeeded = (serverId) => {
  const server = mcpServerSettings.value.find(s => s.id === serverId);
  if (server) {
      closeConfigModal();
      openAuthModal(server);
  }
};

const openAuthModal = (server) => {
  authConfig.server = server;
  let config = server.oauth_config;
  if (!config) {
      const match = preapprovedServers.value.find(s => s.server_name === server.server_name);
      if (match && match.oauth_config) {
          config = match.oauth_config;
      }
  }

  const sharedId = config?.client_id;
  if (sharedId) {
      authConfig.client_id = sharedId;
      authConfig.usingSharedId = true;
  } else {
      authConfig.client_id = server.client_id || '';
      authConfig.usingSharedId = false;
  }
  
  authConfig.client_secret = '';
  showAuthModal.value = true;
};

const closeAuthModal = () => {
  showAuthModal.value = false;
  authConfig.server = null;
};

const startOAuthFlow = async () => {
  if (!authConfig.usingSharedId && !authConfig.client_id) {
     toast.warning("Please provide Client ID");
     return;
  }
  
  const headers = getAuthHeaders();
  if(!headers) return;

  try {
     const initRes = await fetch(`${BACKEND_BASE_URL}/api/mcp/oauth/init`, {
         method: 'POST',
         headers,
         body: JSON.stringify({
             server_name: authConfig.server.server_name,
             server_url: authConfig.server.server_url,
             client_id: authConfig.client_id,
             client_secret: authConfig.server.client_secret || "", 
             scope: authConfig.server.scope || "",
             authorization_url: authConfig.server.authorization_url || "",
             token_url: authConfig.server.token_url || "",
             redirect_uri: `${BACKEND_BASE_URL}/api/mcp/oauth/callback`
         })
     });
     
     if (!initRes.ok) {
         const err = await initRes.json();
         toast.error(`Error starting auth: ${err.detail}`);
         return;
     }
     
     const { auth_url } = await initRes.json();
     
     const popup = window.open(auth_url, 'OAuth', 'width=600,height=700');
     
     const messageHandler = async (event) => {
         if (event.data.type === 'oauth-callback') {
             window.removeEventListener('message', messageHandler);
             try {
                 const finalRes = await fetch(`${BACKEND_BASE_URL}/api/mcp/oauth/finalize?code=${event.data.code}&state=${event.data.state}`, {
                     method: 'POST',
                     headers
                 });
                 if (finalRes.ok) {
                     toast.success("Connected successfully!");
                     closeAuthModal();
                     fetchMcpServerSettings();
                 } else {
                     const err = await finalRes.json();
                     toast.error(`Failed to finalize connection: ${err.detail}`);
                 }
             } catch(e) {
                 console.error(e);
                 toast.error("Error finalizing connection.");
             }
         }
     };
     window.addEventListener('message', messageHandler);
     
  } catch(e) {
      console.error(e);
      toast.error("Error initiating auth flow.");
  }
};

onMounted(() => {
    fetchMcpServerSettings();
    fetchPreapprovedServers();
});
</script>

<style scoped>
/* Replicating/Refining styles for independent component */
.settings-group {
    min-height: 100%;
    display: flex;
    flex-direction: column;
}

h3 {
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.settings-group > h3:first-child {
    margin-top: 0;
}

.settings-divider {
  border: none;
  border-top: 1px solid var(--border-color);
  margin: 1.5rem 0;
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 0;
  border-bottom: 1px solid var(--border-color);
}

.setting-item.save-section {
  justify-content: flex-end;
}

.setting-info {
  flex-grow: 1;
  padding-right: 1.5rem;
}

.setting-info label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  margin-bottom: 0.2rem;
  color: var(--text-primary);
}

.setting-description {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.4;
}

.small-text {
  font-size: 0.75rem;
}

.setting-control {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.form-input {
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  transition: all 0.2s;
  background-color: var(--bg-secondary);
  color: var(--text-primary);
  width: 100%;
}

.form-input:focus {
  outline: none;
  border-color: var(--accent-color);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--accent-color) 25%, transparent);
}

.form-button {
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  font-weight: 500;
  border-radius: 6px;
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.2s;
  background-color: var(--accent-color);
  color: var(--bg-primary);
  border-color: var(--accent-color);
}

.form-button:hover {
  background-color: var(--accent-hover);
}

.form-button.secondary-button {
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
}

.form-button.secondary-button:hover {
  background-color: var(--hover-bg);
  border-color: var(--text-secondary);
  opacity: 1;
}

.form-button.small-button {
  padding: 0.3rem 0.6rem;
  font-size: 0.8rem;
}

.toggle-switch {
  position: relative;
  display: inline-block;
  width: 40px;
  height: 24px;
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
  transition: .4s;
  border-radius: 24px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: .4s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: var(--accent-color);
}

input:checked + .slider:before {
  transform: translateX(16px);
}

.action-footer {
    display: flex;
    justify-content: flex-end;
}

@keyframes spin { 
  100% { transform: rotate(360deg); } 
}
.spin { 
  animation: spin 1s linear infinite; 
}

/* Modal Styles Reuse */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background-color: var(--bg-primary);
  border-radius: 8px; /* Compact */
  padding: 1.5rem; /* Compact */
  width: 90%;
  max-width: 450px; /* Compact */
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  border: 1px solid var(--border-color);
}

.modal-title {
  margin-top: 0;
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 1rem;
}

.modal-footer {
  margin-top: 1.5rem;
  display: flex; /* Ensure button group is flex */
  justify-content: flex-end; /* Align right */
  gap: 0.75rem; /* Spacing between buttons */
}
</style>
