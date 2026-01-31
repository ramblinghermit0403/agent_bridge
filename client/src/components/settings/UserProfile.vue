<template>
  <div class="settings-group">
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
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { useToast } from 'vue-toastification';

const BACKEND_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';
const toast = useToast();

const isEditingProfile = ref(false);
const profileForm = reactive({ username: '', email: '' });

const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  if (!token) {
    toast.error('Authentication token not found. Please log in.'); return null;
  }
  return { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` };
};

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
};

const cancelEditingProfile = () => {
  isEditingProfile.value = false;
  loadProfileData();
};

const handleProfileUpdate = async () => {
  const headers = getAuthHeaders(); if (!headers) return;
  try {
    const response = await fetch(`${BACKEND_BASE_URL}/users/me`, { method: 'PUT', headers, body: JSON.stringify(profileForm) });
    const updatedUser = await response.json();
    if (!response.ok) throw new Error(updatedUser.detail || 'Failed to update profile.');
    localStorage.setItem('user', JSON.stringify(updatedUser));
    toast.success('Profile updated successfully!');
    isEditingProfile.value = false;
  } catch (error) {
    toast.error(error.message);
  }
};

onMounted(() => {
  loadProfileData();
});
</script>

<style scoped>
/* Reusing styles from settings.vue */
.settings-group {
    height: 100%;
    display: flex;
    flex-direction: column;
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 0;
  border-bottom: 1px solid var(--border-color);
}

.settings-group > .setting-item:last-child {
  border-bottom: none;
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
  gap: 0.75rem;
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
</style>
