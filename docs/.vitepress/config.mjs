import { withMermaid } from 'vitepress-plugin-mermaid';

/**
 * @type {import('vitepress').UserConfig}
 */
export default withMermaid({
    title: "Agent Bridge",
    description: "AI Agent Platform with MCP Support",
    head: [
        ['link', { rel: 'icon', href: '/favicon.ico' }]
    ],
    mermaid: {
        // refer to mermaidjs docs for options
        theme: 'default',
    },
    themeConfig: {
        logo: '/favicon.ico',
        nav: [
            { text: 'Home', link: '/' },
            { text: 'Documentation', link: '/guide/getting-started' }
        ],

        sidebar: [
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
        ],

        socialLinks: [
            { icon: 'github', link: 'https://github.com/ramblinghermit0403/agent_bridge' }
        ]
    },
    srcDir: '.',
    rewrites: {
    }
})
