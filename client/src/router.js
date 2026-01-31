import { createRouter, createWebHistory } from 'vue-router'

import AIagent from './components/agent/AIagent.vue'
import dashboard from './view/dashboard.vue' // Assuming dashboard is your main layout component
import settings from './components/settings/settings.vue'
import UserProfile from './components/settings/UserProfile.vue'
import Connections from './components/settings/Connections.vue'
import LearnMoreView from './view/LearnMoreView.vue'; // <-- IMPORT the new view
import login from './components/login/login.vue' // Assuming you have a login component
import { useToast } from 'vue-toastification'
import LibraryView from './components/library/LibraryView.vue'; // <-- IMPORT the library view
import AuthCallback from './view/AuthCallback.vue';
import ClientRegistration from './view/ClientRegistration.vue'; // <-- IMPORT the new view

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
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        redirect: '/agent'
      },
      // The /agent route, which is now the default child of the main layout
      { path: 'agent', component: AIagent, name: 'AIagent' },
      // Other routes within the dashboard layout
      {
        path: 'settings',
        component: settings,
        children: [
          { path: '', redirect: '/settings/user' },
          { path: 'user', component: UserProfile, name: 'UserProfile' },
          { path: 'connections', component: Connections, name: 'Connections' }
        ]
      },
      {
        path: '/learn-more',
        component: LearnMoreView, // <-- Use the imported LearnMoreView component
      },
      {
        path: '/library',
        component: LibraryView, // <-- Use the imported LearnMoreView component
      },
      {
        path: '/client-registration',
        component: ClientRegistration,
      },
      // Add more routes within the dashboard as needed
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard
router.beforeEach(async (to, from, next) => {
  const token = localStorage.getItem('token')

  // Check Auth Requirements
  if (to.matched.some((record) => record.meta.requiresAuth)) {
    if (!token) {
      toast.error('Authentication required. Please log in.')
      return next('/login')
    }

    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      const now = Math.floor(Date.now() / 1000)

      if (payload.exp < now) {
        localStorage.removeItem('token')
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