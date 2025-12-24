"""
PostgreSQL Database Integration for Travel Planner
Cloud-safe (Streamlit) + Local-safe (.env)
FIXED: Better error handling and secrets validation
"""

import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict


# ======================================================
# STREAMLIT DETECTION
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
        """
        self.conn = None
        self.cursor = None
        
        print("🔧 [DATABASE] Initializing...")
        
        try:
            self._load_config()
            print("✅ [DATABASE] Config loaded successfully")
            
            self.connect()
            print("✅ [DATABASE] Connected successfully")
            
            self.ensure_tables()
            print("✅ [DATABASE] All tables verified")
            
        except Exception as e:
            print(f"❌ [DATABASE] Initialization failed: {e}")
            import traceback
            traceback.print_exc()
            raise

    # ======================================================
    # CONFIG
    # ======================================================
    def _load_config(self):
        if is_streamlit():
            import streamlit as st
            
            print("🔍 [DATABASE] Checking Streamlit secrets...")
            
            if not hasattr(st, 'secrets'):
                raise RuntimeError("❌ Streamlit secrets not available")
            
            if 'neon' not in st.secrets:
                raise RuntimeError("❌ [neon] section missing in secrets. Please add it in Streamlit Cloud Settings → Secrets")
            
            cfg = st.secrets["neon"]
            
            # Validate all required fields
            required_fields = ['host', 'database', 'user', 'password']
            missing = [f for f in required_fields if not cfg.get(f)]
            
            if missing:
                raise RuntimeError(f"❌ Missing required secrets: {', '.join(missing)}")

            self.host = cfg.get("host")
            self.port = cfg.get("port", 5432)
            self.database = cfg.get("database")
            self.user = cfg.get("user")
            self.password = cfg.get("password")
            self.sslmode = cfg.get("sslmode", "require")
            
            print(f"✅ [DATABASE] Secrets loaded:")
            print(f"   Host: {self.host}")
            print(f"   Database: {self.database}")
            print(f"   User: {self.user}")
            print(f"   Port: {self.port}")
            print(f"   SSL: {self.sslmode}")

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
                raise RuntimeError("❌ Missing local DB environment variables in .env")

            print(f"✅ [DATABASE] Local config loaded → {self.database}")

    # ======================================================
    # CONNECTION
    # ======================================================
    def connect(self):
        """Connect to database if not already connected"""
        if self.conn:
            # Check if connection is still alive
            try:
                with self.conn.cursor() as test_cursor:
                    test_cursor.execute("SELECT 1")
                print("✅ [DATABASE] Connection is healthy")
                return
            except:
                print("⚠️  [DATABASE] Connection dead, reconnecting...")
                self.conn = None
                self.cursor = None

        try:
            print(f"🔌 [DATABASE] Connecting to {self.host}...")
            
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                sslmode=self.sslmode,
                connect_timeout=10,
            )
            
            self.conn.autocommit = False
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            
            print(f"✅ [DATABASE] Successfully connected to {self.database}")
            
        except psycopg2.OperationalError as e:
            error_msg = str(e)
            print(f"❌ [DATABASE] Connection failed: {error_msg}")
            
            # Provide helpful error messages
            if "password authentication failed" in error_msg:
                print("   → Check: Password is correct")
            elif "could not translate host name" in error_msg:
                print("   → Check: Host address is correct")
            elif "timeout" in error_msg:
                print("   → Check: Network connection / Firewall")
            elif "no such host" in error_msg:
                print("   → Check: Host address spelling")
            
            raise RuntimeError(f"Database connection failed: {error_msg}")
            
        except Exception as e:
            print(f"❌ [DATABASE] Unexpected connection error: {e}")
            raise

    # ======================================================
    # TABLE CREATION
    # ======================================================
    def ensure_tables(self):
        """Ensure all required tables exist"""
        if not self.conn:
            self.connect()

        try:
            print("🔧 [DATABASE] Creating tables...")
            
            # Users table
            self.cursor.execute("""
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

            # Trip history table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS trip_history (
                    trip_id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
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
            
            # Create indexes
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_trip_history_user ON trip_history(user_id)")

            self.conn.commit()
            print("✅ [DATABASE] All tables created/verified")

        except Exception as e:
            print(f"❌ [DATABASE] Table creation failed: {e}")
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
        except Exception as e:
            print(f"⚠️  [DATABASE] Stats error: {e}")
            return {'total_flights': 0, 'total_hotels': 0, 'total_places': 0}

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
            print(f"✅ [DATABASE] Trip saved for user {user_id}")
            return True

        except Exception as e:
            self.conn.rollback()
            print(f"❌ [DATABASE] Save trip failed: {e}")
            return False

    # ======================================================
    # CONNECTION HEALTH
    # ======================================================
    def is_connected(self) -> bool:
        """Check if database is connected and healthy"""
        if not self.conn:
            return False
        try:
            with self.conn.cursor() as test_cursor:
                test_cursor.execute("SELECT 1")
            return True
        except:
            return False

    # ======================================================
    # CLOSE
    # ======================================================
    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
            self.cursor = None
        if self.conn:
            self.conn.close()
            self.conn = None
            print("🔒 [DATABASE] Connection closed")

    def __del__(self):
        """Cleanup on object destruction"""
        try:
            self.close()
        except:
            pass
