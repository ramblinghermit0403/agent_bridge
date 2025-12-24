<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup>
import { onMounted } from 'vue';

onMounted(() => {
  const savedTheme = localStorage.getItem('theme') || 'light';
  document.body.classList.add(`${savedTheme}-theme`);
});
</script>

<style>
.Toastify__toast-container {
  z-index: 99999 !important;
}
</style>