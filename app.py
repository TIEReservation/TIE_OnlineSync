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
from dashboard import show_dashboard
import pandas as pd
from users import load_users, create_user, validate_user
from log import show_log_report, log_activity
from summary_report import show_summary_report

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
        st.title("TIE Reservations Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if username == "Admin" and password == "Admin2024":
                st.session_state.authenticated = True
                st.session_state.username = "Admin"
                st.session_state.role = "Admin"
                st.session_state.current_page = "User Management"
                st.session_state.permissions = {"add": True, "edit": True, "delete": True}
            elif username == "Management" and password == "TIE2024":
                st.session_state.authenticated = True
                st.session_state.username = "Management"
                st.session_state.role = "Management"
                st.session_state.current_page = "Inventory Dashboard"
                st.session_state.permissions = {"add": True, "edit": True, "delete": False}
            elif username == "ReservationTeam" and password == "TIE123":
                st.session_state.authenticated = True
                st.session_state.username = "ReservationTeam"
                st.session_state.role = "ReservationTeam"
                st.session_state.current_page = "Direct Reservations"
                st.session_state.permissions = {"add": True, "edit": False, "delete": False}
            else:
                try:
                    users = supabase.table("users").select("*").eq("username", username).eq("password_hash", password).execute().data
                    if users and len(users) == 1:
                        user_data = users[0]
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.role = user_data["role"]
                        st.session_state.user_data = user_data
                        st.session_state.permissions = user_data.get("permissions", {"add": False, "edit": False, "delete": False})
                        valid_screens = ["Inventory Dashboard", "Direct Reservations", "View Reservations", "Edit Direct Reservation", "Online Reservations", "Edit Online Reservations", "Daily Status", "Daily Management Status", "Analytics", "Monthly Consolidation", "Summary Report"]
                        if st.session_state.role == "Admin":
                            valid_screens.append("User Management")
                            valid_screens.append("Log Report")
                            st.session_state.current_page = "User Management"
                        elif st.session_state.role == "Management":
                            st.session_state.current_page = "Inventory Dashboard"
                        else:
                            st.session_state.current_page = "Direct Reservations"
                        st.session_state.permissions["screens"] = valid_screens
                except Exception as e:
                    st.error(f"Error during login: {e}")
            st.rerun()

def show_user_management():
    """User management page for Admin."""
    if st.session_state.role != "Admin":
        st.error("Access Denied: User Management is only for Admin.")
        return

    st.title("👥 User Management")
    users = load_users(supabase)
    if not users:
        st.info("No users found.")
        return

    df = pd.DataFrame(users)
    st.dataframe(df[["username", "role", "properties", "screens"]], use_container_width=True)

    st.subheader("Create New User")
    new_username = st.text_input("New Username")
    new_password = st.text_input("New Password", type="password")
    new_role = st.selectbox("Role", ["ReservationTeam", "Management"])
    new_properties = st.multiselect("Properties", load_properties())
    new_screens = st.multiselect("Screens", ["Inventory Dashboard", "Direct Reservations", "View Reservations", "Edit Direct Reservation", "Online Reservations", "Edit Online Reservations", "Daily Status", "Daily Management Status", "Analytics", "Monthly Consolidation", "Summary Report"])
    if st.button("Create User"):
        if create_user(supabase, new_username, new_password, new_role, new_properties, new_screens):
            st.success(f"User {new_username} created successfully!")
            st.rerun()

def main():
    check_authentication()
    if not st.session_state.authenticated:
        return

    # === Build the navigation list ===
    page_options = ["Inventory Dashboard", "Direct Reservations", "View Reservations", "Edit Direct Reservation", "Online Reservations"]
    if edit_online_available:
        page_options.append("Edit Online Reservations")
    page_options.extend(["Daily Status", "Daily Management Status", "Analytics", "Monthly Consolidation", "Summary Report"])
    if st.session_state.role == "Admin":
        page_options.extend(["User Management", "Log Report"])
    elif st.session_state.role not in ["Management", "Admin"]:
        if "Dashboard" in page_options:
            page_options.remove("Dashboard")

    # === Backward compatibility for old URLs ===
    query_params = st.query_params
    query_page = query_params.get("page", [st.session_state.current_page])[0]
    url_mapping = {
        "Dashboard": "Inventory Dashboard",
        "Edit Reservations": "Edit Direct Reservation"
    }
    if query_page in url_mapping:
        st.session_state.current_page = url_mapping[query_page]
        st.query_params["page"] = st.session_state.current_page

    # === Sidebar Navigation ===
    default_index = page_options.index(st.session_state.current_page) if st.session_state.current_page in page_options else 0
    page = st.sidebar.selectbox("Choose a page", page_options, index=default_index, key="page_select")
    st.session_state.current_page = page

    # === Refresh Button ===
    if st.sidebar.button("Refresh All Data"):
        st.cache_data.clear()
        try:
            st.session_state.reservations = load_reservations_from_supabase()
            st.session_state.online_reservations = load_online_reservations_from_supabase()
            log_activity(supabase, st.session_state.username, "Refreshed all data")
            st.success("Data refreshed from database!")
        except Exception as e:
            st.warning(f"Data refresh partially failed: {e}")
        st.rerun()

    # === Page Routing ===
    if page == "Inventory Dashboard":
        if st.session_state.role not in ["Management", "Admin"]:
            st.error("Access Denied: Inventory Dashboard is only available to Management and Admin.")
            log_activity(supabase, st.session_state.username, "Unauthorized Inventory Dashboard access attempt")
        else:
            show_dashboard()
            log_activity(supabase, st.session_state.username, "Accessed Inventory Dashboard")

    elif page == "Direct Reservations":
        show_new_reservation_form()
        log_activity(supabase, st.session_state.username, "Accessed Direct Reservations")

    elif page == "View Reservations":
        show_reservations()
        log_activity(supabase, st.session_state.username, "Accessed View Reservations")

    elif page == "Edit Direct Reservation":
        show_edit_reservations()
        log_activity(supabase, st.session_state.username, "Accessed Edit Direct Reservation")

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

    elif page == "Daily Management Status":
        show_dms()
        log_activity(supabase, st.session_state.username, "Accessed Daily Management Status")

    elif page == "Analytics":
        if st.session_state.role not in ["Management", "Admin"]:
            st.error("Access Denied: Analytics is only for Management and Admin.")
        else:
            show_analytics()
            log_activity(supabase, st.session_state.username, "Accessed Analytics")

    elif page == "Monthly Consolidation":
        show_monthly_consolidation()
        log_activity(supabase, st.session_state.username, "Accessed Monthly Consolidation")

    elif page == "Summary Report":
        if st.session_state.role not in ["Management", "Admin"]:
            st.error("Access Denied: Summary Report is only for Management and Admin.")
            log_activity(supabase, st.session_state.username, "Unauthorized Summary Report access attempt")
        else:
            show_summary_report()
            log_activity(supabase, st.session_state.username, "Accessed Summary Report")

    elif page == "User Management" and st.session_state.role == "Admin":
        show_user_management()
        log_activity(supabase, st.session_state.username, "Accessed User Management")

    elif page == "Log Report" and st.session_state.role == "Admin":
        show_log_report(supabase)
        log_activity(supabase, st.session_state.username, "Accessed Log Report")

    # === Footer: User Info & Logout ===
    if st.session_state.authenticated:
        st.sidebar.write(f"Logged in as: **{st.session_state.username}**")

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
        st.session_state.current_page = "Direct Reservations"
        st.session_state.selected_booking_id = None
        st.query_params.clear()
        st.rerun()

if __name__ == "__main__":
    main()
