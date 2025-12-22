<template>
  <div class="callback-container">
    <h2>Authenticating...</h2>
    <p>Please wait while we complete the connection.</p>
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();

onMounted(() => {
  const code = route.query.code;
  const state = route.query.state;

  if (window.opener) {
    if (code && state) {
      window.opener.postMessage({ type: 'oauth-callback', code, state }, '*');
    } else {
        window.opener.postMessage({ type: 'oauth-error', error: 'No code returned' }, '*');
    }
    window.close();
  } else {
      console.error("No opener window found. Cannot complete auth.");
  }
});
</script>

<style scoped>
.callback-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f5f5f5;
  color: #333;
}
</style>
