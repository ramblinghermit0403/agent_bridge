from mcp.client.sse import sse_client
import inspect

spec = inspect.getfullargspec(sse_client)
print(spec.args)
print(spec.defaults)
print(spec.kwonlyargs)
print(spec.kwonlydefaults)
