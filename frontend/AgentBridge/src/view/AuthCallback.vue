<template>
  <div class="callback-container">
    <h2>Authenticating...</h2>
    <p>Please wait while we complete the connection.</p>
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { useToast } from 'vue-toastification';

const route = useRoute();
const toast = useToast();

onMounted(() => {
  const code = route.query.code;
  const state = route.query.state;

  if (window.opener) {
    if (code && state) {
      window.opener.postMessage({ type: 'oauth-callback', code, state }, '*');
      toast.success('Authenticated successfully. Closing...');
    } else {
        window.opener.postMessage({ type: 'oauth-error', error: 'No code returned' }, '*');
        toast.error('Authentication failed: No code returned.');
    }
    setTimeout(() => window.close(), 1500);
  } else {
      console.error("No opener window found. Cannot complete auth.");
      toast.error('Authentication error: Original window not found.');
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
