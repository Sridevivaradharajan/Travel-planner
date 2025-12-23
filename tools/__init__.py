"""
Tools Package - Collection of all travel planning tools
"""
from .flight_tool import search_flights
from .hotel_tool import search_hotels
from .places_tool import discover_places
from .weather_tool import get_weather_forecast
from .budget_tool import calculate_budget

# Create aliases to match different naming conventions
recommend_hotels = search_hotels  # Alias for search_hotels
get_weather = get_weather_forecast  # Alias for get_weather_forecast

__all__ = [
    'search_flights',
    'search_hotels',
    'recommend_hotels',
    'discover_places',
    'get_weather_forecast',
    'get_weather',  # Add alias
    'calculate_budget'
]