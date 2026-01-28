<template>
  <div class="registration-guide">
    <div class="guide-container">
        <!-- Header -->
        <div class="guide-header">
             <h1 class="title">OAuth Client Registration</h1>
             <p class="subtitle">Securely connect your Agent Bridge to verification providers or internal servers.</p>
        </div>

        <el-tabs v-model="activeTab" class="demo-tabs" type="border-card">
            
            <!-- MANUAL TAB -->
            <el-tab-pane label="SaaS Platforms (Manual)" name="manual">
                <div class="tab-content">
                    <el-alert title="Required for Public SaaS (Notion, GitHub, Figma)" type="info" show-icon :closable="false" style="margin-bottom: 20px;">
                        <div>Major providers do not support dynamic registration. You must manually create an app in their portal.</div>
                    </el-alert>
                    
                    <el-steps :active="1" finish-status="success" align-center style="margin-bottom: 40px;">
                        <el-step title="Open Portal" description="Go to Developer settings" />
                        <el-step title="Create App" description="Register new integration" />
                        <el-step title="Set callback" description="Configure Redirect URI" />
                        <el-step title="Get Keys" description="Copy ID & Secret" />
                    </el-steps>

                    <el-divider content-position="left">Select Provider</el-divider>

                    <div class="provider-grid">
                        <el-card shadow="hover" class="provider-card" @click="openLink('https://www.notion.so/my-integrations')">
                            <div class="card-header">
                                <!-- Using FontAwesome icons that are registered in main.js -->
                                <span>Notion</span>
                            </div>
                            <p>My Integrations</p>
                            <el-button type="primary" link>Open Portal</el-button>
                        </el-card>

                        <el-card shadow="hover" class="provider-card" @click="openLink('https://github.com/settings/applications/new')">
                            <div class="card-header">
                                <font-awesome-icon :icon="['fab', 'github']" class="icon github" />
                                <span>GitHub</span>
                            </div>
                             <p>OAuth Apps</p>
                             <el-button type="primary" link>Open Portal</el-button>
                        </el-card>

                        <el-card shadow="hover" class="provider-card" @click="openLink('https://www.figma.com/developers/apps')">
                            <div class="card-header">
                                <font-awesome-icon :icon="['fas', 'pen']" class="icon figma" />
                                <span>Figma</span>
                            </div>
                             <p>My Apps</p>
                             <el-button type="primary" link>Open Portal</el-button>
                        </el-card>
                    </div>

                    <el-divider content-position="left">Configure Redirect URI</el-divider>

                    <el-alert type="warning" :closable="false">
                        <template #title>
                            <div style="font-weight: bold;">Critical Step</div>
                        </template>
                        <div>
                            You must copy this URL exactly into the "Redirect URI" or "Callback URL" field of your app settings.
                            <div class="code-block">
                                {{ redirectUri }}
                                <el-button type="primary" link size="small" @click="copyUri">Copy</el-button>
                            </div>
                        </div>
                    </el-alert>
                </div>
            </el-tab-pane>

             <!-- DYNAMIC TAB -->
            <el-tab-pane label="Enterprise Servers (Dynamic Discovery)" name="dynamic">
                 <div class="tab-content" style="padding: 20px;">
                    <el-timeline>
                        <el-timeline-item timestamp="Step 1" placement="top" type="primary">
                          <el-card>
                            <h4>Find Discovery Endpoint</h4>
                            <p>Most enterprise/internal MCP servers expose metadata at <code>{server_url}/.well-known/oauth-authorization-server</code>, allowing you to discover the correct endpoints automatically.</p>
                          </el-card>
                        </el-timeline-item>
                        <el-timeline-item timestamp="Step 2" placement="top" type="primary">
                          <el-card>
                            <h4>Check Capabilities</h4>
                            <p>Ensure the server returns a <code>registration_endpoint</code> in the JSON response.</p>
                          </el-card>
                        </el-timeline-item>
                        <el-timeline-item timestamp="Step 3" placement="top" type="success">
                          <el-card>
                            <h4>Register</h4>
                            <p>Send a POST request to generated credentials dynamically.</p>
                            <div class="code-block" style="font-size: 0.8em; margin-top:10px;">
                                curl -X POST endpoint -d '{ "client_name": "Agent Bridge", ... }'
                            </div>
                          </el-card>
                        </el-timeline-item>
                      </el-timeline>
                 </div>
            </el-tab-pane>

             <!-- INSPECTOR TAB -->
            <el-tab-pane label="Server Inspector" name="inspector">
                <div class="tab-content" style="padding: 20px;">
                    <p class="subtitle" style="margin-bottom: 20px; font-size: 1rem;">Enter a Server URL to discover its capability and auth configuration.</p>
                    <div style="display: flex; gap: 10px; margin-bottom: 20px;">
                        <el-input v-model="inspectorUrl" placeholder="Enter Server URL (e.g. http://localhost:8000/sse)" clearable @keyup.enter="inspectServer" />
                        <el-button type="primary" :loading="inspecting" @click="inspectServer">Analyze</el-button>
                    </div>

                    <div v-if="inspectionReport" class="report-container">
                         <el-alert v-if="inspectionReport.discovered_config" title="Discovery Successful!" type="success" show-icon :closable="false" style="margin-bottom: 10px;">
                            <div>
                                Authorization URL: <code>{{ inspectionReport.discovered_config.authorization_url }}</code><br>
                                Token URL: <code>{{ inspectionReport.discovered_config.token_url }}</code>
                            </div>
                         </el-alert>
                         <el-alert v-else title="Discovery Failed" type="warning" show-icon :closable="false" style="margin-bottom: 10px;">
                            <div>No automatic config found. You must use Manual Configuration.</div>
                         </el-alert>
                         
                         <div class="code-block" style="display:block; white-space: pre-wrap;">{{ JSON.stringify(inspectionReport, null, 2) }}</div>
                    </div>
                </div>
            </el-tab-pane>

             <!-- TECHNICAL SPECS TAB -->
            <el-tab-pane label="Technical Specs" name="specs">
                <div class="tab-content" style="padding: 20px;">
                    <h3>Authentication Protocol</h3>
                    <p>Agent Bridge implements a secure <strong>OAuth 2.1</strong> flow using <strong>Authorization Code Grant with PKCE</strong> (Proof Key for Code Exchange).</p>
                    
                    <div class="specs-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px;">
                        <el-card>
                            <template #header><div class="card-header">Discovery Mechanisms</div></template>
                            <ul style="text-align: left; padding-left: 20px;">
                                <li><strong>RFC 8414</strong>: <code>/.well-known/oauth-authorization-server</code></li>
                                <li><strong>OpenID Connect</strong>: <code>/.well-known/openid-configuration</code></li>
                                <li><strong>Header-Based</strong>: <code>WWW-Authenticate</code> response parsing.</li>
                            </ul>
                        </el-card>

                        <el-card>
                            <template #header><div class="card-header">Required Endpoints</div></template>
                            <ul style="text-align: left; padding-left: 20px;">
                                <li><code>authorization_endpoint</code>: For user consent.</li>
                                <li><code>token_endpoint</code>: For code exchange.</li>
                                <li><code>registration_endpoint</code> (Optional): For dynamic client creation.</li>
                            </ul>
                        </el-card>
                    </div>

                    <el-divider />

                    <h3>Security Standards</h3>
                    <el-descriptions border :column="1">
                        <el-descriptions-item label="PKCE Method">S256 (SHA-256)</el-descriptions-item>
                        <el-descriptions-item label="State Parameter">UUID v4 (Stored in Redis with 10m TTL)</el-descriptions-item>
                        <el-descriptions-item label="Token Storage">Standard OAuth 2.0 Bearer Token usage.</el-descriptions-item>
                    </el-descriptions>
                </div>
            </el-tab-pane>
        </el-tabs>

        <div class="footer-actions">
            <el-button type="primary" size="large" @click="$router.push('/settings')">Back to Settings</el-button>
        </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useToast } from 'vue-toastification';

const activeTab = ref('manual');
const toast = useToast();

// Use Vite environment variable or default
const BACKEND_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';
const redirectUri = computed(() => `${BACKEND_BASE_URL}/api/mcp/oauth/callback`);

const openLink = (url) => {
    window.open(url, '_blank');
};

const copyUri = () => {
    navigator.clipboard.writeText(redirectUri.value);
    toast.success('Callback URI copied!');
};

// --- INSPECTOR LOGIC ---
const inspectorUrl = ref('');
const inspecting = ref(false);
const inspectionReport = ref(null);

const inspectServer = async () => {
    if (!inspectorUrl.value) { toast.warning("Please enter a URL"); return; }
    inspecting.value = true;
    inspectionReport.value = null;
    try {
        const res = await fetch(`${BACKEND_BASE_URL}/api/mcp/inspect`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({server_url: inspectorUrl.value})
        });
        if (res.ok) {
            inspectionReport.value = await res.json();
            toast.success("Analysis complete");
        } else {
            const err = await res.json();
            toast.error(`Analysis failed: ${err.detail}`);
        }
    } catch(e) {
        toast.error("Error inspecting server");
    } finally {
        inspecting.value = false;
    }
};
</script>

<style scoped>
.registration-guide {
    padding: 40px;
    padding-bottom: 100px; /* Ensure bottom content is scrollable */
    background: #fdfdfd;
    height: 100%; /* Fit within parent container (dashboard) */
    overflow-y: auto;
    box-sizing: border-box;
    
    /* Scrollbar for Firefox */
    scrollbar-width: thin;
    scrollbar-color: #c1c1c1 #f1f1f1;
}

/* Scrollbar for Chrome/Edge/Safari */
.registration-guide::-webkit-scrollbar {
    width: 8px;
}
.registration-guide::-webkit-scrollbar-track {
    background: #f1f1f1;
}
.registration-guide::-webkit-scrollbar-thumb {
    background: #c1c1c1;
    border-radius: 4px;
}
.registration-guide::-webkit-scrollbar-thumb:hover {
    background: #a8a8a8;
}

.guide-container {
    max-width: 1000px;
    margin: 0 auto;
}
.guide-header {
    text-align: center;
    margin-bottom: 40px;
}
.title {
    font-size: 2.5rem;
    font-weight: 700;
    color: #303133;
    margin-bottom: 10px;
}
.subtitle {
    font-size: 1.2rem;
    color: #606266;
}

.provider-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
    margin-top: 20px;
    margin-bottom: 40px;
}

.provider-card {
    cursor: pointer;
    transition: transform 0.2s;
    text-align: center;
    border-radius: 12px;
}
.provider-card:hover {
    transform: translateY(-5px);
}

.card-header {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    font-size: 1.2rem;
    font-weight: 600;
    margin-bottom: 10px;
}

.icon { font-size: 1.5rem; }
.github { color: #24292e; }
.figma { color: #f24e1e; }

.code-block {
    background: #f4f4f5;
    padding: 10px;
    border-radius: 4px;
    font-family: monospace;
    margin-top: 10px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    word-break: break-all;
    font-size: 0.9rem;
    border: 1px solid #e4e7ed;
}

.footer-actions {
    margin-top: 40px;
    text-align: center;
}

/* Element Plus Overrides if needed */
.el-tabs--border-card {
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}
</style>
