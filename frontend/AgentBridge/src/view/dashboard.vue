<template>
  <div :class="['app-container', themeClass]">
    <aside class="sidebar" :class="{ collapsed: isSidebarCollapsed }">
      <div class="sidebar-header">
        <button class="sidebar-toggle" @click="toggleSidebar" aria-label="Toggle sidebar">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="3" y1="12" x2="21" y2="12"></line>
            <line x1="3" y1="6" x2="21" y2="6"></line>
            <line x1="3" y1="18" x2="21" y2="18"></line>
          </svg>
        </button>
      </div>

      <nav class="sidebar-nav">
        <router-link to="/agent" class="nav-link">
          <div class="nav-icon-wrapper"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"
              viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
              stroke-linejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg></div>
          <span>New Chat</span>
        </router-link>
        <router-link to="/library" class="nav-link">
          <div class="nav-icon-wrapper">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path>
              <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path>
            </svg>
          </div>
          <span>Library</span>
        </router-link>
      </nav>

      <div class="past-chats-wrapper">
        <template v-if="conversations.length > 0">
          <div class="past-chats-header">
            <hr class="sidebar-divider" />
            <div class="sidebar-section-title">Chats</div>
          </div>
          <div class="past-chats-list">
            <router-link v-for="conv in conversations" :key="conv.id" :to="`/agent?session=${conv.id}`"
              class="past-chat-link" :class="{ 'past-chat-link-active': isActivePastChat(conv.id) }">
              <div class="nav-icon-wrapper">

              </div>
              <span class="chat-title">{{ conv.title || 'Untitled Chat' }}</span>
            </router-link>
          </div>
        </template>
      </div>

      <div class="sidebar-footer">
        <SidebarCarousel />
      </div>

    </aside>

    <div class="main-content">
      <header class="main-header">
        <div class="brand-title">AgentBridge</div>
        <div class="header-controls">
          <button class="control-button" @click="toggleTheme" aria-label="Toggle theme"><svg v-if="isDarkMode"
              xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="5"></circle>
              <line x1="12" y1="1" x2="12" y2="3"></line>
              <line x1="12" y1="21" x2="12" y2="23"></line>
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
              <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
              <line x1="1" y1="12" x2="3" y2="12"></line>
              <line x1="21" y1="12" x2="23" y2="12"></line>
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
            </svg><svg v-else xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
            </svg></button>
          <div class="profile-button-wrapper">
            <button @click="toggleProfilePopup" class="control-button profile-button" aria-label="Profile"
              ref="profileButton">
              <span v-if="isLoggedIn" class="profile-avatar-initial">{{ userInitial }}</span>
              <svg v-else xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                <circle cx="12" cy="7" r="4"></circle>
              </svg>
            </button>
            <transition name="popup-fade">
              <div v-if="isProfilePopupVisible" class="profile-popup" ref="profilePopup">
                <div v-if="isLoggedIn">
                  <div class="popup-user-info">
                    <div class="user-avatar">{{ userInitial }}</div>
                    <div class="user-details"><span class="user-name">{{ userName }}</span><span class="user-email">{{
                        userEmail }}</span></div>
                  </div>
                  <hr class="popup-divider" />
                  <ul class="popup-menu">
                    <li><button @click="goToSettings" class="popup-menu-item"><svg xmlns="http://www.w3.org/2000/svg"
                          width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                          stroke-linecap="round" stroke-linejoin="round">
                          <circle cx="12" cy="12" r="3"></circle>
                          <path
                            d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z">
                          </path>
                        </svg><span>Settings</span></button></li>
                  </ul>
                  <hr class="popup-divider" />
                  <ul class="popup-menu">
                    <li><button @click="logout" class="popup-menu-item"><svg xmlns="http://www.w3.org/2000/svg"
                          width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                          stroke-linecap="round" stroke-linejoin="round">
                          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                          <polyline points="16 17 21 12 16 7"></polyline>
                          <line x1="21" y1="12" x2="9" y2="12"></line>
                        </svg><span>Sign out</span></button></li>
                  </ul>
                </div>
                <div v-else class="popup-logged-out"><button @click="login" class="popup-login-button">Sign in</button>
                </div>
              </div>
            </transition>
          </div>
        </div>
      </header>
      <main class="content-area">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import SidebarCarousel from './SidebarCarousel.vue';

import { useToast } from 'vue-toastification';

const router = useRouter();
const route = useRoute();
const toast = useToast();

const isSidebarCollapsed = ref(false);
const isDarkMode = ref(false);
const isProfilePopupVisible = ref(false);
const isLoggedIn = ref(false);
const userEmail = ref('');
const userName = ref('');
const profilePopup = ref(null);
const profileButton = ref(null);
const conversations = ref([]);
const api_url = import.meta.env.VITE_API_URL || 'http://localhost:8001';

const userInitial = computed(() => (userName.value ? userName.value.charAt(0).toUpperCase() : '?'));
const themeClass = computed(() => (isDarkMode.value ? 'dark-theme' : 'light-theme'));

const isActivePastChat = (sessionId) => {
  return route.path === '/agent' && route.query.session === sessionId;
};

const logout = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  isLoggedIn.value = false;
  userEmail.value = '';
  userName.value = '';
  closeProfilePopup();
  toast.success('Signed out successfully.');
  router.push('/login');
};
const login = () => { closeProfilePopup(); router.push('/login'); };
const toggleSidebar = () => { isSidebarCollapsed.value = !isSidebarCollapsed.value; };
const toggleTheme = () => {
  isDarkMode.value = !isDarkMode.value;
  const theme = isDarkMode.value ? 'dark' : 'light';
  localStorage.setItem('theme', theme);
  document.body.classList.remove('light-theme', 'dark-theme');
  document.body.classList.add(`${theme}-theme`);
};
const goToSettings = () => { router.push('/settings'); closeProfilePopup(); };
const toggleProfilePopup = () => { isProfilePopupVisible.value = !isProfilePopupVisible.value; };
const closeProfilePopup = () => { isProfilePopupVisible.value = false; };

const handleClickOutside = (event) => {
  if (isProfilePopupVisible.value && profilePopup.value && !profilePopup.value.contains(event.target) && profileButton.value && !profileButton.value.contains(event.target)) {
    closeProfilePopup();
  }
};

const loadConversationsList = async () => {
  const token = localStorage.getItem('token');
  if (!token) {
    conversations.value = [];
    return;
  }

  try {
    const response = await fetch(`${api_url}/api/chats/`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (response.ok) {
      conversations.value = await response.json();
    } else if (response.status === 401) {
      console.error("Authentication expired. Please log in again.");
      logout();
    } else {
      const errorData = await response.json();
      console.error("Failed to load conversation list:", errorData.detail);
      conversations.value = [];
    }
  } catch (error) {
    console.error("Network error loading conversation list:", error);
    conversations.value = [];
  }
};

onMounted(() => {
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme) {
    isDarkMode.value = savedTheme === 'dark';
  } else {
    isDarkMode.value = window.matchMedia('(prefers-color-scheme: dark)').matches;
  }

  const token = localStorage.getItem('token');
  const storedUser = localStorage.getItem('user');
  if (token && storedUser) {
    try {
      const userData = JSON.parse(storedUser);
      isLoggedIn.value = true;
      userEmail.value = userData.email || '';
      userName.value = userData.username || '';
    } catch (e) {
      console.error("Failed to parse user data", e);
      logout();
    }
  }

  if (isLoggedIn.value) {
    loadConversationsList();
  }

  window.addEventListener('click', handleClickOutside);
});

onBeforeUnmount(() => {
  window.removeEventListener('click', handleClickOutside);
});

watch(isLoggedIn, (newVal) => {
  if (newVal) {
    loadConversationsList();
  } else {
    conversations.value = [];
  }
});
</script>

<style>
/* ... (root, theme, and other basic styles remain the same) ... */

/* Default nav-link styles for main navigation (Home, Chat) */
.nav-link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px 10px 10px;
  text-decoration: none;
  color: var(--text-secondary);
  font-weight: 500;
  border-radius: 8px;
  white-space: nowrap;
  transition: color 0.2s ease, background-color 0.2s ease;
}

.nav-link:hover {
  background-color: var(--bg-primary);
  color: var(--text-primary);
}

.nav-link.router-link-exact-active {
  background-color: var(--bg-primary);
  color: var(--text-primary);
}

.nav-link.router-link-exact-active:hover {
  background-color: var(--bg-primary);
}

/* --- Styles for Past Chats --- */
.past-chat-link {
  font-size: 0.85rem;
  color: var(--text-secondary);
  padding: 6px 16px 6px 10px;
  background-color: transparent;
  border-left: 3px solid transparent;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  transition: background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease;
}

.past-chat-link:hover {
  background-color: var(--bg-primary);
  color: var(--text-primary);
  border-left-color: var(--text-secondary);
}

.past-chat-link .chat-title {
  font-weight: 500;
  flex-grow: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* MODIFIED: Active past chat link style now has a gray tone */
.past-chat-link.past-chat-link-active {
  background-color: var(--bg-primary);
  color: var(--text-primary);
  border-left-color: var(--text-primary);
}

/* Hovering over an active gray link shouldn't change it */
.past-chat-link.past-chat-link-active:hover {
  background-color: var(--bg-primary);
  border-left-color: var(--text-primary);
}

.past-chat-link svg {
  width: 20px;
  height: 20px;
  opacity: 0.7;
  color: var(--text-secondary);
}

.past-chat-link.past-chat-link-active svg {
  opacity: 1;
  color: var(--text-primary);
}

/* --- Sidebar Collapse Logic --- */

.sidebar.collapsed {
  width: 78px;
}

/* MODIFIED: Hide the entire past chats section when the sidebar is collapsed */
.sidebar.collapsed .past-chats-wrapper {
  display: none;
}

/* Only apply collapsing styles to main nav links and their text */
.sidebar.collapsed .nav-link {
  gap: 0;
  padding-left: 10px;
}

.sidebar.collapsed .nav-link span {
  opacity: 0;
  width: 0;
  visibility: hidden;
}


/* --- NEW: Separate static and scrollable chat sections --- */

.past-chats-wrapper {
  display: flex;
  flex-direction: column;
  flex-grow: 1;
  min-height: 0;
}

.past-chats-header {
  flex-shrink: 0;
  padding: 0 16px;
}

.past-chats-list {
  flex-grow: 1;
  overflow-y: auto;
  padding: 0 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  -ms-overflow-style: none; /* Hide scrollbar for Internet Explorer and Edge */
  scrollbar-width: none; /* Hide scrollbar for Firefox */
}

/* Hide scrollbar for Chrome, Safari, and Opera */
.past-chats-list::-webkit-scrollbar {
  display: none;
}

/* --- Other unchanged styles (for completeness) --- */

.app-container {
  display: flex;
  height: 100vh;
  width: 100vw;
  background-color: var(--bg-primary);
  color: var(--text-primary);
  font-family: var(--font-sans);
  overflow: hidden;
}

.main-content {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
}

.sidebar {
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  width: 240px;
  background-color: var(--bg-secondary);
  border-right: 1px solid var(--border-color);
  transition: width var(--transition-speed) var(--transition-ease);
  overflow-x: hidden;
}

.sidebar-header {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 64px;
  width: 78px;
  flex-shrink: 0;
}

.sidebar-toggle {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 8px;
  border-radius: 50%;
  display: flex;
  transition: color 0.2s ease, background-color 0.2s ease;
}

.sidebar-toggle:hover {
  background-color: var(--bg-primary);
  color: var(--text-primary);
}

.sidebar-nav {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 0 16px;
  padding-bottom: 20px;
}

.sidebar.collapsed .sidebar-nav {
  padding: 0 16px;
}

.sidebar-footer {
  flex-shrink: 0;
  transition: opacity 0.3s ease, visibility 0.3s ease;
}

.sidebar.collapsed .sidebar-footer {
  opacity: 0;
  visibility: hidden;
  height: 0;
  overflow: hidden;
  margin: 0;
  padding: 0;
}

.sidebar-divider {
  border: none;
  border-top: 1px solid var(--border-color);
  margin: 16px 0;
}

.sidebar-section-title {
  font-size: 0.85rem;
  color: var(--text-secondary);
  font-weight: 600;
  padding: 4px 10px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 4px;
}

.nav-icon-wrapper {
  height: 100%;
  flex-shrink: 0;
  display: flex;
  justify-content: center;
  align-items: center;
}

.nav-link svg {
  width: 24px;
  height: 24px;
}

.main-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  height: 64px;
  flex-shrink: 0;

  background-color: var(--bg-primary);
  position: sticky;
  top: 0;
  z-index: 100;
}

.brand-title {
  font-size: 1.25rem;
  font-weight: 600;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.control-button {
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 8px;
  border-radius: 50%;
  transition: color 0.2s ease, background-color 0.2s ease;
}

.control-button:hover {
  color: var(--text-primary);
  background-color: var(--bg-primary);
}

.profile-button-wrapper {
  position: relative;
}

.profile-button {
  padding: 0;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border: 1px solid var(--border-color);
}

.profile-button:hover {
  border-color: var(--text-primary);
}

.profile-avatar-initial {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.profile-popup {
  position: absolute;
  top: calc(100% + 12px);
  right: 0;
  width: 280px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  padding: 0.5rem;
  display: flex;
  flex-direction: column;
}

.popup-user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0.75rem 0.75rem;
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: var(--accent-color);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  font-weight: 500;
  flex-shrink: 0;
}

.user-details {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.user-name {
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-email {
  font-size: 0.8rem;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.popup-divider {
  border: none;
  height: 1px;
  background-color: var(--border-color);
  margin: 0.25rem 0;
}

.popup-menu {
  list-style: none;
  padding: 0;
  margin: 0.25rem 0;
}

.popup-menu-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  text-align: left;
  padding: 0.75rem;
  background: none;
  border: none;
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.popup-menu-item svg {
  color: var(--text-secondary);
  flex-shrink: 0;
}

.popup-menu-item:hover {
  background-color: var(--bg-primary);
}

.popup-logged-out {
  padding: 1rem;
}

.popup-login-button {
  width: 100%;
  padding: 0.75rem;
  font-weight: 600;
  color: white;
  background-color: var(--accent-color);
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.popup-login-button:hover {
  background-color: var(--accent-hover);
}

.popup-fade-enter-active,
.popup-fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.popup-fade-enter-from,
.popup-fade-leave-to {
  opacity: 0;
  transform: translateY(-5px);
}

.content-area {
  flex-grow: 1;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>