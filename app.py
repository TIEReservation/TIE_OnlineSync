import streamlit as st
import os
from supabase import create_client, Client
from directreservation import show_new_reservation_form, show_reservations, show_edit_reservations, show_analytics, load_reservations_from_supabase
from online_reservation import show_online_reservations, load_online_reservations_from_supabase
try:
    from editOnline import show_edit_online_reservations
    edit_online_available = True
except Exception as e:
    st.error(f"Failed to import editOnline module: {e}. 'Edit Online Reservations' page will be disabled.")
    show_edit_online_reservations = None
    edit_online_available = False
from inventory import show_daily_status
from dms import show_dms
from monthlyconsolidation import show_monthly_consolidation
import pandas as pd
from log import show_log_report, log_activity
from dashboard import show_dashboard  # Added import for dashboard

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
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.role = None
        st.session_state.reservations = []
        st.session_state.online_reservations = []
        st.session_state.edit_mode = False
        st.session_state.edit_index = None
        st.session_state.online_edit_mode = False
        st.session_state.online_edit_index = None
        st.session_state.current_page = "Direct Reservations"
        st.session_state.selected_booking_id = None
        st.session_state.user_data = None
        st.session_state.permissions = None  # Initialize permissions attribute

    if not st.session_state.authenticated:
        st.title("🔐 TIE Reservations Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("🔑 Login"):
            if username == "Admin" and password == "Admin2024":
                st.session_state.authenticated = True
                st.session_state.username = "Admin"
                st.session_state.role = "Admin"
                st.session_state.current_page = "User Management"
                st.session_state.permissions = {"add": True, "edit": True, "delete": True}  # Default for Admin
            elif username == "Management" and password == "TIE2024":
                st.session_state.authenticated = True
                st.session_state.username = "Management"
                st.session_state.role = "Management"
                st.session_state.current_page = "Direct Reservations"
                st.session_state.permissions = {"add": True, "edit": True, "delete": False}  # Example for Management
            elif username == "ReservationTeam" and password == "TIE123":
                st.session_state.authenticated = True
                st.session_state.username = "ReservationTeam"
                st.session_state.role = "ReservationTeam"
                st.session_state.current_page = "Direct Reservations"
                st.session_state.permissions = {"add": True, "edit": False, "delete": False}  # Example for ReservationTeam
            else:
                try:
                    users = supabase.table("users").select("*").eq("username", username).eq("password_hash", password).execute().data
                    if users and len(users) == 1:
                        user_data = users[0]
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.role = user_data["role"]
                        st.session_state.user_data = user_data
                        st.session_state.permissions = user_data.get("permissions", {"add": False, "edit": False, "delete": False})  # Extract permissions
                        valid_screens = ["Direct Reservations", "View Reservations", "Edit Reservations", "Online Reservations", "Edit Online Reservations", "Daily Status", "Daily Management Status", "Analytics", "Monthly Consolidation"]
                        st.session_state.current_page = "Direct Reservations"
                except Exception as e:
                    st.error(f"Login failed: {e}")
        return False  # Indicate that authentication is not complete
    return True  # Indicate that authentication is complete

def main():
    if not check_authentication():  # Only show login screen if not authenticated
        return

    st.title("🏢 TIE Reservations")
    st.markdown("---")
    st.sidebar.title("Navigation")
    page_options = ["Direct Reservations", "View Reservations", "Edit Reservations", "Online Reservations", "Daily Status", "Daily Management Status", "Monthly Consolidation"]
    if st.session_state.role == "Management":
        page_options.append("Analytics")
    if edit_online_available:
        page_options.insert(4, "Edit Online Reservations")
    if st.session_state.role == "Admin":
        page_options.append("User Management")
        page_options.append("Log Report")  # Added Log Report for Admin
    if st.session_state.role in ["Management", "Admin"]:
        page_options.append("Dashboard")  # Added Dashboard for Management and Admin

    if st.session_state.user_data:
        page_options = [p for p in page_options if p in st.session_state.user_data.get("screens", page_options)]

    page = st.sidebar.selectbox("Choose a page", page_options, index=page_options.index(st.session_state.current_page) if st.session_state.current_page in page_options else 0, key="page_select")
    st.session_state.current_page = page

    if st.sidebar.button("🔄 Refresh All Data"):
        st.cache_data.clear()
        try:
            st.session_state.reservations = load_reservations_from_supabase()
            st.session_state.online_reservations = load_online_reservations_from_supabase()
            log_activity(supabase, st.session_state.username, "Refreshed all data")
            st.success("✅ Data refreshed from database!")
        except Exception as e:
            st.warning(f"⚠️ Data refresh partially failed: {e}")
        st.rerun()

    if page == "Direct Reservations":
        show_new_reservation_form()
        log_activity(supabase, st.session_state.username, "Accessed Direct Reservations")
    elif page == "View Reservations":
        show_reservations()
        log_activity(supabase, st.session_state.username, "Accessed View Reservations")
    elif page == "Edit Reservations":
        show_edit_reservations()
        log_activity(supabase, st.session_state.username, "Accessed Edit Reservations")
    elif page == "Online Reservations":
        show_online_reservations()
        log_activity(supabase, st.session_state.username, "Accessed Online Reservations")
    elif page == "Edit Online Reservations" and edit_online_available:
        show_edit_online_reservations(st.session_state.selected_booking_id)
        if st.session_state.selected_booking_id:
            st.session_state.selected_booking_id = None
            st.query_params.clear()
        log_activity(supabase, st.session_state.username, "Accessed Edit Online Reservations")
    elif page == "Daily Status":
        show_daily_status()
        log_activity(supabase, st.session_state.username, "Accessed Daily Status")
    elif page == "Daily Management Status" and st.session_state.current_page == "Daily Management Status":
        show_dms()
        log_activity(supabase, st.session_state.username, "Accessed Daily Management Status")
    elif page == "Analytics" and st.session_state.role == "Management":
        show_analytics()
        log_activity(supabase, st.session_state.username, "Accessed Analytics")
    elif page == "Monthly Consolidation":
        show_monthly_consolidation()
        log_activity(supabase, st.session_state.username, "Accessed Monthly Consolidation")
    elif page == "User Management" and st.session_state.role == "Admin":
        show_user_management()
        log_activity(supabase, st.session_state.username, "Accessed User Management")
    elif page == "Log Report" and st.session_state.role == "Admin":
        show_log_report(supabase)
        log_activity(supabase, st.session_state.username, "Accessed Log Report")
    elif page == "Dashboard":
        show_dashboard()
        log_activity(supabase, st.session_state.username, "Accessed Dashboard")

    # Display username before Log Out button
    if st.session_state.authenticated:
        st.sidebar.write(f"Logged in as: {st.session_state.username}")
    if st.sidebar.button("Log Out"):
        log_activity(supabase, st.session_state.username, "Logged out")
        st.cache_data.clear()
        st.cache_resource.clear()
        for key in list(st.session_state.keys()):
            del st.session_state[key]
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
        st.query_params.clear()
        st.rerun()

if __name__ == "__main__":
    main()
