<template>
  <div class="settings-container">
    <header class="settings-header">
      <h2 class="settings-title">Settings</h2>
      <div class="search-bar-wrapper">
        <svg class="search-icon" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
        <input type="text" placeholder="Search settings" class="search-input">
      </div>
    </header>

    <div class="settings-body">
      <aside class="settings-nav">
        <ul>
          <li class="nav-heading">User</li>
          <li><a href="#" @click.prevent="setActiveCategory('profile')" :class="{ active: activeCategory === 'profile' }"><svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>Profile</a></li>
          <li class="nav-heading">Application</li>
          <li><a href="#" @click.prevent="setActiveCategory('appearance')" :class="{ active: activeCategory === 'appearance' }"><svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"></path></svg>Appearance</a></li>
          <li><a href="#" @click.prevent="setActiveCategory('connections')" :class="{ active: activeCategory === 'connections' }"><svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>Connections</a></li>
        </ul>
      </aside>

      <main class="settings-content">
        <!-- ==== UPDATED PROFILE SECTION ==== -->
        <div v-if="activeCategory === 'profile'" class="settings-group">
          <div v-if="profileMessage" :class="['message', isProfileError ? 'error' : 'success']">
            {{ profileMessage }}
          </div>
          <div class="setting-item">
            <div class="setting-info">
              <label for="userName">Username</label>
              <p class="setting-description">This name will be displayed in your profile and used for mentions.</p>
            </div>
            <div class="setting-control">
              <input type="text" id="userName" v-model="profileForm.username" class="form-input" :disabled="!isEditingProfile">
            </div>
          </div>
          <div class="setting-item">
            <div class="setting-info">
              <label for="userEmail">Email Address</label>
              <p class="setting-description">Your primary email for notifications and account management.</p>
            </div>
            <div class="setting-control">
              <input type="email" id="userEmail" v-model="profileForm.email" class="form-input" :disabled="!isEditingProfile">
            </div>
          </div>
          <div class="setting-item action-footer">
            <div v-if="!isEditingProfile" class="button-group">
              <button @click="startEditingProfile" class="form-button">Edit Profile</button>
            </div>
            <div v-else class="button-group">
              <button @click="cancelEditingProfile" class="form-button secondary-button">Cancel</button>
              <button @click="handleProfileUpdate" class="form-button">Save Changes</button>
            </div>
          </div>
        </div>
        <!-- ==== END UPDATED PROFILE SECTION ==== -->

        <!-- UNCHANGED APPEARANCE SECTION -->
        <div v-if="activeCategory === 'appearance'" class="settings-group">
          <div class="setting-item">
            <div class="setting-info">
              <label class="setting-label">UI Theme</label>
              <p class="setting-description">The theme toggle is available globally in the header.</p>
            </div>
            <div class="setting-control">
              <p class="setting-description">Use <svg xmlns="http://www.w3.org/2000/svg" style="display:inline-block; vertical-align: sub;" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg> / <svg xmlns="http://www.w3.org/2000/svg" style="display:inline-block; vertical-align: sub;" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg> in top right.</p>
            </div>
          </div>
          <div class="setting-item">
            <div class="setting-info">
              <label class="setting-label">Compact UI</label>
              <p class="setting-description">Reduce padding and margins for a denser interface.</p>
            </div>
            <div class="setting-control">
              <label class="toggle-switch">
                <input type="checkbox" v-model="compactUiEnabled">
                <span class="slider"></span>
              </label>
            </div>
          </div>
        </div>

        <!-- UNCHANGED CONNECTIONS SECTION -->
        <div v-if="activeCategory === 'connections'" class="settings-group">
          <h3>MCP Server Connections</h3>
          <p class="setting-description">Manage your stored Modern Context Protocol (MCP) server configurations. These are typically HTTP(S) endpoints for Server-Sent Events (SSE).</p>
          <div v-if="mcpServerSettings.length > 0">
            <div v-for="setting in mcpServerSettings" :key="setting.id" class="setting-item connection-item">
              <div class="setting-info">
                <label class="setting-label">{{ setting.server_name }}</label>
                <p class="setting-description">{{ setting.server_url }}</p>
                <p v-if="setting.description" class="setting-description small-text">{{ setting.description }}</p>
              </div>
              <div class="setting-control">
                <button @click="editSetting(setting)" class="form-button small-button">Edit</button>
                <button @click="deleteSetting(setting.id)" class="form-button small-button delete-button">Delete</button>
                <label class="toggle-switch"><input type="checkbox" v-model="setting.is_active" @change="toggleSettingActive(setting)"><span class="slider"></span></label>
              </div>
            </div>
          </div>
          <p v-else class="setting-description" style="margin-top: 1rem;">No MCP server connections saved yet.</p>
          <hr class="settings-divider">
          
          <h3>Available Preapproved Servers</h3>
          <div v-if="preapprovedServers.length > 0">
             <div v-for="server in preapprovedServers" :key="server.server_name" class="setting-item connection-item">
               <div class="setting-info">
                 <label class="setting-label">{{ server.server_name }}</label>
                 <p class="setting-description">{{ server.description }}</p>
                 <p class="setting-description small-text">URL: {{ server.server_url }} <span v-if="server.type === 'local'" style="color: var(--accent-color); font-weight: bold;">(Requires Local Setup)</span></p>
               </div>
               <div class="setting-control">
                  <button @click="addPreapprovedServer(server)" class="form-button small-button" :disabled="mcpServerSettings.some(s => s.server_name === server.server_name)">
                    {{ mcpServerSettings.some(s => s.server_name === server.server_name) ? 'Added' : 'Add' }}
                  </button>
               </div>
             </div>
          </div>
          <p v-else class="setting-description">No preapproved servers available.</p>
          
          <hr class="settings-divider">
          <h3>Add New MCP Server</h3>
          <div class="setting-item">
            <div class="setting-info"><label for="newServerName" class="setting-label">Server Name</label><p class="setting-description">A friendly, unique name for this connection (e.g., "My Dev MCP").</p></div>
            <div class="setting-control"><input type="text" id="newServerName" v-model="newMcpServer.server_name" class="form-input"></div>
          </div>
          <div class="setting-item">
            <div class="setting-info"><label for="newMcpServerUrl" class="setting-label">MCP Server URL</label><p class="setting-description">The HTTP(S) endpoint for the Modern Context Protocol (SSE) server (e.g., `http://localhost:8001/v1/socket`).</p></div>
            <div class="setting-control"><input type="text" id="newMcpServerUrl" v-model="newMcpServer.server_url" class="form-input"></div>
          </div>
          <div class="setting-item">
            <div class="setting-info"><label for="newServerDescription" class="setting-label">Description (Optional)</label><p class="setting-description">Brief notes about this server or its purpose.</p></div>
            <div class="setting-control"><input type="text" id="newServerDescription" v-model="newMcpServer.description" class="form-input"></div>
          </div>
          <div class="setting-item save-section">
            <button @click="testNewConnection" class="form-button secondary-button">Test New Connection</button>
            <button @click="saveNewConnection" class="form-button primary-button">Save New Connection</button>
          </div>
        </div>

      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';

const BACKEND_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';
const activeCategory = ref('profile'); // Default to profile

// --- Profile State ---
const isEditingProfile = ref(false);
const profileForm = reactive({ username: '', email: '' });
const profileMessage = ref('');
const isProfileError = ref(false);

// --- Appearance State ---
const compactUiEnabled = ref(false);

// --- Connections State ---
const mcpServerSettings = ref([]);
const preapprovedServers = ref([]);
const newMcpServer = reactive({ server_name: '', server_url: '', is_active: true, description: '' });

// --- UTILITY & NAVIGATION ---
const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  if (!token) {
    alert('Authentication token not found. Please log in.'); return null;
  }
  return { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` };
};

const setActiveCategory = (category) => {
  activeCategory.value = category;
  if (category === 'profile') loadProfileData();
  if (category === 'profile') loadProfileData();
  if (category === 'connections') {
    fetchMcpServerSettings();
    fetchPreapprovedServers();
  }
};

// --- PROFILE METHODS ---
const loadProfileData = () => {
  const storedUser = localStorage.getItem('user');
  if (storedUser) {
    try {
      const userData = JSON.parse(storedUser);
      profileForm.username = userData.username || '';
      profileForm.email = userData.email || '';
    } catch (e) { console.error("Failed to parse user data", e); }
  }
};

const startEditingProfile = () => {
  isEditingProfile.value = true;
  profileMessage.value = '';
};

const cancelEditingProfile = () => {
  isEditingProfile.value = false;
  loadProfileData(); // Revert any changes by reloading from localStorage
};

const handleProfileUpdate = async () => {
  const headers = getAuthHeaders(); if (!headers) return;
  profileMessage.value = 'Saving...'; isProfileError.value = false;
  try {
    const response = await fetch(`${BACKEND_BASE_URL}/users/me`, { method: 'PUT', headers, body: JSON.stringify(profileForm) });
    const updatedUser = await response.json();
    if (!response.ok) throw new Error(updatedUser.detail || 'Failed to update profile.');
    localStorage.setItem('user', JSON.stringify(updatedUser));
    profileMessage.value = 'Profile updated successfully!';
    isEditingProfile.value = false;
  } catch (error) {
    profileMessage.value = error.message; isProfileError.value = true;
  }
};

// --- CONNECTIONS METHODS (Unchanged logic) ---
const fetchMcpServerSettings = async () => {
  const headers = getAuthHeaders(); if (!headers) return;
  try {
    const response = await fetch(`${BACKEND_BASE_URL}/api/mcp/settings/`, { headers });
    if (response.ok) mcpServerSettings.value = await response.json();
    else { const e = await response.json(); alert(`Fetch failed: ${e.detail}`); }
  } catch (e) { alert(`Error: ${e.message}`); }
};

const fetchPreapprovedServers = async () => {
  const headers = getAuthHeaders(); if (!headers) return;
  try {
    const response = await fetch(`${BACKEND_BASE_URL}/api/mcp/preapproved-servers`, { headers });
    if (response.ok) preapprovedServers.value = await response.json();
    else { console.error("Failed to fetch preapproved servers"); }
  } catch (e) { console.error("Error fetching preapproved servers:", e); }
};

const addPreapprovedServer = async (server) => {
  const exists = mcpServerSettings.value.some(s => s.server_name === server.server_name);
  if (exists) { alert('This server is already in your list.'); return; }
  
  const headers = getAuthHeaders(); if (!headers) return;
  
  const finalPayload = {
      server_name: server.server_name,
      server_url: server.server_url,
      description: server.description,
      is_active: true
  };

  try {
      const res = await fetch(`${BACKEND_BASE_URL}/api/mcp/settings/`, { method: 'POST', headers, body: JSON.stringify(finalPayload) });
      if (res.ok) {
        const saved = await res.json();
        alert('Server added successfully!');
        mcpServerSettings.value.push(saved);
      } else { const e = await res.json(); alert(`Failed to add server: ${e.detail}`); }
  } catch(e) { alert(`Error: ${e.message}`); }
};

const testNewConnection = async () => {
  if (!newMcpServer.server_url) { alert('Please enter a server URL.'); return; }
  try {
    const res = await fetch(`${BACKEND_BASE_URL}/api/mcp/test-connection`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ server_url: newMcpServer.server_url }),
    });
    const data = await res.json();
    alert(res.ok ? `Success: ${data.message}` : `Failed: ${data.detail}`);
  } catch (e) { alert(`Error: ${e.message}`); }
};

const saveNewConnection = async () => {
  if (!newMcpServer.server_name || !newMcpServer.server_url) { alert('Please provide a server name and URL.'); return; }
  const headers = getAuthHeaders(); if (!headers) return;
  try {
    const res = await fetch(`${BACKEND_BASE_URL}/api/mcp/settings/`, { method: 'POST', headers, body: JSON.stringify(newMcpServer) });
    if (res.ok) {
      const saved = await res.json();
      alert('Connection saved!'); mcpServerSettings.value.push(saved);
      Object.assign(newMcpServer, { server_name: '', server_url: '', is_active: true, description: '' });
    } else { const e = await res.json(); alert(`Save failed: ${e.detail}`); }
  } catch (e) { alert(`Error: ${e.message}`); }
};

const editSetting = (setting) => alert(`Editing: ${setting.server_name}`);

const toggleSettingActive = async (setting) => {
  const headers = getAuthHeaders(); if (!headers) { setting.is_active = !setting.is_active; return; }
  try {
    const res = await fetch(`${BACKEND_BASE_URL}/api/mcp/settings/${setting.id}`, { method: 'PATCH', headers, body: JSON.stringify({ is_active: setting.is_active }) });
    if (!res.ok) { const e = await res.json(); alert(`Update failed: ${e.detail}`); setting.is_active = !setting.is_active; }
  } catch (e) { alert(`Error: ${e.message}`); setting.is_active = !setting.is_active; }
};

const deleteSetting = async (settingId) => {
  if (!confirm('Are you sure you want to delete this connection?')) return;
  const headers = getAuthHeaders(); if (!headers) return;
  try {
    const res = await fetch(`${BACKEND_BASE_URL}/api/mcp/settings/${settingId}`, { method: 'DELETE', headers });
    if (res.ok) { alert('Deleted!'); mcpServerSettings.value = mcpServerSettings.value.filter(s => s.id !== settingId); }
    else { const e = await res.json(); alert(`Delete failed: ${e.detail}`); }
  } catch (e) { alert(`Error: ${e.message}`); }
};

// --- LIFECYCLE HOOK ---
onMounted(() => {
  // Load data for the default active category
  if (activeCategory.value === 'profile') {
    loadProfileData();
  }
});
</script>

<style scoped>
/* Main Container & Layout */
/* Main Container & Layout */
.settings-container {
  display: flex;
  flex-direction: column;
  height: 100vh; /* Full viewport height so scrolling works properly */
  background-color: var(--bg-primary);
  color: var(--text-primary);
}

.settings-header {
  display: flex;
  align-items: center;
  gap: 2rem;
  padding: 1rem 2rem;
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0; /* Keep header height fixed */
}

.settings-title {
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0;
}

.settings-body {
  display: flex;
  flex-grow: 1;
  height: 100%;
  overflow: hidden; /* Prevent page-level scrollbars */
}

/* Search */
.search-bar-wrapper {
  position: relative;
  width: 100%;
  max-width: 400px;
}

.search-icon {
  position: absolute;
  top: 50%;
  left: 12px;
  transform: translateY(-50%);
  color: var(--text-secondary);
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: 0.6rem 1rem 0.6rem 2.5rem;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 1rem;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: var(--accent-color);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--accent-color) 25%, transparent);
}

/* Nav */
.settings-nav {
  width: 260px;
  flex-shrink: 0;
  padding: 1.5rem 1rem;
  border-right: 1px solid var(--border-color);
  overflow-y: auto; /* Nav can scroll if needed */
}

.settings-nav ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.settings-nav li {
  margin-bottom: 4px;
}

.nav-heading {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  color: var(--text-secondary);
  padding: 1rem 0.75rem 0.5rem;
}

.settings-nav a {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  text-decoration: none;
  color: var(--text-secondary);
  border-radius: 6px;
  font-weight: 500;
  transition: background-color 0.2s, color 0.2s;
}

.settings-nav a:hover {
  background-color: var(--bg-secondary);
  color: var(--text-primary);
}

.settings-nav a.active {
  background-color: var(--accent-color);
  color: white;
}

.settings-nav a.active svg {
  stroke: white;
}

/* Content */
.settings-content {
  flex-grow: 1;
  padding: 2.5rem 3rem;
  padding-bottom: 70px;
  overflow-y: auto; /* Scrollbar appears here */
  height: 100%;
}


/* --- Custom Scrollbar Styling (for Webkit) --- */
.settings-content::-webkit-scrollbar {
  width: 8px;
}
.settings-content::-webkit-scrollbar-track {
  background: transparent;
}
.settings-content::-webkit-scrollbar-thumb {
  background-color: var(--text-secondary);
  border-radius: 10px;
  border: 2px solid var(--bg-primary);
}
.settings-content::-webkit-scrollbar-thumb:hover {
  background-color: var(--text-primary);
}

/* Settings Group + Items */
.settings-group h3 {
  margin-top: 2rem;
  margin-bottom: 1rem;
  font-size: 1.25rem;
  color: var(--text-primary);
}

.settings-divider {
  border: none;
  border-top: 1px solid var(--border-color);
  margin: 2rem 0;
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 0;
  border-bottom: 1px solid var(--border-color);
}

.settings-group > .setting-item:last-child {
  border-bottom: none;
}

.setting-info {
  flex-grow: 1;
  padding-right: 2rem;
}

.setting-info label {
  display: block;
  font-size: 1rem;
  font-weight: 500;
  margin-bottom: 0.25rem;
  color: var(--text-primary);
}

.setting-description {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin: 0;
}

.small-text {
  font-size: 0.8rem;
}

.setting-control {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 1rem;
}

/* Form Elements */
.message {
  margin-bottom: 1.5rem;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.9rem;
  text-align: center;
}

.message.success {
  background-color: color-mix(in srgb, var(--accent-color) 15%, transparent);
  color: var(--accent-color);
  border: 1px solid color-mix(in srgb, var(--accent-color) 30%, transparent);
}

.message.error {
  background-color: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.2);
}

.form-input {
  padding: 0.6rem 1rem;
  font-size: 1rem;
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

.form-input:disabled {
  background-color: var(--bg-primary);
  color: var(--text-secondary);
  cursor: not-allowed;
  border-color: transparent;
}

.action-footer {
  justify-content: flex-end;
}

.button-group {
  display: flex;
  gap: 1rem;
}

.form-button {
  padding: 0.6rem 1.25rem;
  font-size: 0.9rem;
  font-weight: 500;
  border-radius: 6px;
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.2s;
}

.form-button {
  background-color: var(--accent-color);
  color: white;
  border-color: var(--accent-color);
}

.form-button:hover {
  background-color: var(--accent-hover);
}

.form-button.primary-button {
  background-color: var(--accent-color);
}

.form-button.primary-button:hover {
  background-color: var(--accent-hover);
}

.form-button.secondary-button {
  background-color: var(--bg-secondary);
  color: var(--text-primary);
  border-color: var(--border-color);
}

.form-button.secondary-button:hover {
  background-color: var(--bg-primary);
  border-color: var(--text-secondary);
}

.form-button.small-button {
  padding: 0.4rem 0.8rem;
  font-size: 0.875rem;
}

.form-button.delete-button {
  background-color: #dc3545;
  border-color: #dc3545;
}

.form-button.delete-button:hover {
  background-color: #c82333;
}

.save-section {
  justify-content: flex-end;
  padding-top: 1rem;
  border-top: none;
  margin-top: 1rem;
  display: flex;
  gap: 1rem;
}

.save-section .form-button {
  min-width: 150px;
}

.connection-item {
  padding: 1rem 0;
  border-bottom: 1px dashed var(--border-color);
}

.connection-item:last-of-type {
  border-bottom: none;
}

/* Toggle Switch */
.toggle-switch {
  position: relative;
  display: inline-block;
  width: 44px;
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
  background-color: color-mix(in srgb, var(--text-secondary) 50%, transparent);
  border-radius: 24px;
  transition: background-color 0.2s;
}

.slider:before {
  position: absolute;
  content: "";
  height: 20px;
  width: 20px;
  left: 2px;
  bottom: 2px;
  background-color: white;
  border-radius: 50%;
  transition: transform 0.2s;
}

.toggle-switch input:checked + .slider {
  background-color: var(--accent-color);
}

.toggle-switch input:checked + .slider:before {
  transform: translateX(20px);
}

</style>