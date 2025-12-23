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
