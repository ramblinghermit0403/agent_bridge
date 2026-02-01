import DefaultTheme from 'vitepress/theme'
import { h } from 'vue'
import Mermaid from 'vitepress-plugin-mermaid/Mermaid.vue'
import ArcadeHero from './components/ArcadeHero.vue'
import './custom.css'

export default {
    extends: DefaultTheme,
    Layout() {
        return h(DefaultTheme.Layout, null, {
            'home-hero-after': () => h(ArcadeHero)
        })
    },
    enhanceApp({ app }) {
        // Register Mermaid component globally
        app.component('Mermaid', Mermaid)
    }
}
