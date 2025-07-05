#!/usr/bin/env python3
"""
MCP Server with Weather Tool
Provides weather data through the Model Context Protocol
"""

import asyncio
import json
import os
from typing import Any, Sequence
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    CallToolResult,
    ListToolsResult,
)
import requests
import datetime as dt

# Environment variables
API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
if not API_KEY:
    raise RuntimeError("OPENWEATHER_API_KEY environment variable is required")

GEO_URL = "https://api.openweathermap.org/geo/1.0/direct"
CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"

# Initialize MCP server
server = Server("weather-server")

@server.list_tools()
async def handle_list_tools() -> ListToolsResult:
    """List available tools"""
    return ListToolsResult(
        tools=[
            Tool(
                name="weather",
                description="Get current weather for a location",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "Location in format 'City, CC' where CC is ISO-3166 country code or US state code (e.g., 'San Juan, PR', 'Paris, FR')"
                        }
                    },
                    "required": ["location"]
                }
            )
        ]
    )

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> CallToolResult:
    """Handle tool calls"""
    if name != "weather":
        return CallToolResult(
            content=[TextContent(type="text", text=f"Unknown tool: {name}")],
            isError=True
        )
    
    # Get weather data
    result = await get_weather(arguments.get("location", ""))
    
    if "error" in result:
        return CallToolResult(
            content=[TextContent(type="text", text=result["error"])],
            isError=True
        )
    
    # Format successful response
    formatted_result = format_weather_result(result)
    return CallToolResult(
        content=[TextContent(type="text", text=formatted_result)]
    )

async def get_weather(location: str) -> dict:
    """Get weather data from OpenWeatherMap API"""
    try:
        # Parse location
        if "," not in location:
            return {"error": "Location must be 'City, CC' format"}
        
        city, cc = (p.strip() for p in location.split(",", 1))
        if len(cc) != 2:
            return {"error": "Country/state code must be two letters"}
        
        # Geocode location
        geo_response = requests.get(
            GEO_URL,
            params={"q": f"{city},{cc}", "limit": 1, "appid": API_KEY},
            timeout=7,
        )
        geo_data = geo_response.json()
        
        if not geo_data:
            return {"error": f"Location not found: {city}, {cc.upper()}"}
        
        lat, lon = geo_data[0]["lat"], geo_data[0]["lon"]
        
        # Get current weather
        weather_response = requests.get(
            CURRENT_URL,
            params={"lat": lat, "lon": lon, "units": "imperial", "appid": API_KEY},
            timeout=7,
        )
        weather_data = weather_response.json()
        
        # Calculate local time
        unix_utc = weather_data["dt"]
        tz_shift = weather_data.get("timezone", 0)
        local_dt = dt.datetime.utcfromtimestamp(unix_utc + tz_shift)
        local_str = local_dt.strftime("%Y-%m-%d %H:%M")
        
        # Extract weather info
        main = weather_data["main"]
        wind = weather_data["wind"]
        desc = weather_data["weather"][0]["description"]
        
        return {
            "location": f"{city}, {cc.upper()}",
            "local_time": local_str,
            "temperature": main["temp"],
            "feels_like": main["feels_like"],
            "humidity": main["humidity"],
            "wind_speed": wind["speed"],
            "description": desc,
        }
        
    except requests.RequestException as e:
        return {"error": f"Weather API request failed: {str(e)}"}
    except (KeyError, IndexError, TypeError) as e:
        return {"error": f"Unexpected response format: {str(e)}"}
    except Exception as e:
        return {"error": f"Weather lookup failed: {str(e)}"}

def format_weather_result(result: dict) -> str:
    """Format weather result for display"""
    time = result.get("local_time", "")
    temp = round(result["temperature"])
    feel = round(result["feels_like"])
    hum = result["humidity"]
    wind = result["wind_speed"]
    desc = result["description"]
    
    return (
        f"Weather in {result['location']} (local time {time}): "
        f"{temp}°F, {desc}. Feels like {feel}°F. "
        f"Humidity: {hum}%, Wind: {wind} mph"
    )

async def main():
    """Main entry point for the MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="weather-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())