## Project Overview

This project provides a minimal implementation of the Model Context Protocol (MCP) using a local Gemma-3 model served via llama.cpp and a simple HTML/JS chat UI. It allows users to interact with the assistant in a chat interface and optionally retrieve weather data through a dedicated tool.

## File Structure

```
project-root/
├── mcp_server/                        # Backend service implementing MCP
│   ├── prompts/
│   │   └── system_prompts.yaml        # Single system prompt defining assistant behavior and tool schema
│   ├── tools/
│   │   └── weather_tool.py            # Implements the 'weather' MCP tool via OpenWeatherMap
│   ├── main.py                        # FastAPI app exposing JSON-RPC /rpc endpoint
│   ├── llama_client.py                # Wrapper for llama.cpp streaming API with Gemma-3
│   ├── config.py                      # Configuration: model path, API keys, server settings
│   └── requirements.txt               # Python dependencies (fastapi, uvicorn, llama-cpp-python)
│
├── frontend/                          # Static HTML/JS chat UI
│   ├── index.html                     # Chat interface and weather toggle switch
│   ├── chat.js                        # Client code to connect via SSE/WebSocket and render streams
│   ├── tools.js                       # Manages toggle state and includes tool flags in requests
│   └── styles.css                     # Basic styling for chat and controls
│
├── docker/                            # Docker configurations
│   ├── Dockerfile.server              # Builds and runs the MCP server
│   └── Dockerfile.frontend            # Serves the static frontend via a web server
│
├── .gitignore                         # Specifies files and folders for Git to ignore
├── README.md                          # Project documentation (this file)
└── LICENSE.md                         # MIT License
```

## Setup Instructions

1. **Clone the repository**:

   ```bash
   git clone https://github.com/<your-username>/gemma3-mcp-chat.git
   cd gemma3-mcp-chat
   ```

2. **Backend setup**:

   * Navigate to `mcp_server/` and create a virtual environment:

     ```bash
     python -m venv env
     .\env\Scripts\activate
     ```
   * Install dependencies:

     ```bash
     pip install -r requirements.txt
     ```
   * Start the server:

     ```bash
     uvicorn main:app --reload --port 8000
     ```

3. **Frontend setup**:

   * Open `frontend/index.html` in your browser, or serve via a simple HTTP server:

     ```bash
     cd frontend
     python -m http.server 8080
     ```

4. **Interacting**:

   * Access the chat UI at `http://localhost:8080`.
   * Type messages in the chat box, use the weather toggle to enable or disable the weather tool, and view streamed responses from Gemma-3.

## License

This project is licensed under the MIT License. See `LICENSE.md` for details.