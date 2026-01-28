// https://vitepress.dev/guide/custom-theme
import DefaultTheme from 'vitepress/theme'
import { h } from 'vue'
import Mermaid from 'vitepress-plugin-mermaid/Mermaid.vue'
import './custom.css'

export default {
    extends: DefaultTheme,
    enhanceApp({ app }) {
        // Register Mermaid component globally
        app.component('Mermaid', Mermaid)
    }
}
