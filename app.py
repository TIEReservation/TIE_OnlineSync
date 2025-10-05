import streamlit as st
import os
import time
from supabase import create_client, Client
from streamlit_cookies_manager import EncryptedCookieManager
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from directreservation import show_new_reservation_form, show_reservations, show_edit_reservations, show_analytics, load_reservations_from_supabase
from online_reservation import show_online_reservations, load_online_reservations_from_supabase
from inventory import show_daily_status
from dms import show_dms

# Import editOnline with error handling
def log_import_error(module, error):
    """Log import errors and stop execution."""
    st.error(f"Failed to import {module}: {error}. Check file existence or dependencies.")
    st.stop()

try:
    from editOnline import show_edit_online_reservations
except Exception as e:
    log_import_error("editOnline", e)

# Page config
st.set_page_config(
    page_title="TIE Reservations",
    page_icon="https://github.com/TIEReservation/TIEReservation-System/raw/main/TIE_Logo_Icon.png",
    layout="wide"
)

# Display logo
st.image("https://github.com/TIEReservation/TIEReservation-System/raw/main/TIE_Logo_Icon.png", width=100)

# Initialize Supabase client
try:
    os.environ["SUPABASE_URL"] = "https://oxbrezracnmazucnnqox.supabase.co"
    os.environ["SUPABASE_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im94YnJlenJhY25tYXp1Y25ucW94Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM3NjUxMTgsImV4cCI6MjA2OTM0MTExOH0.nqBK2ZxntesLY9qYClpoFPVnXOW10KrzF-UI_DKjbKo"
    supabase: Client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
except Exception as e:
    st.error(f"Failed to initialize Supabase client: {e}")
    st.stop()

# Get cookie password
def get_cookie_password():
    """Get cookie password from secrets, env, or default (local dev only)."""
    try:
        return st.secrets["cookies"]["password"]
    except KeyError:
        env_password = os.environ.get("COOKIE_PASSWORD")
        if env_password:
            return env_password
        st.warning("No cookie password in secrets or env. Using default (not secure for production).")
        return "default_secure_pass_123"

# Debug mode
debug_enabled = os.environ.get("DEBUG", "false").lower() == "true"
try:
    debug_enabled = debug_enabled or st.secrets["debug"]["enabled"]
except KeyError:
    pass

# Initialize cookie manager
# For Streamlit Cloud, ensure secrets.toml has:
# [cookies]
# password = "your_secure_password"
# Or set env var COOKIE_PASSWORD
# Note: streamlit-cookies-manager may not support max_age; cookies persist until deleted
cookies = EncryptedCookieManager(prefix="tie_reservations_", password=get_cookie_password())
if not cookies.ready():
    st.error("Cookie manager not ready. Check secrets or environment configuration.")
    st.stop()

if debug_enabled:
    st.write(f"Debug: Initial cookie auth_role = {cookies.get('auth_role')}")

def init_session_state():
    """Initialize all session state keys with defaults."""
    defaults = {
        'authenticated': False,
        'role': None,
        'reservations': [],
        'online_reservations': [],
        'edit_mode': False,
        'edit_index': None,
        'online_edit_mode': False,
        'online_edit_index': None,
        'current_page': "Direct Reservations",
        'selected_booking_id': None,
        'logout_triggered': False,
        'last_logout_time': 0.0  # Timestamp for click lock
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    if debug_enabled:
        st.write(f"Debug: Session state initialized: {dict(st.session_state)}")

def clear_session_state():
    """Reset session state to defaults."""
    defaults = {
        'authenticated': False,
        'role': None,
        'reservations': [],
        'online_reservations': [],
        'edit_mode': False,
        'edit_index': None,
        'online_edit_mode': False,
        'online_edit_index': None,
        'current_page': "Direct Reservations",
        'selected_booking_id': None,
        'logout_triggered': False,
        'last_logout_time': time.time()
    }
    for key, value in defaults.items():
        st.session_state[key] = value
    if debug_enabled:
        st.write(f"Debug: Session state reset: {dict(st.session_state)}")

@retry(stop=stop_after_attempt(3), wait=wait_fixed(0.2), retry=retry_if_exception_type(Exception))
def delete_auth_cookie(cookies):
    """Clear all cookies with retry (3 attempts, 0.2s delay)."""
    if not cookies.ready():
        raise Exception("Cookie manager not ready")
    cookies.clear()
    cookies.save()
    time.sleep(0.1)
    if debug_enabled:
        st.write(f"Debug: All cookies cleared, auth_role = {cookies.get('auth_role')}")

def validate_post_logout_state():
    """Ensure no residual auth state post-logout."""
    if st.session_state.get('authenticated', False) or st.session_state.get('role'):
        clear_session_state()
    if cookies.get('auth_role'):
        try:
            cookies.clear()
            cookies.save()
            time.sleep(0.1)
            if debug_enabled:
                st.write(f"Debug: Cleared stale auth_role cookie post-logout")
        except Exception as e:
            if debug_enabled:
                st.write(f"Debug: Failed to clear stale cookie: {e}")

def logout():
    """Handle logout with click lock and full state reset."""
    current_time = time.time()
    if st.session_state.get('last_logout_time', 0.0) > current_time - 2:  # 2s cooldown
        if debug_enabled:
            st.write("Debug: Logout skipped due to click lock")
        return
    st.session_state.last_logout_time = current_time
    st.info("Logging out...")
    try:
        delete_auth_cookie(cookies)
    except Exception as e:
        if debug_enabled:
            st.write(f"Debug: Cookie deletion failed: {e}")
    clear_session_state()
    st.session_state.logout_triggered = True
    validate_post_logout_state()
    st.query_params.clear()
    if debug_enabled:
        st.write(f"Debug: Post-logout, auth_role = {cookies.get('auth_role')}, session = {dict(st.session_state)}")
    st.rerun()

def check_authentication():
    # Initialize session state
    init_session_state()

    # Check for recent logout (within 5s)
    current_time = time.time()
    if st.session_state.get('logout_triggered', False) or st.session_state.get('last_logout_time', 0.0) > current_time - 5:
        validate_post_logout_state()
        st.session_state.logout_triggered = False
        return

    # Check cookie for persistent auth
    saved_role = cookies.get('auth_role')
    if saved_role in ["Management", "ReservationTeam"]:
        st.session_state.authenticated = True
        st.session_state.role = saved_role
        try:
            st.session_state.reservations = load_reservations_from_supabase()
            st.session_state.online_reservations = load_online_reservations_from_supabase()
        except Exception as e:
            st.session_state.reservations = []
            st.session_state.online_reservations = []
            st.warning(f"Failed to fetch reservations: {e}")
        # Preserve page and booking
        query_params = st.query_params
        query_page = query_params.get("page", [st.session_state.current_page])[0]
        if query_page in ["Direct Reservations", "View Reservations", "Edit Reservations", "Online Reservations", "Edit Online Reservations", "Daily Status", "Daily Management Status", "Analytics"]:
            st.session_state.current_page = query_page
        query_booking_id = query_params.get("booking_id", [None])[0]
        if query_booking_id:
            st.session_state.selected_booking_id = query_booking_id
        return

    if not st.session_state.authenticated:
        st.title("🔐 TIE Reservations Login")
        st.write("Please select your role and enter the password to access the system.")
        role = st.selectbox("Select Role", ["Management", "ReservationTeam"])
        password = st.text_input("Enter password:", type="password")
        if st.button("🔑 Login"):
            if role == "Management" and password == "TIE2024":
                st.session_state.authenticated = True
                st.session_state.role = "Management"
                try:
                    cookies['auth_role'] = {"value": "Management", "max_age": 2592000}  # 30 days
                    cookies.save()
                    time.sleep(0.1)
                except Exception as e:
                    if debug_enabled:
                        st.write(f"Debug: Failed to set cookie max_age: {e}")
                    cookies['auth_role'] = "Management"
                    cookies.save()
                    time.sleep(0.1)
                try:
                    st.session_state.reservations = load_reservations_from_supabase()
                    st.session_state.online_reservations = load_online_reservations_from_supabase()
                    st.success("✅ Management login successful! Reservations fetched.")
                except Exception as e:
                    st.session_state.reservations = []
                    st.session_state.online_reservations = []
                    st.warning(f"✅ Management login successful, but failed to fetch reservations: {e}")
                st.rerun()
            elif role == "ReservationTeam" and password == "TIE123":
                st.session_state.authenticated = True
                st.session_state.role = "ReservationTeam"
                try:
                    cookies['auth_role'] = {"value": "ReservationTeam", "max_age": 2592000}  # 30 days
                    cookies.save()
                    time.sleep(0.1)
                except Exception as e:
                    if debug_enabled:
                        st.write(f"Debug: Failed to set cookie max_age: {e}")
                    cookies['auth_role'] = "ReservationTeam"
                    cookies.save()
                    time.sleep(0.1)
                try:
                    st.session_state.reservations = load_reservations_from_supabase()
                    st.session_state.online_reservations = load_online_reservations_from_supabase()
                    st.success("✅ Agent login successful! Reservations fetched.")
                except Exception as e:
                    st.session_state.reservations = []
                    st.session_state.online_reservations = []
                    st.warning(f"✅ Agent login successful, but failed to fetch reservations: {e}")
                st.rerun()
            else:
                st.error("❌ Invalid password. Please try again.")
        st.stop()

    # Preserve current page and booking ID
    query_params = st.query_params
    query_page = query_params.get("page", [st.session_state.current_page])[0]
    if query_page in ["Direct Reservations", "View Reservations", "Edit Reservations", "Online Reservations", "Edit Online Reservations", "Daily Status", "Daily Management Status", "Analytics"]:
        st.session_state.current_page = query_page
    query_booking_id = query_params.get("booking_id", [None])[0]
    if query_booking_id:
        st.session_state.selected_booking_id = query_booking_id

def main():
    check_authentication()
    st.title("🏢 TIE Reservations")
    st.markdown("---")
    st.sidebar.title("Navigation")
    page_options = ["Direct Reservations", "View Reservations", "Edit Reservations", "Online Reservations", "Edit Online Reservations", "Daily Status", "Daily Management Status"]
    if st.session_state.get('role') == "Management":
        page_options.append("Analytics")
    
    page = st.sidebar.selectbox("Choose a page", page_options, index=page_options.index(st.session_state.current_page) if st.session_state.current_page in page_options else 0, key="page_select")
    st.session_state.current_page = page

    if page == "Direct Reservations":
        show_new_reservation_form()
    elif page == "View Reservations":
        show_reservations()
    elif page == "Edit Reservations":
        show_edit_reservations()
    elif page == "Online Reservations":
        show_online_reservations()
    elif page == "Edit Online Reservations":
        show_edit_online_reservations(st.session_state.selected_booking_id)
        if st.session_state.selected_booking_id:
            st.session_state.selected_booking_id = None
            if "booking_id" in st.query_params:
                del st.query_params["booking_id"]
    elif page == "Daily Status":
        show_daily_status()
    elif page == "Daily Management Status" and st.session_state.get('role') == "Management":
        show_dms()
    elif page == "Analytics" and st.session_state.get('role') == "Management":
        show_analytics()

    st.sidebar.markdown("---")
    if st.sidebar.button("Log Out"):
        logout()

if __name__ == "__main__":
    main()
