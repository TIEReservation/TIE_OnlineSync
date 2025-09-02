import streamlit as st
import os
import sys
from datetime import datetime, date, timedelta
from supabase import create_client, Client

# Add the current directory to the path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import existing modules
try:
    from directreservation import show_new_reservation_form, show_reservations, show_edit_reservations, show_analytics, load_reservations_from_supabase
    from online_reservation import show_online_reservations, load_online_reservations_from_supabase
    from editOnline import show_edit_online_reservations
    from inventory import main as inventory_main, show_calendar_navigation, export_daily_report
    from utils import safe_int, safe_float  # Assuming you have utils.py
except ImportError as e:
    st.error(f"Error importing modules: {e}")
    st.info("Please ensure all required modules are in the same directory as app.py")

# Page config
st.set_page_config(
    page_title="TIE Hotel Management System",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Supabase client with environment variables
try:
    os.environ["SUPABASE_URL"] = "https://oxbrezracnmazucnnqox.supabase.co"
    os.environ["SUPABASE_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im94YnJlenJhY25tYXp1Y25ucW94Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM3NjUxMTgsImV4cCI6MjA2OTM0MTExOH0.nqBK2ZxntesLY9qYClpoFPVnXOW10KrzF-UI_DKjbKo"
    supabase: Client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
except Exception as e:
    st.error(f"Failed to initialize Supabase client: {e}")
    st.stop()

def initialize_session_state():
    """Initialize session state variables."""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'role' not in st.session_state:
        st.session_state.role = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'reservations' not in st.session_state:
        st.session_state.reservations = []
    if 'online_reservations' not in st.session_state:
        st.session_state.online_reservations = []
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False
    if 'edit_index' not in st.session_state:
        st.session_state.edit_index = None
    if 'online_edit_mode' not in st.session_state:
        st.session_state.online_edit_mode = False
    if 'online_edit_index' not in st.session_state:
        st.session_state.online_edit_index = None

def authenticate_user(username, password):
    """Authenticate user credentials with enhanced role-based access."""
    # Enhanced authentication with multiple user types
    valid_users = {
        "admin": {"password": "TIE2024", "role": "Management"},
        "manager": {"password": "TIE2024", "role": "Management"},
        "reservation": {"password": "TIE123", "role": "ReservationTeam"},
        "staff": {"password": "TIE123", "role": "Staff"},
        "reception": {"password": "TIE123", "role": "Reception"}
    }
    
    if username in valid_users and valid_users[username]["password"] == password:
        return True, valid_users[username]["role"]
    return False, None

def show_login():
    """Enhanced login interface."""
    # Display logo in top-left corner
    st.image("https://github.com/TIEReservation/TIEReservation-System/raw/main/TIE_Logo_Icon.png", width=100)
    
    st.title("🏨 TIE Hotel Management System")
    st.markdown("---")
    
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.subheader("🔐 Login")
            
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                submitted = st.form_submit_button("Login", use_container_width=True)
                
                if submitted:
                    authenticated, role = authenticate_user(username, password)
                    if authenticated:
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.role = role
                        
                        # Load reservation data
                        try:
                            st.session_state.reservations = load_reservations_from_supabase()
                            st.session_state.online_reservations = load_online_reservations_from_supabase()
                            st.success(f"✅ Welcome, {username}! Reservations loaded successfully.")
                        except Exception as e:
                            st.session_state.reservations = []
                            st.session_state.online_reservations = []
                            st.warning(f"✅ Login successful, but failed to fetch reservations: {e}")
                        
                        st.rerun()
                    else:
                        st.error("❌ Invalid credentials. Please try again.")

def show_sidebar():
    """Enhanced navigation sidebar with role-based access."""
    with st.sidebar:
        st.title("🏨 TIE Navigation")
        st.markdown(f"**User:** {st.session_state.username}")
        st.markdown(f"**Role:** {st.session_state.role}")
        st.markdown("---")
        
        # Navigation menu with role-based filtering
        menu_options = {
            "🏠 Dashboard": "dashboard",
            "🏨 Daily Status": "inventory",
            "📝 Direct Reservations": "direct_reservations",
            "🌐 Online Reservations": "online_reservations",
            "✏️ Edit Direct Reservations": "edit_reservations",
            "🔧 Edit Online Reservations": "edit_online_reservations"
        }
        
        # Add analytics for Management only
        if st.session_state.role == "Management":
            menu_options["📊 Analytics & Reports"] = "analytics"
            menu_options["⚙️ Settings"] = "settings"
        
        # Role-based menu filtering for Reception
        if st.session_state.role == "Reception":
            menu_options = {
                "🏠 Dashboard": "dashboard",
                "🏨 Daily Status": "inventory",
                "📝 Direct Reservations": "direct_reservations",
                "🌐 Online Reservations": "online_reservations"
            }
        
        selected_page = st.radio("Select Page", list(menu_options.keys()))
        
        st.markdown("---")
        
        # Quick actions
        st.subheader("⚡ Quick Actions")
        
        # Today's summary
        today = date.today()
        if st.button("📅 Today's Status", use_container_width=True):
            st.session_state.quick_date = today
            st.session_state.page = "inventory"
        
        # Tomorrow's summary
        tomorrow = today + timedelta(days=1)
        if st.button("📅 Tomorrow's Status", use_container_width=True):
            st.session_state.quick_date = tomorrow
            st.session_state.page = "inventory"
        
        # Export today's report
        if st.button("📥 Export Today's Report", use_container_width=True):
            try:
                report_df = export_daily_report(today)
                if report_df is not None and not report_df.empty:
                    csv = report_df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"daily_report_{today.strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                else:
                    st.info("No data available for today's report.")
            except Exception as e:
                st.error(f"Error generating report: {e}")
        
        st.markdown("---")
        
        # Logout
        if st.button("🚪 Logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        return menu_options[selected_page]

def show_dashboard_overview():
    """Enhanced dashboard overview with quick stats."""
    # Display logo
    st.image("https://github.com/TIEReservation/TIEReservation-System/raw/main/TIE_Logo_Icon.png", width=100)
    
    st.title("🏨 TIE Hotel Management Dashboard")
    st.markdown("---")
    
    # Quick stats for today and tomorrow
    today = date.today()
    tomorrow = today + timedelta(days=1)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📅 Today's Overview")
        show_quick_summary(today)
    
    with col2:
        st.subheader("📅 Tomorrow's Overview") 
        show_quick_summary(tomorrow)
    
    st.markdown("---")
    
    # Recent activity section
    st.subheader("📋 Recent Reservation Activity")
    try:
        recent_reservations = st.session_state.reservations[-5:] if st.session_state.reservations else []
        recent_online = st.session_state.online_reservations[-5:] if st.session_state.online_reservations else []
        
        if recent_reservations or recent_online:
            st.write("**Latest Direct Reservations:**")
            for res in recent_reservations:
                st.write(f"• {res.get('guest_name', 'N/A')} - {res.get('property_name', 'N/A')} ({res.get('check_in', 'N/A')})")
            
            if recent_online:
                st.write("**Latest Online Reservations:**")
                for res in recent_online:
                    st.write(f"• {res.get('guest_name', 'N/A')} - {res.get('property_name', 'N/A')} ({res.get('check_in', 'N/A')})")
        else:
            st.info("No recent reservation activity.")
    except Exception as e:
        st.info("Recent activity data not available.")
    
    st.markdown("---")
    
    # Navigation shortcuts
    st.subheader("🚀 Quick Navigation")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🏨 Daily Status", use_container_width=True):
            st.session_state.page = "inventory"
            st.rerun()
    
    with col2:
        if st.button("📝 New Booking", use_container_width=True):
            st.session_state.page = "direct_reservations"
            st.rerun()
    
    with col3:
        if st.button("🌐 Online Bookings", use_container_width=True):
            st.session_state.page = "online_reservations"
            st.rerun()
    
    with col4:
        if st.button("📊 Analytics", use_container_width=True):
            st.session_state.page = "analytics"
            st.rerun()

def show_quick_summary(target_date):
    """Show quick summary for a specific date."""
    try:
        # Use existing reservations data from session state
        direct_reservations = st.session_state.reservations
        online_reservations = st.session_state.online_reservations
        
        # Filter for target date (check both direct and online)
        daily_direct = [
            res for res in direct_reservations 
            if str(res.get("check_in", "")) == str(target_date)
        ]
        
        daily_online = [
            res for res in online_reservations 
            if str(res.get("check_in", "")) == str(target_date)
        ]
        
        total_bookings = len(daily_direct) + len(daily_online)
        
        if total_bookings > 0:
            # Calculate metrics
            direct_revenue = sum(res.get("total_tariff", 0) for res in daily_direct)
            online_revenue = sum(res.get("total_tariff", 0) for res in daily_online)
            total_revenue = direct_revenue + online_revenue
            
            total_overbooked = sum(1 for res in daily_direct if res.get("inventory_no") == "Overbooked")
            total_overbooked += sum(1 for res in daily_online if res.get("inventory_no") == "Overbooked")
            
            # Properties with bookings
            properties = set()
            for res in daily_direct + daily_online:
                if res.get("property_name"):
                    properties.add(res["property_name"])
            
            # Display metrics
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Check-ins", total_bookings)
                st.metric("Properties", len(properties))
            with col2:
                st.metric("Revenue", f"₹{total_revenue:,.0f}")
                if total_overbooked > 0:
                    st.metric("🚨 Overbookings", total_overbooked, delta=total_overbooked, delta_color="inverse")
                else:
                    st.metric("✅ Overbookings", 0)
            
            # Show property breakdown
            if properties:
                st.write("**Properties:**")
                for prop in sorted(properties):
                    prop_direct = [res for res in daily_direct if res.get("property_name") == prop]
                    prop_online = [res for res in daily_online if res.get("property_name") == prop]
                    prop_total = len(prop_direct) + len(prop_online)
                    prop_overbooked = sum(1 for res in prop_direct + prop_online if res.get("inventory_no") == "Overbooked")
                    status_emoji = "🚨" if prop_overbooked > 0 else "✅"
                    st.write(f"{status_emoji} {prop}: {prop_total} bookings")
        else:
            st.info(f"No check-ins scheduled for {target_date.strftime('%B %d, %Y')}")
    
    except Exception as e:
        st.error(f"Error loading summary: {e}")

def show_settings():
    """Enhanced settings page with role-based access."""
    st.title("⚙️ Settings")
    st.markdown("---")
    
    # User management (for Management role only)
    if st.session_state.role == "Management":
        st.subheader("👥 User Management")
        st.info("User management features would be implemented here.")
        
        st.subheader("🏨 Property Configuration")
        st.info("Property and inventory configuration would be implemented here.")
        
        st.subheader("💾 Database Management")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh All Data", use_container_width=True):
                # Clear all cached data and reload
                try:
                    st.session_state.reservations = load_reservations_from_supabase()
                    st.session_state.online_reservations = load_online_reservations_from_supabase()
                    # Clear other cached data
                    for key in ['all_reservations', 'selected_month', 'selected_year']:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.success("✅ Data refreshed successfully!")
                except Exception as e:
                    st.error(f"Error refreshing data: {e}")
                st.rerun()
        
        with col2:
            if st.button("📊 System Health Check", use_container_width=True):
                st.info("System health check would be implemented here.")
    else:
        st.subheader("👤 User Profile")
        st.write(f"**Username:** {st.session_state.username}")
        st.write(f"**Role:** {st.session_state.role}")
        st.write(f"**Login Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        st.subheader("🎨 Display Preferences")
        theme = st.selectbox("Theme", ["Light", "Dark", "Auto"])
        language = st.selectbox("Language", ["English", "Hindi", "Tamil"])
        timezone = st.selectbox("Timezone", ["Asia/Kolkata", "UTC"])
        
        if st.button("💾 Save Preferences"):
            st.success("✅ Preferences saved!")

def show_enhanced_direct_reservations():
    """Enhanced direct reservations page with tabs."""
    st.title("📝 Direct Reservations")
    st.markdown("---")
    
    # Tabs for different actions
    tab1, tab2, tab3 = st.tabs(["📋 View Reservations", "➕ New Reservation", "🔍 Search"])
    
    with tab1:
        show_reservations()
    
    with tab2:
        show_new_reservation_form()
    
    with tab3:
        st.subheader("🔍 Search Reservations")
        search_term = st.text_input("Search by Booking ID, Guest Name, or Mobile")
        if search_term and st.session_state.reservations:
            # Simple search functionality
            search_results = []
            for i, res in enumerate(st.session_state.reservations):
                if (search_term.lower() in str(res.get('guest_name', '')).lower() or
                    search_term.lower() in str(res.get('mobile', '')).lower() or
                    search_term.lower() in str(res.get('booking_id', '')).lower()):
                    search_results.append((i, res))
            
            if search_results:
                st.write(f"Found {len(search_results)} result(s):")
                for idx, res in search_results:
                    with st.expander(f"{res.get('guest_name', 'N/A')} - {res.get('property_name', 'N/A')}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Guest:** {res.get('guest_name', 'N/A')}")
                            st.write(f"**Mobile:** {res.get('mobile', 'N/A')}")
                            st.write(f"**Check-in:** {res.get('check_in', 'N/A')}")
                        with col2:
                            st.write(f"**Property:** {res.get('property_name', 'N/A')}")
                            st.write(f"**Room:** {res.get('inventory_no', 'N/A')}")
                            st.write(f"**Total:** ₹{res.get('total_tariff', 0)}")
            else:
                st.info("No reservations found matching your search.")

def show_enhanced_online_reservations():
    """Enhanced online reservations page with tabs."""
    st.title("🌐 Online Reservations")
    st.markdown("---")
    
    # Tabs for different actions
    tab1, tab2, tab3 = st.tabs(["📋 View Reservations", "🔄 Sync Data", "🔍 Search"])
    
    with tab1:
        show_online_reservations()
    
    with tab2:
        st.subheader("🔄 Sync Online Data")
        if st.button("🔄 Refresh from Database"):
            try:
                st.session_state.online_reservations = load_online_reservations_from_supabase()
                st.success("✅ Online reservations refreshed successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Error refreshing online reservations: {e}")
    
    with tab3:
        st.subheader("🔍 Search Online Reservations")
        search_term = st.text_input("Search by Booking ID, Guest Name, or Mobile", key="online_search")
        if search_term and st.session_state.online_reservations:
            # Simple search functionality for online reservations
            search_results = []
            for i, res in enumerate(st.session_state.online_reservations):
                if (search_term.lower() in str(res.get('guest_name', '')).lower() or
                    search_term.lower() in str(res.get('mobile', '')).lower() or
                    search_term.lower() in str(res.get('booking_id', '')).lower()):
                    search_results.append((i, res))
            
            if search_results:
                st.write(f"Found {len(search_results)} result(s):")
                for idx, res in search_results:
                    with st.expander(f"{res.get('guest_name', 'N/A')} - {res.get('property_name', 'N/A')}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Guest:** {res.get('guest_name', 'N/A')}")
                            st.write(f"**Mobile:** {res.get('mobile', 'N/A')}")
                            st.write(f"**Check-in:** {res.get('check_in', 'N/A')}")
                        with col2:
                            st.write(f"**Property:** {res.get('property_name', 'N/A')}")
                            st.write(f"**Room:** {res.get('inventory_no', 'N/A')}")
                            st.write(f"**Total:** ₹{res.get('total_tariff', 0)}")
            else:
                st.info("No online reservations found matching your search.")

def load_custom_css():
    """Load custom CSS for enhanced styling."""
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
    }
    
    .overbooked-alert {
        background-color: #ffebee;
        border: 2px solid #f44336;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .success-message {
        background-color: #e8f5e8;
        border: 2px solid #4caf50;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom button styling */
    .stButton > button {
        border-radius: 8px;
        border: none;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8f9fa;
    }
    </style>
    """, unsafe_allow_html=True)

def main():
    """Main application function with integrated features."""
    # Load custom CSS
    load_custom_css()
    
    # Initialize session state
    initialize_session_state()
    
    # Check authentication
    if not st.session_state.authenticated:
        show_login()
        return
    
    # Show sidebar navigation
    selected_page = show_sidebar()
    
    # Handle quick date selection
    if hasattr(st.session_state, 'quick_date'):
        st.session_state.selected_year = st.session_state.quick_date.year
        st.session_state.selected_month = st.session_state.quick_date.month
        selected_page = "inventory"
        del st.session_state.quick_date
    
    # Route to appropriate page
    try:
        if selected_page == "dashboard":
            show_dashboard_overview()
        elif selected_page == "inventory":
            inventory_main()
        elif selected_page == "direct_reservations":
            show_enhanced_direct_reservations()
        elif selected_page == "online_reservations":
            show_enhanced_online_reservations()
        elif selected_page == "edit_reservations":
            show_edit_reservations()
        elif selected_page == "edit_online_reservations":
            show_edit_online_reservations()
        elif selected_page == "analytics" and st.session_state.role == "Management":
            show_analytics()
        elif selected_page == "settings":
            show_settings()
        else:
            show_dashboard_overview()
    except Exception as e:
        st.error(f"Error loading page: {e}")
        st.info("Falling back to dashboard...")
        show_dashboard_overview()

# Legacy compatibility function
def check_authentication():
    """Legacy authentication check - redirects to new system."""
    initialize_session_state()
    
    if not st.session_state.authenticated:
        st.title("🔐 TIE Reservations Login")
        st.write("Please select your role and enter the password to access the system.")
        
        # Legacy role selection for backwards compatibility
        role = st.selectbox("Select Role", ["Management", "ReservationTeam"])
        password = st.text_input("Enter password:", type="password")
        
        if st.button("🔑 Login"):
            legacy_success = False
            
            if role == "Management" and password == "TIE2024":
                st.session_state.authenticated = True
                st.session_state.role = "Management"
                st.session_state.username = "admin"
                legacy_success = True
            elif role == "ReservationTeam" and password == "TIE123":
                st.session_state.authenticated = True
                st.session_state.role = "ReservationTeam"
                st.session_state.username = "reservation"
                legacy_success = True
            
            if legacy_success:
                try:
                    st.session_state.reservations = load_reservations_from_supabase()
                    st.session_state.online_reservations = load_online_reservations_from_supabase()
                    st.success(f"✅ {role} login successful! Reservations fetched.")
                except Exception as e:
                    st.session_state.reservations = []
                    st.session_state.online_reservations = []
                    st.warning(f"✅ {role} login successful, but failed to fetch reservations: {e}")
                st.rerun()
            else:
                st.error("❌ Invalid password. Please try again.")
        st.stop()

if __name__ == "__main__":
    main()
