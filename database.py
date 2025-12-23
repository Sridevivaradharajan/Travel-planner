"""
PostgreSQL Database Integration for Travel Planner
Handles data storage, retrieval, and user trip history using PostgreSQL
Works with Streamlit Cloud secrets AND local environment
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import sql
import json
from datetime import datetime
from typing import List, Dict, Optional
import os

class TravelDatabase:
    """
    Manages PostgreSQL database operations for the Travel Planner application.
    """
    def __init__(self):
        """Initialize with Streamlit secrets (cloud) or environment variables (local)"""
    
        # 1️⃣ Try Streamlit Cloud secrets first
        try:
            import streamlit as st
            if "neon" in st.secrets:
                cfg = st.secrets["neon"]
                self.host = cfg["host"]
                self.port = cfg["port"]
                self.database = cfg["database"]
                self.user = cfg["user"]
                self.password = cfg["password"]
                self.sslmode = cfg.get("sslmode", "require")
                print("📡 Using Streamlit Cloud Neon configuration")
            else:
                raise KeyError
        except Exception:
            # 2️⃣ Fallback to local .env / environment variables
            self.host = os.getenv("DB_HOST")
            self.port = os.getenv("DB_PORT", "5432")
            self.database = os.getenv("DB_NAME")
            self.user = os.getenv("DB_USER")
            self.password = os.getenv("DB_PASSWORD")
            self.sslmode = os.getenv("DB_SSLMODE", "require")
            print("💻 Using local environment variables for database")
    
        # 3️⃣ Validate configuration
        if not all([self.host, self.database, self.user, self.password]):
            raise RuntimeError("❌ Database configuration is incomplete")
    
        self.conn = None
        self.cursor = None
    
        self._connect()
        self._create_tables()
        
    def _connect(self):
        """Establish PostgreSQL database connection with SSL for cloud"""
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                sslmode=self.sslmode,
                connect_timeout=10  # Add timeout
            )
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            print(f"✅ Connected to PostgreSQL database: {self.database}")
        except psycopg2.OperationalError as e:
            print(f"❌ Database connection failed!")
            print(f"Host: {self.host}")
            print(f"Port: {self.port}")
            print(f"Database: {self.database}")
            print(f"User: {self.user}")
            print(f"Error: {str(e)}")
            raise Exception(f"PostgreSQL connection error: {str(e)}\n"
                          f"Check your database credentials and network connection.")
        except Exception as e:
            raise Exception(f"Unexpected database error: {str(e)}")
    
    def _create_tables(self):
        """Create database tables"""
        try:
            # Flights table
            self.cursor.execute("""
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
            
            # Hotels table
            self.cursor.execute("""
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
            
            # Places table
            self.cursor.execute("""
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
            
            # Trip history table - UPDATED to use INTEGER user_id
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS trip_history (
                    trip_id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
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
            
            # Create indexes
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_flights_route 
                ON flights(from_city, to_city, price)
            """)
            
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_hotels_city 
                ON hotels(city, price_per_night, stars)
            """)
            
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_places_city 
                ON places(city, type, rating)
            """)
            
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_trip_user 
                ON trip_history(user_id, created_at DESC)
            """)
            
            self.conn.commit()
            print("✅ Database tables created/verified successfully")
            
        except psycopg2.Error as e:
            self.conn.rollback()
            print(f"⚠️ Error creating tables: {str(e)}")
    
    def load_json_data_to_db(self, flights_file: str, hotels_file: str, places_file: str):
        """Load data from JSON files into PostgreSQL database"""
        try:
            # Load and insert flights
            if os.path.exists(flights_file):
                with open(flights_file, 'r', encoding='utf-8') as f:
                    flights = json.load(f)
                    print(f"📥 Loading {len(flights)} flights...")
                    for flight in flights:
                        self.insert_flight(flight)
                    self.conn.commit()
                    print(f"✅ {len(flights)} flights loaded")
            
            # Load and insert hotels
            if os.path.exists(hotels_file):
                with open(hotels_file, 'r', encoding='utf-8') as f:
                    hotels = json.load(f)
                    print(f"📥 Loading {len(hotels)} hotels...")
                    for hotel in hotels:
                        self.insert_hotel(hotel)
                    self.conn.commit()
                    print(f"✅ {len(hotels)} hotels loaded")
            
            # Load and insert places
            if os.path.exists(places_file):
                with open(places_file, 'r', encoding='utf-8') as f:
                    places = json.load(f)
                    print(f"📥 Loading {len(places)} places...")
                    for place in places:
                        self.insert_place(place)
                    self.conn.commit()
                    print(f"✅ {len(places)} places loaded")
            
            print("✅ All data successfully loaded into PostgreSQL database")
            
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Error loading JSON data: {str(e)}")
    
    def insert_flight(self, flight_data: Dict) -> Optional[int]:
        """Insert flight data into database"""
        try:
            self.cursor.execute("""
                INSERT INTO flights 
                (flight_id, airline, from_city, to_city, departure_time, arrival_time, price)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (flight_id) DO NOTHING
                RETURNING id
            """, (
                flight_data.get('flight_id'),
                flight_data.get('airline'),
                flight_data.get('from'),
                flight_data.get('to'),
                flight_data.get('departure_time'),
                flight_data.get('arrival_time'),
                flight_data.get('price')
            ))
            
            result = self.cursor.fetchone()
            return result['id'] if result else None
            
        except psycopg2.Error as e:
            print(f"Error inserting flight: {str(e)}")
            return None
    
    def insert_hotel(self, hotel_data: Dict) -> Optional[int]:
        """Insert hotel data into database"""
        try:
            amenities_str = json.dumps(hotel_data.get('amenities', []))
            
            self.cursor.execute("""
                INSERT INTO hotels 
                (hotel_id, name, city, stars, price_per_night, amenities)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (hotel_id) DO NOTHING
                RETURNING id
            """, (
                hotel_data.get('hotel_id'),
                hotel_data.get('name'),
                hotel_data.get('city'),
                hotel_data.get('stars'),
                hotel_data.get('price_per_night'),
                amenities_str
            ))
            
            result = self.cursor.fetchone()
            return result['id'] if result else None
            
        except psycopg2.Error as e:
            print(f"Error inserting hotel: {str(e)}")
            return None
    
    def insert_place(self, place_data: Dict) -> Optional[int]:
        """Insert place/POI data into database"""
        try:
            self.cursor.execute("""
                INSERT INTO places 
                (place_id, name, city, type, rating)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (place_id) DO NOTHING
                RETURNING id
            """, (
                place_data.get('place_id'),
                place_data.get('name'),
                place_data.get('city'),
                place_data.get('type'),
                place_data.get('rating')
            ))
            
            result = self.cursor.fetchone()
            return result['id'] if result else None
            
        except psycopg2.Error as e:
            print(f"Error inserting place: {str(e)}")
            return None
    
    def get_flights(self, source: str, destination: str, 
                    max_price: Optional[float] = None,
                    limit: int = 10) -> List[Dict]:
        """Query flights with filters"""
        try:
            query = """
                SELECT * FROM flights 
                WHERE LOWER(from_city) = LOWER(%s) 
                AND LOWER(to_city) = LOWER(%s)
            """
            params = [source, destination]
            
            if max_price:
                query += " AND price <= %s"
                params.append(max_price)
            
            query += " ORDER BY price ASC LIMIT %s"
            params.append(limit)
            
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()
            
            return [dict(row) for row in rows]
            
        except psycopg2.Error as e:
            print(f"Error querying flights: {str(e)}")
            return []
    
    def get_hotels(self, city: str, 
                   min_stars: int = 0,
                   max_price: Optional[float] = None,
                   amenities: Optional[List[str]] = None,
                   limit: int = 10) -> List[Dict]:
        """Query hotels with filters"""
        try:
            query = "SELECT * FROM hotels WHERE LOWER(city) = LOWER(%s) AND stars >= %s"
            params = [city, min_stars]
            
            if max_price:
                query += " AND price_per_night <= %s"
                params.append(max_price)
            
            query += " ORDER BY stars DESC, price_per_night ASC LIMIT %s"
            params.append(limit)
            
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()
            
            hotels = [dict(row) for row in rows]
            
            # Filter by amenities if provided
            if amenities:
                filtered_hotels = []
                for hotel in hotels:
                    hotel_amenities_str = hotel.get('amenities', '[]')
                    try:
                        hotel_amenities = json.loads(hotel_amenities_str)
                    except:
                        hotel_amenities = []
                    
                    if any(amenity.strip().lower() in [a.strip().lower() 
                           for a in hotel_amenities] for amenity in amenities):
                        filtered_hotels.append(hotel)
                
                return filtered_hotels[:limit]
            
            return hotels
            
        except psycopg2.Error as e:
            print(f"Error querying hotels: {str(e)}")
            return []
    
    def get_places(self, city: str, 
                   place_type: Optional[str] = None,
                   min_rating: float = 0,
                   limit: int = 20) -> List[Dict]:
        """Query places/attractions with filters"""
        try:
            query = "SELECT * FROM places WHERE LOWER(city) = LOWER(%s) AND rating >= %s"
            params = [city, min_rating]
            
            if place_type:
                query += " AND LOWER(type) LIKE LOWER(%s)"
                params.append(f"%{place_type}%")
            
            query += " ORDER BY rating DESC LIMIT %s"
            params.append(limit)
            
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()
            
            return [dict(row) for row in rows]
            
        except psycopg2.Error as e:
            print(f"Error querying places: {str(e)}")
            return []
    
    def save_user_trip(self, user_id: int, trip_data: Dict) -> Optional[int]:
        """Save trip for specific user"""
        try:
            self.cursor.execute("""
                INSERT INTO trip_history 
                (user_id, source_city, destination_city, start_date, end_date,
                 duration_days, total_budget, itinerary_json, agent_response)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING trip_id
            """, (
                user_id,
                trip_data.get('source_city'),
                trip_data.get('destination_city'),
                trip_data.get('start_date'),
                trip_data.get('end_date'),
                trip_data.get('duration_days'),
                trip_data.get('total_budget'),
                json.dumps(trip_data.get('itinerary', {})),
                trip_data.get('agent_response', '')
            ))
            
            self.conn.commit()
            result = self.cursor.fetchone()
            return result['trip_id'] if result else None
            
        except psycopg2.Error as e:
            self.conn.rollback()
            print(f"Error saving user trip: {str(e)}")
            return None
    
    def get_user_trips(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get trips for specific user"""
        try:
            self.cursor.execute("""
                SELECT * FROM trip_history 
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (user_id, limit))
            
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
            
        except psycopg2.Error as e:
            print(f"Error retrieving user trips: {str(e)}")
            return []
    
    def get_database_stats(self) -> Dict:
        """Get statistics about the database"""
        try:
            stats = {}
            
            self.cursor.execute("SELECT COUNT(*) as count FROM flights")
            stats['total_flights'] = self.cursor.fetchone()['count']
            
            self.cursor.execute("SELECT COUNT(*) as count FROM hotels")
            stats['total_hotels'] = self.cursor.fetchone()['count']
            
            self.cursor.execute("SELECT COUNT(*) as count FROM places")
            stats['total_places'] = self.cursor.fetchone()['count']
            
            self.cursor.execute("SELECT COUNT(*) as count FROM trip_history")
            stats['total_trips'] = self.cursor.fetchone()['count']
            
            self.cursor.execute("SELECT COUNT(DISTINCT city) as count FROM hotels")
            stats['total_cities'] = self.cursor.fetchone()['count']
            
            return stats
            
        except psycopg2.Error as e:
            print(f"Error getting stats: {str(e)}")
            return {}
        
    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            print("Database connection closed")
    
    def __del__(self):
        """Destructor to ensure connection is closed"""
        try:
            self.close()
        except:
            pass


if __name__ == "__main__":
    print("✅ Database module loaded successfully")
