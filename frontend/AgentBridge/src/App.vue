<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script>
export default {
  name: 'App',
};
</script>

<style>
.Toastify__toast-container {
  z-index: 99999 !important;
}

:root {
  --font-sans: 'Inter', sans-serif;
  --transition-speed: 0.3s;
  --transition-ease: ease-in-out;
  --bg-primary-light: #f4f5f7;
  --bg-secondary-light: #ffffff;
  --text-primary-light: #172b4d;
  --text-secondary-light: #5e6c84;
  --border-light: #dfe1e6;
  --accent-light: #0052cc;
  --accent-hover-light: #0065ff;
  --bg-primary-dark: #0d1117;
  --bg-secondary-dark: #161b22;
  --text-primary-dark: #c9d1d9;
  --text-secondary-dark: #8b949e;
  --border-dark: #30363d;
  --accent-dark: #58a6ff;
  --accent-hover-dark: #79c0ff;
}

.light-theme {
  --bg-primary: var(--bg-primary-light);
  --bg-secondary: var(--bg-secondary-light);
  --text-primary: var(--text-primary-light);
  --text-secondary: var(--text-secondary-light);
  --border-color: var(--border-light);
  --accent-color: var(--accent-light);
  --accent-hover: var(--accent-hover-light);
}

.dark-theme {
  --bg-primary: var(--bg-primary-dark);
  --bg-secondary: var(--bg-secondary-dark);
  --text-primary: var(--text-primary-dark);
  --text-secondary: var(--text-secondary-dark);
  --border-color: var(--border-dark);
  --accent-color: var(--accent-dark);
  --accent-hover: var(--accent-hover-dark);
}
</style>