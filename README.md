# weather — Enhanced MCP Weather Server

<img width="1123" height="869" alt="Screenshot 2025-11-15 at 6 37 38 PM" src="https://github.com/user-attachments/assets/717f5316-8553-4d96-a139-93d56ba17b3e" />

<img width="318" height="245" alt="Screenshot 2025-11-15 at 7 23 28 PM" src="https://github.com/user-attachments/assets/ac1a0203-d479-4a26-aa33-1392c84f2f1b" />






A feature-rich MCP (Model Context Protocol) server that provides comprehensive weather data using the NWS (National Weather Service) public APIs. Includes input validation, error handling, geocoding, and a unique weather comparison feature.

## Quick start

1. Install uv (macOS / Linux):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# restart your terminal
```

2. Create project, venv and install deps:

```bash
uv init weather
cd weather
uv venv
source .venv/bin/activate
uv add "mcp[cli]" httpx
```

3. Run the server:

```bash
uv run main.py
# or
uv run weather.py
```

## Available Tools

The server provides the following MCP tools:

### 1. `get_alerts(state: str)`
Get active weather alerts for a US state.
- **Input**: Two-letter US state code (e.g., "CA", "NY", "TX")
- **Features**: Validates state codes, provides detailed alert information

### 2. `get_forecast(latitude: float, longitude: float)`
Get detailed weather forecast for a location using coordinates.
- **Input**: Latitude (-90 to 90) and Longitude (-180 to 180)
- **Features**: 10-period forecast (5 days), includes humidity and precipitation probability

### 3. `get_forecast_by_city(city_name: str)`
Get weather forecast by city name (no coordinates needed!).
- **Input**: City name (e.g., "San Francisco", "New York", "Chicago")
- **Features**: Automatic geocoding, works with city names

### 4. `get_current_conditions(latitude: float, longitude: float)`
Get real-time current weather conditions.
- **Input**: Latitude and Longitude
- **Features**: Temperature, humidity, wind, pressure, visibility, and more

### 5. `compare_weather(location1: str, location2: str)` 
Compare weather conditions between two locations side-by-side.
- **Input**: Two locations (city names or "lat,lon" format)
- **Features**: Side-by-side comparison, temperature difference analysis, supports both city names and coordinates

## Features

- ✅ **Input Validation**: Validates state codes and coordinate ranges
- ✅ **Better Error Handling**: Specific, helpful error messages
- ✅ **Geocoding Support**: Search by city name using Open-Meteo geocoding API
- ✅ **Current Conditions**: Real-time weather observations
- ✅ **Enhanced Forecasts**: More detailed information including humidity and precipitation
- ✅ **Weather Comparison**: Unique feature to compare two locations
- ✅ **Location Detection**: Automatically detects and displays city/state names

## Files

- `weather.py` — Main MCP server implementation with all tools
- `main.py` — Entry point that imports and runs the server

## Notes

- **Python 3.11+** required (see `pyproject.toml`)
- **NWS Coverage**: The NWS API only covers US territories. International locations will not work.
- **Transport**: The server uses stdio transport by default
- **MCP Clients**: Use Claude Desktop, `mcp` CLI, or another MCP client to connect
- **Geocoding**: City name search uses Open-Meteo's free geocoding API (no API key required)

## Example Usage

Once connected to an MCP client, you can use the tools like:

```
# Get alerts for California
get_alerts("CA")

# Get forecast by city name
get_forecast_by_city("San Francisco")

# Get current conditions
get_current_conditions(37.7749, -122.4194)

# Compare weather between two cities
compare_weather("New York", "Los Angeles")
```

## License

Apache License 2.0 — see `LICENSE`. Replace the placeholder year/name in `LICENSE` if needed.

---
