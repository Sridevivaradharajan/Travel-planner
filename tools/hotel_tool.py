"""
Hotel Recommendation Tool - Find hotels using real data
"""
from langchain.tools import tool
from typing import Optional
import json
import os

def load_hotels_data():
    """Load hotels data from JSON file"""
    data_path = os.path.join("data", "hotels.json")
    try:
        with open(data_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: {data_path} not found. Using empty data.")
        return []

@tool
def search_hotels(city: str, budget: Optional[str] = "medium", nights: Optional[int] = 3) -> str:
    """
    Recommend hotels in a city based on budget and preferences using real hotel data.
    
    Args:
        city: City name (e.g., "Goa", "Jaipur", "Mumbai")
        budget: Budget level - "low" (2 stars), "medium" (3-4 stars), or "high" (5 stars)
        nights: Number of nights (default: 3)
    
    Returns:
        Hotel recommendations with prices and ratings
    """
    
    # Load hotel data
    all_hotels = load_hotels_data()
    
    # Normalize city name
    city_lower = city.lower()
    
    # Filter hotels by city
    city_hotels = [
        hotel for hotel in all_hotels
        if hotel['city'].lower() == city_lower
    ]
    
    if not city_hotels:
        return f"❌ No hotels found in {city}. Please try another city."
    
    # Map budget to star rating
    budget_map = {
        "low": [2],
        "medium": [3, 4],
        "high": [5]
    }
    
    # Normalize budget input
    budget_key = budget.lower() if budget else "medium"
    if budget_key not in budget_map:
        budget_key = "medium"
    
    # Filter by budget (star rating)
    filtered_hotels = [
        hotel for hotel in city_hotels
        if hotel['stars'] in budget_map[budget_key]
    ]
    
    # If no hotels match the budget, show all city hotels
    if not filtered_hotels:
        filtered_hotels = city_hotels
        result_note = f"\n⚠️ Limited options for {budget_key} budget, showing all available hotels.\n\n"
    else:
        result_note = ""
    
    # Sort by price
    filtered_hotels.sort(key=lambda x: x['price_per_night'])
    
    # Take top 5
    hotels = filtered_hotels[:5]
    
    # Calculate total costs
    for hotel in hotels:
        hotel['total_cost'] = hotel['price_per_night'] * nights
    
    # Format response
    result = f"🏨 **Hotels in {city}** ({budget_key.capitalize()} Budget)\n"
    result += f"📅 For {nights} night(s)\n"
    result += result_note + "\n"
    
    for i, hotel in enumerate(hotels, 1):
        stars = "⭐" * hotel['stars']
        result += f"{i}. **{hotel['name']}** {stars}\n"
        result += f"   🏷️ Rating: {hotel['stars']}-star hotel\n"
        result += f"   💰 ₹{hotel['price_per_night']:,}/night | Total: ₹{hotel['total_cost']:,}\n"
        result += f"   ✨ Amenities: {', '.join(hotel['amenities'])}\n"
        result += f"   🆔 Hotel ID: {hotel['hotel_id']}\n\n"
    
    return result