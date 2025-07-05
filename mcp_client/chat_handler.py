#!/usr/bin/env python3
"""
MCP Client - Orchestration layer for MCP server communication
Handles connection to MCP server and provides API for chat service
"""

import asyncio
import json
import subprocess
import sys
from typing import Dict, Any, Optional, List
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPClient:
    """Client for communicating with MCP server"""
    
    def __init__(self, server_script_path: str = "mcp_server/server.py"):
        self.server_script_path = server_script_path
        self.session: Optional[ClientSession] = None
        self.available_tools: Dict[str, Any] = {}
        self.connected = False
    
    async def connect(self):
        """Connect to MCP server"""
        try:
            server_params = StdioServerParameters(
                command=sys.executable,
                args=[self.server_script_path],
                env=None
            )
            
            stdio_transport = await stdio_client(server_params)
            self.session = ClientSession(stdio_transport[0], stdio_transport[1])
            
            await self.session.initialize()
            
            # Get available tools
            tools_result = await self.session.list_tools()
            self.available_tools = {tool.name: tool for tool in tools_result.tools}
            
            self.connected = True
            print(f"Connected to MCP server with {len(self.available_tools)} tools")
            
        except Exception as e:
            print(f"Failed to connect to MCP server: {e}")
            self.connected = False
            raise
    
    async def disconnect(self):
        """Disconnect from MCP server"""
        if self.session:
            await self.session.close()
            self.session = None
        self.connected = False
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the MCP server"""
        if not self.connected or not self.session:
            return {"error": "Not connected to MCP server"}
        
        if name not in self.available_tools:
            return {"error": f"Tool '{name}' not available"}
        
        try:
            result = await self.session.call_tool(name, arguments)
            
            if result.isError:
                return {"error": result.content[0].text if result.content else "Tool call failed"}
            
            return {"result": result.content[0].text if result.content else ""}
            
        except Exception as e:
            return {"error": f"Tool call failed: {str(e)}"}
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names"""
        return list(self.available_tools.keys())
    
    def is_connected(self) -> bool:
        """Check if connected to MCP server"""
        return self.connected

class MCPOrchestrator:
    """Orchestrates MCP client and provides high-level interface"""
    
    def __init__(self):
        self.client = MCPClient()
        self.tools_enabled = False
    
    async def initialize(self):
        """Initialize the orchestrator"""
        await self.client.connect()
    
    async def shutdown(self):
        """Shutdown the orchestrator"""
        await self.client.disconnect()
    
    def enable_tools(self, enabled: bool):
        """Enable or disable tools"""
        self.tools_enabled = enabled
    
    async def handle_tool_call(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a tool call request"""
        if not self.tools_enabled:
            return {"error": "Tools are disabled"}
        
        if not self.client.is_connected():
            return {"error": "MCP server not connected"}
        
        return await self.client.call_tool(tool_name, parameters)
    
    def get_tool_status(self) -> Dict[str, Any]:
        """Get current tool status"""
        return {
            "connected": self.client.is_connected(),
            "tools_enabled": self.tools_enabled,
            "available_tools": self.client.get_available_tools()
        }

# Global orchestrator instance
orchestrator = MCPOrchestrator()

async def main():
    """Test the MCP client"""
    try:
        await orchestrator.initialize()
        orchestrator.enable_tools(True)
        
        # Test weather tool
        result = await orchestrator.handle_tool_call(
            "weather", 
            {"location": "San Juan, PR"}
        )
        print(f"Weather result: {result}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await orchestrator.shutdown()

if __name__ == "__main__":
    asyncio.run(main())