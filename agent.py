"""
Travel Planning AI Agent - Fixed for PostgreSQL Database
Optimized for Gemini Flash with correct database methods
"""
import os
from typing import List, Dict
from dotenv import load_dotenv
import json

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import Tool

from tenacity import (
    retry, 
    stop_after_attempt, 
    wait_exponential, 
    retry_if_exception_type
)
from google.api_core import exceptions

load_dotenv()

try:
    from database import TravelDatabase
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    print("⚠️ Warning: TravelDatabase not available")


class TravelAgent:
    """AI Travel Planning Agent powered by Google Gemini 1.5 Flash"""
    
    def __init__(self, google_api_key: str = None):
        """Initialize agent with cloud configuration support"""
        if google_api_key is None:
            from config import Config
            google_api_key = Config.get_google_api_key()
            if not google_api_key:
                raise ValueError("GOOGLE_API_KEY not found in configuration")
        
        # Initialize database
        self.db = None
        if DATABASE_AVAILABLE:
            try:
                self.db = TravelDatabase()
                print("Database connected")
            except Exception as e:
                print(f"Database error: {e}")
        
        # Initialize Gemini Flash
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",  # Using stable model
            google_api_key=google_api_key,
            temperature=0.7,
            convert_system_message_to_human=True,
            max_retries=2
        )
        
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        self.tools = self._create_tools()
        self.agent_executor = self._create_agent()
        
        print("TravelAgent initialized with Gemini 1.5 Flash")
        print("Quota: ~1,500 requests/day (Free Tier)")
    
    def _create_tools(self) -> List[Tool]:
        """Create tools with CORRECT database methods"""
        tools = []
        
        if self.db:
            tools.append(Tool(
                name="search_all_travel_data",
                func=self._search_all_data,
                description="""
                Get ALL travel data: flights, hotels, and places.
                Input: "from_city|to_city|budget_level|interests"
                Example: "Mumbai|Goa|moderate|beaches,food"
                Returns complete travel data in ONE call.
                """
            ))
        
        return tools
    
    def _create_agent(self) -> AgentExecutor:
        """Create agent with optimized prompt"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are Lumina, an expert AI travel planner.

CRITICAL: Use search_all_travel_data tool ONCE to get data, then create a plan.

Your response MUST include:
1. ✈️ FLIGHTS - Top 2 options with airline, price, times
2. 🏨 HOTELS - Top 2 with name, rating, price, amenities
3. 📅 ITINERARY - Day-by-day plan with places to visit
4. 💰 BUDGET - Breakdown (flights, hotels, food, transport, total)
5. 📝 TIPS - 3 helpful travel tips

Format cleanly. Be specific with numbers and names from the data."""),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        agent = create_tool_calling_agent(self.llm, self.tools, prompt)
        
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            max_iterations=3,
            max_execution_time=60,
            handle_parsing_errors=True
        )
    
    def _search_all_data(self, query: str) -> str:
        """Combined search using CORRECT database methods"""
        if not self.db:
            return "❌ Database not available"
        
        try:
            parts = query.split("|")
            if len(parts) < 3:
                return "❌ Invalid format. Use: from_city|to_city|budget_level|interests"
            
            from_city = parts[0].strip().title()
            to_city = parts[1].strip().title()
            budget_level = parts[2].strip().lower()
            interests = parts[3].strip() if len(parts) > 3 else ""
            
            result = ""
            
            # 1. Get flights using correct method: get_flights()
            flights = self.db.get_flights(from_city, to_city, limit=5)
            if flights:
                result += f"✈️ FLIGHTS ({from_city} → {to_city}):\n"
                for i, f in enumerate(flights[:3], 1):
                    result += f"{i}. {f['airline']} - ₹{f['price']:,}\n"
                    result += f"   Departure: {f['departure_time']} | Arrival: {f['arrival_time']}\n"
                result += "\n"
            else:
                result += f"⚠️ No direct flights found for {from_city} → {to_city}\n\n"
            
            # 2. Get hotels using correct method: get_hotels()
            budget_multiplier = {"budget": 0.7, "moderate": 1.0, "luxury": 1.5}.get(budget_level, 1.0)
            max_hotel_price = 5000 * budget_multiplier
            
            hotels = self.db.get_hotels(to_city, min_stars=3, max_price=max_hotel_price, limit=5)
            if hotels:
                result += f"🏨 HOTELS in {to_city}:\n"
                for i, h in enumerate(hotels[:3], 1):
                    amenities = json.loads(h['amenities']) if h['amenities'] else []
                    result += f"{i}. {h['name']} - ₹{h['price_per_night']:,}/night | ⭐{h['stars']}\n"
                    result += f"   Amenities: {', '.join(amenities[:5])}\n"
                result += "\n"
            else:
                result += f"⚠️ No hotels found in {to_city}\n\n"
            
            # 3. Get places using correct method: get_places()
            places = self.db.get_places(to_city, min_rating=3.5, limit=15)
            if places:
                result += f"🗺️ TOP ATTRACTIONS in {to_city}:\n"
                
                # Group by type
                place_types = {}
                for p in places:
                    ptype = p['type'] or 'General'
                    if ptype not in place_types:
                        place_types[ptype] = []
                    place_types[ptype].append(p)
                
                for ptype, plist in list(place_types.items())[:5]:
                    result += f"\n{ptype}:\n"
                    for p in plist[:3]:
                        result += f"  • {p['name']} - ⭐{p['rating']}/5\n"
                result += "\n"
            else:
                result += f"⚠️ No attractions found in {to_city}\n\n"
            
            # 4. Budget calculation
            avg_flight = sum(f['price'] for f in flights[:2]) / 2 if len(flights) >= 2 else 5000
            avg_hotel = sum(h['price_per_night'] for h in hotels[:2]) / 2 if len(hotels) >= 2 else 2500
            
            result += f"💰 BUDGET ESTIMATE ({budget_level.title()}):\n"
            result += f"Round-trip Flights: ₹{(avg_flight * 2 * budget_multiplier):,.0f}\n"
            result += f"Hotel per night: ₹{(avg_hotel * budget_multiplier):,.0f}\n"
            result += f"Food per day: ₹{(1500 * budget_multiplier):,.0f}\n"
            result += f"Transport per day: ₹{(800 * budget_multiplier):,.0f}\n"
            result += f"\nInterests: {interests}\n"
            
            return result
            
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    @retry(
        retry=retry_if_exception_type(exceptions.ResourceExhausted),
        wait=wait_exponential(multiplier=2, min=30, max=120),
        stop=stop_after_attempt(2)
    )
    def plan_trip(self, user_query: str) -> str:
        """Plan trip with rate limiting"""
        try:
            response = self.agent_executor.invoke({"input": user_query})
            return response.get("output", "❌ No response")
            
        except exceptions.ResourceExhausted as e:
            return f"""⚠️ **Rate Limit Exceeded**
            
Free tier: 20 requests/day. Please wait or upgrade your API key.

Error: {str(e)[:200]}"""
            
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def chat(self, message: str) -> str:
        """Chat about existing trip plan"""
        try:
            response = self.agent_executor.invoke({"input": message})
            return response.get("output", "❌ No response")
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def get_structured_data(self, from_city: str, to_city: str, budget: str) -> Dict:
        """Get structured data for dashboard (no AI call)"""
        if not self.db:
            return {}
        
        try:
            budget_multiplier = {"budget": 0.7, "moderate": 1.0, "luxury": 1.5}.get(budget.lower(), 1.0)
            max_hotel_price = 5000 * budget_multiplier
            
            flights = self.db.get_flights(from_city, to_city, limit=10)
            hotels = self.db.get_hotels(to_city, min_stars=3, max_price=max_hotel_price, limit=10)
            places = self.db.get_places(to_city, min_rating=3.5, limit=20)
            
            # Parse amenities
            for h in hotels:
                h['amenities_list'] = json.loads(h['amenities']) if h['amenities'] else []
            
            return {
                'flights': flights,
                'hotels': hotels,
                'places': places
            }
        except Exception as e:
            print(f"Error getting structured data: {e}")
            return {}
    
    def reset_memory(self):
        """Clear conversation memory"""
        self.memory.clear()
        print("🔄 Memory cleared")


if __name__ == "__main__":
    print("🚀 Testing Fixed Agent...")
    
    try:
        agent = TravelAgent()
        test_query = "Plan a 3-day moderate trip from Mumbai to Goa for 2 people interested in beaches and food"
        
        print("\n" + "="*60)
        print("Test Query:", test_query)
        print("="*60 + "\n")
        
        response = agent.plan_trip(test_query)
        print("\n📋 RESPONSE:\n")
        print(response)
        
    except Exception as e:
        print(f"❌ Error: {e}")
