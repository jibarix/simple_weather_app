# Gemma3 MCP Chat

A minimal Model Context Protocol (MCP) implementation using Gemma-3 via llama.cpp with streaming chat interface and weather tool support.

## Features

- Real-time streaming chat with Gemma-3 model
- Weather tool integration via OpenWeatherMap API
- Clean web interface with tool toggles
- Docker deployment support
- JSON-RPC backend with FastAPI

## File Structure

```
project-root/
├── mcp_server/                        # Backend MCP server
│   ├── prompts/
│   │   └── system_prompts.yaml        # System prompt and tool definitions
│   ├── tools/
│   │   └── weather_tool.py            # Weather tool implementation
│   ├── main.py                        # FastAPI server with JSON-RPC endpoint
│   ├── llama_client.py                # Llama.cpp streaming client
│   ├── config.py                      # Configuration management
│   └── requirements.txt               # Python dependencies
│
├── frontend/                          # Static web interface
│   ├── index.html                     # Main chat interface
│   ├── styles.css                     # Styling and responsive design
│   ├── chat.js                        # Streaming chat client
│   └── tools.js                       # Tool management
│
├── docker/                            # Docker configurations
│   ├── Dockerfile.server              # Backend container
│   └── Dockerfile.frontend            # Frontend container
│
└── README.md                          # This file
```

## Setup

### Local Development (Windows)

1. **Backend Setup**:
   ```bash
   cd mcp_server
   python -m venv env
   .\env\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   ```bash
   set MODEL_PATH="C:\path\to\your\gemma-3-model.gguf"
   set OPENWEATHER_API_KEY="your-api-key"
   ```

3. **Start Server**:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

4. **Frontend** (open new terminal):
   ```bash
   cd frontend
   python -m http.server 8080
   ```

### Local Development (Linux/macOS)

1. **Backend Setup**:
   ```bash
   cd mcp_server
   python -m venv env
   source env/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   ```bash
   export MODEL_PATH="/path/to/your/gemma-3-model.gguf"
   export OPENWEATHER_API_KEY="your-api-key"
   ```

3. **Start Server**:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

4. **Frontend**:
   ```bash
   cd frontend
   python -m http.server 8080
   ```

### Docker Deployment

1. **Build Images**:
   ```bash
   docker build -f docker/Dockerfile.server -t mcp-server .
   docker build -f docker/Dockerfile.frontend -t mcp-frontend .
   ```

2. **Run with Docker Compose**:
   ```yaml
   version: '3.8'
   services:
     mcp-server:
       build:
         context: .
         dockerfile: docker/Dockerfile.server
       ports:
         - "8000:8000"
       environment:
         - MODEL_PATH=/app/models/gemma-3.gguf
         - OPENWEATHER_API_KEY=your-key
       volumes:
         - ./models:/app/models
     
     mcp-frontend:
       build:
         context: .
         dockerfile: docker/Dockerfile.frontend
       ports:
         - "8080:80"
       depends_on:
         - mcp-server
   ```

## Usage

1. Open browser to `http://localhost:8080`
2. Toggle weather tool on/off as needed
3. Type messages and receive streaming responses
4. Weather queries automatically trigger tool calls when enabled

## Configuration

Environment variables in `mcp_server/config.py`:
- `MODEL_PATH`: Path to Gemma-3 GGUF model file
- `OPENWEATHER_API_KEY`: OpenWeatherMap API key
- `SERVER_HOST`: Server host (default: 0.0.0.0)
- `SERVER_PORT`: Server port (default: 8000)

## API Endpoints

- `POST /rpc`: JSON-RPC endpoint for chat and tool operations
- `GET /health`: Health check endpoint

## License

MIT License