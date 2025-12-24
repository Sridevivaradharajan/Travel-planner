"""
PostgreSQL Database Integration for Travel Planner
Cloud-safe (Streamlit) + Local-safe (.env)
FIXED: Auto-connect on initialization
"""

import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict


# ======================================================
# STREAMLIT DETECTION (CORRECT WAY)
# ======================================================
def is_streamlit():
    try:
        import streamlit as st
        return hasattr(st, "secrets")
    except Exception:
        return False


# ======================================================
# DATABASE CLASS
# ======================================================
class TravelDatabase:
    def __init__(self):
        """
        Load configuration AND connect immediately.
        ✅ This ensures db.conn is available for auth system
        """
        self.conn = None
        self.cursor = None
        self._load_config()
        self.connect()  # ✅ ADDED: Connect immediately
        self.ensure_tables()  # ✅ ADDED: Ensure tables exist

    # ======================================================
    # CONFIG
    # ======================================================
    def _load_config(self):
        if is_streamlit():
            import streamlit as st
            cfg = st.secrets["neon"]

            self.host = cfg["host"]
            self.port = cfg.get("port", 5432)
            self.database = cfg["database"]
            self.user = cfg["user"]
            self.password = cfg["password"]
            self.sslmode = cfg.get("sslmode", "require")

            print("✅ Using Streamlit Cloud secrets")

        else:
            from dotenv import load_dotenv
            load_dotenv()
            
            self.host = os.getenv("DB_HOST")
            self.port = os.getenv("DB_PORT", "5432")
            self.database = os.getenv("DB_NAME")
            self.user = os.getenv("DB_USER")
            self.password = os.getenv("DB_PASSWORD")
            self.sslmode = os.getenv("DB_SSLMODE", "require")

            if not all([self.host, self.database, self.user, self.password]):
                raise RuntimeError("❌ Missing local DB environment variables")

            print("✅ Using local .env configuration")

    # ======================================================
    # CONNECTION
    # ======================================================
    def connect(self):
        """Connect to database if not already connected"""
        if self.conn:
            # Check if connection is still alive
            try:
                self.cursor.execute("SELECT 1")
                return  # Connection is healthy
            except:
                # Connection is dead, reconnect
                self.conn = None
                self.cursor = None

        try:
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                sslmode=self.sslmode,
                connect_timeout=10,  # Increased timeout for cloud
            )
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            print(f"✅ Connected to PostgreSQL → {self.database}")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            raise

    # ======================================================
    # TABLE CREATION
    # ======================================================
    def ensure_tables(self):
        """Ensure all required tables exist"""
        if not self.conn:
            self.connect()

        try:
            # Users table for authentication
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    full_name VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Flights table
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

            # Hotels table
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

            # Places table
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

            # Trip history table (with user_id foreign key)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS trip_history (
                    trip_id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(user_id),
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
            print("✅ All tables verified/created")

        except Exception as e:
            print(f"❌ Table creation failed: {e}")
            self.conn.rollback()
            raise

    # ======================================================
    # QUERY METHODS
    # ======================================================
    def get_flights(self, from_city: str, to_city: str, limit: int = 10) -> List[Dict]:
        """Get flights between two cities"""
        if not self.conn:
            self.connect()
            
        self.cursor.execute("""
            SELECT * FROM flights
            WHERE LOWER(from_city) = LOWER(%s)
            AND LOWER(to_city) = LOWER(%s)
            ORDER BY price ASC
            LIMIT %s
        """, (from_city, to_city, limit))
        return [dict(row) for row in self.cursor.fetchall()]

    def get_hotels(self, city: str, min_stars: int = 0, max_price=None, limit: int = 10) -> List[Dict]:
        """Get hotels in a city with optional filters"""
        if not self.conn:
            self.connect()

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

    def get_places(self, city: str, min_rating: float = 0, limit: int = 20) -> List[Dict]:
        """Get places to visit in a city"""
        if not self.conn:
            self.connect()
            
        self.cursor.execute("""
            SELECT * FROM places
            WHERE LOWER(city) = LOWER(%s)
            AND rating >= %s
            ORDER BY rating DESC
            LIMIT %s
        """, (city, min_rating, limit))
        return [dict(row) for row in self.cursor.fetchall()]

    def get_database_stats(self) -> Dict:
        """Get statistics about the database"""
        if not self.conn:
            self.connect()
            
        try:
            self.cursor.execute("SELECT COUNT(*) as count FROM flights")
            total_flights = self.cursor.fetchone()['count']
            
            self.cursor.execute("SELECT COUNT(*) as count FROM hotels")
            total_hotels = self.cursor.fetchone()['count']
            
            self.cursor.execute("SELECT COUNT(*) as count FROM places")
            total_places = self.cursor.fetchone()['count']
            
            return {
                'total_flights': total_flights,
                'total_hotels': total_hotels,
                'total_places': total_places
            }
        except:
            return {'total_flights': 0, 'total_hotels': 0, 'total_places': 0}

    # ======================================================
    # SAVE TRIP
    # ======================================================
    def save_user_trip(self, user_id: int, trip_data: dict) -> bool:
        """Save a trip for a specific user"""
        if not self.conn:
            self.connect()

        try:
            self.cursor.execute("""
                INSERT INTO trip_history (
                    user_id, source_city, destination_city,
                    start_date, end_date, duration_days,
                    total_budget, itinerary_json, agent_response
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                user_id,
                trip_data.get("source_city"),
                trip_data.get("destination_city"),
                trip_data.get("start_date"),
                trip_data.get("end_date"),
                trip_data.get("duration_days"),
                trip_data.get("total_budget"),
                json.dumps(trip_data.get("itinerary")),
                trip_data.get("agent_response")
            ))

            self.conn.commit()
            print(f"✅ Trip saved for user {user_id}")
            return True

        except Exception as e:
            self.conn.rollback()
            print(f"❌ Save trip failed: {e}")
            return False

    # ======================================================
    # CLOSE
    # ======================================================
    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            print("🔒 DB connection closed")

    def __del__(self):
        """Cleanup on object destruction"""
        self.close()
