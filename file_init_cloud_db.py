"""
Initialize Cloud PostgreSQL Database
Loads all data from JSON files into cloud database
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import os
from config import Config

def connect_to_database():
    """Connect to cloud PostgreSQL database"""
    try:
        db_config = Config.get_database_config()
        if not db_config:
            print("❌ Database configuration not found!")
            print("\n💡 Make sure you have either:")
            print("   1. .streamlit/secrets.toml (for local testing)")
            print("   2. .env file with DB credentials")
            return None
        
        print(f"🔌 Connecting to {db_config['host']}...")
        
        conn = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password'],
            sslmode=db_config.get('sslmode', 'require')
        )
        
        print(f"✅ Connected to database: {db_config['database']}")
        return conn
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Check your credentials in .streamlit/secrets.toml")
        print("   2. Verify database exists on cloud provider")
        print("   3. Check firewall/security settings")
        return None


def create_tables(conn):
    """Create all required tables"""
    cursor = conn.cursor()
    
    try:
        print("\n📋 Creating database schema...")
        
        # Flights table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS flights (
                id SERIAL PRIMARY KEY,
                flight_id VARCHAR(20) UNIQUE NOT NULL,
                airline VARCHAR(100) NOT NULL,
                from_city VARCHAR(100) NOT NULL,
                to_city VARCHAR(100) NOT NULL,
                departure_time TIMESTAMP,
                arrival_time TIMESTAMP,
                price DECIMAL(10, 2) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  ✓ Flights table")
        
        # Hotels table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hotels (
                id SERIAL PRIMARY KEY,
                hotel_id VARCHAR(20) UNIQUE NOT NULL,
                name VARCHAR(200) NOT NULL,
                city VARCHAR(100) NOT NULL,
                stars INTEGER,
                price_per_night DECIMAL(10, 2) NOT NULL,
                amenities TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  ✓ Hotels table")
        
        # Places table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS places (
                id SERIAL PRIMARY KEY,
                place_id VARCHAR(20) UNIQUE NOT NULL,
                name VARCHAR(200) NOT NULL,
                city VARCHAR(100) NOT NULL,
                type VARCHAR(100),
                rating DECIMAL(3, 2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  ✓ Places table")
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                full_name VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)
        print("  ✓ Users table")
        
        # Trip history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trip_history (
                trip_id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
                source_city VARCHAR(100) NOT NULL,
                destination_city VARCHAR(100) NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                duration_days INTEGER,
                total_budget DECIMAL(10, 2),
                selected_flight_id VARCHAR(20),
                selected_hotel_id VARCHAR(20),
                itinerary_json TEXT,
                agent_response TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  ✓ Trip history table")
        
        # Create indexes
        print("\n📊 Creating indexes...")
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_flights_route 
            ON flights(from_city, to_city, price)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_hotels_city 
            ON hotels(city, price_per_night, stars)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_places_city 
            ON places(city, type, rating)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_email 
            ON users(email)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_username 
            ON users(username)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_trip_history_user 
            ON trip_history(user_id, created_at DESC)
        """)
        
        print("  ✓ All indexes created")
        
        conn.commit()
        print("\n✅ Schema created successfully")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error creating schema: {e}")
        raise
    finally:
        cursor.close()


def load_json_data(conn, data_dir='data'):
    """Load data from JSON files into database"""
    cursor = conn.cursor()
    
    try:
        # Load flights
        flights_file = os.path.join(data_dir, 'flights.json')
        if os.path.exists(flights_file):
            print(f"\n✈️  Loading flights from {flights_file}...")
            with open(flights_file, 'r', encoding='utf-8') as f:
                flights = json.load(f)
                
                loaded = 0
                for flight in flights:
                    try:
                        cursor.execute("""
                            INSERT INTO flights 
                            (flight_id, airline, from_city, to_city, 
                             departure_time, arrival_time, price)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (flight_id) DO NOTHING
                        """, (
                            flight['flight_id'],
                            flight['airline'],
                            flight['from'],
                            flight['to'],
                            flight.get('departure_time'),
                            flight.get('arrival_time'),
                            flight['price']
                        ))
                        loaded += 1
                    except Exception as e:
                        print(f"  ⚠️  Skipped flight {flight.get('flight_id')}: {e}")
                
                conn.commit()
                print(f"  ✓ Loaded {loaded}/{len(flights)} flights")
        else:
            print(f"\n⚠️  File not found: {flights_file}")
        
        # Load hotels
        hotels_file = os.path.join(data_dir, 'hotels.json')
        if os.path.exists(hotels_file):
            print(f"\n🏨  Loading hotels from {hotels_file}...")
            with open(hotels_file, 'r', encoding='utf-8') as f:
                hotels = json.load(f)
                
                loaded = 0
                for hotel in hotels:
                    try:
                        amenities_str = json.dumps(hotel.get('amenities', []))
                        cursor.execute("""
                            INSERT INTO hotels 
                            (hotel_id, name, city, stars, price_per_night, amenities)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (hotel_id) DO NOTHING
                        """, (
                            hotel['hotel_id'],
                            hotel['name'],
                            hotel['city'],
                            hotel.get('stars'),
                            hotel['price_per_night'],
                            amenities_str
                        ))
                        loaded += 1
                    except Exception as e:
                        print(f"  ⚠️  Skipped hotel {hotel.get('hotel_id')}: {e}")
                
                conn.commit()
                print(f"  ✓ Loaded {loaded}/{len(hotels)} hotels")
        else:
            print(f"\n⚠️  File not found: {hotels_file}")
        
        # Load places
        places_file = os.path.join(data_dir, 'places.json')
        if os.path.exists(places_file):
            print(f"\n🗺️  Loading places from {places_file}...")
            with open(places_file, 'r', encoding='utf-8') as f:
                places = json.load(f)
                
                loaded = 0
                for place in places:
                    try:
                        cursor.execute("""
                            INSERT INTO places 
                            (place_id, name, city, type, rating)
                            VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT (place_id) DO NOTHING
                        """, (
                            place['place_id'],
                            place['name'],
                            place['city'],
                            place.get('type'),
                            place.get('rating')
                        ))
                        loaded += 1
                    except Exception as e:
                        print(f"  ⚠️  Skipped place {place.get('place_id')}: {e}")
                
                conn.commit()
                print(f"  ✓ Loaded {loaded}/{len(places)} places")
        else:
            print(f"\n⚠️  File not found: {places_file}")
        
        print("\n✅ All data loaded successfully")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error loading data: {e}")
        raise
    finally:
        cursor.close()


def get_database_stats(conn):
    """Display database statistics"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        print("\n" + "=" * 60)
        print("📊 Database Statistics")
        print("=" * 60)
        
        # Flights
        cursor.execute("SELECT COUNT(*) as count FROM flights")
        flights_count = cursor.fetchone()['count']
        print(f"  ✈️  Flights: {flights_count}")
        
        # Hotels
        cursor.execute("SELECT COUNT(*) as count FROM hotels")
        hotels_count = cursor.fetchone()['count']
        print(f"  🏨  Hotels: {hotels_count}")
        
        # Places
        cursor.execute("SELECT COUNT(*) as count FROM places")
        places_count = cursor.fetchone()['count']
        print(f"  🗺️  Places: {places_count}")
        
        # Users
        cursor.execute("SELECT COUNT(*) as count FROM users")
        users_count = cursor.fetchone()['count']
        print(f"  👤  Users: {users_count}")
        
        # Trips
        cursor.execute("SELECT COUNT(*) as count FROM trip_history")
        trips_count = cursor.fetchone()['count']
        print(f"  📝  Trips: {trips_count}")
        
        # Cities
        cursor.execute("SELECT COUNT(DISTINCT city) as count FROM hotels")
        cities_count = cursor.fetchone()['count']
        print(f"  🌆  Cities: {cities_count}")
        
        # Routes
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM (SELECT DISTINCT from_city, to_city FROM flights) as routes
        """)
        routes_count = cursor.fetchone()['count']
        print(f"  🛫  Flight Routes: {routes_count}")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error getting stats: {e}")
    finally:
        cursor.close()


def verify_data(conn):
    """Verify loaded data with samples"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        print("\n🔍 Verifying data...")
        
        # Sample flight
        cursor.execute("SELECT * FROM flights LIMIT 1")
        flight = cursor.fetchone()
        if flight:
            print(f"\n✓ Sample Flight:")
            print(f"  {flight['airline']} - {flight['from_city']} → {flight['to_city']}")
            print(f"  Price: ₹{flight['price']}")
        else:
            print("\n⚠️  No flights in database")
        
        # Sample hotel
        cursor.execute("SELECT * FROM hotels LIMIT 1")
        hotel = cursor.fetchone()
        if hotel:
            print(f"\n✓ Sample Hotel:")
            print(f"  {hotel['name']} - {hotel['city']}")
            print(f"  {hotel['stars']}★ - ₹{hotel['price_per_night']}/night")
        else:
            print("\n⚠️  No hotels in database")
        
        # Sample place
        cursor.execute("SELECT * FROM places LIMIT 1")
        place = cursor.fetchone()
        if place:
            print(f"\n✓ Sample Place:")
            print(f"  {place['name']} - {place['city']}")
            print(f"  {place['type']} - {place['rating']}★")
        else:
            print("\n⚠️  No places in database")
        
        print("\n✅ Data verification complete")
        
    except Exception as e:
        print(f"\n❌ Verification error: {e}")
    finally:
        cursor.close()


def main():
    """Main initialization flow"""
    print("=" * 60)
    print("🚀 Lumina Travel Planner - Cloud Database Setup")
    print("=" * 60)
    
    # Validate configuration
    is_valid, errors = Config.validate()
    if not is_valid:
        print("\n❌ Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        print("\n💡 Fix configuration in .streamlit/secrets.toml or .env")
        return
    
    print("\n✅ Configuration validated")
    
    # Connect to database
    conn = connect_to_database()
    if not conn:
        return
    
    try:
        # Create schema
        create_tables(conn)
        
        # Ask if user wants to load data
        print("\n" + "=" * 60)
        load_data = input("📥 Load sample data from JSON files? (y/n): ").lower().strip()
        
        if load_data == 'y':
            load_json_data(conn)
            verify_data(conn)
        else:
            print("\n⏭️  Skipping data load")
        
        # Show stats
        get_database_stats(conn)
        
        print("\n" + "=" * 60)
        print("✅ Database initialization complete!")
        print("=" * 60)
        print("\n🎉 Next steps:")
        print("  1. Test locally: streamlit run app.py")
        print("  2. Push to GitHub")
        print("  3. Deploy on Streamlit Cloud")
        print("  4. Add secrets in Streamlit Cloud settings")
        print("\n📚 Your app will be live at: https://your-app-name.streamlit.app")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
    finally:
        if conn:
            conn.close()
            print("\n🔌 Database connection closed")


if __name__ == "__main__":
    main()
