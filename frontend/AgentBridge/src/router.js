import { createRouter, createWebHistory } from 'vue-router'

import AIagent from './components/agent/AIagent.vue'
import dashboard from './view/dashboard.vue' // Assuming dashboard is your main layout component
import settings from './components/settings/settings.vue'
import LearnMoreView from './view/LearnMoreView.vue'; // <-- IMPORT the new view
import login from './components/login/login.vue' // Assuming you have a login component
import { useToast } from 'vue-toastification'
import LibraryView from './components/library/LibraryView.vue'; // <-- IMPORT the library view

const toast = useToast()

const routes = [
  // This route handles the root path and redirects to /agent
  {
    path: '/',
    redirect: '/agent'
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
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')

  if (to.matched.some((record) => record.meta.requiresAuth)) {
    if (!token) {
      toast.error('Session expired. Please log in again.')
      return next('/')
    }

    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      const now = Math.floor(Date.now() / 1000)

      if (payload.exp < now) {
        localStorage.removeItem('token')
        toast.error('Session expired. Please log in again.')
        return next('/')
      }
    } catch (error) {
      localStorage.removeItem('token')
      toast.error('Invalid session. Please log in again.')
      return next('/')
    }
  }

  next()
})

export default router;