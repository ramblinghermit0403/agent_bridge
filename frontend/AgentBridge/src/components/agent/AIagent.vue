<template>
  <div class="chat-container">
    <div class="branding">
    </div>

<div v-if="messages.length === 0 && !isTyping && !isAgentProcessing" class="greeting-container">
  
  <div v-if="!isWelcomeBoxClosed" class="welcome-box">
    <button @click="closeWelcomeBox" class="close-welcome-button" title="Close">×</button>
    
    <h2 class="welcome-title">Welcome to Agent Bridge</h2>
    
    <p class="welcome-subtitle">
      Your central hub for orchestrating tasks across multiple MCP servers. Connect your tools, leverage powerful LLMs, and automate complex workflows.
      <span class="learn-more-container"><u><router-link to="/learn-more">Learn More</router-link></u></span>
    </p>


    <div class="capabilities-grid">
      <div class="capability-card">
        <h3 class="capability-title">Connect Your Servers</h3>
        <p class="capability-desc">Easily add and manage connections to your various Modern Context Protocol (MCP) servers in one place.</p>
      </div>
      <div class="capability-card">
        <h3 class="capability-title">Orchestrate Complex Tasks</h3>
        <p class="capability-desc">Use natural language to combine tools from different servers to achieve multi-step goals effortlessly.</p>
      </div>
      <div class="capability-card"> 
        <h3 class="capability-title">Unified Tool Access</h3>
        <p class="capability-desc">Simply describe what you need. Agent Bridge finds and uses the right tool from any connected server for you.</p>
      </div>
    </div>
    

  </div>
      
      <h1 v-else class="greeting-text">
        {{ greetingText }}<span class="cursor-blink">|</span>
      </h1>
    </div>

    <div v-else ref="chatList" class="messages-list styled-scrollbar">
      <div v-for="(msg, index) in messages" :key="index" class="message-row" :class="[msg.role === 'user' ? 'justify-end' : 'justify-start']">
        
        <!-- Standard Message Bubble -->
        <div v-if="msg.role !== 'permission_request'" class="flex flex-col" :class="msg.role === 'user' ? 'items-end' : 'items-start'">
          
          <div v-if="msg.role === 'agent' && msg.scratchpad && msg.scratchpad.length > 0" class="scratchpad-area">
            <details :open="isAgentProcessing && index === currentAgentMessageIndex">
              <summary>Agent Thoughts</summary>
              <div class="scratchpad-content">
                <p v-for="(thought, tIndex) in msg.scratchpad" :key="tIndex" class="scratchpad-line">
                  {{ thought }}
                </p>
              </div>
            </details>
          </div>

          <div class="message-bubble" :class="[msg.role === 'user' ? 'user-bubble' : 'agent-bubble']">
            <div v-if="msg.html" v-html="msg.text"></div>
            <div v-else-if="isAgentProcessing && index === currentAgentMessageIndex && msg.text === ''">
                <div class="typing-indicator">
                    <span class="typing-dot" style="animation-delay: 0s"></span>
                    <span class="typing-dot" style="animation-delay: 0.2s"></span>
                    <span class="typing-dot" style="animation-delay: 0.4s"></span>
                </div>
            </div>
            <div v-else>{{ msg.text }}</div>
          </div>

          <div class="message-actions">
            <!-- Actions similar to before -->
             <button @click="copyMessage(msg.text, index)" class="action-button" title="Copy">
              <svg v-if="copiedMessageIndex === index" xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
            </button>
            <template v-if="msg.role === 'agent'">
              <button @click="handleFeedback(index, 'like')" class="action-button" title="Good response"><svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" :class="{'feedback-like' : msg.feedback === 'like'}" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.085a2 2 0 00-1.736.93L5.5 8m7 2v5m0 0h-4" /></svg></button>
              <button @click="handleFeedback(index, 'dislike')" class="action-button" title="Bad response"><svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" :class="{'feedback-dislike' : msg.feedback === 'dislike'}" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.017c.163 0 .326.02.485.06L17 4m-7 10v-5m0 0h4" /></svg></button>
            </template>
          </div>
        </div>

        <!-- Permission Request Message -->
        <div v-else-if="msg.role === 'permission_request'" class="w-full flex justify-start">
             <ToolPermissionMessage 
                :toolName="msg.toolName"
                :serverName="msg.serverName"
                :payload="msg.payload"
                :approvalId="msg.approvalId"
                @approve="(data) => handleToolApproval(data, index)"
                @deny="(data) => handleToolDenial(data, index)"
             />
        </div>

      </div>
    </div>

    <div class="input-area-container">
      <div class="input-area">
        <div class="input-wrapper">
          <div v-if="attachedFile" class="file-preview">
            <div class="file-info"><div class="file-type-badge">{{ fileType }}</div><div class="file-name">{{ attachedFile.name }}</div></div>
            <button @click="clearFile" class="clear-file-button">×</button>
          </div>
          <textarea v-model="inputMessage" @keydown.ctrl.enter.prevent="sendMessage" placeholder="Ask AgentBridge..." class="input-textarea" rows="2" :disabled="isAgentProcessing"></textarea>
          <div class="input-actions">
            <div class="left-actions">
                <button @click="triggerFileInput" class="attach-button" :disabled="isAgentProcessing"><svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" /></svg></button>
                <input ref="fileInput" type="file" @change="handleFile" style="display: none" />
                
                <select v-model="selectedModel" class="model-select" :disabled="isAgentProcessing">
                    <option value="gemini">Gemini 2.5 Flash</option>
                    <option value="nova-pro">Amazon Nova Pro</option>
                </select>
            </div>
            <button @click="sendMessage" class="send-button" :disabled="(!inputMessage.trim() && !attachedFile) || isAgentProcessing"><span>Send</span><span class="shortcut-keys"><kbd>Ctrl</kbd><span>+</span><kbd>↵</kbd></span></button>
          </div>
        </div>
      </div>
    </div>


  </div>
</template>

<script>
import { nextTick, defineAsyncComponent } from "vue";
import { useToast } from "vue-toastification";

export default {
  components: {
    ToolPermissionMessage: defineAsyncComponent(() => import('./ToolPermissionMessage.vue'))
  },
  setup() {
    const toast = useToast();
    return { toast };
  },
  data() {
    return {
      api_url: import.meta.env.VITE_API_URL || "http://localhost:8001",
      isWelcomeBoxClosed: false,
      token: localStorage.getItem("token"),
      messages: [],
      inputMessage: "",
      isTyping: false,
      isAgentProcessing: false,
      attachedFile: null,
      fileType: "",
      greetingText: "",
      fullGreeting: "How can I assist you?",
      typingInterval: null,
      copiedMessageIndex: null,
      eventSource: null,
      currentAgentMessageIndex: -1,
      selectedModel: 'gemini', // Default model
      // Permission dialog state removed
    };
  },

  computed: {
    sessionId() {
      return this.$route.query.session || null;
    }
  },

  watch: {
    sessionId(newId, oldId) {
      if (newId !== oldId) {
        this.loadConversation();
      }
    },
    messages: {
        handler() {
            this.scrollToBottom();
        },
        deep: true,
    },
  },
  
  created() {
    this.loadConversation();
  },

  beforeUnmount() {
    clearInterval(this.typingInterval);
    if (this.eventSource) {
      this.eventSource.close();
      console.log("SSE connection closed on unmount.");
    }
  },
  methods: {
    async loadConversation() {
      if (this.eventSource) {
        this.eventSource.close();
      }
      this.isAgentProcessing = false;

      if (!this.sessionId) {
        this.messages = [];
        this.isWelcomeBoxClosed = false;
        return;
      }

      this.isWelcomeBoxClosed = true;

      try {
        const response = await fetch(`${this.api_url}/api/chats/${this.sessionId}`, {
          headers: {
            'Authorization': `Bearer ${this.token}`
          }
        });

        if (response.ok) {
          const conversation = await response.json();
          this.messages = conversation.messages.map(msg => {
            let messageText;
            let isHtml = false;

            if (msg.role === "agent" && msg.additional_kwargs?.html) {
              const cleanedHtml = msg.additional_kwargs.html.replace(/```html/g, '').replace(/```/g, '').trim();
              messageText = cleanedHtml;
              isHtml = true;
            } else {
              messageText = msg.content;
            }

            return {
              role: msg.role,
              text: messageText,
              scratchpad: msg.additional_kwargs?.scratchpad || [],
              html: isHtml,
              feedback: null,
            };
          });
        } else if (response.status === 404) {
          this.messages = [];
          this.isWelcomeBoxClosed = false;
        } else {
          const errorData = await response.json();
          console.error("Failed to load chat history:", errorData.detail);
          this.messages = [{ role: 'agent', text: `Error: Could not load conversation. ${errorData.detail}` }];
        }
      } catch (error) {
        console.error("Network error loading chat history:", error);
        this.toast.error("Failed to load conversation history.");
        this.messages = [{ role: 'agent', text: `Error: Could not connect to the server to load history.` }];
      }
    },
    
    startTypewriter() {
      let i = 0;
      this.greetingText = "";
      this.typingInterval = setInterval(() => {
        if (i < this.fullGreeting.length) {
          this.greetingText += this.fullGreeting.charAt(i);
          i++;
        } else {
          clearInterval(this.typingInterval);
          this.typingInterval = null;
        }
      }, 80);
    },

    closeWelcomeBox() {
      this.isWelcomeBoxClosed = true;
      this.startTypewriter();
    },

    async sendMessage() {
      const prompt = this.inputMessage.trim();
      const userToken = this.token;
      if (!prompt && !this.attachedFile || this.isAgentProcessing) return;

      this.messages.push({ role: "user", text: prompt });
      this.inputMessage = "";

      this.currentAgentMessageIndex = this.messages.length;
      this.messages.push({
        role: "agent", text: "", feedback: null, html: false, scratchpad: [],
      });

      this.isAgentProcessing = true;
      this.isTyping = false;

      try {
        if (this.eventSource) this.eventSource.close();

        const baseUrl = `${this.api_url}/ask/stream`;
        const params = new URLSearchParams();
        params.append("prompt", prompt);
        params.append("token", userToken);
        
        if (this.sessionId) {
          params.append("session_id", this.sessionId);
        }
        
        // --- Add Model Params ---
        if (this.selectedModel === 'nova-pro') {
            params.append("model_provider", "bedrock");
            // Use cross-region inference profile for on-demand access in APAC
            params.append("model", "apac.amazon.nova-pro-v1:0");
        } else {
             // Default Gemini
             params.append("model_provider", "gemini");
             params.append("model", "gemini-2.5-flash");
        }

        this.eventSource = new EventSource(`${baseUrl}?${params.toString()}`);

        this.eventSource.onopen = () => {
          console.log("SSE connection opened!");
        };

        this.eventSource.addEventListener("scratchpad", (event) => {
            const data = JSON.parse(event.data);
            let thought = ""; 

            if (data.type === 'tool_start') {
                thought = `Tool Used: ${data.tool_name} with input ${JSON.stringify(data.tool_input)}`;
            } else if (data.type === 'tool_end') {
                thought = `Tool Output: ${data.observation}`;
            } else if (data.type === 'agent_status') {
                thought = `Status: ${data.content}`;
            }

            if (this.messages[this.currentAgentMessageIndex] && thought) {
                this.messages[this.currentAgentMessageIndex].scratchpad.push(thought);
            }
        });

        this.eventSource.addEventListener("llm_token", (event) => {
          const data = JSON.parse(event.data);
          if (this.messages[this.currentAgentMessageIndex]) {
            this.messages[this.currentAgentMessageIndex].text += data.content;
          }
        });

        this.eventSource.addEventListener("plain_text_answer", (event) => {
          const data = JSON.parse(event.data);
          console.log("Received plain text answer:", data.content);
          if (this.messages[this.currentAgentMessageIndex]) {
              this.messages[this.currentAgentMessageIndex].text = data.content;
          }
        });

        this.eventSource.addEventListener("final_html_output", (event) => {
          const data = JSON.parse(event.data);
          if (this.messages[this.currentAgentMessageIndex]) {
            const rawHtml = data.content;
            const cleanedHtml = rawHtml.replace(/```html/g, '').replace(/```/g, '').trim();

            this.messages[this.currentAgentMessageIndex].text = cleanedHtml;
            this.messages[this.currentAgentMessageIndex].html = true;
          }
          console.log("Received final HTML output.");
        });

        // Tool approval required event
        this.eventSource.addEventListener("tool_approval_required", (event) => {
            const data = JSON.parse(event.data);
            console.log("Tool approval required:", data);
            
            // Push permission request message to chat
            this.messages.push({
                role: 'permission_request',
                toolName: data.tool_name,
                serverName: data.server_name,
                payload: data.payload,
                approvalId: data.approval_id
            });
            // Don't update currentAgentMessageIndex, let agent continue updating the "thinking" block
            this.scrollToBottom();
        });

        // Tool approved event
        this.eventSource.addEventListener("tool_approved", (event) => {
          const data = JSON.parse(event.data);
          console.log("Tool approved:", data.tool_name);
          this.toast.success(`Tool ${data.tool_name} approved`);
        });

        // Tool denied event
        this.eventSource.addEventListener("tool_denied", (event) => {
          const data = JSON.parse(event.data);
          console.log("Tool denied:", data.tool_name);
          this.toast.warning(`Tool ${data.tool_name} was denied`);
        });

        this.eventSource.addEventListener("stream_end", (event) => {
          const data = JSON.parse(event.data);
          if (!this.sessionId && data.session_id) {
            this.$router.replace({
              query: { ...this.$route.query, session: data.session_id }
            });
          }
          console.log("SSE stream ended.", data);
          this.isAgentProcessing = false;
          this.isTyping = false;
          this.eventSource.close();
        });

        this.eventSource.onerror = (error) => {
          console.error("EventSource failed:", error);
          this.toast.error("Connection lost. Please try again.");
          if (this.messages[this.currentAgentMessageIndex]) {
            this.messages[this.currentAgentMessageIndex].text =
              "❌ Error: Could not get a real-time response. Please try again.";
            this.messages[this.currentAgentMessageIndex].scratchpad = [];
            this.messages[this.currentAgentMessageIndex].html = false;
          }
          this.isAgentProcessing = false;
          this.isTyping = false;
          this.eventSource.close();
        };
      } catch (error) {
        console.error("Error initiating SSE connection:", error);
        this.toast.error("Failed to send message.");
        if (this.messages[this.currentAgentMessageIndex]) {
          this.messages[this.currentAgentMessageIndex].text =
            "❌ Error: Failed to initiate streaming connection.";
          this.messages[this.currentAgentMessageIndex].scratchpad = [];
          this.messages[this.currentAgentMessageIndex].html = false;
        }
        this.isAgentProcessing = false;
        this.isTyping = false;
      }
    },
    scrollToBottom() {
      nextTick(() => {
        const chatList = this.$refs.chatList;
        if (chatList) {
          chatList.scrollTop = chatList.scrollHeight;
        }
      });
    },
    triggerFileInput() {
      this.$refs.fileInput.click();
    },
    handleFile(event) {
      const file = event.target.files[0];
      if (file) {
        this.attachedFile = file;
        this.fileType = file.name.split(".").pop().toUpperCase() || "FILE";
      }
    },
    clearFile() {
      this.attachedFile = null;
      this.fileType = "";
      this.$refs.fileInput.value = "";
    },
    copyMessage(text, index) {
      let textToCopy = text;
      if (typeof text === 'string' && (text.includes('<') && text.includes('>'))) {
        const tempEl = document.createElement('div');
        tempEl.innerHTML = text;
        textToCopy = tempEl.textContent || tempEl.innerText || '';
      }
      
      navigator.clipboard.writeText(textToCopy).then(() => {
        this.copiedMessageIndex = index;
        setTimeout(() => {
          this.copiedMessageIndex = null;
        }, 2000);
      });
    },
    handleFeedback(index, type) {
      const message = this.messages[index];
      message.feedback = message.feedback === type ? null : type;
    },
    
    // Tool Approval Handlers
    getAuthHeaders() {
      const token = localStorage.getItem('token');
      if (!token) return null;
      return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      };
    },

    async handleToolApproval(data, index) {
      if (!data.approvalId) return;

      try {
        const response = await fetch(`${this.api_url}/api/tool-execution/approve`, {
          method: 'POST',
          headers: this.getAuthHeaders(),
          body: JSON.stringify({
            approval_id: data.approvalId,
            approved: true,
            approval_type: data.approvalType || 'once'
          })
        });

        if (!response.ok) {
          throw new Error('Failed to approve tool');
        }

        // Remove the permission request message from the list
        if (index !== undefined && index >= 0) {
            this.messages.splice(index, 1);
        }
        
      } catch (err) {
        console.error("Error approving tool:", err);
        this.toast.error("Failed to approve tool execution");
      }
    },

    async handleToolDenial(data, index) {
      if (!data.approvalId) return;

      try {
        const response = await fetch(`${this.api_url}/api/tool-execution/approve`, {
          method: 'POST',
          headers: this.getAuthHeaders(),
          body: JSON.stringify({
            approval_id: data.approvalId,
            approved: false
          })
        });

        if (!response.ok) {
          throw new Error('Failed to deny tool');
        }

        // Remove the permission request message from the list
        if (index !== undefined && index >= 0) {
            this.messages.splice(index, 1);
        }
      } catch (err) {
        console.error("Error denying tool:", err);
        this.toast.error("Failed to deny tool execution");
      }
    },
  },
};
</script>
<style scoped>
/* All existing styles remain the same, with the following changes and additions */

/* --- Main Container Layout --- */
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100vh; /* Use viewport height for a full-page container */
  overflow: hidden; /* This is the key: prevents the container itself from scrolling */
  background-color: var(--bg-primary);
  color: var(--text-primary);
  font-weight: 400;
}

.messages-list {
  flex-grow: 1;
  overflow-y: auto; /* This will now work correctly */
  padding: 1rem 1.5rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
  /* Add scrollbar styling */
  scrollbar-width: thin;
  scrollbar-color: var(--text-secondary) transparent;
  max-height: 65vh; /* Limit height to prevent overflow */
}

/* --- Custom Scrollbar Styling (for Webkit) --- */
.messages-list::-webkit-scrollbar {
  width: 8px;
}
.messages-list::-webkit-scrollbar-track {
  background: transparent;
}
.messages-list::-webkit-scrollbar-thumb {
  background-color: var(--text-secondary);
  border-radius: 10px;
  border: 2px solid var(--bg-primary);
}
.messages-list::-webkit-scrollbar-thumb:hover {
  background-color: var(--text-primary);
}

.input-area-container { 
  flex-shrink: 0; /* Prevents the input area from shrinking */ 
  position: sticky; 
  bottom: 0; 
  padding: 1.5rem; 
  background-color: var(--bg-primary); 
  display: flex; 
  justify-content: center; 
}


/* All other existing styles... */
.welcome-box { 
  position: relative; 
  max-width: 48rem; 
  width: 100%; 
  padding: 3rem; 
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color); 
  border-radius: 8px;
  animation: fade-in 0.6s cubic-bezier(0.16, 1, 0.3, 1); 
}
@keyframes fade-in { from { opacity: 0; transform: translateY(20px); scale: 0.98; } to { opacity: 1; transform: translateY(0); scale: 1; } }

.close-welcome-button { position: absolute; top: 1rem; right: 1rem; width: 2.5rem; height: 2.5rem; border-radius: 50%; background: var(--bg-primary); border: 1px solid var(--border-color); color: var(--text-secondary); font-size: 1.25rem; line-height: 1; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1); }
.close-welcome-button:hover { background-color: var(--text-primary); color: var(--bg-primary); border-color: var(--text-primary); transform: rotate(90deg); }

.welcome-title { font-size: 2.25rem; font-weight: 700; text-align: center; color: var(--text-primary); margin-bottom: 1rem; letter-spacing: -0.02em; }
.welcome-subtitle { text-align: center; color: var(--text-secondary); margin-bottom: 3rem; max-width: 32rem; margin-left: auto; margin-right: auto; font-size: 1.125rem; line-height: 1.6; }

.capabilities-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1.5rem; }

.capability-card { 
  padding: 1.5rem; 
  background-color: var(--bg-primary);
  border: 1px solid var(--border-color); 
  border-radius: 8px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); 
  position: relative; 
  overflow: hidden; 
}
.capability-card:hover { 
  transform: translateY(-2px); 
  border-color: var(--text-primary);
  background-color: var(--hover-bg);
}

.capability-title { font-weight: 700; margin-bottom: 0.75rem; color: var(--text-primary); font-size: 1.1rem; }
.capability-desc { font-size: 0.95rem; color: var(--text-secondary); line-height: 1.6; }
.branding { padding: 1rem 1.5rem; flex-shrink: 0; }
.greeting-container { flex-grow: 1; display: flex; align-items: center; justify-content: center; padding: 1rem; max-height: 65vh; }
.greeting-text { font-size: 2.25rem; font-weight: 600; text-align: center; color: var(--text-primary); }
.cursor-blink { animation: cursor-blink-animation 1s step-end infinite; font-weight: 300; }
@keyframes cursor-blink-animation { from, to { color: transparent; } 50% { color: var(--text-primary); } }

.message-row { width: 100%; max-width: 48rem; display: flex; }
.justify-end { justify-content: flex-end; }
.justify-start { justify-content: flex-start; }
.flex.flex-col { display:flex; flex-direction: column;}
.items-end { align-items: flex-end; }
.items-start { align-items: flex-start; }
.message-bubble { display: inline-block; padding: 0.75rem 1rem; word-break: break-word; }
.user-bubble { max-width: 32rem; background-color: var(--text-primary); color: var(--bg-primary); border-radius: 8px; }
.agent-bubble { width: 100%; color: var(--text-primary); }
.message-actions { display: flex; align-items: center; gap: 0.5rem; margin-top: 0.5rem; }
.action-button { padding: 0.25rem; border-radius: 9999px; color: var(--text-secondary); transition: background-color 0.2s, color 0.2s; }
.action-button:hover { background-color: var(--bg-secondary); color: var(--text-primary); }
.feedback-like { color: var(--text-primary) !important; opacity: 1; }
.feedback-dislike { color: var(--text-primary) !important; opacity: 1; }
.typing-indicator { display: flex; align-items: center; height: 24px; }
.typing-dot { display: inline-block; width: 0.5rem; height: 0.5rem; background-color: var(--text-secondary); border-radius: 9999px; margin: 0 0.25rem; animation: typing-blink 1.4s infinite both; }
@keyframes typing-blink { 0% { opacity: 0.2; } 20% { opacity: 1; } 100% { opacity: 0.2; } }

.input-area { width: 100%; max-width: 48rem; background-color: var(--bg-secondary); border-radius: 1.5rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -2px rgba(0,0,0,0.1); border: 1px solid var(--border-color); }
.input-wrapper { border-radius: 1.5rem; display: flex; flex-direction: column; min-height: 100px; padding: 1rem; width: 100%; }
.input-textarea { background: transparent; color: var(--text-primary); outline: none; resize: none; flex-grow: 1; font-size: 1rem; }
.input-textarea::placeholder { color: var(--text-secondary); opacity: 0.8; }
.input-actions { display: flex; justify-content: space-between; align-items: center; margin-top: 0.75rem; }
.attach-button { width: 2.25rem; height: 2.25rem; background-color: var(--bg-primary); border: 1px solid var(--border-color); color: var(--text-secondary); border-radius: 9999px; display: flex; align-items: center; justify-content: center; transition: all 0.2s; }
.attach-button:hover { background-color: var(--hover-bg); color: var(--text-primary); }

.left-actions { display: flex; align-items: center; gap: 0.75rem; }
.model-select { 
    background-color: var(--bg-primary); 
    color: var(--text-secondary); 
    border: 1px solid var(--border-color); 
    border-radius: 0.5rem; 
    padding: 0.25rem 0.5rem; 
    font-size: 0.8rem; 
    outline: none; 
    cursor: pointer;
    max-width: 150px;
}
.model-select:hover { border-color: var(--text-primary); color: var(--text-primary); }

.send-button { display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 1rem; background-color: var(--text-primary); border-radius: 0.5rem; color: var(--bg-primary); font-weight: 600; transition: opacity 0.2s; }
.send-button:hover { opacity: 0.9; }
.send-button:disabled { opacity: 0.5; cursor: not-allowed; }
.shortcut-keys { display: flex; align-items: center; gap: 0.25rem; font-size: 0.75rem; opacity: 0.7; }
kbd { background-color: rgba(255, 255, 255, 0.2); border-radius: 4px; border: 1px solid rgba(255, 255, 255, 0.25); padding: 2px 6px; font-size: 0.75rem; line-height: 1; }
.file-preview { position: relative; width: max-content; max-width: 16rem; margin-bottom: 0.5rem; }
.file-info { background-color: var(--bg-primary); border: 1px solid var(--border-color); color: var(--text-primary); border-radius: 0.75rem; padding: 0.75rem 2.5rem 0.75rem 1rem; display: flex; align-items: center; gap: 0.5rem; }
.file-type-badge { background-color: var(--text-primary); font-size: 0.75rem; padding: 2px 8px; border-radius: 0.25rem; font-weight: 600; color: var(--bg-primary); }
.file-name { overflow: hidden; white-space: nowrap; text-overflow: ellipsis; max-width: 150px; font-size: 0.875rem; }
.clear-file-button { position: absolute; top: -0.5rem; right: -0.5rem; background-color: #9ca3af; color: white; border-radius: 9999px; width: 1.25rem; height: 1.25rem; font-size: 0.75rem; display: flex; align-items: center; justify-content: center; }
.clear-file-button:hover { background-color: #6b7280; }
.agent-bubble :deep(table) { width: 100%; margin: 1rem 0; border-collapse: collapse; border: 1px solid var(--border-color); }
.agent-bubble :deep(th), .agent-bubble :deep(td) { border: 1px solid var(--border-color); padding: 0.5rem; text-align: left; }
.agent-bubble :deep(th) { background-color: var(--bg-secondary); font-weight: 600; }
.agent-bubble :deep(h1), .agent-bubble :deep(h2), .agent-bubble :deep(h3), .agent-bubble :deep(h4) { font-weight: 600; margin-top: 1rem; margin-bottom: 0.5rem; }
.agent-bubble :deep(h1) { font-size: 1.5rem; } .agent-bubble :deep(h2) { font-size: 1.25rem; } .agent-bubble :deep(h3) { font-size: 1.125rem; } .agent-bubble :deep(h4) { font-size: 1rem; }
.agent-bubble :deep(p) { margin: 0.5rem 0; } .agent-bubble :deep(b), .agent-bubble :deep(strong) { font-weight: 600; }
.agent-bubble :deep(ul), .agent-bubble :deep(ol) { margin: 0.5rem 0; padding-left: 1.5rem; list-style-position: outside; }
.agent-bubble :deep(ul) { list-style-type: disc; } .agent-bubble :deep(ol) { list-style-type: decimal; }
.agent-bubble :deep(li) { margin-bottom: 0.25rem; }
.agent-bubble :deep(pre) { background-color: #1f2937; color: #f9fafb; border-radius: 0.5rem; margin: 1rem 0; padding: 1rem; overflow-x: auto; }
.agent-bubble :deep(code) { background-color: var(--bg-secondary); color: #db2777; border-radius: 0.25rem; padding: 2px 4px; font-family: monospace; font-size: 0.875rem; }
.agent-bubble :deep(pre code) { background-color: transparent; color: inherit; padding: 0; }
.scratchpad-area { margin-top: 0.5rem; width: 100%; max-width: 48rem; text-align: left; font-size: 0.75rem; color: var(--text-secondary); }
.scratchpad-area details { background-color: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 0.5rem; padding: 0.5rem 1rem; cursor: pointer; }
.scratchpad-area summary { font-weight: 600; color: var(--text-primary); list-style: inside; }
.scratchpad-content { margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px dashed var(--border-color); white-space: pre-wrap; word-break: break-all; }
.scratchpad-line { margin-bottom: 0.25rem; color: var(--text-secondary); }
</style>