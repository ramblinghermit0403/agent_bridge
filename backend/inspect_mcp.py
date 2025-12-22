import mcp.client.streamable_http
print("Attributes:")
for x in dir(mcp.client.streamable_http):
    if not x.startswith("_"):
        print(x)
