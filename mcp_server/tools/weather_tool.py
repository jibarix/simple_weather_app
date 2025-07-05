import requests
import json
from config import OPENWEATHER_API_KEY, OPENWEATHER_BASE_URL

class WeatherTool:
    def __init__(self):
        self.api_key = OPENWEATHER_API_KEY
        self.base_url = OPENWEATHER_BASE_URL
    
    def get_weather(self, location: str) -> dict:
        """Get current weather for a location"""
        if not self.api_key:
            return {"error": "OpenWeather API key not configured"}
        
        try:
            params = {
                "q": location,
                "appid": self.api_key,
                "units": "metric"
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "location": data["name"],
                "country": data["sys"]["country"],
                "temperature": data["main"]["temp"],
                "feels_like": data["main"]["feels_like"],
                "description": data["weather"][0]["description"],
                "humidity": data["main"]["humidity"],
                "wind_speed": data["wind"]["speed"]
            }
            
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to fetch weather data: {str(e)}"}
        except KeyError as e:
            return {"error": f"Unexpected response format: {str(e)}"}
        except Exception as e:
            return {"error": f"Weather service error: {str(e)}"}

def execute_tool(tool_name: str, parameters: dict) -> dict:
    """Execute a tool with given parameters"""
    if tool_name == "weather":
        weather_tool = WeatherTool()
        location = parameters.get("location")
        if not location:
            return {"error": "Location parameter is required"}
        return weather_tool.get_weather(location)
    else:
        return {"error": f"Unknown tool: {tool_name}"}