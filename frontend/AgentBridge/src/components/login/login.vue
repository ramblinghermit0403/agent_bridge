<template>
  <div class="auth-page-container">
    <div class="auth-card">
      
      <!-- Header -->
      <div class="auth-header">
        <h1>AgentBridge</h1>
        <p>{{ viewTitle }}</p>
      </div>
      
      <!-- Success or Error Messages -->
      <div v-if="message" :class="['message', isError ? 'error' : 'success']">
        {{ message }}
      </div>

      <!-- Form container with transition -->
      <transition name="form-swap" mode="out-in">
        <!-- Login Form -->
        <form v-if="isLoginView" @submit.prevent="handleLogin" class="auth-form" key="login">
          <div class="form-group">
            <label for="login-email">Email</label>
            <input type="email" id="login-email" v-model="loginForm.email" required class="form-input">
          </div>
          <div class="form-group">
            <label for="login-password">Password</label>
            <input type="password" id="login-password" v-model="loginForm.password" required class="form-input">
          </div>
          <button type="submit" class="form-button">Sign In</button>
        </form>

        <!-- Register Form -->
        <form v-else @submit.prevent="handleRegister" class="auth-form" key="register">
          <div class="form-group">
            <label for="register-username">Username</label>
            <input type="text" id="register-username" v-model="registerForm.username" required class="form-input">
          </div>
          <div class="form-group">
            <label for="register-email">Email</label>
            <input type="email" id="register-email" v-model="registerForm.email" required class="form-input">
          </div>
          <div class="form-group">
            <label for="register-password">Password</label>
            <input type="password" id="register-password" v-model="registerForm.password" required class="form-input">
          </div>
          <button type="submit" class="form-button">Create Account</button>
        </form>
      </transition>
      
      <!-- Link to switch between forms -->
      <div class="form-switcher">
        <span>{{ isLoginView ? "Don't have an account?" : "Already have an account?" }}</span>
        <a href="#" @click.prevent="switchView">
          {{ isLoginView ? 'Sign Up' : 'Sign In' }}
        </a>
      </div>
    </div>
  </div>
</template>


<script setup>
import { ref, reactive, computed } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const loginForm = reactive({ email: '', password: '' });
const registerForm = reactive({ username: '', email: '', password: '' });
const isLoginView = ref(true);
const message = ref('');
const isError = ref(false);

const viewTitle = computed(() => isLoginView.value ? 'Sign in to your account' : 'Create a new account');

const switchView = () => {
  isLoginView.value = !isLoginView.value;
  message.value = '';
  isError.value = false;
};

// --- NEW HELPER FUNCTION TO FETCH USER DETAILS ---
const fetchUserDetails = async (token) => {
  try {
    const response = await fetch('http://localhost:8001/users/me', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    if (!response.ok) {
      throw new Error('Failed to fetch user details.');
    }
    const userDetails = await response.json();
    // Save the user details object as a JSON string in localStorage
    localStorage.setItem('user', JSON.stringify(userDetails));
    return true;
  } catch (error) {
    console.error('Error fetching user details:', error);
    // Even if this fails, the user is logged in with a valid token.
    // Clear any stale user data.
    localStorage.removeItem('user');
    return false;
  }
};

const handleLogin = async () => {
  message.value = 'Signing in...';
  isError.value = false;
  const formData = new URLSearchParams();
  formData.append('username', loginForm.email);
  formData.append('password', loginForm.password);
  
  try {
    // Step 1: Log in to get the token
    const loginResponse = await fetch('http://localhost:8001/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData.toString()
    });

    const loginData = await loginResponse.json();
    if (!loginResponse.ok) {
      throw new Error(loginData.detail || 'Login failed.');
    }

    const token = loginData.access_token;
    localStorage.setItem('token', token);

    // Step 2: Use the new token to fetch user details
    message.value = 'Fetching user details...';
    await fetchUserDetails(token);
    
    // Step 3: Redirect
    message.value = 'Success! Redirecting...';
    setTimeout(() => router.push('/agent'), 1000);

  } catch (error) {
    message.value = error.message;
    isError.value = true;
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  }
};

const handleRegister = async () => {
  // Unchanged from previous version
  message.value = 'Creating account...';
  isError.value = false;
  const payload = { username: registerForm.username, email: registerForm.email, password: registerForm.password };
  try {
    const response = await fetch('http://localhost:8001/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await response.json();
    if (response.ok) {
      message.value = data.message || 'Registration successful! Please sign in.';
      isError.value = false;
      setTimeout(() => {
        switchView();
        registerForm.username = '';
        registerForm.email = '';
        registerForm.password = '';
      }, 2000);
    } else {
      throw new Error(data.detail || 'Registration failed.');
    }
  } catch (error) {
    message.value = error.message;
    isError.value = true;
  }
};
</script>

<style scoped>
.auth-page-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 2rem;
  background-color: var(--bg-primary, #f9fafb);
  font-family: var(--font-sans, 'Segoe UI', sans-serif);
  color: var(--text-primary, #111827);
  animation: fadeIn 0.5s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.auth-card {
  position: relative;
  width: 100%;
  max-width: 420px;
  padding: 2.5rem 2rem;
  background-color: var(--bg-secondary, #ffffff);
  border: 1px solid var(--border-color, #e5e7eb);
  border-radius: 16px;
  box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.auth-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, transparent, var(--accent-color, #3b82f6), transparent);
  opacity: 0.8;
}

.auth-header {
  text-align: center;
  margin-bottom: 2rem;
}
.auth-header h1 {
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-primary, #111827);
}
.auth-header p {
  font-size: 1rem;
  color: var(--text-secondary, #6b7280);
}

.message {
  padding: 0.75rem 1rem;
  margin-bottom: 1.5rem;
  border-radius: 8px;
  text-align: center;
  font-weight: 500;
  font-size: 0.9rem;
}
.message.success {
  background-color: #dcfce7;
  color: #15803d;
  border: 1px solid #bbf7d0;
}
.message.error {
  background-color: #fee2e2;
  color: #b91c1c;
  border: 1px solid #fecaca;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.form-group {
  display: flex;
  flex-direction: column;
}
.form-group label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-secondary, #6b7280);
  margin-bottom: 0.5rem;
}
.form-input {
  width: 100%;
  padding: 0.75rem 1rem;
  background-color: var(--bg-secondary, #fff);
  border: 1px solid var(--border-color, #d1d5db);
  border-radius: 8px;
  color: var(--text-primary, #111827);
  font-size: 1rem;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.form-input:hover {
  border-color: #9ca3af;
}
.form-input:focus {
  outline: none;
  border-color: var(--accent-color, #3b82f6);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
}

.form-button {
  padding: 0.8rem;
  margin-top: 0.5rem;
  font-weight: 600;
  font-size: 1rem;
  color: white;
  background-color: var(--accent-color, #3b82f6);
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease-out;
}
.form-button:hover {
  background-color: var(--accent-hover, #2563eb);
  box-shadow: 0 4px 15px rgba(59, 130, 246, 0.25);
}
.form-button:disabled {
  background-color: #a5b4fc;
  cursor: not-allowed;
}

.form-switcher {
  text-align: center;
  margin-top: 2rem;
  font-size: 0.9rem;
  color: var(--text-secondary, #6b7280);
}
.form-switcher a {
  font-weight: 600;
  color: var(--accent-color, #3b82f6);
  text-decoration: none;
  margin-left: 0.35rem;
}
.form-switcher a:hover {
  text-decoration: underline;
}

.form-swap-enter-active,
.form-swap-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.form-swap-enter-from { opacity: 0; transform: translateY(10px); }
.form-swap-leave-to { opacity: 0; transform: translateY(-10px); }

@media (max-width: 480px) {
  .auth-card {
    padding: 2rem 1.25rem;
  }
}
</style>
