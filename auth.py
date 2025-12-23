"""
User Authentication System
Handles user registration, login, and session management
"""
import streamlit as st
import bcrypt
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import Optional, Dict, Tuple

class UserAuth:
    """Handle user authentication and session management"""
    
    def __init__(self, db_connection):
        """Initialize with database connection"""
        self.conn = db_connection
        self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        self._create_user_tables()
    
    def _create_user_tables(self):
        """Create user-related tables"""
        try:
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
            
            # Create index on email and username
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)
            """)
            
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)
            """)
            
            self.conn.commit()
            print("✅ User authentication tables ready")
            
        except psycopg2.Error as e:
            self.conn.rollback()
            print(f"⚠️  User tables note: {e}")
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception as e:
            print(f"Password verification error: {e}")
            return False
    
    def register(self, username: str, email: str, password: str, full_name: str = "") -> Tuple[bool, str]:
        """
        Register new user
        Returns: (success: bool, message: str)
        """
        try:
            # Validate inputs
            if len(username) < 3:
                return False, "Username must be at least 3 characters"
            
            if len(password) < 6:
                return False, "Password must be at least 6 characters"
            
            if '@' not in email:
                return False, "Invalid email format"
            
            # Hash password
            password_hash = self.hash_password(password)
            
            # Insert user
            self.cursor.execute("""
                INSERT INTO users (username, email, password_hash, full_name)
                VALUES (%s, %s, %s, %s)
                RETURNING user_id
            """, (username.lower(), email.lower(), password_hash, full_name))
            
            result = self.cursor.fetchone()
            self.conn.commit()
            
            return True, f"Account created successfully! User ID: {result['user_id']}"
            
        except psycopg2.IntegrityError as e:
            self.conn.rollback()
            if 'username' in str(e).lower():
                return False, "Username already exists"
            elif 'email' in str(e).lower():
                return False, "Email already registered"
            else:
                return False, "Registration failed"
                
        except Exception as e:
            self.conn.rollback()
            print(f"Registration error: {e}")
            return False, "Registration failed. Please try again."
    
    def login(self, email_or_username: str, password: str) -> Optional[Dict]:
        """
        Authenticate user
        Returns: User dict if successful, None if failed
        """
        try:
            # Try login with email or username
            self.cursor.execute("""
                SELECT user_id, username, email, password_hash, full_name, created_at
                FROM users
                WHERE (LOWER(email) = LOWER(%s) OR LOWER(username) = LOWER(%s))
                AND is_active = TRUE
            """, (email_or_username, email_or_username))
            
            user = self.cursor.fetchone()
            
            if not user:
                return None
            
            # Verify password
            if self.verify_password(password, user['password_hash']):
                # Update last login
                self.cursor.execute("""
                    UPDATE users 
                    SET last_login = CURRENT_TIMESTAMP
                    WHERE user_id = %s
                """, (user['user_id'],))
                self.conn.commit()
                
                # Return user data (without password hash)
                return {
                    'user_id': user['user_id'],
                    'username': user['username'],
                    'email': user['email'],
                    'full_name': user['full_name'],
                    'created_at': user['created_at']
                }
            
            return None
            
        except Exception as e:
            print(f"Login error: {e}")
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user information by ID"""
        try:
            self.cursor.execute("""
                SELECT user_id, username, email, full_name, created_at, last_login
                FROM users
                WHERE user_id = %s AND is_active = TRUE
            """, (user_id,))
            
            user = self.cursor.fetchone()
            return dict(user) if user else None
            
        except Exception as e:
            print(f"Error fetching user: {e}")
            return None
    
    def update_profile(self, user_id: int, full_name: str = None, email: str = None) -> bool:
        """Update user profile"""
        try:
            updates = []
            params = []
            
            if full_name:
                updates.append("full_name = %s")
                params.append(full_name)
            
            if email:
                updates.append("email = %s")
                params.append(email.lower())
            
            if not updates:
                return False
            
            params.append(user_id)
            query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = %s"
            
            self.cursor.execute(query, params)
            self.conn.commit()
            
            return True
            
        except psycopg2.IntegrityError:
            self.conn.rollback()
            return False
        except Exception as e:
            self.conn.rollback()
            print(f"Update error: {e}")
            return False
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> Tuple[bool, str]:
        """Change user password"""
        try:
            # Verify old password
            self.cursor.execute("""
                SELECT password_hash FROM users WHERE user_id = %s
            """, (user_id,))
            
            result = self.cursor.fetchone()
            if not result:
                return False, "User not found"
            
            if not self.verify_password(old_password, result['password_hash']):
                return False, "Current password is incorrect"
            
            # Validate new password
            if len(new_password) < 6:
                return False, "New password must be at least 6 characters"
            
            # Update password
            new_hash = self.hash_password(new_password)
            self.cursor.execute("""
                UPDATE users SET password_hash = %s WHERE user_id = %s
            """, (new_hash, user_id))
            
            self.conn.commit()
            return True, "Password changed successfully"
            
        except Exception as e:
            self.conn.rollback()
            print(f"Password change error: {e}")
            return False, "Failed to change password"
    
    def get_user_stats(self, user_id: int) -> Dict:
        """Get user statistics"""
        try:
            stats = {}
            
            # Total trips
            self.cursor.execute("""
                SELECT COUNT(*) as count FROM trip_history WHERE user_id = %s
            """, (user_id,))
            stats['total_trips'] = self.cursor.fetchone()['count']
            
            # Most visited destination
            self.cursor.execute("""
                SELECT destination_city, COUNT(*) as visits
                FROM trip_history
                WHERE user_id = %s
                GROUP BY destination_city
                ORDER BY visits DESC
                LIMIT 1
            """, (user_id,))
            
            result = self.cursor.fetchone()
            stats['favorite_destination'] = result['destination_city'] if result else "None"
            stats['destination_visits'] = result['visits'] if result else 0
            
            # Total budget spent
            self.cursor.execute("""
                SELECT COALESCE(SUM(total_budget), 0) as total
                FROM trip_history
                WHERE user_id = %s AND total_budget IS NOT NULL
            """, (user_id,))
            
            stats['total_spent'] = float(self.cursor.fetchone()['total'])
            
            return stats
            
        except Exception as e:
            print(f"Stats error: {e}")
            return {
                'total_trips': 0,
                'favorite_destination': 'None',
                'destination_visits': 0,
                'total_spent': 0
            }


def init_session_state():
    """Initialize session state for authentication"""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'auth' not in st.session_state:
        st.session_state.auth = None


def logout():
    """Logout user and clear session"""
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.chat_history = []
    st.session_state.trip_data = None
    st.session_state.ai_response = None
    st.session_state.form_data = {}


if __name__ == "__main__":
    print("✅ Auth module loaded successfully")
