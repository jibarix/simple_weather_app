# Gemma-3 MCP Chat

A Model Context Protocol (MCP) compliant chat application using Gemma-3 via llama.cpp with streaming interface and weather tool support. This implementation follows MCP standards for tool integration and interoperability.

## Architecture Overview

This application demonstrates a modern MCP-compliant architecture that separates concerns into specialized components. Think of it as having dedicated specialists working together rather than one person doing everything.

The system consists of three main layers:

**MCP Server Layer**: A pure MCP server that provides weather tools through the standard MCP protocol. This server can be used by any MCP-compliant client, not just our chat interface.

**Orchestration Layer**: An MCP client that coordinates between the chat service and MCP server. This layer handles the complexity of MCP protocol communication and provides a clean interface for the chat service.

**Chat Service Layer**: Handles the language model and user interactions. This layer generates responses and identifies when tools need to be called, but delegates the actual tool execution to the MCP server through the orchestration layer.

## Features

The application maintains all the functionality of a traditional chat interface while gaining the benefits of MCP compliance:

- Real-time streaming chat with Gemma-3 model using llama.cpp
- Weather tool integration through MCP protocol via OpenWeatherMap API
- Clean web interface with tool enable/disable toggles
- Modular architecture allowing independent component updates
- Standard MCP protocol compliance for interoperability
- Docker deployment support for containerized environments

## Project Structure

The new architecture organizes code into logical components that each handle specific responsibilities:

```
project-root/
├── mcp_server/                        # MCP Server - Pure tool provider
│   └── server.py                      # MCP protocol server with weather tool
│
├── mcp_client/                        # MCP Client - Orchestration layer
│   └── client.py                      # MCP client and orchestrator classes
│
├── chat_service/                      # Chat Service - LLM integration
│   ├── prompts/
│   │   └── system_prompts.yaml        # Function calling system prompts
│   └── chat_handler.py                # Chat service with MCP integration
│
├── api_layer/                         # API Layer - HTTP endpoints
│   └── main.py                        # FastAPI server coordinating all services
│
├── frontend/                          # Frontend - Web interface
│   ├── index.html                     # Main chat interface
│   ├── styles.css                     # Styling and responsive design
│   ├── chat.js                        # Updated streaming chat client
│   └── tools.js                       # Tool management interface
│
├── docker/                            # Docker configurations
│   ├── Dockerfile.server              # Backend container
│   └── Dockerfile.frontend            # Frontend container
│
├── requirements.txt                   # Combined Python dependencies
├── .env                              # Environment variables
└── README.md                          # This file
```

## Understanding the MCP Benefits

This architectural transformation provides several key advantages over traditional monolithic chat applications:

**Modularity**: Each component has a single, clear responsibility. You can update the weather tool without touching the chat interface, or swap out the language model without affecting the tools.

**Interoperability**: Other applications can use your weather tool through the standard MCP protocol, and your chat interface can connect to other MCP servers to access additional tools.

**Testability**: Each component can be tested independently, making it easier to identify and fix issues when they arise.

**Scalability**: You can run different components on different servers, scale them independently, or run multiple instances of the same component for load distribution.

## Setup Instructions

### Prerequisites

Before setting up the application, ensure you have the following:

- Python 3.11 or higher installed on your system
- A Gemma-3 model file in GGUF format (we recommend the 12B parameter version for best results)
- An OpenWeatherMap API key for weather functionality
- Git for cloning the repository

### Local Development Setup

Setting up the development environment involves creating a virtual environment and installing dependencies:

**Step 1: Create Virtual Environment**
```bash
# Navigate to project root
cd path/to/project

# Create virtual environment at root level
python -m venv env

# Activate virtual environment
# On Windows:
.\env\Scripts\activate
# On Linux/macOS:
source env/bin/activate
```

**Step 2: Install Dependencies**
```bash
# Install all required packages
pip install -r requirements.txt
```

**Step 3: Configure Environment Variables**

Create a `.env` file in the project root with your configuration:
```
MODEL_PATH=C:\path\to\your\gemma-3-model.gguf
OPENWEATHER_API_KEY=your-openweather-api-key
```

Alternatively, you can set these as system environment variables:
```bash
# Windows
set MODEL_PATH="C:\path\to\your\gemma-3-model.gguf"
set OPENWEATHER_API_KEY="your-openweather-api-key"

# Linux/macOS
export MODEL_PATH="/path/to/your/gemma-3-model.gguf"
export OPENWEATHER_API_KEY="your-openweather-api-key"
```

**Step 4: Start the Application**
```bash
# Start the main API server (this coordinates all services)
python api_layer/main.py

# Or using uvicorn directly:
uvicorn api_layer.main:app --reload --port 8000
```

**Step 5: Access the Web Interface**
```bash
# In a new terminal, serve the frontend
cd frontend
python -m http.server 8080
```

Open your browser to `http://localhost:8080` to access the chat interface.

### Docker Deployment

For production deployments, Docker provides a consistent environment across different systems:

**Step 1: Build Docker Images**
```bash
# Build the backend services container
docker build -f docker/Dockerfile.server -t mcp-server .

# Build the frontend container
docker build -f docker/Dockerfile.frontend -t mcp-frontend .
```

**Step 2: Run with Docker Compose**

Create a `docker-compose.yml` file:
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
      - OPENWEATHER_API_KEY=your-api-key
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

Then run:
```bash
docker-compose up -d
```

## Usage Guide

### Basic Chat Functionality

The chat interface works like any modern messaging application. Type your message in the input field and press Enter or click Send to receive responses from the Gemma-3 model.

### Weather Tool Integration

The weather tool can be enabled or disabled using the toggle switch in the header. When enabled, you can ask natural language questions about weather conditions:

- "What's the weather like in San Juan, PR?"
- "How's the weather in Paris, France?"
- "Tell me about the current conditions in New York, NY"

The system automatically detects when weather information is needed and calls the appropriate tool through the MCP protocol.

### Understanding the Response Flow

When you send a message, here's what happens behind the scenes:

1. Your message reaches the API layer through the web interface
2. The API layer forwards it to the chat service, which processes it with the language model
3. If the model determines a tool call is needed, it generates a function call
4. The orchestration layer intercepts this call and forwards it to the MCP server
5. The MCP server executes the weather tool and returns the result
6. The result flows back through the layers and is streamed to your interface

This architecture ensures that each component focuses on its specific responsibility while maintaining seamless user experience.

## Configuration Options

The application provides several configuration options through environment variables:

**Model Configuration**:
- `MODEL_PATH`: Path to your Gemma-3 GGUF model file
- `MODEL_CONTEXT_SIZE`: Context window size (default: 4096)
- `MODEL_TEMPERATURE`: Generation temperature (default: 0.7)
- `MODEL_MAX_TOKENS`: Maximum tokens per response (default: 1024)

**Server Configuration**:
- `SERVER_HOST`: API server host (default: 0.0.0.0)
- `SERVER_PORT`: API server port (default: 8000)
- `CORS_ORIGINS`: Allowed CORS origins for frontend access

**External Services**:
- `OPENWEATHER_API_KEY`: Your OpenWeatherMap API key
- `LOG_LEVEL`: Logging verbosity (default: INFO)

## API Documentation

The application provides several endpoints for different purposes:

**POST /rpc**: The main JSON-RPC endpoint for chat operations. This endpoint accepts chat messages and returns streaming responses with tool integration.

**GET /health**: A health check endpoint that returns the status of all system components, including MCP server connectivity and model loading status.

The JSON-RPC protocol supports both streaming and non-streaming modes, with streaming being the default for real-time chat experiences.

## Troubleshooting Common Issues

**Model Loading Problems**: If you encounter issues with model loading, verify that your model path is correct and that the model file is in GGUF format. Check the console output for specific error messages.

**MCP Connection Issues**: If the MCP server fails to start, ensure that all dependencies are properly installed and that no other processes are using the required ports.

**Weather Tool Errors**: Weather tool failures are usually related to API key issues or network connectivity. Verify that your OpenWeatherMap API key is valid and that your system can reach the OpenWeatherMap servers.

**Frontend Connection Problems**: If the frontend cannot connect to the backend, check that the API server is running on the expected port and that CORS settings allow your frontend origin.

## Development and Extension

The MCP architecture makes it easy to extend the application with new capabilities:

**Adding New Tools**: Create new tools in the MCP server following the same pattern as the weather tool. The MCP protocol will automatically make them available to the chat service.

**Modifying Chat Behavior**: Update the system prompts in the chat service to change how the language model interacts with tools or responds to users.

**Frontend Customization**: The frontend is completely independent of the backend architecture, so you can modify the interface without affecting the underlying services.

## Resources and References

To learn more about the technologies and standards used in this application:

**Gemma-3 Model**: Download the latest models from [Hugging Face](https://huggingface.co/google/gemma-3-12b-it-qat-q4_0-gguf)

**OpenWeatherMap API**: Get your API key and explore the documentation at [OpenWeatherMap](https://openweathermap.org/)

**Model Context Protocol**: Learn about the MCP standard at the [official documentation](https://modelcontextprotocol.io/introduction)

**llama.cpp**: Explore the underlying model inference engine at [llama.cpp repository](https://github.com/ggerganov/llama.cpp)

## Contributing

This project demonstrates MCP compliance patterns that can be applied to other applications. When contributing, please maintain the separation of concerns between the MCP server, orchestration layer, and chat service.

## License

MIT License - Feel free to use this code as a foundation for your own MCP-compliant applications.