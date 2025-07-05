import json
import yaml
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
    
    def _extract_tool_call(self, text: str) -> tuple[str, dict]:
        """Extract tool call from model response"""
        try:
            start = text.find('{"tool_name":')
            if start == -1:
                start = text.find('{"tool_name" :')
            if start == -1:
                return None, None
            
            brace_count = 0
            end = start
            for i, char in enumerate(text[start:], start):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end = i + 1
                        break
            
            json_str = text[start:end]
            tool_call = json.loads(json_str)
            
            tool_name = tool_call.get('tool_name')
            parameters = tool_call.get('parameters', {})
            
            return tool_name, parameters
            
        except (json.JSONDecodeError, KeyError):
            return None, None
    
    def stream_chat(self, messages: list, tools_enabled: bool = False) -> Iterator[Dict[str, Any]]:
        """Stream chat response with optional tool support"""
        formatted_prompt = self._format_messages(messages)
        
        response_text = ""
        buffered_tokens = []
        
        # Generate response
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
                    buffered_tokens.append(token)
                    
                    # Check for tool calls if tools are enabled
                    if tools_enabled:
                        tool_name, parameters = self._extract_tool_call(response_text)
                        if tool_name and parameters:
                            # Tool call detected - execute it instead of showing model response
                            yield {"type": "tool_call", "tool_name": tool_name, "parameters": parameters}
                            
                            # Execute the tool
                            tool_result = execute_tool(tool_name, parameters)
                            yield {"type": "tool_result", "result": tool_result}
                            yield {"type": "end"}
                            return
                    
                    # Stream token if no tool call detected
                    yield {"type": "token", "content": token}
        
        except Exception as e:
            print(f"Error during generation: {e}")
            yield {"type": "token", "content": f"Error: {str(e)}"}
        
        yield {"type": "end"}