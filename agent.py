"""
Travel Planning AI Agent - Fixed Version
Compatible with PostgreSQL Database and Gemini Flash
Fixes: DateTime serialization, Agent format errors, Better error handling, LIST INPUT BUG
"""
import os
from typing import List, Dict
from dotenv import load_dotenv
import json
from datetime import datetime, date
from decimal import Decimal

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from langchain.tools import Tool

from tenacity import (
    retry, 
    stop_after_attempt, 
    wait_exponential, 
    retry_if_exception_type
)
from google.api_core import exceptions

load_dotenv()

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

try:
    from database import TravelDatabase
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    print("Warning: TravelDatabase not available")


def json_serializer(obj):
    """Convert non-serializable objects to JSON-compatible format"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return float(obj)
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    return str(obj)


def prepare_for_json(data):
    """Recursively prepare data for JSON serialization"""
    if isinstance(data, (datetime, date)):
        return data.isoformat()
    elif isinstance(data, Decimal):
        return float(data)
    elif isinstance(data, dict):
        return {k: prepare_for_json(v) for k, v in data.items()}
    elif isinstance(data, (list, tuple)):
        return [prepare_for_json(item) for item in data]
    return data


def ensure_string(value):
    """Convert any value to string safely - FIX FOR LIST INPUT BUG"""
    if isinstance(value, list):
        return ", ".join(str(x) for x in value)
    elif value is None:
        return ""
    elif isinstance(value, (datetime, date)):
        return value.isoformat()
    elif isinstance(value, Decimal):
        return str(float(value))
    return str(value)


class TravelAgent:
    """AI Travel Planning Agent powered by Google Gemini 1.5 Flash"""
    
    def __init__(self, google_api_key: str = None):
        """Initialize agent with cloud configuration support"""
        if google_api_key is None:
            # Try Streamlit secrets (Cloud)
            if STREAMLIT_AVAILABLE:
                google_api_key = st.secrets.get("GOOGLE_API_KEY")
        
            # Fallback to environment variable (local)
            if not google_api_key:
                google_api_key = os.getenv("GOOGLE_API_KEY")
        
            # Final check
            if not google_api_key:
                raise ValueError(
                    "GOOGLE_API_KEY not found. Add it to Streamlit secrets or .env"
                )

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
            model="gemini-flash-latest",
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
                Get ALL travel data: flights, hotels, and places in ONE call.
                Input format: "from_city|to_city|budget_level|interests"
                Example: "Mumbai|Goa|moderate|beaches,food"
                
                This tool returns:
                - Available flights with prices and times
                - Hotels with ratings and amenities
                - Tourist attractions by category
                - Budget estimates
                
                USE THIS TOOL ONLY ONCE, then create your complete plan.
                """
            ))
        
        return tools
    
    def _create_agent(self) -> AgentExecutor:
        """Create agent with improved format handling"""
        
        agent_kwargs = {
            "prefix": """You are Lumina, an expert AI travel planner with access to real travel data.

WORKFLOW (CRITICAL - FOLLOW EXACTLY):
1. Call search_all_travel_data tool ONCE with the required format
2. Wait for the Observation with all travel data
3. Analyze the data you received
4. Respond with "Final Answer:" followed by your complete travel plan

NEVER call the tool multiple times. NEVER respond before receiving the Observation.

Your Final Answer MUST be a complete travel plan including:

1. FLIGHTS Section
   - List top 2 flight options with airline, price, departure/arrival times
   - Clearly mark the recommended option

2. HOTELS Section  
   - List top 2 hotels with name, star rating, price per night, key amenities
   - Explain why you recommend each option

3. ITINERARY Section
   - Create a day-by-day schedule
   - Include specific places to visit from the attractions data
   - Add morning, afternoon, and evening activities
   - Align activities with user's stated interests

4. BUDGET BREAKDOWN Section
   - Calculate total costs based on:
     * Round-trip flights (multiply by number of travelers)
     * Hotels (price × number of nights)
     * Food estimates (per day × days × travelers)
     * Local transport (per day × days)
   - Show calculations clearly
   - Present final total

5. TRAVEL TIPS Section
   - Provide 3 practical, specific tips
   - Base tips on the destination and trip type

Format your response with clear sections, tables where helpful, and emoji headers.""",

            "format_instructions": """Use this format STRICTLY:

Thought: [Understand what the user wants]
Action: search_all_travel_data
Action Input: from_city|to_city|budget|interests
Observation: [Wait for the tool output - DO NOT SKIP THIS]
Thought: I now have all the data. I will create a complete travel plan.
Final Answer: [Your complete formatted travel plan with all 5 sections]

CRITICAL RULES:
- After receiving Observation, your next output MUST start with "Thought:" then "Final Answer:"
- NEVER write additional text without proper Thought/Action/Final Answer format
- If you get an error, think about it, then provide Final Answer with available info""",

            "suffix": """Begin! Remember: Call the tool ONCE, wait for data, then give Final Answer.

Question: {input}
{agent_scratchpad}"""
        }
        
        return initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            memory=self.memory,
            agent_kwargs=agent_kwargs,
            max_iterations=5,
            max_execution_time=90,
            early_stopping_method="generate",
            handle_parsing_errors=True
        )
    
    def _search_all_data(self, query: str) -> str:
        """Combined search using CORRECT database methods with proper formatting
        
        FIX: Handles both string and list inputs safely
        """
        if not self.db:
            return "Database not available"
        
        try:
            # ========== CRITICAL FIX: HANDLE LIST INPUTS ==========
            # Convert query to string if it's a list
            if isinstance(query, list):
                query = "|".join(ensure_string(item) for item in query)
            elif not isinstance(query, str):
                query = ensure_string(query)
            # ======================================================
            
            parts = query.split("|")
            if len(parts) < 3:
                return "Invalid format. Use: from_city|to_city|budget_level|interests"
            
            # Safely convert each part to string
            from_city = ensure_string(parts[0]).strip().title()
            to_city = ensure_string(parts[1]).strip().title()
            budget_level = ensure_string(parts[2]).strip().lower()
            interests = ensure_string(parts[3]).strip() if len(parts) > 3 else ""
            
            result = []
            
            # 1. Get flights
            flights = self.db.get_flights(from_city, to_city, limit=5)
            if flights:
                result.append(f"FLIGHTS ({from_city} → {to_city}):")
                for i, f in enumerate(flights[:3], 1):
                    # Convert datetime to string for display
                    dept_time = f['departure_time'].strftime('%Y-%m-%d %H:%M:%S') if isinstance(f['departure_time'], datetime) else str(f['departure_time'])
                    arr_time = f['arrival_time'].strftime('%Y-%m-%d %H:%M:%S') if isinstance(f['arrival_time'], datetime) else str(f['arrival_time'])
                    
                    result.append(f"{i}. {f['airline']} - ₹{float(f['price']):,.0f}")
                    result.append(f"   Departure: {dept_time} | Arrival: {arr_time}")
                result.append("")
            else:
                result.append(f"No direct flights found for {from_city} → {to_city}\n")
            
            # 2. Get hotels
            budget_multiplier = {"budget": 0.7, "moderate": 1.0, "luxury": 1.5}.get(budget_level, 1.0)
            max_hotel_price = 5000 * budget_multiplier
            
            hotels = self.db.get_hotels(to_city, min_stars=3, max_price=max_hotel_price, limit=5)
            if hotels:
                result.append(f"HOTELS in {to_city}:")
                for i, h in enumerate(hotels[:3], 1):
                    amenities = h['amenities'].split(',') if h['amenities'] else []
                    amenities_str = json.dumps(amenities[:5])  # Convert to JSON string for cleaner display
                    result.append(f"{i}. {h['name']} - ₹{float(h['price_per_night']):,.2f}/night | ⭐{h['stars']}")
                    result.append(f"   Amenities: {amenities_str}")
                result.append("")
            else:
                result.append(f"No hotels found in {to_city}\n")
            
            # 3. Get places
            places = self.db.get_places(to_city, min_rating=3.5, limit=15)
            if places:
                result.append(f"TOP ATTRACTIONS in {to_city}:\n")
                
                # Group by type
                place_types = {}
                for p in places:
                    ptype = p['type'] or 'general'
                    if ptype not in place_types:
                        place_types[ptype] = []
                    place_types[ptype].append(p)
                
                for ptype, plist in list(place_types.items())[:5]:
                    result.append(f"{ptype}:")
                    for p in plist[:3]:
                        result.append(f"  • {p['name']} - ⭐{float(p['rating']):.2f}/5")
                    result.append("")
            else:
                result.append(f"No attractions found in {to_city}\n")
            
            # 4. Budget calculation
            if flights and hotels:
                avg_flight = sum(float(f['price']) for f in flights[:2]) / min(2, len(flights))
                avg_hotel = sum(float(h['price_per_night']) for h in hotels[:2]) / min(2, len(hotels))
                
                result.append(f"BUDGET ESTIMATE ({budget_level.title()}):")
                result.append(f"Round-trip Flights: ₹{float(avg_flight) * 2:,.0f}")
                result.append(f"Hotel per night: ₹{float(avg_hotel):,.0f}")
                result.append(f"Food per day: ₹{int(1500 * budget_multiplier):,}")
                result.append(f"Transport per day: ₹{int(800 * budget_multiplier):,}")
            
            result.append(f"\nInterests: {interests}")
            
            return "\n".join(result)
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Error in _search_all_data: {error_details}")
            return f"Error searching travel data: {str(e)}\nPlease try again or contact support."
    
    @retry(
        retry=retry_if_exception_type(exceptions.ResourceExhausted),
        wait=wait_exponential(multiplier=2, min=30, max=120),
        stop=stop_after_attempt(2)
    )
    def plan_trip(self, user_query: str) -> str:
        """Plan trip with rate limiting and better error handling
        
        FIX: Ensures user_query is always a string
        """
        try:
            # ========== CRITICAL FIX: ENSURE STRING INPUT ==========
            if not isinstance(user_query, str):
                user_query = ensure_string(user_query)
            # =======================================================
            
            response = self.agent_executor.invoke({"input": user_query})
            return response.get("output", "No response generated")
            
        except exceptions.ResourceExhausted as e:
            return f"""⚠️ **Rate Limit Exceeded**
            
Free tier: 1,500 requests/day. Please wait a moment or upgrade your API key.

Error: {str(e)[:200]}"""
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Error in plan_trip: {error_details}")
            return f"Error planning trip: {str(e)}\n\nPlease try rephrasing your request or contact support."
    
    def chat(self, message: str) -> str:
        """Chat about existing trip plan
        
        FIX: Ensures message is always a string
        """
        try:
            # ========== CRITICAL FIX: ENSURE STRING INPUT ==========
            if not isinstance(message, str):
                message = ensure_string(message)
            # =======================================================
            
            response = self.agent_executor.invoke({"input": message})
            return response.get("output", "No response generated")
        except Exception as e:
            return f"Error: {str(e)}"
    
    def get_structured_data(self, from_city: str, to_city: str, budget: str) -> Dict:
        """Get structured data for dashboard (no AI call) with proper serialization"""
        if not self.db:
            return {}
        
        try:
            budget_multiplier = {"budget": 0.7, "moderate": 1.0, "luxury": 1.5}.get(budget.lower(), 1.0)
            max_hotel_price = 5000 * budget_multiplier
            
            flights = self.db.get_flights(from_city, to_city, limit=10)
            hotels = self.db.get_hotels(to_city, min_stars=3, max_price=max_hotel_price, limit=10)
            places = self.db.get_places(to_city, min_rating=3.5, limit=20)
            
            # Prepare data for JSON serialization
            flights = prepare_for_json(flights)
            hotels = prepare_for_json(hotels)
            places = prepare_for_json(places)
            
            # Parse amenities for hotels
            for h in hotels:
                if isinstance(h.get('amenities'), str):
                    h['amenities_list'] = h['amenities'].split(',') if h['amenities'] else []
                else:
                    h['amenities_list'] = []
            
            return {
                'flights': flights,
                'hotels': hotels,
                'places': places
            }
        except Exception as e:
            import traceback
            print(f"Error getting structured data: {traceback.format_exc()}")
            return {}
    
    def save_trip_plan(self, user_id: str, trip_data: Dict) -> bool:
        """Save trip plan with proper JSON serialization"""
        if not self.db:
            return False
        
        try:
            # Prepare data for JSON serialization
            serializable_data = prepare_for_json(trip_data)
            
            # Convert to JSON string
            trip_json = json.dumps(serializable_data, default=json_serializer)
            
            # Save to database
            self.db.save_trip(user_id, trip_json)
            print("Trip saved successfully")
            return True
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"[DATABASE] Save trip failed: {error_details}")
            return False
    
    def reset_memory(self):
        """Clear conversation memory"""
        self.memory.clear()
        print("Memory cleared")


if __name__ == "__main__":
    print("Testing Fixed Agent...")
    
    try:
        agent = TravelAgent()
        test_query = "Plan a 3-day moderate budget trip from Mumbai to Goa for 2 people interested in beaches and food"
        
        print("\n" + "="*60)
        print("Test Query:", test_query)
        print("="*60 + "\n")
        
        response = agent.plan_trip(test_query)
        print("\n RESPONSE:\n")
        print(response)
        
    except Exception as e:
        import traceback
        print(f"❌ Error: {traceback.format_exc()}")
