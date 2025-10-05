# app.py
import streamlit as st
import os
import time
from supabase import create_client, Client
from streamlit_cookies_manager import EncryptedCookieManager
from directreservation import show_new_reservation_form, show_reservations, show_edit_reservations, show_analytics, load_reservations_from_supabase
from online_reservation import show_online_reservations, load_online_reservations_from_supabase
from editOnline import show_edit_online_reservations
from inventory import show_daily_status
from dms import show_dms

# Page config
st.set_page_config(
    page_title="TIE Reservations",
    page_icon="https://github.com/TIEReservation/TIEReservation-System/raw/main/TIE_Logo_Icon.png",
    layout="wide"
)

# Display logo in top-left corner
st.image("https://github.com/TIEReservation/TIEReservation-System/raw/main/TIE_Logo_Icon.png", width=100)

# Initialize Supabase client with environment variables
try:
    os.environ["SUPABASE_URL"] = "https://oxbrezracnmazucnnqox.supabase.co"
    os.environ["SUPABASE_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im94YnJlenJhY25tYXp1Y25ucW94Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM3NjUxMTgsImV4cCI6MjA2OTM0MTExOH0.nqBK2ZxntesLY9qYClpoFPVnXOW10KrzF-UI_DKjbKo"
    supabase: Client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
except Exception as e:
    st.error(f"Failed to initialize Supabase client: {e}")
    st.stop()

# Cookie manager for persistent authentication
cookies = EncryptedCookieManager(
    prefix="tie_reservations_",
    password=st.secrets["cookies"]["password"]  # Set in Streamlit secrets
)
if not cookies.ready():
    st.stop()

def check_authentication():
    # Initialize session state if not already set
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.role = None
        st.session_state.reservations = []
        st.session_state.online_reservations = []
        st.session_state.edit_mode = False
        st.session_state.edit_index = None
        st.session_state.online_edit_mode = False
        st.session_state.online_edit_index = None
        st.session_state.current_page = "Direct Reservations"
        st.session_state.selected_booking_id = None

    # Check for persistent cookie
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
        # Preserve page and booking from query params
        query_params = st.query_params
        query_page = query_params.get("page", [st.session_state.current_page])[0]
        if query_page in ["Direct Reservations", "View Reservations", "Edit Reservations", "Online Reservations", "Edit Online Reservations", "Daily Status", "Daily Management Status", "Analytics"]:
            st.session_state.current_page = query_page
        query_booking_id = query_params.get("booking_id", [None])[0]
        if query_booking_id:
            st.session_state.selected_booking_id = query_booking_id
        return  # Already authenticated via cookie

    if not st.session_state.authenticated:
        st.title("🔐 TIE Reservations Login")
        st.write("Please select your role and enter the password to access the system.")
        role = st.selectbox("Select Role", ["Management", "ReservationTeam"])
        password = st.text_input("Enter password:", type="password")
        if st.button("🔑 Login"):
            if role == "Management" and password == "TIE2024":
                st.session_state.authenticated = True
                st.session_state.role = "Management"
                cookies['auth_role'] = "Management"
                cookies.save()
                time.sleep(0.1)  # Ensure cookie sync
                # ... (load reservations, success, rerun as before)
                st.rerun()
            elif role == "ReservationTeam" and password == "TIE123":
                st.session_state.authenticated = True
                st.session_state.role = "ReservationTeam"
                cookies['auth_role'] = "ReservationTeam"
                cookies.save()
                time.sleep(0.1)  # Ensure cookie sync
                # ... (load, success, rerun as before)
                st.rerun()
            else:
                st.error("❌ Invalid password. Please try again.")
        st.stop()

    # If authenticated (non-cookie path), preserve query params as before

def main():
    check_authentication()
    # ... (title, sidebar, page selection as before)

    # Logout button
    st.sidebar.markdown("---")
    if st.sidebar.button("Log Out"):
        if 'auth_role' in cookies:
            del cookies['auth_role']
            cookies.save()
            time.sleep(0.1)
        st.session_state.authenticated = False
        st.session_state.role = None
        # ... (clear other state, query_params.clear(), rerun as before)

if __name__ == "__main__":
    main()
