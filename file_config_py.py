"""
Cloud Configuration Management
Automatically detects environment (local vs cloud) and loads appropriate configs
"""
import os
import streamlit as st

class Config:
    """Centralized configuration for cloud deployment"""
    
    @staticmethod
    def get_database_config():
        """
        Get database configuration from Streamlit secrets or environment variables
        Priority: Streamlit Cloud secrets > .env file
        """
        try:
            # Try Streamlit Cloud secrets first (when deployed)
            if hasattr(st, 'secrets') and 'database' in st.secrets:
                db = st.secrets['database']
                return {
                    'host': db['host'],
                    'port': int(db.get('port', 5432)),
                    'database': db['database'],
                    'user': db['user'],
                    'password': db['password'],
                    'sslmode': db.get('sslmode', 'require')
                }
            
            # Fallback to .env for local development
            from dotenv import load_dotenv
            load_dotenv()
            
            return {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': int(os.getenv('DB_PORT', 5432)),
                'database': os.getenv('DB_NAME', 'travel_planner'),
                'user': os.getenv('DB_USER', 'postgres'),
                'password': os.getenv('DB_PASSWORD', ''),
                'sslmode': os.getenv('DB_SSLMODE', 'prefer')
            }
            
        except Exception as e:
            print(f"❌ Config error: {e}")
            return None
    
    @staticmethod
    def get_google_api_key():
        """
        Get Google API key from Streamlit secrets or environment
        Priority: Streamlit Cloud secrets > .env file
        """
        try:
            # Try Streamlit Cloud secrets
            if hasattr(st, 'secrets') and 'api' in st.secrets:
                return st.secrets['api']['google_api_key']
            
            # Fallback to .env
            from dotenv import load_dotenv
            load_dotenv()
            return os.getenv('GOOGLE_API_KEY')
            
        except Exception as e:
            print(f"❌ API key error: {e}")
            return None
    
    @staticmethod
    def is_cloud():
        """Check if running on Streamlit Cloud"""
        return hasattr(st, 'secrets')
    
    @staticmethod
    def get_app_config():
        """Get application settings"""
        try:
            if hasattr(st, 'secrets') and 'app' in st.secrets:
                app = st.secrets['app']
                return {
                    'environment': app.get('environment', 'production'),
                    'debug': app.get('debug', False),
                    'max_trips_per_user': int(app.get('max_trips_per_user', 100)),
                    'session_timeout': int(app.get('session_timeout', 3600))
                }
            
            return {
                'environment': os.getenv('ENVIRONMENT', 'development'),
                'debug': os.getenv('DEBUG', 'False').lower() == 'true',
                'max_trips_per_user': int(os.getenv('MAX_TRIPS_PER_USER', 100)),
                'session_timeout': int(os.getenv('SESSION_TIMEOUT', 3600))
            }
        except:
            return {
                'environment': 'production',
                'debug': False,
                'max_trips_per_user': 100,
                'session_timeout': 3600
            }
    
    @staticmethod
    def validate():
        """Validate configuration"""
        errors = []
        
        # Check database config
        db_config = Config.get_database_config()
        if not db_config:
            errors.append("Database configuration not found")
        else:
            required_fields = ['host', 'port', 'database', 'user', 'password']
            for field in required_fields:
                if not db_config.get(field):
                    errors.append(f"Missing database field: {field}")
        
        # Check API key
        api_key = Config.get_google_api_key()
        if not api_key:
            errors.append("Google API key not found")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def print_config(hide_sensitive=True):
        """Print current configuration (for debugging)"""
        print("\n" + "=" * 60)
        print("📋 Configuration Status")
        print("=" * 60)
        
        # Environment
        is_cloud = Config.is_cloud()
        print(f"Environment: {'☁️  Streamlit Cloud' if is_cloud else '💻 Local Development'}")
        
        # Database
        db_config = Config.get_database_config()
        if db_config:
            print(f"\nDatabase:")
            print(f"  Host: {db_config['host']}")
            print(f"  Port: {db_config['port']}")
            print(f"  Database: {db_config['database']}")
            print(f"  User: {db_config['user']}")
            if hide_sensitive:
                print(f"  Password: {'*' * 8}")
            else:
                print(f"  Password: {db_config['password']}")
        else:
            print("\n❌ Database: Not configured")
        
        # API Key
        api_key = Config.get_google_api_key()
        if api_key:
            if hide_sensitive:
                print(f"\nGoogle API Key: {'*' * 8} (Set)")
            else:
                print(f"\nGoogle API Key: {api_key[:20]}...")
        else:
            print("\n❌ Google API Key: Not configured")
        
        # Validation
        is_valid, errors = Config.validate()
        if is_valid:
            print("\n✅ Configuration is valid")
        else:
            print("\n❌ Configuration errors:")
            for error in errors:
                print(f"  - {error}")
        
        print("=" * 60 + "\n")


# Singleton instance
config = Config()


if __name__ == "__main__":
    # Test configuration
    print("🧪 Testing Configuration...")
    Config.print_config(hide_sensitive=False)
