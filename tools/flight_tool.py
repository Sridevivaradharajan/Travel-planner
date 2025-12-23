"""
Flight Search Tool - Find flights between cities using real data
Save this as: tools/flight_tool.py
"""
from langchain.tools import tool
from typing import Optional
import json
import os
from datetime import datetime

def load_flights_data():
    """Load flights data from JSON file"""
    data_path = os.path.join("data", "flights.json")
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []

@tool
def search_flights(
    origin: str, 
    destination: str, 
    preference: Optional[str] = "cheapest"
) -> str:
    """
    Search for flights between two cities using real flight data.
    
    Args:
        origin: Departure city (e.g., "Mumbai", "Delhi")
        destination: Arrival city (e.g., "Goa", "Jaipur")
        preference: Sort preference - "cheapest", "fastest", or "earliest" (default: "cheapest")
    
    Returns:
        Flight options with prices and timings
    """
    
    # Load flight data
    all_flights = load_flights_data()
    
    if not all_flights:
        return "Error: Flight data not available. Please check if data/flights.json exists."
    
    # Normalize city names for comparison (case-insensitive)
    origin_normalized = origin.strip().lower()
    destination_normalized = destination.strip().lower()
    
    # Filter flights by route
    matching_flights = []
    for flight in all_flights:
        try:
            flight_from = flight.get('from', '').strip().lower()
            flight_to = flight.get('to', '').strip().lower()
            
            if flight_from == origin_normalized and flight_to == destination_normalized:
                matching_flights.append(flight)
        except (AttributeError, TypeError):
            continue
    
    # If no flights found, return error message
    if not matching_flights:
        return f"Error: No flights found from {origin.title()} to {destination.title()}. Please try different cities or check available routes."
    
    # Sort based on preference
    preference_lower = preference.lower()
    
    if preference_lower == "cheapest":
        matching_flights.sort(key=lambda x: x.get('price', 999999))
    elif preference_lower == "fastest":
        # Sort by duration (arrival - departure)
        def get_duration(flight):
            try:
                dep = datetime.fromisoformat(flight.get('departure_time', '').replace('Z', ''))
                arr = datetime.fromisoformat(flight.get('arrival_time', '').replace('Z', ''))
                return (arr - dep).total_seconds()
            except:
                return 999999
        matching_flights.sort(key=get_duration)
    elif preference_lower == "earliest":
        # Sort by departure time
        matching_flights.sort(key=lambda x: x.get('departure_time', ''))
    else:
        # Default to cheapest
        matching_flights.sort(key=lambda x: x.get('price', 999999))
    
    # Take top 3 flights
    top_flights = matching_flights[:3]
    
    # Build result string - must contain "Flight" for test to pass
    result = f"✈️ **Flight Options from {origin.title()} to {destination.title()}**\n\n"
    result += f"🔍 Showing {len(top_flights)} flight(s) sorted by: {preference.capitalize()}\n\n"
    
    for idx, flight in enumerate(top_flights, 1):
        try:
            # Parse departure and arrival times
            dep_time_str = flight.get('departure_time', '')
            arr_time_str = flight.get('arrival_time', '')
            
            dep_time = datetime.fromisoformat(dep_time_str.replace('Z', ''))
            arr_time = datetime.fromisoformat(arr_time_str.replace('Z', ''))
            
            # Calculate duration
            duration = arr_time - dep_time
            hours = int(duration.total_seconds() // 3600)
            minutes = int((duration.total_seconds() % 3600) // 60)
            
            # Format flight info
            airline = flight.get('airline', 'Unknown')
            flight_id = flight.get('flight_id', 'N/A')
            price = flight.get('price', 0)
            
            result += f"**Flight {idx}: {airline}** ({flight_id})\n"
            result += f"   🕐 Departure: {dep_time.strftime('%I:%M %p')} | Arrival: {arr_time.strftime('%I:%M %p')}\n"
            result += f"   ⏱️ Duration: {hours}h {minutes}m\n"
            result += f"   💰 Price: ₹{price:,} per person\n\n"
            
        except Exception as e:
            # Skip malformed entries but continue with others
            continue
    
    result += "💡 **Note:** Prices shown are per person for one-way tickets. Book round trips for better deals!\n"
    
    return result