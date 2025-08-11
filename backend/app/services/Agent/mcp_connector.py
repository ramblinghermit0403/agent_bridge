import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client


import json
class MCPConnector:
    def __init__(self, sse_url: str):
        self.sse_url = sse_url

    async def list_tools(self):
        async with sse_client(self.sse_url) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                tools_result = await session.list_tools()
                print(tools_result)

                tool_list = []
                for tool in tools_result.tools:
                    # Use inputSchema instead of parameters
                    input_schema = None

                    # Check if tool has inputSchema attribute
                    if hasattr(tool, "inputSchema"):
                        # If inputSchema is a string, parse JSON
                        if isinstance(tool.inputSchema, str):
                            try:
                                input_schema = json.loads(tool.inputSchema)
                            except json.JSONDecodeError:
                                input_schema = None
                        else:
                            input_schema = tool.inputSchema

                    tool_list.append({
                        "name": tool.name,
                        "description": tool.description,
                        "argument_schema": input_schema,
                    })

                return tool_list
            
    # async def run_tool(self, tool_name: str, parameters: dict):
    #     async with sse_client(self.sse_url) as (read_stream, write_stream):
    #         async with ClientSession(read_stream, write_stream) as session:
    #             await session.initialize()
    #             result = await session.run_tool(tool_name=tool_name, input=parameters)
    #             return result.output if hasattr(result, "output") else result

  
    async def run_tool(self, tool_name: str, parameters: dict):
        try:
            async with sse_client(self.sse_url) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()

                    # Find the tool first
                    tools_result = await session.list_tools()
                    tool = next((t for t in tools_result.tools if t.name == tool_name), None)
                    if not tool:
                        raise ValueError(f"Tool '{tool_name}' not found.")

                    # ✅ Correct way to run tool using MCP session
                    # result = await session.call_tool(tool, parameters)
                    result = await session.call_tool(tool.name, parameters)


                    # Return the result
                    return result.output if hasattr(result, "output") else result

        except AttributeError as e:
            raise RuntimeError(f"Tool execution failed due to missing method: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to run tool '{tool_name}': {e}")
