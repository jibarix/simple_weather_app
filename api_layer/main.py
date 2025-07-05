#!/usr/bin/env python3
"""
API Layer - FastAPI endpoints for MCP-integrated chat service
"""

import os
import json
import asyncio
import sys
from pathlib import Path
from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_client.client import MCPOrchestrator
from chat_service.chat_handler import ChatHandler

# Configuration
MODEL_PATH = os.getenv("MODEL_PATH", "./models/gemma-2-2b-it-q4_k_m.gguf")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080").split(",")

# Global instances
orchestrator = MCPOrchestrator()
chat_handler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global chat_handler
    try:
        # Initialize services
        chat_handler = ChatHandler(MODEL_PATH, orchestrator)
        await chat_handler.initialize()
        print("Services initialized successfully")
        yield
    except Exception as e:
        print(f"Initialization error: {e}")
        raise
    finally:
        # Cleanup
        if chat_handler:
            await chat_handler.shutdown()
        print("Services shut down")

app = FastAPI(
    title="MCP Chat API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    status = chat_handler.get_status() if chat_handler else {"error": "not initialized"}
    return {"status": "healthy", "service": "mcp-chat-api", "details": status}

@app.post("/rpc")
async def json_rpc_endpoint(request: Request):
    """JSON-RPC endpoint for chat operations"""
    try:
        body = await request.json()
        
        if not isinstance(body, dict) or body.get("jsonrpc") != "2.0":
            raise HTTPException(status_code=400, detail="Invalid JSON-RPC format")
        
        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")
        
        if method == "chat":
            messages = params.get("messages", [])
            tools_enabled = params.get("tools_enabled", False)
            stream = params.get("stream", False)
            
            if stream:
                return StreamingResponse(
                    generate_chat_stream(messages, tools_enabled, request_id),
                    media_type="text/plain"
                )
            else:
                result = await generate_chat_response(messages, tools_enabled)
                return {"jsonrpc": "2.0", "result": result, "id": request_id}
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
        yield f"data: {json.dumps({'type': 'start', 'id': request_id})}\n\n"
        
        async for chunk in chat_handler.handle_chat_stream(messages, tools_enabled):
            chunk_type = chunk.get("type")
            
            if chunk_type == "token":
                yield f"data: {json.dumps({'type': 'content', 'content': chunk['content']})}\n\n"
            
            elif chunk_type == "tool_result":
                result = chunk["result"]
                if isinstance(result, dict) and "error" in result:
                    content = f"\n\nError: {result['error']}"
                else:
                    content = f"\n\n{format_tool_result(result)}"
                yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
            
            elif chunk_type == "error":
                yield f"data: {json.dumps({'type': 'error', 'error': chunk['content']})}\n\n"
            
            elif chunk_type == "end":
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                break
        
        await asyncio.sleep(0.01)
        
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

async def generate_chat_response(messages: list, tools_enabled: bool) -> dict:
    """Generate non-streaming chat response"""
    try:
        content = ""
        
        async for chunk in chat_handler.handle_chat_stream(messages, tools_enabled):
            chunk_type = chunk.get("type")
            
            if chunk_type == "token":
                content += chunk["content"]
            elif chunk_type == "tool_result":
                result = chunk["result"]
                if isinstance(result, dict) and "error" in result:
                    content += f"\n\nError: {result['error']}"
                else:
                    content += f"\n\n{format_tool_result(result)}"
            elif chunk_type == "error":
                return {"error": chunk["content"]}
            elif chunk_type == "end":
                break
        
        return {"content": content}
        
    except Exception as e:
        return {"error": str(e)}

def format_tool_result(result: dict) -> str:
    """Format tool result for display"""
    if isinstance(result, dict) and "result" in result:
        return result["result"]
    elif isinstance(result, dict) and "error" in result:
        return f"Error: {result['error']}"
    return str(result)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)