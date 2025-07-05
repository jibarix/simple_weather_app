#!/usr/bin/env python3
"""
Chat Service with MCP Integration
Handles LLM communication and coordinates with MCP client for tool calls
"""

import json
import yaml
import re
import asyncio
from typing import Iterator, Dict, Any, Optional
from llama_cpp import Llama
from pathlib import Path

class ChatService:
    def __init__(self, model_path: str, mcp_orchestrator):
        self.model_path = model_path
        self.mcp_orchestrator = mcp_orchestrator
        self.llm = None
        self.system_prompt = self._load_system_prompt()
        self.context_size = 4096
        self.temperature = 0.7
        self.max_tokens = 1024
    
    def initialize(self):
        """Initialize the LLM"""
        try:
            print(f"Loading model from: {self.model_path}")
            self.llm = Llama(
                model_path=self.model_path,
                n_ctx=self.context_size,
                n_gpu_layers=0,
                verbose=False
            )
            print("Model loaded successfully")
        except Exception as e:
            print(f"Error loading model: {e}")
            raise
    
    def _load_system_prompt(self) -> str:
        """Load system prompt from YAML file"""
        prompts_path = Path(__file__).parent / "prompts" / "system_prompts.yaml"
        try:
            with open(prompts_path, 'r') as f:
                prompts = yaml.safe_load(f)
                return prompts.get('system_prompt', '')
        except Exception as e:
            print(f"Error loading system prompt: {e}")
            return "You are a helpful AI assistant with access to tools."
    
    def _format_messages(self, messages: list, tools_enabled: bool) -> str:
        """Format messages for Gemma-3 chat template"""
        system_context = self.system_prompt
        if not tools_enabled:
            system_context += "\n\nIMPORTANT: Tools are disabled. Answer normally without calling functions."
        
        formatted = f"<bos><start_of_turn>system\n{system_context}<end_of_turn>\n"
        
        for message in messages:
            role = message.get('role', 'user')
            content = message.get('content', '')
            formatted += f"<start_of_turn>{role}\n{content}<end_of_turn>\n"
        
        formatted += "<start_of_turn>model\n"
        return formatted
    
    def _extract_function_call(self, text: str) -> tuple:
        """Extract function call from LLM response"""
        # Look for function call pattern: function_name(parameters)
        pattern = r'(\w+)\s*\(\s*([^)]*)\s*\)'
        match = re.search(pattern, text)
        
        if match:
            func_name = match.group(1)
            params_str = match.group(2).strip()
            
            # Parse parameters
            try:
                # Handle simple parameter formats
                if params_str.startswith('"') and params_str.endswith('"'):
                    # Single quoted parameter
                    params = {"location": params_str[1:-1]}
                elif '=' in params_str:
                    # Named parameter format
                    params = {}
                    for param in params_str.split(','):
                        if '=' in param:
                            key, value = param.split('=', 1)
                            params[key.strip()] = value.strip().strip('"')
                else:
                    # Assume it's a location parameter
                    params = {"location": params_str.strip('"')}
                
                # Remove function call from text
                clean_text = text[:match.start()] + text[match.end():]
                clean_text = re.sub(r'\s+', ' ', clean_text).strip()
                
                return func_name, params, clean_text
            except Exception:
                pass
        
        return None, None, text
    
    async def stream_chat(self, messages: list, tools_enabled: bool = False) -> Iterator[Dict[str, Any]]:
        """Stream chat response with MCP tool integration"""
        if not self.llm:
            yield {"type": "error", "content": "Model not initialized"}
            return
        
        formatted_prompt = self._format_messages(messages, tools_enabled)
        response_text = ""
        
        try:
            # Generate response
            for output in self.llm(
                formatted_prompt,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=True,
                stop=["<end_of_turn>", "<start_of_turn>"]
            ):
                token = ""
                if isinstance(output, dict):
                    if 'choices' in output and len(output['choices']) > 0:
                        choice = output['choices'][0]
                        if 'delta' in choice and 'content' in choice['delta']:
                            token = choice['delta']['content']
                        elif 'text' in choice:
                            token = choice['text']
                    elif 'text' in output:
                        token = output['text']
                elif isinstance(output, str):
                    token = output
                
                if token:
                    response_text += token
            
            # Check for function calls
            func_name, parameters, clean_text = self._extract_function_call(response_text)
            
            if func_name and parameters:
                # Stream clean text first
                if clean_text.strip():
                    words = clean_text.split()
                    for word in words:
                        yield {"type": "token", "content": word + " "}
                
                # Handle tool call
                if tools_enabled and func_name == "weather":
                    yield {"type": "tool_call", "tool_name": func_name, "parameters": parameters}
                    
                    # Call MCP tool
                    result = await self.mcp_orchestrator.handle_tool_call(func_name, parameters)
                    yield {"type": "tool_result", "result": result}
                else:
                    yield {"type": "token", "content": "\n\nSorry, tools are not currently enabled. Please enable the weather tool to use this feature."}
            else:
                # No function call, stream normally
                words = response_text.split()
                for word in words:
                    yield {"type": "token", "content": word + " "}
        
        except Exception as e:
            print(f"Error during generation: {e}")
            yield {"type": "error", "content": f"Generation error: {str(e)}"}
        
        yield {"type": "end"}

class ChatHandler:
    """Handles chat requests and coordinates with MCP"""
    
    def __init__(self, model_path: str, mcp_orchestrator):
        self.chat_service = ChatService(model_path, mcp_orchestrator)
        self.mcp_orchestrator = mcp_orchestrator
    
    async def initialize(self):
        """Initialize chat handler"""
        self.chat_service.initialize()
        await self.mcp_orchestrator.initialize()
    
    async def shutdown(self):
        """Shutdown chat handler"""
        await self.mcp_orchestrator.shutdown()
    
    async def handle_chat_stream(self, messages: list, tools_enabled: bool = False):
        """Handle streaming chat with tool integration"""
        # Enable tools in orchestrator
        self.mcp_orchestrator.enable_tools(tools_enabled)
        
        # Stream chat response
        async for chunk in self.chat_service.stream_chat(messages, tools_enabled):
            yield chunk
    
    def get_status(self) -> Dict[str, Any]:
        """Get chat handler status"""
        return {
            "model_loaded": self.chat_service.llm is not None,
            "mcp_status": self.mcp_orchestrator.get_tool_status()
        }