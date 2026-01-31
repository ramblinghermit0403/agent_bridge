<template>
  <div class="settings-container">
    <header class="settings-header">
      <h2 class="settings-title">Settings</h2>
      <div class="search-bar-wrapper">
        <svg class="search-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
        <input type="text" placeholder="Search settings" class="search-input">
      </div>
    </header>

    <div class="settings-body">
      <aside class="settings-nav">
        <ul>
          <li class="nav-heading">User</li>
          <li>
            <router-link to="/settings/user" class="nav-link">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
              Profile
            </router-link>
          </li>
          <li class="nav-heading">Application</li>
          <li>
            <router-link to="/settings/connections" class="nav-link">
              <svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="5" r="3"></circle><circle cx="5" cy="19" r="3"></circle><circle cx="19" cy="19" r="3"></circle><line x1="12" y1="8" x2="5" y2="16"></line><line x1="12" y1="8" x2="19" y2="16"></line></svg>
              Connections
            </router-link>
          </li>
        </ul>
      </aside>

      <main class="settings-content">
        <router-view></router-view>
      </main>
    </div>
  </div>
</template>

<script setup>
// No script logic needed for the layout itself currently
</script>

<style scoped>
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
  gap: 1.5rem;
  padding: 0.75rem 1.5rem;
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0; /* Keep header height fixed */
}

.settings-title {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0;
}

.settings-body {
  display: flex;
  flex-grow: 1;
  min-height: 0;
  overflow: hidden; /* Prevent page-level scrollbars */
}

/* Search */
.search-bar-wrapper {
  position: relative;
  width: 100%;
  max-width: 320px;
}

.search-icon {
  position: absolute;
  top: 50%;
  left: 10px;
  transform: translateY(-50%);
  color: var(--text-secondary);
  pointer-events: none;
  width: 16px; 
  height: 16px;
}

.search-input {
  width: 100%;
  padding: 0.5rem 0.75rem 0.5rem 2.25rem;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-primary);
  font-size: 0.875rem;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: var(--accent-color);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--accent-color) 25%, transparent);
}

/* Nav */
.settings-nav {
  width: 220px;
  flex-shrink: 0;
  padding: 1rem 0.75rem;
  border-right: 1px solid var(--border-color);
  overflow-y: auto; /* Nav can scroll if needed */
}

.settings-nav ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.settings-nav li {
  margin-bottom: 2px;
}

.nav-heading {
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  color: var(--text-secondary);
  padding: 0.75rem 0.5rem 0.25rem;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  text-decoration: none;
  color: var(--text-secondary);
  border-radius: 6px;
  font-weight: 500;
  font-size: 0.875rem;
  transition: background-color 0.2s, color 0.2s;
}

.nav-link:hover {
  background-color: var(--bg-secondary);
  color: var(--text-primary);
}

.nav-link.router-link-active {
  background-color: var(--text-primary);
  color: var(--bg-primary);
}

.nav-link.router-link-active svg {
  stroke: var(--bg-primary);
}

.nav-icon {
  width: 16px;
  height: 16px;
}

/* Content */
.settings-content {
  flex-grow: 1;
  padding: 1.5rem 2rem;
  padding-bottom: 80px;
  overflow-y: auto; /* Scrollbar appears here */
}

/* Webkit scrollbar styling */
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
</style>