import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def main():
    url = "https://mcp.figma.com/mcp"
    print(f"Connecting to {url} using streamablehttp_client...")
    try:
        async with streamablehttp_client(url) as (read, write, transport):
            print("Stream opened (Streamable HTTP), initializing session...")
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("Connected!")
                tools = await session.list_tools()
                print(f"Tools found: {len(tools.tools)}")
                for t in tools.tools:
                    print(f"- {t.name}: {t.description}")
    except Exception:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
