# app.py
import streamlit as st
import os
from supabase import create_client, Client
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

    query_params = st.query_params

    # Auto-login if role is in query params (persists across refreshes)
    if not st.session_state.authenticated:
        if "role" in query_params:
            role_from_query = query_params["role"][0]
            if role_from_query in ["Management", "ReservationTeam"]:
                st.session_state.authenticated = True
                st.session_state.role = role_from_query
                try:
                    st.session_state.reservations = load_reservations_from_supabase()
                    st.session_state.online_reservations = load_online_reservations_from_supabase()
                except Exception as e:
                    st.session_state.reservations = []
                    st.session_state.online_reservations = []
                    st.warning(f"Failed to fetch reservations: {e}")
                # Preserve intended page and booking ID from query params
                query_page = query_params.get("page", ["Direct Reservations"])[0]
                if query_page in ["Direct Reservations", "View Reservations", "Edit Reservations", "Online Reservations", "Edit Online Reservations", "Daily Status", "Daily Management Status", "Analytics"]:
                    st.session_state.current_page = query_page
                query_booking_id = query_params.get("booking_id", [None])[0]
                if query_booking_id:
                    st.session_state.selected_booking_id = query_booking_id
                st.rerun()

    # Preserve current page and selected booking ID from query params if authenticated
    if st.session_state.authenticated:
        query_page = query_params.get("page", [st.session_state.current_page])[0]
        if query_page in ["Direct Reservations", "View Reservations", "Edit Reservations", "Online Reservations", "Edit Online Reservations", "Daily Status", "Daily Management Status", "Analytics"]:
            st.session_state.current_page = query_page
        query_booking_id = query_params.get("booking_id", [None])[0]
        if query_booking_id:
            st.session_state.selected_booking_id = query_booking_id

    if not st.session_state.authenticated:
        st.title("🔐 TIE Reservations Login")
        st.write("Please select your role and enter the password to access the system.")
        role = st.selectbox("Select Role", ["Management", "ReservationTeam"])
        password = st.text_input("Enter password:", type="password")
        if st.button("🔑 Login"):
            if role == "Management" and password == "TIE2024":
                st.session_state.authenticated = True
                st.session_state.role = "Management"
                # Set role in query params to persist across refreshes
                st.query_params["role"] = "Management"
                # Preserve intended page and booking ID from query params after login
                query_page = query_params.get("page", ["Direct Reservations"])[0]
                if query_page in ["Direct Reservations", "View Reservations", "Edit Reservations", "Online Reservations", "Edit Online Reservations", "Daily Status", "Daily Management Status", "Analytics"]:
                    st.session_state.current_page = query_page
                query_booking_id = query_params.get("booking_id", [None])[0]
                if query_booking_id:
                    st.session_state.selected_booking_id = query_booking_id
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
                # Set role in query params to persist across refreshes
                st.query_params["role"] = "ReservationTeam"
                # Preserve intended page and booking ID from query params after login
                query_page = query_params.get("page", ["Direct Reservations"])[0]
                if query_page in ["Direct Reservations", "View Reservations", "Edit Reservations", "Online Reservations", "Edit Online Reservations", "Daily Status"]:
                    st.session_state.current_page = query_page
                query_booking_id = query_params.get("booking_id", [None])[0]
                if query_booking_id:
                    st.session_state.selected_booking_id = query_booking_id
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

def main():
    check_authentication()
    st.title("🏢 TIE Reservations")
    st.markdown("---")
    st.sidebar.title("Navigation")
    page_options = ["Direct Reservations", "View Reservations", "Edit Reservations", "Online Reservations", "Edit Online Reservations", "Daily Status", "Daily Management Status"]
    if st.session_state.role == "Management":
        page_options.append("Analytics")
    
    # Use session state for current page as default
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
        # Clear selected booking ID after displaying the page to prevent stale selections
        if st.session_state.selected_booking_id:
            st.session_state.selected_booking_id = None
            st.query_params.clear()
    elif page == "Daily Status":
        show_daily_status()
    elif page == "Daily Management Status" and st.session_state.role == "Management":
        show_dms()
    elif page == "Analytics" and st.session_state.role == "Management":
        show_analytics()

    # Logout button at the bottom of the sidebar
    st.sidebar.markdown("---")  # Separator for visual bottom placement
    if st.sidebar.button("Log Out"):
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
        if "role" in st.query_params:
            del st.query_params["role"]
        st.query_params.clear()
        st.rerun()

if __name__ == "__main__":
    main()
