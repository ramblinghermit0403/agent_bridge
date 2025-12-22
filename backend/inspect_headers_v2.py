import mcp.client.streamable_http
import inspect
try:
    sig = inspect.signature(mcp.client.streamable_http.streamablehttp_client)
    print(f"Signature: {sig}")
except Exception as e:
    print(f"Error: {e}")
