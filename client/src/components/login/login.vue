<template>
  <div class="auth-container">
    <!-- Left Side: Branding -->
    <div class="auth-brand">
      <div class="brand-content">
        <h1 class="brand-title">AgentBridge</h1>
        <p class="brand-tagline">Connect. Orchestrate. Automate.</p>
        <div class="brand-features">
          <div class="feature-item">→ Multi-server orchestration</div>
          <div class="feature-item">→ Natural language control</div>
          <div class="feature-item">→ Unified tool access</div>
        </div>
      </div>
    </div>

    <!-- Right Side: Form -->
    <div class="auth-form-container">
      <div class="auth-form-wrapper">
        <div class="form-header">
          <h2>{{ isLoginView ? 'Welcome back' : 'Get started' }}</h2>
          <p>{{ isLoginView ? 'Sign in to your account' : 'Create your account' }}</p>
        </div>

        <transition name="form-fade" mode="out-in">
          <!-- Login Form -->
          <form v-if="isLoginView" @submit.prevent="handleLogin" class="form" key="login">
            <div class="input-group">
              <label for="login-email">Email</label>
              <input 
                type="email" 
                id="login-email" 
                v-model="loginForm.email" 
                required 
                class="input-field"
                placeholder="you@example.com"
              >
            </div>
            <div class="input-group">
              <label for="login-password">Password</label>
              <input 
                type="password" 
                id="login-password" 
                v-model="loginForm.password" 
                required 
                class="input-field"
                placeholder="••••••••"
              >
            </div>
            <button type="submit" class="submit-btn">Sign In</button>
          </form>

          <!-- Register Form -->
          <form v-else @submit.prevent="handleRegister" class="form" key="register">
            <div class="input-group">
              <label for="register-username">Username</label>
              <input 
                type="text" 
                id="register-username" 
                v-model="registerForm.username" 
                required 
                class="input-field"
                placeholder="johndoe"
              >
            </div>
            <div class="input-group">
              <label for="register-email">Email</label>
              <input 
                type="email" 
                id="register-email" 
                v-model="registerForm.email" 
                required 
                class="input-field"
                placeholder="you@example.com"
              >
            </div>
            <div class="input-group">
              <label for="register-password">Password</label>
              <input 
                type="password" 
                id="register-password" 
                v-model="registerForm.password" 
                required 
                class="input-field"
                placeholder="••••••••"
              >
            </div>
            <button type="submit" class="submit-btn">Create Account</button>
          </form>
        </transition>

        <div class="form-footer">
          <span>{{ isLoginView ? "Don't have an account?" : "Already have an account?" }}</span>
          <button @click="switchView" class="switch-btn">
            {{ isLoginView ? 'Sign Up' : 'Sign In' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>


<script setup>
import { ref, reactive, computed } from 'vue'; // Restored imports
import { useRouter } from 'vue-router';
import { useToast } from 'vue-toastification';

const router = useRouter();
const toast = useToast();
const loginForm = reactive({ email: '', password: '' });
const registerForm = reactive({ username: '', email: '', password: '' });
const isLoginView = ref(true);
const api_url = import.meta.env.VITE_API_URL || 'http://localhost:8001';

const viewTitle = computed(() => isLoginView.value ? 'Sign in to your account' : 'Create a new account');

const switchView = () => {
  isLoginView.value = !isLoginView.value;
};

// --- NEW HELPER FUNCTION TO FETCH USER DETAILS ---
const fetchUserDetails = async (token) => {
  try {
    const response = await fetch(`${api_url}/users/me`, {
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
  const formData = new URLSearchParams();
  formData.append('username', loginForm.email);
  formData.append('password', loginForm.password);
  
  try {
    // Step 1: Log in to get the token
    const loginResponse = await fetch(`${api_url}/auth/login`, {
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
    await fetchUserDetails(token);
    
    // Step 3: Redirect
    toast.success('Successfully logged in!');
    router.push('/agent');

  } catch (error) {
    toast.error(error.message);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  }
};

const handleRegister = async () => {
  const payload = { username: registerForm.username, email: registerForm.email, password: registerForm.password };
  
  const token = localStorage.getItem('token');
  const headers = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  try {
    const response = await fetch(`${api_url}/register`, {
      method: 'POST',
      headers: headers,
      body: JSON.stringify(payload)
    });
    const data = await response.json();
    if (response.ok) {
      toast.success(data.message || 'Registration successful! Please sign in.');
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
    toast.error(error.message);
  }
};
</script>

<style scoped>
/* Minimal Split-Screen Auth Layout */
.auth-container {
  display: flex;
  min-height: 100vh;
  background-color: var(--bg-primary);
}

/* Left Side: Brand */
.auth-brand {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--text-primary);
  color: var(--bg-primary);
  padding: 3rem;
}

.brand-content {
  max-width: 500px;
}

.brand-title {
  font-size: 3.5rem;
  font-weight: 700;
  margin: 0 0 1rem 0;
  letter-spacing: -0.02em;
}

.brand-tagline {
  font-size: 1.25rem;
  margin: 0 0 3rem 0;
  opacity: 0.8;
}

.brand-features {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.feature-item {
  font-size: 1rem;
  opacity: 0.7;
  font-family: 'Courier New', monospace;
}

/* Right Side: Form */
.auth-form-container {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  background-color: var(--bg-primary);
}

.auth-form-wrapper {
  width: 100%;
  max-width: 400px;
}

.form-header {
  margin-bottom: 3rem;
}

.form-header h2 {
  font-size: 2rem;
  font-weight: 700;
  margin: 0 0 0.5rem 0;
  color: var(--text-primary);
}

.form-header p {
  font-size: 0.95rem;
  margin: 0;
  color: var(--text-secondary);
}

/* Form Styles */
.form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.input-group label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-primary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.input-field {
  width: 100%;
  padding: 0.75rem 0;
  background: transparent;
  border: none;
  border-bottom: 1px solid var(--border-color);
  color: var(--text-primary);
  font-size: 1rem;
  font-family: var(--font-sans);
  transition: border-color var(--transition-speed) var(--transition-ease);
}

.input-field::placeholder {
  color: var(--text-secondary);
  opacity: 0.5;
}

.input-field:focus {
  outline: none;
  border-bottom-color: var(--text-primary);
}

.submit-btn {
  margin-top: 1rem;
  padding: 1rem;
  background-color: var(--text-primary);
  color: var(--bg-primary);
  border: none;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity var(--transition-speed) var(--transition-ease);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.submit-btn:hover {
  opacity: 0.9;
}

.submit-btn:active {
  opacity: 0.8;
}

/* Form Footer */
.form-footer {
  margin-top: 2rem;
  text-align: center;
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.switch-btn {
  background: none;
  border: none;
  color: var(--text-primary);
  font-weight: 600;
  cursor: pointer;
  text-decoration: underline;
  margin-left: 0.5rem;
  font-size: 0.875rem;
  transition: opacity var(--transition-speed) var(--transition-ease);
}

.switch-btn:hover {
  opacity: 0.7;
}

/* Form Transition */
.form-fade-enter-active,
.form-fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.form-fade-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.form-fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* Responsive Design */
@media (max-width: 768px) {
  .auth-container {
    flex-direction: column;
  }

  .auth-brand {
    min-height: 40vh;
    padding: 2rem;
  }

  .brand-title {
    font-size: 2.5rem;
  }

  .brand-tagline {
    font-size: 1rem;
  }

  .auth-form-container {
    padding: 2rem;
  }
}
</style>

