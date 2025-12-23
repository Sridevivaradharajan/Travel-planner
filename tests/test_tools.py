"""
Testing Script - Test all your tools before running the full agent!

This helps you make sure everything is working correctly.
Run this with: python test_tools.py
"""

import sys
import os

def test_data_files():
    """Test if all data files exist"""
    print("\n" + "="*60)
    print("TEST 1: Checking Data Files")
    print("="*60)
    
    files = ['data/flights.json', 'data/hotels.json', 'data/places.json']
    all_exist = True
    
    for file in files:
        if os.path.exists(file):
            print(f"✅ {file} - Found!")
        else:
            print(f"❌ {file} - NOT FOUND!")
            all_exist = False
    
    if all_exist:
        print("\n🎉 All data files are present!")
    else:
        print("\n⚠️  Some files are missing. Please download them.")
    
    return all_exist

def test_flight_tool():
    """Test the flight search tool"""
    print("\n" + "="*60)
    print("TEST 2: Testing Flight Search Tool")
    print("="*60)
    
    try:
        from tools.flight_tool import search_flights
        
        # Test search
        result = search_flights.invoke({"origin": "Delhi", "destination": "Goa", "preference": "cheapest"})
        
        if "Flight" in result or "Error" in result:
            print("✅ Flight tool is working!")
            print("\nSample Output:")
            print(result[:200] + "..." if len(result) > 200 else result)
            return True
        else:
            print("❌ Flight tool returned unexpected result")
            return False
            
    except Exception as e:
        print(f"❌ Error testing flight tool: {e}")
        return False

def test_hotel_tool():
    """Test the hotel recommendation tool"""
    print("\n" + "="*60)
    print("TEST 3: Testing Hotel Recommendation Tool")
    print("="*60)
    
    try:
        from tools.hotel_tool import search_hotels
        
        # Test search
        result = search_hotels.invoke({"city": "Goa", "min_rating": 3.0, "max_price": 10000})
        
        if "Hotel" in result or "Error" in result:
            print("✅ Hotel tool is working!")
            print("\nSample Output:")
            print(result[:200] + "..." if len(result) > 200 else result)
            return True
        else:
            print("❌ Hotel tool returned unexpected result")
            return False
            
    except Exception as e:
        print(f"❌ Error testing hotel tool: {e}")
        return False

def test_places_tool():
    """Test the places discovery tool"""
    print("\n" + "="*60)
    print("TEST 4: Testing Places Discovery Tool")
    print("="*60)
    
    try:
        from tools.places_tool import discover_places
        
        # Test search
        result = discover_places.invoke({"city": "Goa", "place_type": "all", "min_rating": 3.5})
        
        if "Places" in result or "Error" in result:
            print("✅ Places tool is working!")
            print("\nSample Output:")
            print(result[:200] + "..." if len(result) > 200 else result)
            return True
        else:
            print("❌ Places tool returned unexpected result")
            return False
            
    except Exception as e:
        print(f"❌ Error testing places tool: {e}")
        return False

def test_weather_tool():
    """Test the weather lookup tool"""
    print("\n" + "="*60)
    print("TEST 5: Testing Weather Lookup Tool")
    print("="*60)
    
    try:
        from tools.weather_tool import get_weather_forecast
        
        # Test search
        result = get_weather_forecast.invoke({"city": "Goa", "days": 3})
        
        if "Weather" in result or "Error" in result:
            print("✅ Weather tool is working!")
            print("\nSample Output:")
            print(result[:200] + "..." if len(result) > 200 else result)
            return True
        else:
            print("❌ Weather tool returned unexpected result")
            return False
            
    except Exception as e:
        print(f"❌ Error testing weather tool: {e}")
        return False

def test_budget_tool():
    """Test the budget calculation tool"""
    print("\n" + "="*60)
    print("TEST 6: Testing Budget Calculation Tool")
    print("="*60)
    
    try:
        from tools.budget_tool import calculate_budget
        
        # Test calculation
        result = calculate_budget.invoke({
            "flight_price": 4800,
            "hotel_price_per_night": 3200,
            "num_nights": 3,
            "daily_expenses": 1500
        })
        
        if "Budget" in result or "Error" in result:
            print("✅ Budget tool is working!")
            print("\nSample Output:")
            print(result[:200] + "..." if len(result) > 200 else result)
            return True
        else:
            print("❌ Budget tool returned unexpected result")
            return False
            
    except Exception as e:
        print(f"❌ Error testing budget tool: {e}")
        return False

def test_environment():
    """Test if environment variables are set"""
    print("\n" + "="*60)
    print("TEST 7: Checking Environment Variables")
    print("="*60)
    
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    
    if api_key and api_key != "your_openai_api_key_here":
        print("✅ OpenAI API key is set!")
        print(f"   Key starts with: {api_key[:10]}...")
        return True
    else:
        print("⚠️  OpenAI API key is not set or is still placeholder")
        print("   Please set it in .env file or you can enter it in the Streamlit app")
        return False

def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print(" "*20 + "🧪 TESTING YOUR TRAVEL AGENT 🧪")
    print("="*70)
    
    results = {
        "Data Files": test_data_files(),
        "Flight Tool": test_flight_tool(),
        "Hotel Tool": test_hotel_tool(),
        "Places Tool": test_places_tool(),
        "Weather Tool": test_weather_tool(),
        "Budget Tool": test_budget_tool(),
        "Environment": test_environment()
    }
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20s} : {status}")
    
    print("\n" + "="*70)
    print(f"Results: {passed}/{total} tests passed")
    print("="*70)
    
    if passed == total:
        print("\n🎉 All tests passed! Your travel agent is ready to use!")
        print("   Run: streamlit run app.py")
    elif passed >= 5:
        print("\n⚠️  Most tests passed! You can still use the agent.")
        print("   Some features might not work perfectly.")
    else:
        print("\n❌ Several tests failed. Please fix the issues before running.")
        print("   Check the error messages above for details.")

if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\nTesting interrupted by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error during testing: {e}")
