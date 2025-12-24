"""
Lumina Travel Planner - Professional Edition
Fixed: Correct function definition order
"""
import streamlit as st
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import json
import plotly.graph_objects as go
from decimal import Decimal

load_dotenv()

def is_streamlit():
    """Check if running in Streamlit environment"""
    try:
        import streamlit as st
        return hasattr(st, "secrets")
    except:
        return False

st.set_page_config(
    page_title="Lumina Travel Planner", 
    page_icon="✈", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Try to import required modules with error handling
COMPONENTS_AVAILABLE = False
import_errors = []

try:
    from auth import UserAuth, init_session_state, logout
    print("auth.py imported successfully")
except Exception as e:
    import_errors.append(f"auth.py: {str(e)}")
    print(f"Failed to import auth.py: {e}")
    st.error(f"Failed to import auth.py: {e}")

try:
    from database import TravelDatabase
    print("database.py imported successfully")
except Exception as e:
    import_errors.append(f"database.py: {str(e)}")
    print(f"Failed to import database.py: {e}")
    st.error(f"Failed to import database.py: {e}")

try:
    from agent import TravelAgent
    print("agent.py imported successfully")
    COMPONENTS_AVAILABLE = True
except Exception as e:
    import_errors.append(f"agent.py: {str(e)}")
    print(f"Failed to import agent.py: {e}")
    st.error(f"Failed to import agent.py: {e}")

if import_errors:
    st.error("### Import Errors Detected")
    for error in import_errors:
        st.code(error)
    st.info("Please make sure all required files (auth.py, database.py, agent.py) are in your repository.")
    st.stop()

# Initialize session state
try:
    init_session_state()
    print("Session state initialized")
except Exception as e:
    st.error(f"Failed to initialize session state: {e}")
    st.stop()

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .main { background: #f8fafc; }
    .block-container { padding-top: 2rem !important; }
    
    /* Hide empty containers */
    .element-container:empty { display: none !important; }
    div[data-testid="stVerticalBlock"] > div:empty { display: none !important; }
    .stMarkdown:empty { display: none !important; }
    [data-testid="stMarkdownContainer"]:empty { display: none !important; }
    
    /* Hide containers with only whitespace */
    .element-container:not(:has(*:not(:empty))) { display: none !important; }
    
    /* Remove gap from empty markdown */
    .stMarkdown { min-height: 0 !important; }
    
    /* Hide specific empty divs after hero card */
    .itinerary-card:empty { display: none !important; }
    div[data-testid="stVerticalBlock"] > div[style*="height"] { min-height: 0 !important; }
    
    [data-testid="stSidebar"] { 
        background: #ffffff; 
        padding: 1.5rem 1rem;
        border-right: 1px solid #e2e8f0;
    }
    
    .sidebar-logo { 
        display: flex; 
        align-items: center; 
        gap: 0.75rem; 
        padding: 1rem; 
        margin-bottom: 2rem; 
        border-bottom: 2px solid #e2e8f0; 
    }
    
    .logo-icon { 
        width: 42px; 
        height: 42px; 
        background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%); 
        border-radius: 10px; 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        color: white;
        font-size: 1.2rem;
        font-weight: 700;
    }
    
    .logo-text { 
        font-size: 1.5rem; 
        font-weight: 800; 
        color: #1e293b;
        letter-spacing: -0.5px;
    }
    
    .hero-card { 
        background: linear-gradient(135deg, #1e40af 0%, #1e3a8a 100%); 
        border-radius: 16px; 
        padding: 2.5rem; 
        color: white; 
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .hero-card h1 { 
        font-size: 2.25rem; 
        font-weight: 800; 
        margin-bottom: 0.5rem;
        letter-spacing: -1px;
    }
    
    .hero-card p { 
        font-size: 1rem; 
        opacity: 0.9;
        font-weight: 500;
    }
    
    .form-card { 
        background: white; 
        border-radius: 12px; 
        padding: 2rem; 
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1); 
        margin-bottom: 2rem;
        border: 1px solid #e2e8f0;
    }
    
    .form-title { 
        font-size: 1.25rem; 
        font-weight: 700; 
        color: #1e293b; 
        margin-bottom: 1.5rem;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid #e2e8f0;
    }
    
    .stButton>button { 
        background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%) !important; 
        color: white !important; 
        border-radius: 8px !important; 
        padding: 0.75rem 2rem !important; 
        font-weight: 600 !important;
        width: 100% !important;
        border: none !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4) !important;
    }
    
    .itinerary-card { 
        background: white; 
        border-radius: 12px; 
        padding: 2rem; 
        margin-bottom: 1.5rem; 
        border-left: 4px solid #2563eb;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    }
    
    .stats-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        background: #eff6ff;
        border-radius: 6px;
        color: #1e40af;
        font-weight: 600;
        font-size: 0.875rem;
        margin: 0.25rem;
        border: 1px solid #dbeafe;
    }
    
    .option-card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        border: 1px solid #e2e8f0;
        transition: all 0.2s ease;
    }
    
    .option-card:hover {
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transform: translateY(-2px);
    }
    
    .route-card {
        background: #f0fdf4;
        border: 2px solid #86efac;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .route-card:hover {
        background: #dcfce7;
        transform: translateX(4px);
    }
    
    .warning-box {
        background: #fef3c7;
        border-left: 4px solid #f59e0b;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: 1px solid #fde68a;
    }
    
    .success-box {
        background: #d1fae5;
        border-left: 4px solid #10b981;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        color: #065f46;
        font-weight: 600;
    }
    
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    }
    
    .metric-label {
        font-size: 0.875rem;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-value {
        font-size: 1.875rem;
        font-weight: 800;
        color: #1e293b;
        margin: 0.5rem 0;
    }
    
    .metric-delta {
        font-size: 0.875rem;
        color: #2563eb;
        font-weight: 600;
    }
    
    /* Gold stars */
    .gold-star {
        color: #fbbf24;
    }
</style>
""", unsafe_allow_html=True)


# ===== SESSION STATE INITIALIZATION =====
if 'page' not in st.session_state:
    st.session_state.page = 'overview'
if 'agent' not in st.session_state:
    st.session_state.agent = None
if 'trip_data' not in st.session_state:
    st.session_state.trip_data = None
if 'ai_response' not in st.session_state:
    st.session_state.ai_response = None
if 'form_data' not in st.session_state:
    st.session_state.form_data = {}
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'available_routes' not in st.session_state:
    st.session_state.available_routes = {}
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = None

# ===== DEFINE ALL HELPER FUNCTIONS FIRST =====

@st.cache_data
def get_available_routes():
    """Get all available flight routes from database"""
    try:
        if st.session_state.db:
            db = st.session_state.db
            with db.get_cursor() as cursor:  # Use context manager
                cursor.execute("""
                    SELECT DISTINCT from_city, to_city, COUNT(*) as flight_count
                    FROM flights
                    GROUP BY from_city, to_city
                    ORDER BY from_city, to_city
                """)
                routes = cursor.fetchall()
                
                # Organize by source city
                route_dict = {}
                for route in routes:
                    from_city = route['from_city']
                    to_city = route['to_city']
                    count = route['flight_count']
                    
                    if from_city not in route_dict:
                        route_dict[from_city] = []
                    route_dict[from_city].append({'to': to_city, 'count': count})
                
                return route_dict
        return {}
    except Exception as e:
        print(f"Error loading routes: {e}")
        return {}
        
def safe_float(value):
    """Convert any numeric value to float safely"""
    try:
        if isinstance(value, Decimal):
            return float(value)
        return float(value)
    except (TypeError, ValueError):
        return 0.0

def check_route_availability(from_city, to_city):
    """Check if direct flight exists in the pre-loaded routes"""
    # 1. Access the pre-loaded routes from session state
    routes = st.session_state.get('available_routes', {})
    
    # 2. Check if the starting city exists in our data
    if from_city in routes:
        # 3. Check if any of the destinations for that city match our target 'to_city'
        destinations = [r['to'] for r in routes[from_city]]
        if to_city in destinations:
            return True # Direct flight found
            
    return False # No direct flight found

def get_alternative_routes(from_city, to_city):
    """Get alternative routes if direct not available"""
    routes = st.session_state.available_routes
    alternatives = []
    
    # Check what routes exist from source
    if from_city in routes:
        for dest in routes[from_city]:
            alternatives.append({
                'from': from_city,
                'to': dest['to'],
                'count': dest['count']
            })
    
    # Check routes to destination from anywhere
    for source in routes:
        for dest in routes[source]:
            if dest['to'] == to_city and source != from_city:
                alternatives.append({
                    'from': source,
                    'to': to_city,
                    'count': dest['count']
                })
    
    return alternatives[:10]

def create_budget_chart(flight_cost, hotel_cost, food_cost, transport_cost):
    """Create budget donut chart"""
    labels = ['Flights', 'Hotels', 'Food', 'Transport']
    values = [flight_cost, hotel_cost, food_cost, transport_cost]
    colors = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b']
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.5,
        marker=dict(colors=colors),
        textinfo='label+percent',
        hovertemplate='<b>%{label}</b><br>₹%{value:,.0f}<extra></extra>'
    )])
    
    fig.update_layout(
        title='Budget Breakdown',
        showlegend=True,
        height=400,
        margin=dict(t=60, b=20, l=20, r=20),
        font=dict(family='Inter', size=12)
    )
    
    return fig

def show_login_page():
    """Display login and signup page"""
    st.markdown("""
    <div class="hero-card">
        <h1>Welcome to Lumina Travel Planner</h1>
        <p>Sign in to start planning your next adventure</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.markdown("### Login to Your Account")
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("Email or Username", placeholder="Enter your email or username", key="login_email")
            password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_pass")
            login_submit = st.form_submit_button("Login", use_container_width=True)
        
        if login_submit:
            if not email or not password:
                st.error("Please fill in all fields")
            elif st.session_state.auth is None:
                st.error("Authentication system not available. Please check:")
                with st.expander("Show Debug Info"):
                    st.markdown("""
                    **Possible issues:**
                    - Database connection failed
                    - Check your Streamlit logs for detailed errors
                    """)
            else:
                with st.spinner("Logging in..."):
                    user = st.session_state.auth.login(email, password)
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.user = user
                        st.success(f"Welcome back, {user['full_name'] or user['username']}!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("Invalid credentials. Please try again.")
    
    with tab2:
        st.markdown("### Create New Account")
        with st.form("signup_form", clear_on_submit=False):
            full_name = st.text_input("Full Name", placeholder="Enter your full name", key="signup_name")
            username = st.text_input("Username", placeholder="Choose a username", key="signup_user")
            email = st.text_input("Email", placeholder="Enter your email", key="signup_email")
            col1, col2 = st.columns(2)
            with col1:
                password = st.text_input("Password", type="password", placeholder="Minimum 6 characters", key="signup_pass")
            with col2:
                confirm = st.text_input("Confirm Password", type="password", placeholder="Re-enter password", key="signup_confirm")
            
            signup_submit = st.form_submit_button("Sign Up", use_container_width=True)
        
        if signup_submit:
            if not all([full_name, username, email, password, confirm]):
                st.error("Please fill in all fields")
            elif password != confirm:
                st.error("Passwords don't match")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters")
            elif '@' not in email:
                st.error("Invalid email format")
            elif st.session_state.auth is None:
                st.error("Authentication system not available")
            else:
                with st.spinner("Creating account..."):
                    success, message = st.session_state.auth.register(username, email, password, full_name)
                    if success:
                        st.success("Account created successfully! Please login.")
                        st.balloons()
                    else:
                        st.error(f"{message}")
    
    # Debug info in expander
    with st.expander("🔍 Debug: Check Route Database"):
        if st.session_state.available_routes:
            total_cities = len(st.session_state.available_routes)
            total_routes = sum(len(routes) for routes in st.session_state.available_routes.values())
            st.success(f"✅ Loaded **{total_cities} cities** with **{total_routes} total routes**")
            
            # Show sample routes
            st.write("**Sample routes available in database:**")
            sample_count = 0
            for city, routes in st.session_state.available_routes.items():
                if sample_count >= 5:
                    break
                destinations = ', '.join([r['to'] for r in routes[:3]])
                st.write(f"• **From {city}**: {destinations}")
                sample_count += 1
        else:
            st.error("⚠️ No routes loaded - database connection may have failed")
            st.info("This means the route detection feature won't work properly")
    
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #64748b; padding: 1rem;">
        <small>By signing up, you agree to our Terms of Service and Privacy Policy</small>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #64748b; padding: 1rem;">
        <small>By signing up, you agree to our Terms of Service and Privacy Policy</small>
    </div>
    """, unsafe_allow_html=True)

# ===== DATABASE & AUTH INITIALIZATION =====
if 'db' not in st.session_state:
    st.session_state.db = None

if 'auth' not in st.session_state:
    st.session_state.auth = None
    
if st.session_state.db is None and st.session_state.auth is None:
    print("=" * 50)
    print("STARTING INITIALIZATION")
    print("=" * 50)
    
    if COMPONENTS_AVAILABLE:
        print("Components available")
        
        try:
            from database import TravelDatabase
            from auth import UserAuth
            print("Imports successful")

            # 1. Initialize database connection
            print("Calling TravelDatabase()...")
            st.session_state.db = TravelDatabase()
            print(f"Database initialized: {st.session_state.db is not None}")
            
            # 2. Initialize auth system with database instance
            if st.session_state.db:
                try:
                    print("🔧 Initializing UserAuth...")
                    st.session_state.auth = UserAuth(st.session_state.db)
                    print("✅ Auth system initialized")
                    
                    # --- CRITICAL: ROUTE DETECTION SYNC ---
                    # This pulls all flight data immediately so the form can 
                    # detect direct flights or suggest connecting routes.
                    if not st.session_state.available_routes:
                        print("✈️ Syncing flight routes for detection...")
                        st.session_state.available_routes = get_available_routes()
                        print(f"✅ Route detection ready: {len(st.session_state.available_routes)} cities loaded")
                    # ------------------------------------

                except Exception as e:
                    print(f"❌ Auth init error: {e}")
                    import traceback
                    traceback.print_exc()
                    st.session_state.auth = None
            else:
                print("❌ No database available")
                
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("❌ Components not available - check imports")

# ===== LOGIN CHECK =====
if not st.session_state.logged_in:
    show_login_page()
    st.stop()
    
# ===== AGENT INITIALIZATION AFTER LOGIN =====
if st.session_state.logged_in and st.session_state.agent is None and st.session_state.db and COMPONENTS_AVAILABLE:
    try:
        google_api_key = None
        
        # Try [gemini] section with string cleanup
        if "gemini" in st.secrets:
            try:
                raw_key = st.secrets["gemini"]["GOOGLE_API_KEY"]
                google_api_key = str(raw_key).strip().replace('\n', '').replace('"', '').replace("'", '').strip()
                print(f"✅ API Key length: {len(google_api_key)}")
            except Exception as e:
                print(f"Error reading key: {e}")

        if not google_api_key:
            st.error("❌ API Key not found")
        else:
            from agent import TravelAgent
            st.session_state.agent = TravelAgent(google_api_key=google_api_key)
            st.session_state.agent.db = st.session_state.db
            st.success("🤖 AI Agent Ready!")
            
    except Exception as e:
        st.error(f"Failed: {str(e)}")
        
# ===== SIDEBAR =====

with st.sidebar:
    st.markdown('<div class="sidebar-logo"><div class="logo-icon">L</div><div class="logo-text">Lumina</div></div>', unsafe_allow_html=True)
    
    # User Profile Section
    if st.session_state.user:
        st.markdown(f"""
        <div style="padding: 1rem; background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); 
                    border-radius: 10px; margin-bottom: 1rem; border: 1px solid #bfdbfe;">
            <div style="font-weight: 700; font-size: 1rem; color: #1e40af; margin-bottom: 0.25rem;">
                {st.session_state.user['full_name'] or st.session_state.user['username']}
            </div>
            <div style="font-size: 0.85rem; color: #64748b;">
                {st.session_state.user['email']}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # User Stats
        if st.session_state.auth:
            try:
                stats = st.session_state.auth.get_user_stats(st.session_state.user['user_id'])
                st.markdown(f"""
                <div style="padding: 0.75rem; background: #f8fafc; border-radius: 8px; margin-bottom: 1rem;">
                    <div style="font-size: 0.75rem; color: #64748b; font-weight: 700; margin-bottom: 0.5rem;">
                        YOUR STATS
                    </div>
                    <div style="display: flex; justify-content: space-around; text-align: center;">
                        <div>
                            <div style="font-size: 1.5rem; font-weight: 800; color: #2563eb;">{stats['total_trips']}</div>
                            <div style="font-size: 0.7rem; color: #64748b;">Trips</div>
                        </div>
                        <div>
                            <div style="font-size: 1.5rem; font-weight: 800; color: #10b981;">₹{stats['total_spent']:,.0f}</div>
                            <div style="font-size: 0.7rem; color: #64748b;">Spent</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            except:
                pass
    
    # Database Stats
    if st.session_state.db:
        try:
            stats = st.session_state.db.get_database_stats()
            st.success("Connected")
            st.markdown(f"""
            <div style="padding: 1rem; background: #f8fafc; border-radius: 10px; margin-bottom: 1rem; border: 1px solid #e2e8f0;">
                <div style="font-size: 0.75rem; color: #64748b; font-weight: 700; text-transform: uppercase; 
                            letter-spacing: 0.5px; margin-bottom: 0.75rem;">Database</div>
                <div>
                    <span class="stats-badge">{stats.get('total_flights', 0)} Flights</span>
                    <span class="stats-badge">{stats.get('total_hotels', 0)} Hotels</span>
                    <span class="stats-badge">{stats.get('total_places', 0)} Places</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        except:
            st.warning("DB connection issue")
    else:
        st.error("Not connected")
    
    st.markdown("---")
    
    # Navigation
    if st.button("Dashboard", key="nav_overview", use_container_width=True):
        st.session_state.page = 'overview'
        st.rerun()
    if st.button("Itinerary", key="nav_itinerary", use_container_width=True):
        st.session_state.page = 'itinerary'
        st.rerun()
    if st.button("Chat Assistant", key="nav_chat", use_container_width=True):
        st.session_state.page = 'chat'
        st.rerun()
    
    st.markdown("---")
    
    # Logout button
    if st.button("Logout", key="logout_btn", use_container_width=True, type="secondary"):
        logout()
        st.rerun()

# ===== MAIN PAGES =====

# DASHBOARD PAGE
if st.session_state.page == 'overview':
    st.markdown("""
    <div class="hero-card">
        <h1>Lumina Travel Planner</h1>
        <p>AI-Powered Trip Planning with Smart Route Detection</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Show dashboard if trip generated
    if st.session_state.trip_data and st.session_state.form_data:
        td = st.session_state.trip_data
        fd = st.session_state.form_data
        
        flights = td.get('flights', [])
        hotels = td.get('hotels', [])
        places = td.get('places', [])
        
        # KPI Row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_flight = sum(safe_float(f.get('price', 0)) for f in flights[:3]) / max(len(flights[:3]), 1) if flights else 0
            flight_count = len(flights)
            delta_text = f"Avg: ₹{avg_flight:,.0f}" if avg_flight > 0 else "No flights"
            
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Flight Options</div>
                <div class="metric-value">{flight_count}</div>
                <div class="metric-delta">{delta_text}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            avg_hotel = sum(safe_float(h.get('price_per_night', 0)) for h in hotels[:3]) / max(len(hotels[:3]), 1) if hotels else 0
            hotel_count = len(hotels)
            delta_text = f"Avg: ₹{avg_hotel:,.0f}/night"
            
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Hotel Options</div>
                <div class="metric-value">{hotel_count}</div>
                <div class="metric-delta">{delta_text}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            avg_rating = sum(safe_float(p.get('rating', 0)) for p in places) / max(len(places), 1) if places else 0
            places_count = len(places)
            delta_text = f"Avg Rating: {avg_rating:.1f}"
            
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Attractions</div>
                <div class="metric-value">{places_count}</div>
                <div class="metric-delta">{delta_text}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            total_budget = (avg_flight * 2) + (avg_hotel * fd['duration']) + (2000 * fd['duration'])
            
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Est. Budget</div>
                <div class="metric-value">₹{total_budget:,.0f}</div>
                <div class="metric-delta">{fd['duration']} days</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Charts
        if flights and hotels:
            chart_col1, chart_col2 = st.columns(2)
            
            with chart_col1:
                flight_budget = avg_flight * 2
                hotel_budget = avg_hotel * fd['duration']
                food_budget = 1500 * fd['duration']
                transport_budget = 800 * fd['duration']
                
                fig = create_budget_chart(flight_budget, hotel_budget, food_budget, transport_budget)
                st.plotly_chart(fig, use_container_width=True)
            
            with chart_col2:
                st.markdown("### Flight Price Comparison")
                for i, f in enumerate(flights[:5], 1):
                    price = safe_float(f.get('price', 0))
                    st.markdown(f"""
                    <div class="option-card">
                        <strong>{f.get('airline', 'N/A')}</strong><br>
                        <span style="color: #2563eb; font-size: 1.5rem; font-weight: 800;">₹{price:,.0f}</span>
                    </div>
                    """, unsafe_allow_html=True)
        
        st.markdown("---")
    
    # Form
    col_form, col_preview = st.columns([1, 1], gap="large")
    
    with col_form:
        st.markdown('<div class="form-card"><div class="form-title">Plan Your Trip</div>', unsafe_allow_html=True)
        
        col_a, col_b = st.columns(2)
        with col_a:
            from_city = st.selectbox("From", ["Bangalore", "Delhi", "Mumbai", "Hyderabad", "Kolkata", "Chennai", "Jaipur", "Goa"])
        with col_b:
            to_city = st.selectbox("To", ["Goa", "Bangalore", "Mumbai", "Delhi", "Jaipur", "Kolkata", "Hyderabad", "Chennai"], index=0)
        
        # Check route availability in real-time
        if from_city and to_city and from_city != to_city:
            has_direct_flight = check_route_availability(from_city, to_city)
            
            if not has_direct_flight:
                st.markdown(f"""
                <div class="warning-box">
                    <strong>⚠️ No Direct Flights Available</strong><br>
                    There are no direct flights from <strong>{from_city}</strong> to <strong>{to_city}</strong> in our database.
                </div>
                """, unsafe_allow_html=True)
                
                alternatives = get_alternative_routes(from_city, to_city)
                
                if alternatives:
                    st.markdown("### 🔄 Suggested Alternative Routes:")
                    
                    # Show routes FROM source
                    from_source = [a for a in alternatives if a['from'] == from_city]
                    if from_source:
                        st.markdown(f"**✈️ Flights from {from_city} to:**")
                        cols = st.columns(2)
                        for idx, alt in enumerate(from_source[:6]):
                            with cols[idx % 2]:
                                st.markdown(f"""
                                <div class="route-card" style="cursor: pointer;">
                                    <strong>{alt['from']} → {alt['to']}</strong><br>
                                    <small>✈️ {alt['count']} flights available</small>
                                </div>
                                """, unsafe_allow_html=True)
                    
                    st.markdown("---")
                    
                    # Show routes TO destination
                    to_dest = [a for a in alternatives if a['to'] == to_city]
                    if to_dest:
                        st.markdown(f"**🛬 Flights to {to_city} from:**")
                        cols = st.columns(2)
                        for idx, alt in enumerate(to_dest[:6]):
                            with cols[idx % 2]:
                                st.markdown(f"""
                                <div class="route-card" style="cursor: pointer;">
                                    <strong>{alt['from']} → {alt['to']}</strong><br>
                                    <small>✈️ {alt['count']} flights available</small>
                                </div>
                                """, unsafe_allow_html=True)
                    
                    st.info("💡 **Tip:** Consider booking connecting flights through these cities, or use train/bus for one leg of the journey.")
                else:
                    st.markdown("""
                    <div class="warning-box">
                        <strong>💡 Travel Suggestions:</strong><br>
                        • Consider traveling by <strong>train</strong> or <strong>bus</strong><br>
                        • Check <strong>connecting flights</strong> through major hubs like Mumbai or Delhi<br>
                        • Try selecting different nearby cities
                    </div>
                    """, unsafe_allow_html=True)
            else:
                # Extract the actual count from the route data
                routes = st.session_state.available_routes.get(from_city, [])
                matching_routes = [r for r in routes if r['to'] == to_city]
                route_count = matching_routes[0]['count'] if matching_routes else 0
                
                if route_count > 0:
                    st.markdown(f"""
                    <div class="success-box">
                        ✅ <strong>{route_count} direct flight(s)</strong> available from {from_city} to {to_city}!
                    </div>
                    """, unsafe_allow_html=True)
        
        col_c, col_d = st.columns(2)
        with col_c:
            start_date = st.date_input("Start Date", value=datetime.now() + timedelta(days=7))
        with col_d:
            end_date = st.date_input("End Date", value=datetime.now() + timedelta(days=10))
        
        col_e, col_f = st.columns(2)
        with col_e:
            style = st.selectbox("Travel Style", ["Family", "Romantic", "Solo", "Friends"])
        with col_f:
            budget = st.selectbox("Budget", ["Budget", "Moderate", "Luxury"], index=1)
        
        interests = st.multiselect("Interests", 
            ["Beaches", "History", "Food", "Adventure", "Shopping", "Nightlife", 
             "Nature", "Culture", "Temples", "Museums", "Wildlife", "Photography", 
             "Art", "Architecture", "Relaxation", "Sports", "Festivals"], 
            default=["History"])
        
        amenities = st.multiselect("Preferred Hotel Amenities", 
            ["WiFi", "Swimming Pool", "Gym", "Spa", "Restaurant", "Free Parking", 
             "Room Service", "Air Conditioning", "Bar/Lounge", "Airport Shuttle",
             "Business Center", "Laundry Service", "Pet Friendly", "Beach Access"], 
            default=["WiFi"])
        
        members = st.number_input("Travelers", min_value=1, max_value=10, value=2)
        
        if st.button("Generate Trip Plan", key="generate_trip"):
            if from_city == to_city:
                st.error("Please select different cities")
            elif not st.session_state.agent or not st.session_state.db:
                st.error("Agent/Database not initialized")
            else:
                # Check route before generating
                has_flights = check_route_availability(from_city, to_city)
                
                with st.spinner('Creating your personalized trip plan...'):
                    try:
                        duration = (end_date - start_date).days
                        interests_str = ", ".join(interests) if interests else "sightseeing"
                        
                        st.session_state.form_data = {
                            'from_city': from_city,
                            'to_city': to_city,
                            'start_date': start_date,
                            'end_date': end_date,
                            'duration': duration,
                            'style': style,
                            'budget': budget,
                            'interests': interests_str,
                            'amenities': ', '.join(amenities) if amenities else 'WiFi',
                            'members': members
                        }
                        
                        # Get data from database
                        if st.session_state.db:
                            # Map budget to star ratings
                            budget_map = {
                                'Budget': (0, 3),
                                'Moderate': (3, 4),
                                'Luxury': (4, 5)
                            }
                            min_stars, max_stars = budget_map.get(budget, (0, 5))
                            
                            flights = st.session_state.db.get_flights(from_city, to_city, limit=10)
                            hotels = st.session_state.db.get_hotels(to_city, min_stars=min_stars, limit=10)
                            places = st.session_state.db.get_places(to_city, min_rating=4.0, limit=20)
                            
                            # Add amenities_list for hotels
                            for hotel in hotels:
                                if hotel.get('amenities'):
                                    hotel['amenities_list'] = hotel['amenities'].split(',')
                                else:
                                    hotel['amenities_list'] = []
                            
                            trip_data = {
                                'flights': flights,
                                'hotels': hotels,
                                'places': places
                            }
                        else:
                            trip_data = {'flights': [], 'hotels': [], 'places': []}
                        
                        st.session_state.trip_data = trip_data
                        
                        # Build query
                        if not has_flights:
                            query = f"""Create a {duration}-day {style.lower()} trip plan from {from_city} to {to_city}.

IMPORTANT: There are NO direct flights from {from_city} to {to_city} in the database.
Please suggest:
1. Alternative connecting routes
2. Other transportation options
3. Hotels in {to_city} (data available)
4. Places to visit in {to_city} (data available)

Budget: {budget}
Travelers: {members}
Interests: {interests_str}

Use search_all_travel_data: {from_city}|{to_city}|{budget.lower()}|{interests_str}"""
                        else:
                            query = f"""Create a {duration}-day {style.lower()} trip from {from_city} to {to_city}.

Budget: {budget}
Travelers: {members}
Interests: {interests_str}

Use search_all_travel_data: {from_city}|{to_city}|{budget.lower()}|{interests_str}

Provide complete itinerary with flights, hotels, places, and budget."""
                        
                        ai_response = st.session_state.agent.plan_trip(query)
                        st.session_state.ai_response = ai_response
                        
                        # Save
                        try:
                            trip_record = {
                                'source_city': from_city,
                                'destination_city': to_city,
                                'start_date': start_date,
                                'end_date': end_date,
                                'duration_days': duration,
                                'total_budget': None,
                                'itinerary': trip_data,
                                'agent_response': ai_response
                            }
                            # Use save_user_trip
                            if st.session_state.db:
                                st.session_state.db.save_user_trip(
                                    st.session_state.user['user_id'],
                                    trip_record
                                )
                        except Exception as e:
                            st.warning(f"Could not save trip: {str(e)}")
                        
                        st.success("Trip plan generated successfully!")
                        st.session_state.page = 'itinerary'
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error generating trip: {str(e)}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_preview:
        if st.session_state.trip_data:
            st.markdown("### Quick Preview")
            
            td = st.session_state.trip_data
            flights = td.get('flights', [])[:3]
            hotels = td.get('hotels', [])[:2]
            
            if flights:
                st.markdown("#### Top Flights")
                for f in flights:
                    price = safe_float(f.get('price', 0))
                    st.markdown(f"""
                    <div class="option-card">
                        <strong>{f.get('airline', 'N/A')}</strong><br>
                        <span style="color: #2563eb; font-weight: 800;">₹{price:,.0f}</span><br>
                        <small>{f.get('from_city')} → {f.get('to_city')}</small>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No direct flights available for this route")
            
            if hotels:
                st.markdown("#### Top Hotels")
                for h in hotels:
                    price = safe_float(h.get('price_per_night', 0))
                    stars = int(safe_float(h.get('stars', 0)))
                    star_display = '<span class="gold-star">' + ('★' * stars) + '</span>'
                    st.markdown(f"""
                    <div class="option-card" style="border-left-color: #ef4444;">
                        <strong>{h.get('name', 'N/A')}</strong><br>
                        <span style="color: #ef4444; font-weight: 800;">₹{price:,.0f}/night</span><br>
                        <small>{star_display}</small>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("Fill the form to see available options")

# ITINERARY PAGE
elif st.session_state.page == 'itinerary':
    if st.session_state.ai_response and st.session_state.form_data:
        fd = st.session_state.form_data
        st.markdown(f"""
        <div class="hero-card">
            <h1>{fd["from_city"]} to {fd["to_city"]}</h1>
            <p>{fd["duration"]}-Day Trip • {fd["members"]} Travelers • {fd["budget"]} Budget</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f'<div class="itinerary-card">{st.session_state.ai_response}</div>', unsafe_allow_html=True)
        
        if st.session_state.trip_data:
            st.markdown("---")
            tab1, tab2, tab3 = st.tabs(["Flights", "Hotels", "Places"])
            
            with tab1:
                flights = st.session_state.trip_data.get('flights', [])
                if flights:
                    for f in flights:
                        price = safe_float(f.get('price', 0))
                        with st.expander(f"{f.get('airline')} - ₹{price:,.0f}"):
                            st.write(f"**Route:** {f.get('from_city')} → {f.get('to_city')}")
                            st.write(f"**Departure:** {f.get('departure_time')}")
                            st.write(f"**Arrival:** {f.get('arrival_time')}")
                else:
                    st.warning("No direct flights available for this route. Consider connecting flights or alternative transportation.")
            
            with tab2:
                hotels = st.session_state.trip_data.get('hotels', [])
                if hotels:
                    for h in hotels:
                        price = safe_float(h.get('price_per_night', 0))
                        stars = int(safe_float(h.get('stars', 0)))
                        star_display = '<span class="gold-star">' + ('★' * stars) + '</span>'
                        amenities = h.get('amenities_list', [])
                        with st.expander(f"{h.get('name')} - {stars} Stars"):
                            st.write(f"**Price:** ₹{price:,.0f}/night")
                            st.markdown(f"**Rating:** {star_display}", unsafe_allow_html=True)
                            if amenities:
                                st.write(f"**Amenities:** {', '.join(amenities)}")
                else:
                    st.info("No hotels found")
            
            with tab3:
                places = st.session_state.trip_data.get('places', [])
                if places:
                    for p in places:
                        rating = safe_float(p.get('rating', 0))
                        with st.expander(f"{p.get('name')} - {rating:.1f} Rating"):
                            st.write(f"**Type:** {p.get('type')}")
                            st.write(f"**City:** {p.get('city')}")
                else:
                    st.info("No places found")
    else:
        st.info("Generate a trip first from the Dashboard")

# CHAT PAGE
# CHAT PAGE
elif st.session_state.page == 'chat':
    # Header with clear button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### Chat with Lumina Assistant")
    with col2:
        if st.button("🗑️ Clear Chat", key="clear_chat_top", use_container_width=True, type="secondary"):
            st.session_state.chat_history = []
            if st.session_state.agent:
                st.session_state.agent.reset_memory()
            st.rerun()
    
    st.markdown("---")
    
    if not st.session_state.agent:
        st.error("Agent not initialized")
    elif not st.session_state.ai_response:
        st.info("Generate a trip first to start chatting!")
    else:
        # Chat messages with empty state
        if not st.session_state.chat_history:
            st.markdown("""
            <div style="text-align: center; padding: 3rem; color: #64748b;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">💬</div>
                <div style="font-size: 1.25rem; font-weight: 600; margin-bottom: 0.5rem;">Start a Conversation</div>
                <div>Ask me anything about your trip plan, hotels, activities, or travel tips!</div>
            </div>
            """, unsafe_allow_html=True)
        
        for msg in st.session_state.chat_history:
            if msg['role'] == 'user':
                st.chat_message("user").write(msg['content'])
            else:
                st.chat_message("assistant").write(msg['content'])
        
        # Chat input
        user_input = st.chat_input("Ask about your trip...")
        
        if user_input:
            st.session_state.chat_history.append({'role': 'user', 'content': user_input})
            
            with st.spinner("Thinking..."):
                try:
                    response = st.session_state.agent.chat(user_input)
                    st.session_state.chat_history.append({'role': 'assistant', 'content': response})
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")





































