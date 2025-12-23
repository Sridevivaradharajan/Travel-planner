"""
Weather Forecast Tool - Get real weather data using Open-Meteo API (Free, No API Key)
"""
from langchain.tools import tool
from typing import Optional
import requests
from datetime import datetime, timedelta

# City coordinates for Open-Meteo API
CITY_COORDINATES = {
    "goa": {"lat": 15.2993, "lon": 74.1240},
    "mumbai": {"lat": 19.0760, "lon": 72.8777},
    "delhi": {"lat": 28.7041, "lon": 77.1025},
    "bangalore": {"lat": 12.9716, "lon": 77.5946},
    "chennai": {"lat": 13.0827, "lon": 80.2707},
    "kolkata": {"lat": 22.5726, "lon": 88.3639},
    "hyderabad": {"lat": 17.3850, "lon": 78.4867},
    "jaipur": {"lat": 26.9124, "lon": 75.7873},
    "pune": {"lat": 18.5204, "lon": 73.8567},
    "ahmedabad": {"lat": 23.0225, "lon": 72.5714},
    "kochi": {"lat": 9.9312, "lon": 76.2673},
    "udaipur": {"lat": 24.5854, "lon": 73.7125},
    "varanasi": {"lat": 25.3176, "lon": 82.9739},
    "manali": {"lat": 32.2396, "lon": 77.1887},
    "shimla": {"lat": 31.1048, "lon": 77.1734},
    "agra": {"lat": 27.1767, "lon": 78.0081},
}

@tool
def get_weather_forecast(city: str, days: Optional[int] = 7) -> str:
    """
    Get real weather forecast for a city using Open-Meteo API (Free, No API Key Required).
    
    Args:
        city: City name (e.g., "Goa", "Jaipur", "Mumbai")
        days: Number of days to forecast (default: 7, max: 16)
    
    Returns:
        Weather forecast with temperature and conditions
    """
    
    # Normalize city name
    city_lower = city.lower()
    
    # Get coordinates
    coords = CITY_COORDINATES.get(city_lower)
    
    if not coords:
        # Try to find partial match
        for city_key, city_coords in CITY_COORDINATES.items():
            if city_lower in city_key or city_key in city_lower:
                coords = city_coords
                break
    
    if not coords:
        return f"❌ Weather data not available for {city}. Supported cities: {', '.join([c.title() for c in CITY_COORDINATES.keys()])}"
    
    try:
        # Open-Meteo API endpoint (FREE - No API Key Required)
        url = "https://api.open-meteo.com/v1/forecast"
        
        # Limit days to max 16 (API limit)
        forecast_days = min(days, 16)
        
        params = {
            'latitude': coords['lat'],
            'longitude': coords['lon'],
            'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode',
            'timezone': 'Asia/Kolkata',
            'forecast_days': forecast_days
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if 'daily' not in data:
            return f"❌ Could not fetch weather data for {city}."
        
        daily_data = data['daily']
        
        # Format response
        result = f"🌤️ **Weather Forecast for {city.title()}, India**\n\n"
        
        # Weather code to condition mapping (WMO Weather interpretation codes)
        weather_codes = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Foggy",
            48: "Foggy",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            71: "Slight snow",
            73: "Moderate snow",
            75: "Heavy snow",
            77: "Snow grains",
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            85: "Slight snow showers",
            86: "Heavy snow showers",
            95: "Thunderstorm",
            96: "Thunderstorm with hail",
            99: "Thunderstorm with hail"
        }
        
        rain_days = 0
        total_temp = 0
        
        for i in range(len(daily_data['time'])):
            date_str = daily_data['time'][i]
            date = datetime.strptime(date_str, '%Y-%m-%d')
            
            temp_min = int(daily_data['temperature_2m_min'][i])
            temp_max = int(daily_data['temperature_2m_max'][i])
            precipitation = daily_data['precipitation_sum'][i]
            weather_code = daily_data['weathercode'][i]
            
            condition = weather_codes.get(weather_code, "Unknown")
            
            # Check for rain
            is_rain = precipitation > 0 or weather_code in [51, 53, 55, 61, 63, 65, 80, 81, 82, 95, 96, 99]
            if is_rain:
                rain_days += 1
            
            total_temp += (temp_min + temp_max) / 2
            
            # Weather emoji
            if weather_code in [95, 96, 99]:
                emoji = "⛈️"
            elif is_rain:
                emoji = "🌧️"
            elif weather_code in [2, 3]:
                emoji = "⛅"
            elif weather_code in [0, 1]:
                emoji = "☀️"
            elif weather_code in [45, 48]:
                emoji = "🌫️"
            else:
                emoji = "🌤️"
            
            result += f"{emoji} **{date.strftime('%A, %b %d')}**\n"
            result += f"   🌡️ {temp_min}°C - {temp_max}°C | {condition}\n"
            
            if precipitation > 0:
                result += f"   💧 Precipitation: {precipitation:.1f}mm\n"
            
            result += "\n"
        
        # Add recommendations
        avg_temp = total_temp / len(daily_data['time'])
        
        result += "📋 **Recommendations:**\n"
        if avg_temp > 30:
            result += "   • Hot weather - stay hydrated, use sunscreen ☀️\n"
        elif avg_temp < 20:
            result += "   • Cool weather - pack warm clothes 🧥\n"
        else:
            result += "   • Pleasant weather - perfect for sightseeing! 😊\n"
        
        if rain_days > 2:
            result += "   • Rain expected - pack umbrella and raincoat ☔\n"
        elif rain_days > 0:
            result += "   • Light rain possible - carry an umbrella just in case 🌂\n"
        
        result += f"\n💡 **Data Source:** Open-Meteo API (Free Weather Data)\n"
        
        return result
        
    except requests.exceptions.RequestException as e:
        return f"❌ Error fetching weather data: {str(e)}\n\n" \
               f"Please check your internet connection."
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"


# Alias for backwards compatibility
get_weather = get_weather_forecast