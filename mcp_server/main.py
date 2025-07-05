from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import json
import asyncio
from typing import Dict, Any
from llama_client import LlamaClient
from config import SERVER_HOST, SERVER_PORT, CORS_ORIGINS

app = FastAPI(title="Gemma3 MCP Server", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global LlamaClient instance
llama_client = LlamaClient()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "gemma3-mcp-server"}

@app.post("/rpc")
async def json_rpc_endpoint(request: Request):
    """JSON-RPC endpoint for chat and tool operations"""
    try:
        body = await request.json()
        
        # Validate JSON-RPC format
        if not isinstance(body, dict) or body.get("jsonrpc") != "2.0":
            raise HTTPException(status_code=400, detail="Invalid JSON-RPC format")
        
        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")
        
        if method == "chat":
            # Handle chat streaming
            messages = params.get("messages", [])
            tools_enabled = params.get("tools_enabled", False)
            stream = params.get("stream", False)
            
            if stream:
                return StreamingResponse(
                    generate_chat_stream(messages, tools_enabled, request_id),
                    media_type="text/plain"
                )
            else:
                # Non-streaming response
                result = await generate_chat_response(messages, tools_enabled)
                return {
                    "jsonrpc": "2.0",
                    "result": result,
                    "id": request_id
                }
        else:
            raise HTTPException(status_code=400, detail=f"Unknown method: {method}")
            
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "error": {"code": -32603, "message": str(e)},
            "id": body.get("id") if isinstance(body, dict) else None
        }

async def generate_chat_stream(messages: list, tools_enabled: bool, request_id: str):
    """Generate streaming chat response"""
    try:
        # Send initial response
        yield f"data: {json.dumps({'type': 'start', 'id': request_id})}\n\n"
        
        tool_calls = []
        
        for chunk in llama_client.stream_chat(messages, tools_enabled):
            chunk_type = chunk.get("type")
            
            if chunk_type == "token":
                # Stream content tokens
                yield f"data: {json.dumps({'type': 'content', 'content': chunk['content']})}\n\n"
                
            elif chunk_type == "tool_call":
                # Collect tool calls
                tool_calls.append({
                    "name": chunk["tool_name"],
                    "arguments": chunk["parameters"]
                })
                
            elif chunk_type == "tool_result":
                # Send tool calls first
                if tool_calls:
                    yield f"data: {json.dumps({'type': 'tool_calls', 'tool_calls': tool_calls})}\n\n"
                
                # Format and send tool result
                result = chunk["result"]
                if isinstance(result, dict) and "error" in result:
                    content = f"\n\nError: {result['error']}"
                else:
                    content = f"\n\n{format_tool_result(result)}"
                
                yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
                tool_calls = []  # Clear tool calls after sending
                
            elif chunk_type == "end":
                # Send final tool calls if any
                if tool_calls:
                    yield f"data: {json.dumps({'type': 'tool_calls', 'tool_calls': tool_calls})}\n\n"
                
                # Send completion
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                break
                
        await asyncio.sleep(0.01)  # Small delay to ensure proper streaming
        
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

async def generate_chat_response(messages: list, tools_enabled: bool) -> dict:
    """Generate non-streaming chat response"""
    try:
        content = ""
        tool_calls = []
        
        for chunk in llama_client.stream_chat(messages, tools_enabled):
            chunk_type = chunk.get("type")
            
            if chunk_type == "token":
                content += chunk["content"]
            elif chunk_type == "tool_call":
                tool_calls.append({
                    "name": chunk["tool_name"],
                    "arguments": chunk["parameters"]
                })
            elif chunk_type == "tool_result":
                result = chunk["result"]
                if isinstance(result, dict) and "error" in result:
                    content += f"\n\nError: {result['error']}"
                else:
                    content += f"\n\n{format_tool_result(result)}"
            elif chunk_type == "end":
                break
        
        return {
            "content": content,
            "tool_calls": tool_calls
        }
        
    except Exception as e:
        return {"error": str(e)}

def format_tool_result(result: dict) -> str:
    """Format tool result for display"""
    if isinstance(result, dict) and "error" in result:
        return f"Error: {result['error']}"
    
    if isinstance(result, dict) and "location" in result:
        # Weather result formatting with Fahrenheit
        location = result.get('location', 'Unknown')
        temp = result.get('temperature', 'N/A')
        description = result.get('description', 'No description')
        feels_like = result.get('feels_like', 'N/A')
        humidity = result.get('humidity', 'N/A')
        wind_speed = result.get('wind_speed', 'N/A')
        
        return f"Weather in {location}: {temp}°F, {description}. Feels like {feels_like}°F. Humidity: {humidity}%, Wind: {wind_speed} mph"
    
    return str(result)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)