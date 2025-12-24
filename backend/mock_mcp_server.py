import uvicorn
from fastapi import FastAPI, Request
from sse_starlette.sse import EventSourceResponse
import asyncio
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mock_server")

app = FastAPI()

TOOLS = [
    {
        "name": "calculate_sum",
        "description": "Calculates the sum of two numbers.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "a": {"type": "number"},
                "b": {"type": "number"}
            },
            "required": ["a", "b"]
        }
    },
    {
        "name": "calculate_factorial",
        "description": "Calculates the factorial of a number.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "n": {"type": "integer"}
            },
            "required": ["n"]
        }
    }
]

# Simple session management (In-memory)
queues = {} # session_id -> asyncio.Queue

@app.get("/sse")
async def sse(request: Request):
    # Create a new session for each connection
    import uuid
    session_id = str(uuid.uuid4())
    q = asyncio.Queue()
    queues[session_id] = q
    logger.info(f"New SSE connection: {session_id}")

    async def event_generator():
        # 1. Send endpoint event
        yield {
            "event": "endpoint",
            "data": f"/messages?session_id={session_id}"
        }
        
        try:
            while True:
                if await request.is_disconnected():
                    logger.info(f"SSE disconnected: {session_id}")
                    queues.pop(session_id, None)
                    break
                
                # Wait for messages or keep-alive
                try:
                    # check for message with timeout to allow ping
                    msg = await asyncio.wait_for(q.get(), timeout=5.0)
                    logger.info(f"Sending message to {session_id}: {msg}")
                    yield {"event": "message", "data": json.dumps(msg)}
                except asyncio.TimeoutError:
                    # Keep connection alive
                    yield {"event": "ping", "data": "pong"}
                    
        except asyncio.CancelledError:
            queues.pop(session_id, None)
            logger.info(f"SSE cancelled: {session_id}")

    return EventSourceResponse(event_generator())

@app.post("/messages")
async def handle_messages(request: Request):
    session_id = request.query_params.get("session_id")
    if not session_id or session_id not in queues:
         # Fallback for stateless or simple test? No, MCP requires state.
         logger.error(f"Message received for unknown session: {session_id}")
         return "Session not found", 404

    data = await request.json()
    logger.info(f"Received message from {session_id}: {data}")

    method = data.get("method")
    req_id = data.get("id")
    
    response = None
    
    # JSON-RPC Handler
    if method == "initialize":
        response = {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "serverInfo": {"name": "MockMath", "version": "1.0"}
            }
        }
    elif method == "notifications/initialized":
        # No response expected
        pass
    elif method == "tools/list":
         response = {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": TOOLS
            }
        }
    elif method == "tools/call":
        params = data.get("params", {})
        tool_name = params.get("name")
        args = params.get("arguments", {})
        
        result_content = []
        is_error = False
        
        if tool_name == "calculate_sum":
            try:
                a = float(args.get("a", 0))
                b = float(args.get("b", 0))
                result_content = [{"type": "text", "text": str(a + b)}]
            except Exception as e:
                is_error = True
                result_content = [{"type": "text", "text": str(e)}]
        elif tool_name == "calculate_factorial":
            try:
                 import math
                 n = int(args.get("n", 0))
                 result_content = [{"type": "text", "text": str(math.factorial(n))}]
            except Exception as e:
                is_error = True
                result_content = [{"type": "text", "text": str(e)}]
        else:
             is_error = True
             result_content = [{"type": "text", "text": f"Unknown tool: {tool_name}"}]

        response = {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": result_content,
                "isError": is_error
            }
        }

    if response:
        await queues[session_id].put(response)
        
    return "Accepted"

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
