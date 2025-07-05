# weather_tool.py
#
# Parameters  {"location": "City, CC"}  (CC = ISO-3166 code or US state / territory)
# Returns     {
#               "location": "San Juan, PR",
#               "local_time": "2025-07-04 14:27",
#               "temperature": 86.3,
#               "feels_like": 90.0,
#               "humidity": 77,
#               "wind_speed": 12,
#               "description": "sunny"
#             }
# Errors      {"error": "..."}
from __future__ import annotations
import os, requests, datetime as dt

API_KEY = os.getenv("OPENWEATHER_API_KEY", "").strip()
if not API_KEY:
    raise RuntimeError("Set the OPENWEATHER_API_KEY environment variable")

GEO_URL     = "https://api.openweathermap.org/geo/1.0/direct"
CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"

def execute_tool(tool_name: str, parameters: dict) -> dict:
    if tool_name != "weather":
        return {"error": f"Unknown tool: {tool_name}"}

    # 1. Parse “City, CC”
    loc = parameters.get("location", "").strip()
    if "," not in loc:
        return {"error": "Location must be 'City, CC' (e.g. 'San Juan, PR')"}
    city, cc = (p.strip() for p in loc.split(",", 1))
    if len(cc) != 2:
        return {"error": "Country/state code must be two letters"}

    # 2. Geocode
    try:
        geo = requests.get(
            GEO_URL,
            params={"q": f"{city},{cc}", "limit": 1, "appid": API_KEY},
            timeout=7,
        ).json()
    except requests.RequestException as exc:
        return {"error": f"Geocoding failed: {exc}"}
    if not geo:
        return {"error": f"Location not found: {city}, {cc.upper()}"}
    lat, lon = geo[0]["lat"], geo[0]["lon"]

    # 3. Current weather (imperial units → °F, mph)
    try:
        wx = requests.get(
            CURRENT_URL,
            params={"lat": lat, "lon": lon, "units": "imperial", "appid": API_KEY},
            timeout=7,
        ).json()
    except requests.RequestException as exc:
        return {"error": f"Weather request failed: {exc}"}

    # 4. Build result ─ include local time
    try:
        unix_utc  = wx["dt"]                      # seconds since epoch (UTC)
        tz_shift  = wx.get("timezone", 0)         # seconds east of UTC  ﻿:contentReference[oaicite:0]{index=0}
        local_dt  = dt.datetime.utcfromtimestamp(unix_utc + tz_shift)
        local_str = local_dt.strftime("%Y-%m-%d %H:%M")
        main, wind = wx["main"], wx["wind"]
        desc = wx["weather"][0]["description"]
    except (KeyError, IndexError, TypeError):
        return {"error": "Unexpected response format from OpenWeather"}

    return {
        "location": f"{city}, {cc.upper()}",
        "local_time": local_str,
        "temperature": main["temp"],
        "feels_like": main["feels_like"],
        "humidity": main["humidity"],
        "wind_speed": wind["speed"],
        "description": desc,
    }
