"""
Places Discovery Tool - Find interesting places using real data
"""
from langchain.tools import tool
from typing import Optional
import json
import os

def load_places_data():
    """Load places data from JSON file"""
    data_path = os.path.join("data", "places.json")
    try:
        with open(data_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: {data_path} not found. Using empty data.")
        return []

@tool
def discover_places(city: str, interests: Optional[str] = "general") -> str:
    """
    Discover interesting places to visit in a city using real place data.
    
    Args:
        city: City name (e.g., "Goa", "Jaipur", "Mumbai")
        interests: User interests like "beach", "temple", "fort", "museum", "park", "market" (default: "general")
    
    Returns:
        List of recommended places to visit with ratings
    """
    
    # Load places data
    all_places = load_places_data()
    
    # Normalize inputs
    city_lower = city.lower()
    interest_lower = interests.lower() if interests else "general"
    
    # Filter places by city
    city_places = [
        place for place in all_places
        if place['city'].lower() == city_lower
    ]
    
    if not city_places:
        return f"❌ No places found in {city}. Please try another city."
    
    # If specific interest, filter by type
    if interest_lower != "general":
        interest_filtered = [
            place for place in city_places
            if interest_lower in place['type'].lower()
        ]
        if interest_filtered:
            city_places = interest_filtered
    
    # Sort by rating (highest first)
    city_places.sort(key=lambda x: x['rating'], reverse=True)
    
    # Take top 5
    places = city_places[:5]
    
    # Format response
    result = f"🎯 **Top Places to Visit in {city}**\n\n"
    
    if interests and interests != "general":
        result += f"Based on your interest in: **{interests}**\n\n"
    
    for i, place in enumerate(places, 1):
        # Type emoji mapping
        type_emoji = {
            'beach': '🏖️',
            'temple': '🛕',
            'fort': '🏰',
            'museum': '🏛️',
            'park': '🌳',
            'market': '🛍️',
            'lake': '🏞️',
            'monument': '🗿'
        }
        emoji = type_emoji.get(place['type'].lower(), '📍')
        
        result += f"{i}. {emoji} **{place['name']}** ({place['type'].capitalize()})\n"
        result += f"   ⭐ Rating: {place['rating']}/5.0\n"
        result += f"   🆔 Place ID: {place['place_id']}\n\n"
    
    # Add suggestion to explore more
    if len(city_places) > 5:
        result += f"💡 **Tip:** There are {len(city_places)} more places to explore in {city}!\n"
    
    return result