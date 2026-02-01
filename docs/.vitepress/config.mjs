import { withMermaid } from 'vitepress-plugin-mermaid';

/**
 * @type {import('vitepress').UserConfig}
 */

export default withMermaid({
    // Only use the sub-path during production builds on GitHub
    base: process.env.GITHUB_ACTIONS === 'true'
        ? '/agent_bridge/'
        : '/',

    title: "Agent Bridge",
    description: "AI Agent Platform with MCP Support",
    head: [
        ['link', { rel: 'icon', href: '/favicon.ico' }]
    ],
    mermaid: {
        theme: 'default',
    },
    themeConfig: {
        logo: '/favicon.ico',
        nav: [
            { text: 'Home', link: '/' },
            { text: 'Learning', link: '/dev/learning/index' },
            { text: 'Documentation', link: '/guide/getting-started' }
        ],

        sidebar: {
            '/dev/learning/': [
                {
                    text: 'Agent Learning Course',
                    items: [
                        { text: 'Overview', link: '/dev/learning/index' },
                        { text: '1. The Paradigm', link: '/dev/learning/01_paradigm' },
                        { text: '2. The Orchestrator', link: '/dev/learning/02_orchestrator' },
                        { text: '3. Dynamic Tooling', link: '/dev/learning/03_factory' },
                        { text: '4. Safety & Persistence', link: '/dev/learning/04_safety' },
                        { text: '5. Debugging', link: '/dev/learning/05_debugging' },
                        { text: 'Checklist', link: '/dev/learning/checklist' }
                    ]
                }
            ],
            '/': [
                {
                    text: 'User Guide',
                    items: [
                        { text: 'Getting Started', link: '/guide/getting-started' },
                        { text: 'Use Cases', link: '/guide/use-cases' },
                        { text: 'Connecting Tools (MCP)', link: '/guide/mcp-servers' },
                        { text: 'Authentication', link: '/guide/auth-setup' },
                        { text: 'AI Models', link: '/guide/llm-providers' },
                        { text: 'Permissions', link: '/guide/permissions' }
                    ]
                },
                {
                    text: 'Developer Guide',
                    items: [
                        { text: 'Architecture', link: '/dev/architecture' },
                        { text: 'Agent Core', link: '/dev/agent-core' },
                        { text: 'Extending Platform', link: '/dev/expansion' },
                        { text: 'Frontend', link: '/dev/frontend' },
                        {
                            text: 'API Reference',
                            items: [
                                { text: 'Overview', link: '/api/index' },
                                { text: 'Agent Services', link: '/api/agent-services' },
                                { text: 'MCP Services', link: '/api/mcp-services' },
                                { text: 'Database Models', link: '/api/models' }
                            ]
                        }
                    ]
                }
            ]
        },

        socialLinks: [
            { icon: 'github', link: 'https://github.com/ramblinghermit0403/agent_bridge' }
        ]
    },
    srcDir: '.',
    rewrites: {}
})