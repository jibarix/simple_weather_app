import json
import yaml
import re
from typing import Iterator, Dict, Any
from llama_cpp import Llama
from config import MODEL_PATH, MODEL_CONTEXT_SIZE, MODEL_TEMPERATURE, MODEL_MAX_TOKENS, PROMPTS_PATH
from tools.weather_tool import execute_tool

class LlamaClient:
    def __init__(self):
        try:
            print(f"Loading model from: {MODEL_PATH}")
            self.llm = Llama(
                model_path=MODEL_PATH,
                n_ctx=MODEL_CONTEXT_SIZE,
                n_gpu_layers=0,
                verbose=False  # Reduce verbose output
            )
            print("Model loaded successfully")
        except Exception as e:
            print(f"Error loading model: {e}")
            raise
        self.system_prompt = self._load_system_prompt()
    
    def _load_system_prompt(self) -> str:
        """Load system prompt from YAML file"""
        try:
            with open(PROMPTS_PATH, 'r') as f:
                prompts = yaml.safe_load(f)
                return prompts.get('system_prompt', '')
        except Exception as e:
            print(f"Error loading system prompt: {e}")
            return "You are a helpful AI assistant."
    
    def _format_messages(self, messages: list) -> str:
        """Format messages for Gemma-3 chat template"""
        formatted = f"<bos><start_of_turn>system\n{self.system_prompt}<end_of_turn>\n"
        
        for message in messages:
            role = message.get('role', 'user')
            content = message.get('content', '')
            formatted += f"<start_of_turn>{role}\n{content}<end_of_turn>\n"
        
        formatted += "<start_of_turn>model\n"
        return formatted
    
    def _extract_tool_call(self, text: str) -> tuple[str, dict, str]:
        """Extract tool call from model response, return tool_name, parameters, clean_text"""
        try:
            # Look for JSON tool call pattern
            json_pattern = r'\{[^}]*"tool_name"\s*:\s*"([^"]*)"[^}]*\}'
            match = re.search(json_pattern, text, re.DOTALL)
            
            if match:
                json_str = match.group(0)
                try:
                    tool_call = json.loads(json_str)
                    tool_name = tool_call.get('tool_name')
                    parameters = tool_call.get('parameters', {})
                    
                    # Remove the tool call JSON from the text
                    clean_text = text.replace(json_str, '').strip()
                    # Clean up any extra spaces or newlines
                    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
                    
                    return tool_name, parameters, clean_text
                except json.JSONDecodeError:
                    pass
            
            return None, None, text
            
        except Exception:
            return None, None, text
    
    def stream_chat(self, messages: list, tools_enabled: bool = False) -> Iterator[Dict[str, Any]]:
        """Stream chat response with optional tool support"""
        formatted_prompt = self._format_messages(messages)
        
        # Generate complete response first
        response_text = ""
        
        try:
            for output in self.llm(
                formatted_prompt,
                max_tokens=MODEL_MAX_TOKENS,
                temperature=MODEL_TEMPERATURE,
                stream=True,
                stop=["<end_of_turn>", "<start_of_turn>"]
            ):
                # Handle different output formats
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
            
            # Process the complete response
            tool_name, parameters, clean_text = self._extract_tool_call(response_text)
            
            if tool_name and parameters:
                # Tool call detected
                # Send clean text first
                if clean_text.strip():
                    # Stream clean text word by word for better UX
                    words = clean_text.split()
                    for word in words:
                        yield {"type": "token", "content": word + " "}
                
                if tools_enabled:
                    # Tool is enabled - execute it
                    yield {"type": "tool_call", "tool_name": tool_name, "parameters": parameters}
                    
                    # Execute the tool
                    tool_result = execute_tool(tool_name, parameters)
                    yield {"type": "tool_result", "result": tool_result}
                else:
                    # Tool is disabled - inform user
                    yield {"type": "token", "content": "\n\nSorry, the weather tool is not currently enabled. Please enable it using the toggle above to use this feature."}
            else:
                # No tool call detected, stream the response normally
                words = response_text.split()
                for word in words:
                    yield {"type": "token", "content": word + " "}
        
        except Exception as e:
            print(f"Error during generation: {e}")
            yield {"type": "token", "content": f"Error: {str(e)}"}
        
        yield {"type": "end"}