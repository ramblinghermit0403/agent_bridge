try:
    from mcp.server.fastmcp import FastMCP
    print("FastMCP available")
except ImportError:
    print("FastMCP NOT available")
except Exception as e:
    print(f"Error: {e}")
