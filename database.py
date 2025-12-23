"""
PostgreSQL Database Integration for Travel Planner
Works locally (.env) and on Streamlit Cloud (secrets.toml)
"""
import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Optional


class TravelDatabase:
    def __init__(self):
        """
        Priority:
        1. Streamlit Cloud secrets (only when running on Streamlit)
        2. Local .env environment variables
        """
        # Detect Streamlit runtime
        RUNNING_STREAMLIT = os.getenv("STREAMLIT_RUNTIME") == "true"

        # ==========================
        # STREAMLIT CLOUD
        # ==========================
        if RUNNING_STREAMLIT:
            try:
                import streamlit as st
                cfg = st.secrets["neon"]

                self.host = cfg["host"]
                self.port = cfg["port"]
                self.database = cfg["database"]
                self.user = cfg["user"]
                self.password = cfg["password"]
                self.sslmode = cfg.get("sslmode", "require")

                print("📡 Using Streamlit Cloud secrets")

            except Exception as e:
                raise RuntimeError(f"Streamlit secrets error: {e}")

        # ==========================
        # LOCAL (.env)
        # ==========================
        else:
            self.host = os.getenv("DB_HOST")
            self.port = os.getenv("DB_PORT", "5432")
            self.database = os.getenv("DB_NAME")
            self.user = os.getenv("DB_USER")
            self.password = os.getenv("DB_PASSWORD")
            self.sslmode = os.getenv("DB_SSLMODE", "require")

            if not all([self.host, self.database, self.user, self.password]):
                raise RuntimeError(
                    "Missing database environment variables. "
                    "Check your .env file."
                )

            print("💻 Using local .env configuration")

        self.conn = None
        self.cursor = None
        self._connect()
        self._create_tables()

    # ======================================================
    # CONNECTION
    # ======================================================
    def _connect(self):
        self.conn = psycopg2.connect(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password,
            sslmode=self.sslmode,
            connect_timeout=10,
        )
        self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        print(f"✅ Connected to PostgreSQL → {self.database}")

    # ======================================================
    # TABLES
    # ======================================================
    def _create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS flights (
                id SERIAL PRIMARY KEY,
                flight_id VARCHAR(20) UNIQUE,
                airline VARCHAR(100),
                from_city VARCHAR(100),
                to_city VARCHAR(100),
                departure_time TIMESTAMP,
                arrival_time TIMESTAMP,
                price NUMERIC(10,2)
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS hotels (
                id SERIAL PRIMARY KEY,
                hotel_id VARCHAR(20) UNIQUE,
                name VARCHAR(200),
                city VARCHAR(100),
                stars INTEGER,
                price_per_night NUMERIC(10,2),
                amenities TEXT
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS places (
                id SERIAL PRIMARY KEY,
                place_id VARCHAR(20) UNIQUE,
                name VARCHAR(200),
                city VARCHAR(100),
                type VARCHAR(100),
                rating NUMERIC(3,2)
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS trip_history (
                trip_id SERIAL PRIMARY KEY,
                user_id INTEGER,
                source_city VARCHAR(100),
                destination_city VARCHAR(100),
                start_date DATE,
                end_date DATE,
                duration_days INTEGER,
                total_budget NUMERIC(10,2),
                itinerary_json TEXT,
                agent_response TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.conn.commit()
        print("✅ Tables verified")

    # ======================================================
    # DATA LOADERS
    # ======================================================
    def insert_flight(self, f: Dict):
        self.cursor.execute("""
            INSERT INTO flights (flight_id, airline, from_city, to_city, departure_time, arrival_time, price)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (flight_id) DO NOTHING
        """, (
            f["flight_id"], f["airline"], f["from"], f["to"],
            f.get("departure_time"), f.get("arrival_time"), f["price"]
        ))

    def insert_hotel(self, h: Dict):
        self.cursor.execute("""
            INSERT INTO hotels (hotel_id, name, city, stars, price_per_night, amenities)
            VALUES (%s,%s,%s,%s,%s,%s)
            ON CONFLICT (hotel_id) DO NOTHING
        """, (
            h["hotel_id"], h["name"], h["city"],
            h.get("stars"), h["price_per_night"],
            json.dumps(h.get("amenities", []))
        ))

    def insert_place(self, p: Dict):
        self.cursor.execute("""
            INSERT INTO places (place_id, name, city, type, rating)
            VALUES (%s,%s,%s,%s,%s)
            ON CONFLICT (place_id) DO NOTHING
        """, (
            p["place_id"], p["name"], p["city"],
            p.get("type"), p.get("rating")
        ))

    def load_json_data_to_db(self, flights_file, hotels_file, places_file):
        # Safely open files
        with open(flights_file, 'r', encoding='utf-8') as f:
            for flight in json.load(f):
                self.insert_flight(flight)

        with open(hotels_file, 'r', encoding='utf-8') as f:
            for hotel in json.load(f):
                self.insert_hotel(hotel)

        with open(places_file, 'r', encoding='utf-8') as f:
            for place in json.load(f):
                self.insert_place(place)

        self.conn.commit()
        print("✅ Data loaded")

    # ======================================================
    # QUERY METHODS (Required by agent.py)
    # ======================================================
    def get_flights(self, from_city: str, to_city: str, limit: int = 10) -> List[Dict]:
        """Get flights between two cities"""
        try:
            self.cursor.execute("""
                SELECT * FROM flights 
                WHERE LOWER(from_city) = LOWER(%s) 
                AND LOWER(to_city) = LOWER(%s)
                ORDER BY price ASC
                LIMIT %s
            """, (from_city, to_city, limit))
            return [dict(row) for row in self.cursor.fetchall()]
        except Exception as e:
            print(f"Error fetching flights: {e}")
            return []

    def get_hotels(self, city: str, min_stars: int = 0, max_price: float = None, limit: int = 10) -> List[Dict]:
        """Get hotels in a city"""
        try:
            query = """
                SELECT * FROM hotels 
                WHERE LOWER(city) = LOWER(%s)
                AND stars >= %s
            """
            params = [city, min_stars]
            
            if max_price:
                query += " AND price_per_night <= %s"
                params.append(max_price)
            
            query += " ORDER BY stars DESC, price_per_night ASC LIMIT %s"
            params.append(limit)
            
            self.cursor.execute(query, params)
            return [dict(row) for row in self.cursor.fetchall()]
        except Exception as e:
            print(f"Error fetching hotels: {e}")
            return []

    def get_places(self, city: str, min_rating: float = 0, limit: int = 20) -> List[Dict]:
        """Get tourist places in a city"""
        try:
            self.cursor.execute("""
                SELECT * FROM places 
                WHERE LOWER(city) = LOWER(%s)
                AND rating >= %s
                ORDER BY rating DESC
                LIMIT %s
            """, (city, min_rating, limit))
            return [dict(row) for row in self.cursor.fetchall()]
        except Exception as e:
            print(f"Error fetching places: {e}")
            return []

    # ======================================================
    # TRIP HISTORY - SAVE TO NEON DB
    # ======================================================
    def save_user_trip(self, user_id: int, trip_data: dict) -> bool:
        """
        Save trip to trip_history table in Neon DB
        """
        try:
            # Convert itinerary dict to JSON string
            itinerary_json = json.dumps(trip_data.get('itinerary')) if trip_data.get('itinerary') else None
            
            self.cursor.execute("""
                INSERT INTO trip_history (
                    user_id, 
                    source_city, 
                    destination_city, 
                    start_date, 
                    end_date, 
                    duration_days, 
                    total_budget, 
                    itinerary_json, 
                    agent_response
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING trip_id
            """, (
                user_id,
                trip_data.get('source_city'),
                trip_data.get('destination_city'),
                trip_data.get('start_date'),
                trip_data.get('end_date'),
                trip_data.get('duration_days'),
                trip_data.get('total_budget'),
                itinerary_json,
                trip_data.get('agent_response')
            ))
            
            result = self.cursor.fetchone()
            self.conn.commit()
            
            print(f"✅ Trip saved to Neon DB! Trip ID: {result['trip_id']}, User ID: {user_id}")
            return True
            
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Error saving trip to Neon: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_user_trips(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get all trips for a user"""
        try:
            self.cursor.execute("""
                SELECT * FROM trip_history 
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (user_id, limit))
            return [dict(row) for row in self.cursor.fetchall()]
        except Exception as e:
            print(f"Error fetching user trips: {e}")
            return []

    # ======================================================
    # DATABASE STATS
    # ======================================================
    def get_database_stats(self) -> Dict:
        stats = {}

        # Total rows in tables
        for table in ["flights", "hotels", "places", "trip_history"]:
            self.cursor.execute(f"SELECT COUNT(*) AS count FROM {table}")
            stats[table] = self.cursor.fetchone()['count']

        # Total distinct cities from hotels
        self.cursor.execute("SELECT COUNT(DISTINCT city) AS count FROM hotels")
        stats['total_cities'] = self.cursor.fetchone()['count']

        # Rename keys for display
        return {
            'total_flights': stats.get('flights', 0),
            'total_hotels': stats.get('hotels', 0),
            'total_places': stats.get('places', 0),
            'total_trips': stats.get('trip_history', 0),
            'total_cities': stats.get('total_cities', 0)
        }

    # ======================================================
    # CLOSE CONNECTION
    # ======================================================
    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            print("✅ Database connection closed")


# ======================================================
# TESTING
# ======================================================
if __name__ == "__main__":
    print("🧪 Testing TravelDatabase...")
    
    try:
        db = TravelDatabase()
        
        # Test stats
        stats = db.get_database_stats()
        print(f"\n📊 Database Stats: {stats}")
        
        # Test queries
        flights = db.get_flights("Mumbai", "Goa", limit=3)
        print(f"\n✈️ Found {len(flights)} flights Mumbai→Goa")
        
        hotels = db.get_hotels("Goa", min_stars=3, limit=3)
        print(f"🏨 Found {len(hotels)} hotels in Goa")
        
        places = db.get_places("Goa", min_rating=4.0, limit=5)
        print(f"📍 Found {len(places)} places in Goa")
        
        db.close()
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

✅ Trip saved to Neon DB! Trip ID: X, User ID: Y
