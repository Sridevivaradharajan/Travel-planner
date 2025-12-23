"""
Budget Calculator Tool - Calculate trip costs and breakdown
Save this as: tools/budget_tool.py
"""
from langchain.tools import tool
from typing import Optional

@tool
def calculate_budget(
    flight_price: int,
    hotel_price_per_night: int,
    num_nights: int,
    daily_expenses: Optional[int] = 1500,
    num_travelers: Optional[int] = 1
) -> str:
    """
    Calculate estimated budget for a trip with detailed breakdown.
    
    Args:
        flight_price: Flight price per person (one-way)
        hotel_price_per_night: Hotel price per night (total, not per person)
        num_nights: Number of nights
        daily_expenses: Daily expenses per person for food, transport, activities (default: 1500)
        num_travelers: Number of travelers (default: 1)
    
    Returns:
        Detailed budget breakdown with total cost
    """
    
    # Ensure num_travelers is at least 1
    num_travelers = max(1, num_travelers)
    
    # Calculate totals
    # Flights - round trip for all travelers
    flight_total = flight_price * 2 * num_travelers  # Round trip
    
    # Accommodation - hotel price is total, not per person
    accommodation_total = hotel_price_per_night * num_nights
    
    # Daily expenses - per person per day
    daily_expenses_total = daily_expenses * num_nights * num_travelers
    
    # Subtotal
    subtotal = flight_total + accommodation_total + daily_expenses_total
    
    # Miscellaneous (10% of subtotal)
    misc_total = int(subtotal * 0.1)
    
    # Grand total
    grand_total = subtotal + misc_total
    
    # Format response - must contain "Budget" for test to pass
    result = f"💰 **Budget Breakdown for Your Trip**\n\n"
    result += f"📊 **Trip Details:**\n"
    result += f"   • Duration: {num_nights} night(s)\n"
    result += f"   • Travelers: {num_travelers} person(s)\n\n"
    
    result += f"💵 **Detailed Cost Breakdown (₹):**\n\n"
    
    result += f"✈️ **Flights (Round Trip)**\n"
    result += f"   ₹{flight_price:,}/person × 2 ways × {num_travelers} person(s)\n"
    result += f"   = ₹{flight_total:,}\n\n"
    
    result += f"🏨 **Accommodation**\n"
    result += f"   ₹{hotel_price_per_night:,}/night × {num_nights} night(s)\n"
    result += f"   = ₹{accommodation_total:,}\n\n"
    
    result += f"🍽️ **Daily Expenses** (food, transport, activities)\n"
    result += f"   ₹{daily_expenses:,}/person/day × {num_nights} day(s) × {num_travelers} person(s)\n"
    result += f"   = ₹{daily_expenses_total:,}\n\n"
    
    result += f"📦 **Miscellaneous (10%)**\n"
    result += f"   = ₹{misc_total:,}\n\n"
    
    result += f"{'='*50}\n"
    result += f"✨ **TOTAL ESTIMATED BUDGET: ₹{grand_total:,}** ✨\n"
    result += f"{'='*50}\n\n"
    
    # Budget tips
    result += f"💡 **Money-Saving Tips:**\n"
    result += "   • Book flights and hotels in advance for discounts\n"
    result += "   • Explore local street food for authentic & affordable meals\n"
    result += "   • Use public transport or shared rides to save money\n"
    result += "   • Look for combo deals on attractions and activities\n"
    result += "   • Consider travel insurance for peace of mind\n"
    
    # Per person breakdown
    per_person = grand_total // num_travelers
    result += f"\n💵 **Cost Per Person: ₹{per_person:,}**\n"
    
    return result