"""
Load JSON data files into Neon PostgreSQL database
Run this ONCE to populate your database
"""
import os
from database import TravelDatabase
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def main():
    print("=" * 70)
    print("🚀 Loading Travel Data into Neon PostgreSQL")
    print("=" * 70)
    
    try:
        # Initialize database connection
        print("\n1️⃣ Connecting to database...")
        db = TravelDatabase()
        
        # Check if data files exist
        data_dir = 'data'
        flights_file = os.path.join(data_dir, 'flights.json')
        hotels_file = os.path.join(data_dir, 'hotels.json')
        places_file = os.path.join(data_dir, 'places.json')
        
        missing_files = [f for f in [flights_file, hotels_file, places_file] if not os.path.exists(f)]
        if missing_files:
            print(f"❌ Missing JSON files: {missing_files}")
            print("Please create the 'data/' folder and add these files.")
            return
        
        # Load data
        print("\n2️⃣ Loading JSON data files...")
        db.load_json_data_to_db(flights_file, hotels_file, places_file)
        
        # Display statistics
        print("\n3️⃣ Database statistics:")
        print("=" * 70)
        stats = db.get_database_stats()
        print(f"✈️  Total Flights: {stats.get('total_flights', 0)}")
        print(f"🏨  Total Hotels: {stats.get('total_hotels', 0)}")
        print(f"🗺️  Total Places: {stats.get('total_places', 0)}")
        print(f"🌆  Total Cities: {stats.get('total_cities', 0)}")
        print("=" * 70)
        
        print("\n✅ SUCCESS! Your Neon database is now populated.")
        print("🚀 You can now run your Streamlit app!")
        
        db.close()
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\n💡 Troubleshooting:")
        print("  1. Make sure .env exists with correct Neon credentials")
        print("  2. Ensure Neon database is active")
        print("  3. Check JSON files are valid and present in 'data/' folder")

if __name__ == "__main__":
    main()
