import { createRouter, createWebHistory } from 'vue-router'

import AIagent from './components/agent/AIagent.vue'
import dashboard from './view/dashboard.vue' // Assuming dashboard is your main layout component
import settings from './components/settings/settings.vue'
import LearnMoreView from './view/LearnMoreView.vue'; // <-- IMPORT the new view
import login from './components/login/login.vue' // Assuming you have a login component
import { useToast } from 'vue-toastification'
import LibraryView from './components/library/LibraryView.vue'; // <-- IMPORT the library view
import AuthCallback from './view/AuthCallback.vue';

const toast = useToast()

const routes = [
  // This route handles the root path and redirects to /agent
  {
    path: '/',
    redirect: '/agent'
  },
  {
    path: '/auth-callback',
    component: AuthCallback
  },
  {
    path: '/login',
    component: login
  },


  // This is your main dashboard layout route
  // All other 'protected' routes will be children of this layout
  {
    path: '/', // Keep the path as '/' if dashboard is your main layout that wraps everything
    component: dashboard, // The dashboard component acts as the layout/wrapper
    // meta: { requiresAuth: true }, // Uncomment if the entire dashboard requires auth
    children: [
      // The /agent route, which is now the default child of the main layout
      { path: 'agent', component: AIagent, name: 'AIagent' },
      // Other routes within the dashboard layout
      { path: 'settings', component: settings },
      {
        path: '/learn-more',
        component: LearnMoreView, // <-- Use the imported LearnMoreView component
      },
      {
        path: '/library',
        component: LibraryView, // <-- Use the imported LearnMoreView component
      },
      // Add more routes within the dashboard as needed
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard (no changes needed here for the routing logic)
router.beforeEach(async (to, from, next) => {
  let token = localStorage.getItem('token')

  // Auto-init Guest if no token
  if (!token) {
    try {
      const BACKEND_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';
      const res = await fetch(`${BACKEND_BASE_URL}/auth/login/guest`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        token = data.access_token;
        // Optional: Toast "Entered as Guest"
      } else {
        console.error("Failed to init guest");
      }
    } catch (e) {
      console.error("Error init guest", e);
    }
  }

  // Check Auth Requirements (if any are active)
  if (to.matched.some((record) => record.meta.requiresAuth)) {
    if (!token) {
      toast.error('Session expired. Please log in again.')
      return next('/login') // Fallback to login if guest failed
    }

    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      const now = Math.floor(Date.now() / 1000)

      if (payload.exp < now) {
        localStorage.removeItem('token')
        // Try guest again? Or just redirect login.
        // For simplicity, redirect login if expired.
        toast.error('Session expired. Please log in again.')
        return next('/login')
      }
    } catch (error) {
      localStorage.removeItem('token')
      return next('/login')
    }
  }

  // If going to login but we are already guest?
  // User might want to login to real account.
  // So allow going to login.

  next()
})

export default router;