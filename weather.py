from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("weather")

# Constants
NWS_API_BASE = "https://api.weather.gov"
GEOCODE_API_BASE = "https://geocoding-api.open-meteo.com/v1/search"
USER_AGENT = "weather-app/1.0"

# Valid US state codes
US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC"
}


def validate_state_code(state: str) -> bool:
    """Validate that the state code is a valid 2-letter US state code."""
    return state.upper() in US_STATES


def validate_coordinates(latitude: float, longitude: float) -> bool:
    """Validate that coordinates are within valid ranges."""
    return -90 <= latitude <= 90 and -180 <= longitude <= 180


async def geocode_location(city_name: str) -> tuple[float, float] | None:
    """Geocode a city name to latitude and longitude coordinates.
    
    Returns:
        Tuple of (latitude, longitude) or None if geocoding fails
    """
    async with httpx.AsyncClient() as client:
        try:
            # Try to get US results first by adding country code
            # Open-Meteo supports country_code parameter
            params = {
                "name": city_name,
                "count": 10,  # Get more results to find US cities
                "language": "en",
                "format": "json"
            }
            response = await client.get(
                GEOCODE_API_BASE,
                params=params,
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("results") and len(data["results"]) > 0:
                # Prefer US results (country_code == "US")
                for result in data["results"]:
                    if result.get("country_code") == "US":
                        return (result["latitude"], result["longitude"])
                # If no US result found, return the first result anyway
                # (user might be looking for a non-US city, or it might still work)
                result = data["results"][0]
                return (result["latitude"], result["longitude"])
            return None
        except httpx.RequestError:
            return None
        except Exception:
            return None


async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            return None
        except (httpx.RequestError, httpx.TimeoutException):
            return None
        except Exception:
            return None

def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string."""
    props = feature["properties"]
    return f"""
Event: {props.get('event', 'Unknown')}
Area: {props.get('areaDesc', 'Unknown')}
Severity: {props.get('severity', 'Unknown')}
Description: {props.get('description', 'No description available')}
Instructions: {props.get('instruction', 'No specific instructions provided')}
"""


@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. CA, NY, TX)
    """
    state = state.upper().strip()
    
    if not validate_state_code(state):
        return f"Error: '{state}' is not a valid US state code. Please use a 2-letter code (e.g., CA, NY, TX)."
    
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    if not data or "features" not in data:
        return f"Unable to fetch alerts for {state}. The location may not be supported or the service is unavailable."

    if not data["features"]:
        return f"No active weather alerts for {state}."

    alerts = [format_alert(feature) for feature in data["features"]]
    return f"Weather Alerts for {state}:\n\n" + "\n---\n".join(alerts)

async def get_forecast_data(latitude: float, longitude: float) -> dict[str, Any] | None:
    """Get forecast data for coordinates. Returns None on error."""
    if not validate_coordinates(latitude, longitude):
        return None
    
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data or "properties" not in points_data:
        return None

    forecast_url = points_data["properties"].get("forecast")
    if not forecast_url:
        return None

    forecast_data = await make_nws_request(forecast_url)
    if not forecast_data or "properties" not in forecast_data:
        return None

    # Add location info to the forecast data
    location_info = points_data["properties"].get("relativeLocation", {})
    forecast_data["_location"] = {
        "city": location_info.get("properties", {}).get("city", "Unknown"),
        "state": location_info.get("properties", {}).get("state", "Unknown")
    }
    
    return forecast_data


@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location using coordinates.

    Args:
        latitude: Latitude of the location (-90 to 90)
        longitude: Longitude of the location (-180 to 180)
    """
    if not validate_coordinates(latitude, longitude):
        return "Error: Invalid coordinates. Latitude must be between -90 and 90, longitude between -180 and 180."

    forecast_data = await get_forecast_data(latitude, longitude)
    
    if not forecast_data:
        return f"Unable to fetch forecast data for coordinates ({latitude}, {longitude}). The location may be outside NWS coverage area (US only)."

    periods = forecast_data["properties"]["periods"]
    location = forecast_data.get("_location", {})
    location_str = f"{location.get('city', 'Unknown')}, {location.get('state', 'Unknown')}"
    
    forecasts = []
    for period in periods[:10]:  # Show next 10 periods (5 days)
        forecast = f"""
{period['name']}:
  Temperature: {period['temperature']}°{period['temperatureUnit']}
  Wind: {period['windSpeed']} {period['windDirection']}
  {f"Humidity: {period.get('relativeHumidity', {}).get('value', 'N/A')}%" if period.get('relativeHumidity') else ""}
  {f"Precipitation: {period.get('probabilityOfPrecipitation', {}).get('value', 0)}%" if period.get('probabilityOfPrecipitation') else ""}
  Forecast: {period['detailedForecast']}
"""
        forecasts.append(forecast)

    return f"Weather Forecast for {location_str}:\n" + "\n---\n".join(forecasts)


@mcp.tool()
async def get_forecast_by_city(city_name: str) -> str:
    """Get weather forecast for a city by name.

    Args:
        city_name: Name of the city (e.g., "San Francisco", "New York", "Chicago")
    """
    coords = await geocode_location(city_name)
    
    if not coords:
        return f"Error: Could not find coordinates for '{city_name}'. Please check the city name and try again."
    
    latitude, longitude = coords
    forecast_data = await get_forecast_data(latitude, longitude)
    
    if not forecast_data:
        return f"Unable to fetch forecast data for {city_name}. The location may be outside NWS coverage area (US only)."

    periods = forecast_data["properties"]["periods"]
    location = forecast_data.get("_location", {})
    location_str = f"{location.get('city', city_name)}, {location.get('state', 'Unknown')}"
    
    forecasts = []
    for period in periods[:10]:
        forecast = f"""
{period['name']}:
  Temperature: {period['temperature']}°{period['temperatureUnit']}
  Wind: {period['windSpeed']} {period['windDirection']}
  {f"Humidity: {period.get('relativeHumidity', {}).get('value', 'N/A')}%" if period.get('relativeHumidity') else ""}
  {f"Precipitation: {period.get('probabilityOfPrecipitation', {}).get('value', 0)}%" if period.get('probabilityOfPrecipitation') else ""}
  Forecast: {period['detailedForecast']}
"""
        forecasts.append(forecast)

    return f"Weather Forecast for {location_str}:\n" + "\n---\n".join(forecasts)


@mcp.tool()
async def get_current_conditions(latitude: float, longitude: float) -> str:
    """Get current weather conditions for a location.

    Args:
        latitude: Latitude of the location (-90 to 90)
        longitude: Longitude of the location (-180 to 180)
    """
    if not validate_coordinates(latitude, longitude):
        return "Error: Invalid coordinates. Latitude must be between -90 and 90, longitude between -180 and 180."

    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data or "properties" not in points_data:
        return f"Unable to fetch weather data for coordinates ({latitude}, {longitude})."

    observation_url = points_data["properties"].get("observationStations")
    if not observation_url:
        return "No observation stations available for this location."

    # Get the nearest observation station
    stations_data = await make_nws_request(observation_url)
    if not stations_data or not stations_data.get("features"):
        return "No observation stations found for this location."

    station_id = stations_data["features"][0]["properties"]["stationIdentifier"]
    observations_url = f"{NWS_API_BASE}/stations/{station_id}/observations/latest"
    observations_data = await make_nws_request(observations_url)

    if not observations_data or "properties" not in observations_data:
        return "Unable to fetch current observations."

    props = observations_data["properties"]
    location_info = points_data["properties"].get("relativeLocation", {})
    location_str = f"{location_info.get('properties', {}).get('city', 'Unknown')}, {location_info.get('properties', {}).get('state', 'Unknown')}"

    temp = props.get("temperature", {}).get("value")
    temp_unit = "°C"
    if temp is not None:
        temp_f = (temp * 9/5) + 32
        temp_unit = f"°F ({temp:.1f}°C)"

    dewpoint = props.get("dewpoint", {}).get("value")
    humidity = props.get("relativeHumidity", {}).get("value")
    wind_speed = props.get("windSpeed", {}).get("value")
    wind_direction = props.get("windDirection", {}).get("value")
    pressure = props.get("barometricPressure", {}).get("value")
    visibility = props.get("visibility", {}).get("value")
    text_description = props.get("textDescription", "N/A")

    result = f"Current Conditions for {location_str}:\n\n"
    result += f"Temperature: {temp_f:.1f}{temp_unit}\n" if temp is not None else "Temperature: N/A\n"
    result += f"Conditions: {text_description}\n"
    result += f"Humidity: {humidity:.1f}%\n" if humidity is not None else ""
    result += f"Dewpoint: {dewpoint * 9/5 + 32:.1f}°F\n" if dewpoint is not None else ""
    result += f"Wind: {wind_speed * 2.237:.1f} mph from {wind_direction}°\n" if wind_speed is not None and wind_direction is not None else ""
    result += f"Pressure: {pressure / 100:.2f} hPa\n" if pressure is not None else ""
    result += f"Visibility: {visibility / 1609.34:.2f} miles\n" if visibility is not None else ""

    return result


@mcp.tool()
async def compare_weather(location1: str, location2: str) -> str:
    """Compare current weather conditions between two locations.
    
    This unique feature allows you to compare weather at two different places side-by-side.

    Args:
        location1: First location (city name or "lat,lon" format, e.g., "New York" or "40.7128,-74.0060")
        location2: Second location (city name or "lat,lon" format, e.g., "Los Angeles" or "34.0522,-118.2437")
    """
    def parse_location(loc: str) -> tuple[float, float] | None:
        """Parse location string to coordinates.
        
        Only parses if the string is clearly in "lat,lon" format (both parts are numeric).
        Returns None for city names (even if they contain commas like "New York, NY").
        """
        # Check if it's in "lat,lon" format
        if "," in loc:
            parts = loc.split(",")
            # Only try to parse if we have exactly 2 parts
            if len(parts) == 2:
                try:
                    # Try to parse both parts as floats
                    lat_str = parts[0].strip()
                    lon_str = parts[1].strip()
                    lat, lon = float(lat_str), float(lon_str)
                    # Validate coordinates are in valid ranges
                    if validate_coordinates(lat, lon):
                        return (lat, lon)
                except ValueError:
                    # If parsing fails, it's not coordinates (probably a city name with comma)
                    pass
        # Not in coordinate format, will need geocoding
        return None

    # Get coordinates for both locations
    # Try parsing as coordinates first (e.g., "40.7128,-74.0060")
    coords1 = parse_location(location1)
    if not coords1:
        # If not coordinates, try geocoding the city name
        coords1 = await geocode_location(location1)
        if not coords1:
            return f"Error: Could not find coordinates for '{location1}'. Please check the city name or use 'lat,lon' format (e.g., '40.7128,-74.0060')."

    coords2 = parse_location(location2)
    if not coords2:
        # If not coordinates, try geocoding the city name
        coords2 = await geocode_location(location2)
        if not coords2:
            return f"Error: Could not find coordinates for '{location2}'. Please check the city name or use 'lat,lon' format (e.g., '40.7128,-74.0060')."

    # Get forecast data for both locations
    forecast1 = await get_forecast_data(coords1[0], coords1[1])
    forecast2 = await get_forecast_data(coords2[0], coords2[1])

    if not forecast1:
        return f"Unable to fetch weather data for '{location1}' (coordinates: {coords1[0]}, {coords1[1]}). The location may be outside NWS coverage area (US territories only)."
    if not forecast2:
        return f"Unable to fetch weather data for '{location2}' (coordinates: {coords2[0]}, {coords2[1]}). The location may be outside NWS coverage area (US territories only)."

    loc1_info = forecast1.get("_location", {})
    loc2_info = forecast2.get("_location", {})
    loc1_str = f"{loc1_info.get('city', location1)}, {loc1_info.get('state', 'Unknown')}"
    loc2_str = f"{loc2_info.get('city', location2)}, {loc2_info.get('state', 'Unknown')}"

    # Get current period (first period) for each location
    period1 = forecast1["properties"]["periods"][0] if forecast1["properties"]["periods"] else None
    period2 = forecast2["properties"]["periods"][0] if forecast2["properties"]["periods"] else None

    if not period1 or not period2:
        return "Unable to get current conditions for comparison."

    result = f"🌤️  Weather Comparison\n"
    result += f"{'='*60}\n\n"
    result += f"{loc1_str:<30} | {loc2_str}\n"
    result += f"{'-'*60}\n"
    result += f"Temperature: {period1['temperature']}°{period1['temperatureUnit']:<25} | {period2['temperature']}°{period2['temperatureUnit']}\n"
    result += f"Wind: {period1['windSpeed']} {period1['windDirection']:<25} | {period2['windSpeed']} {period2['windDirection']}\n"
    
    if period1.get('relativeHumidity') and period2.get('relativeHumidity'):
        result += f"Humidity: {period1['relativeHumidity']['value']}%{'':<25} | {period2['relativeHumidity']['value']}%\n"
    
    if period1.get('probabilityOfPrecipitation') and period2.get('probabilityOfPrecipitation'):
        result += f"Precip Chance: {period1['probabilityOfPrecipitation']['value']}%{'':<22} | {period2['probabilityOfPrecipitation']['value']}%\n"
    
    result += f"\nForecast:\n"
    result += f"{loc1_str}: {period1['detailedForecast']}\n"
    result += f"{loc2_str}: {period2['detailedForecast']}\n"

    # Add temperature difference analysis
    temp_diff = period1['temperature'] - period2['temperature']
    if abs(temp_diff) > 5:
        warmer = loc1_str if temp_diff > 0 else loc2_str
        result += f"\n💡 {warmer} is {abs(temp_diff)}°{period1['temperatureUnit']} warmer!"

    return result


def main():
    # Initialize and run the server
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()