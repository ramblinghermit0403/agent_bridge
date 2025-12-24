import { createApp } from 'vue'
import App from './App.vue'
import router from './router.js'
import './assets/main.css'
import Toast, { POSITION } from 'vue-toastification'
import 'vue-toastification/dist/index.css'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import { Toaster } from 'vue-sonner'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'

/* import the fontawesome core */
import { library } from '@fortawesome/fontawesome-svg-core'
// In frontend/src/main.js

/*
  import specific icons we want to use.
  This is "tree-shaking" - it keeps the final app size small
  by only including the icons we actually need.
  Find more icons at: https://fontawesome.com/search?m=free&s=solid
*/

import { faGithub, faLinkedin, faTwitter } from '@fortawesome/free-brands-svg-icons'
import {
  faTrash,
  faCube, // For Logic/Condition
  faFileAlt, // For Log Data
  faBullhorn, // For Send Broadcast
  faPaperPlane,
  faArrowLeft,
  faGear,
  faEllipsisV,
  faPen,
  faSyncAlt,
  faBolt
  // For the Save button
} from '@fortawesome/free-solid-svg-icons'

/* add icons to the library */
library.add(faCube, faSyncAlt, faFileAlt, faBullhorn, faPaperPlane, faTrash, faArrowLeft, faGear, faBolt, faEllipsisV, faPen, faGithub, faLinkedin, faTwitter)

const app = createApp(App)
app.component('ToasterVue', Toaster)
// Make the component globally available
app.component('FontAwesomeIcon', FontAwesomeIcon)
app.use(ElementPlus)
app.use(Toast, {
  position: POSITION.BOTTOM_LEFT,
  timeout: 5000,
  zIndex: 2147483647,
  toastClassName: 'custom-toast',
  bodyClassName: 'custom-toast-body',
  hideProgressBar: true,
  closeButton: false,
  icon: false
})

// Enable devtools in production
app.config.devtools = true
const API_URL = import.meta.env.VITE_API_URL;
console.log('API URL:', API_URL)

app.use(router).mount('#app')
