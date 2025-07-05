import os
from pathlib import Path

# Model configuration
MODEL_PATH = os.getenv("MODEL_PATH", "./models/gemma-2-2b-it-q4_k_m.gguf")
MODEL_CONTEXT_SIZE = int(os.getenv("MODEL_CONTEXT_SIZE", "4096"))
MODEL_TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE", "0.7"))
MODEL_MAX_TOKENS = int(os.getenv("MODEL_MAX_TOKENS", "1024"))

# Server configuration
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080,http://localhost:3000,http://127.0.0.1:3000").split(",")

# API keys and external services
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

# System prompts
PROMPTS_PATH = Path(__file__).parent / "prompts" / "system_prompts.yaml"

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")