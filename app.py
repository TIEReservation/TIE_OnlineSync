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
from log import show_log_report, show_user_dashboard, log_activity

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
        st.session_state.permissions = None

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
                st.session_state.permissions = {"add": True, "edit": True, "delete": True}
            elif username == "Management" and password == "TIE2024":
                st.session_state.authenticated = True
                st.session_state.username = "Management"
                st.session_state.role = "Management"
                st.session_state.current_page = "Direct Reservations"
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
                        valid_screens = ["Direct Reservations", "View Reservations", "Edit Reservations", "Online Reservations", "Edit Online Reservations", "Daily Status", "Daily Management Status", "Analytics", "Monthly Consolidation", "User Dashboard"]
                        if st.session_state.role == "Admin":
                            valid_screens.append("User Management")
                            valid_screens.append("Log Report")
                        elif st.session_state.role == "Management":
                            valid_screens = [s for s in valid_screens if s not in ["User Management", "Log Report"]]
                        st.session_state.current_page = next((s for s in valid_screens if s in user_data.get("screens", ["Direct Reservations"])), "Direct Reservations")
                    else:
                        st.error("❌ Invalid username or password.")
                except Exception as e:
                    st.warning(f"⚠️ Database query failed: {e}. Falling back to hardcoded credentials.")
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
                        st.session_state.current_page = "Direct Reservations"
                        st.session_state.permissions = {"add": True, "edit": True, "delete": False}
                    elif username == "ReservationTeam" and password == "TIE123":
                        st.session_state.authenticated = True
                        st.session_state.username = "ReservationTeam"
                        st.session_state.role = "ReservationTeam"
                        st.session_state.current_page = "Direct Reservations"
                        st.session_state.permissions = {"add": True, "edit": False, "delete": False}
                    else:
                        st.error("❌ Invalid username or password.")
            if st.session_state.authenticated:
                query_params = st.query_params
                query_booking_id = query_params.get("booking_id", [None])[0]
                if query_booking_id:
                    st.session_state.selected_booking_id = query_booking_id
                try:
                    st.session_state.reservations = load_reservations_from_supabase()
                    st.session_state.online_reservations = load_online_reservations_from_supabase()
                    st.success(f"✅ {username} login successful!")
                except Exception as e:
                    st.session_state.reservations = []
                    st.session_state.online_reservations = []
                    st.warning(f"✅ {username} login successful, but failed to fetch data: {e}")
                st.rerun()
        st.stop()
    else:
        query_params = st.query_params
        query_page = query_params.get("page", [st.session_state.current_page])[0]
        valid_screens = ["Direct Reservations", "View Reservations", "Edit Reservations", "Online Reservations", "Edit Online Reservations", "Daily Status", "Daily Management Status", "Analytics", "Monthly Consolidation", "User Dashboard"]
        if st.session_state.role == "Admin":
            valid_screens.append("User Management")
            valid_screens.append("Log Report")
        elif st.session_state.role == "Management":
            valid_screens = [s for s in valid_screens if s not in ["User Management", "Log Report"]]
        if st.session_state.user_data and query_page not in st.session_state.user_data.get("screens", valid_screens):
            st.error(f"❌ Access Denied: You do not have permission to view {query_page}.")
            st.session_state.current_page = "Direct Reservations"
        elif query_page in valid_screens:
            st.session_state.current_page = query_page
        query_booking_id = query_params.get("booking_id", [None])[0]
        if query_booking_id:
            st.session_state.selected_booking_id = query_booking_id

def show_user_management():
    if st.session_state.role != "Admin":
        st.error("❌ Access Denied: User Management is available only for Admin.")
        return
    st.header("👥 User Management")

    users = supabase.table("users").select("*").execute().data
    if not users:
        st.info("No users found.")
        return
    df = pd.DataFrame(users)
    st.subheader("Existing Users")
    st.dataframe(df[["username", "role", "properties", "screens", "permissions"]])

    # Create new user
    st.subheader("Create New User")
    with st.form("create_user_form"):
        new_username = st.text_input("Username")
        new_password = st.text_input("Password", type="password")
        new_role = st.selectbox("Role", ["Management", "ReservationTeam"])
        all_properties = [
            "Le Poshe Beach view", "La Millionaire Resort", "Le Poshe Luxury", "Le Poshe Suite",
            "La Paradise Residency", "La Paradise Luxury", "La Villa Heritage", "Le Pondy Beach Side",
            "Le Royce Villa", "La Tamara Luxury", "Eden Beach Resort", "Le Poshe Beach", "La Millionaire",
            "Le Poshe Deluxe", "La Paradise"
        ]
        new_properties = st.multiselect("Visible Properties", all_properties, default=all_properties)
        all_screens = ["Direct Reservations", "View Reservations", "Edit Reservations", "Online Reservations", "Edit Online Reservations", "Daily Status", "Daily Management Status", "Analytics", "Monthly Consolidation", "User Dashboard"]
        default_screens = all_screens if new_role == "Management" else [s for s in all_screens if s not in ["Daily Management Status", "Analytics"]]
        new_screens = st.multiselect("Visible Screens", all_screens, default=default_screens)
        add_perm = st.checkbox("Add Permission", value=True)
        edit_perm = st.checkbox("Edit Permission", value=True)
        delete_perm = st.checkbox("Delete Permission", value=True)
        if st.form_submit_button("Create User"):
            existing = supabase.table("users").select("*").eq("username", new_username).execute().data
            if existing:
                st.error("Username already exists.")
            else:
                new_user = {
                    "username": new_username,
                    "password_hash": new_password,
                    "role": new_role,
                    "properties": new_properties,
                    "screens": new_screens,
                    "permissions": {"add": add_perm, "edit": edit_perm, "delete": delete_perm}
                }
                try:
                    supabase.table("users").insert(new_user).execute()
                    log_activity(supabase, st.session_state.username, f"Created user {new_username}")
                    st.success(f"✅ User {new_username} created successfully!")
                except Exception as e:
                    st.error(f"❌ Failed to create user: {e}")
                st.rerun()

    # Modify user
    st.subheader("Modify User")
    modify_username = st.selectbox("Select User to Modify", [u["username"] for u in users if u["username"] != "Admin"])
    if modify_username:
        user_to_modify = next(u for u in users if u["username"] == modify_username)
        with st.form("modify_user_form"):
            mod_role = st.selectbox("Role", ["Management", "ReservationTeam"], index=0 if user_to_modify["role"] == "Management" else 1)
            all_properties = [
                "Le Poshe Beach view", "La Millionaire Resort", "Le Poshe Luxury", "Le Poshe Suite",
                "La Paradise Residency", "La Paradise Luxury", "La Villa Heritage", "Le Pondy Beach Side",
                "Le Royce Villa", "La Tamara Luxury", "Eden Beach Resort", "Le Poshe Beach", "La Millionaire",
                "Le Poshe Deluxe", "La Paradise"
            ]
            default_properties = [prop for prop in user_to_modify.get("properties", []) if prop in all_properties]
            mod_properties = st.multiselect("Visible Properties", all_properties, default=default_properties if default_properties else all_properties)
            all_screens = ["Direct Reservations", "View Reservations", "Edit Reservations", "Online Reservations", "Edit Online Reservations", "Daily Status", "Daily Management Status", "Analytics", "Monthly Consolidation", "User Dashboard"]
            mod_screens = st.multiselect("Visible Screens", all_screens, default=user_to_modify["screens"])
            perms = user_to_modify["permissions"]
            mod_add = st.checkbox("Add Permission", value=perms["add"])
            mod_edit = st.checkbox("Edit Permission", value=perms["edit"])
            mod_delete = st.checkbox("Delete Permission", value=perms["delete"])
            if st.form_submit_button("Update User"):
                updated_user = {
                    "role": mod_role,
                    "properties": mod_properties,
                    "screens": mod_screens,
                    "permissions": {"add": mod_add, "edit": mod_edit, "delete": mod_delete}
                }
                try:
                    supabase.table("users").update(updated_user).eq("username", modify_username).execute()
                    log_activity(supabase, st.session_state.username, f"Modified user {modify_username}")
                    st.success(f"✅ User {modify_username} updated successfully!")
                except Exception as e:
                    st.error(f"❌ Failed to update user: {e}")
                st.rerun()

    # Delete user
    st.subheader("Delete User")
    delete_username = st.selectbox("Select User to Delete", [u["username"] for u in users if u["username"] not in ["Admin", "Management", "ReservationTeam"]])
    if delete_username and st.button("Delete User"):
        try:
            supabase.table("users").delete().eq("username", delete_username).execute()
            log_activity(supabase, st.session_state.username, f"Deleted user {delete_username}")
            st.success(f"🗑️ User {delete_username} deleted successfully!")
        except Exception as e:
            st.error(f"❌ Failed to delete user: {e}")
        st.rerun()

def load_property_room_map():
    return {
        "Le Poshe Beach view": {"Double Room": ["101", "102", "202", "203", "204"], "Standard Room": ["201"], "Deluex Double Room Seaview": ["301", "302", "303", "304"], "Day Use": ["Day Use 1", "Day Use 2"], "No Show": ["No Show"]},
        "La Millionaire Resort": {"Double Room": ["101", "102", "103", "105"], "Deluex Double Room with Balcony": ["205", "304", "305"], "Deluex Triple Room with Balcony": ["201", "202", "203", "204", "301", "302", "303"], "Deluex Family Room with Balcony": ["206", "207", "208", "306", "307", "308"], "Deluex Triple Room": ["402"], "Deluex Family Room": ["401"], "Day Use": ["Day Use 1", "Day Use 2", "Day Use 3", "Day Use 5"], "No Show": ["No Show"]},
        "Le Poshe Luxury": {"2BHA Appartment": ["101&102", "101", "102"], "2BHA Appartment with Balcony": ["201&202", "201", "202", "301&302", "301", "302", "401&402", "401", "402"], "3BHA Appartment": ["203to205", "203", "204", "205", "303to305", "303", "304", "305", "403to405", "403", "404", "405"], "Double Room with Private Terrace": ["501"], "Day Use": ["Day Use 1", "Day Use 2"], "No Show": ["No Show"]},
        "Le Poshe Suite": {"2BHA Appartment": ["601&602", "601", "602", "603", "604", "703", "704"], "2BHA Appartment with Balcony": ["701&702", "701", "702"], "Double Room with Terrace": ["801"], "Day Use": ["Day Use 1", "Day Use 2"], "No Show": ["No Show"]},
        "La Paradise Residency": {"Double Room": ["101", "102", "103", "301", "302", "304"], "Family Room": ["201", "203"], "Triple Room": ["202", "303"], "Day Use": ["Day Use 1", "Day Use 2"], "No Show": ["No Show"]},
        "La Paradise Luxury": {"3BHA Appartment": ["101to103", "101", "102", "103", "201to203", "201", "202", "203"], "Day Use": ["Day Use 1", "Day Use 2"], "No Show": ["No Show"]},
        "La Villa Heritage": {"Double Room": ["101", "102", "103"], "4BHA Appartment": ["201to203&301", "201", "202", "203", "301"], "Day Use": ["Day Use 1", "Day Use 2"], "No Show": ["No Show"]},
        "Le Pondy Beach Side": {"Villa": ["101to104", "101", "102", "103", "104"], "Day Use": ["Day Use 1", "Day Use 2"], "No Show": ["No Show"]},
        "Le Royce Villa": {"Villa": ["101to102&201to202", "101", "102", "201", "202"], "Day Use": ["Day Use 1", "Day Use 2"], "No Show": ["No Show"]},
        "La Tamara Luxury": {"3BHA": ["101to103", "101", "102", "103", "104to106", "104", "105", "106", "201to203", "201", "202", "203", "204to206", "204", "205", "206", "301to303", "301", "302", "303", "304to306", "304", "305", "306"], "4BHA": ["401to404", "401", "402", "403", "404"], "Day Use": ["Day Use 1", "Day Use 2"], "No Show": ["No Show"]},
        "La Antilia Luxury": {"Deluex Suite Room": ["101"], "Deluex Double Room": ["203", "204", "303", "304"], "Family Room": ["201", "202", "301", "302"], "Deluex suite Room with Tarrace": ["404"], "Day Use": ["Day Use 1", "Day Use 2"], "No Show": ["No Show"]},
        "La Tamara Suite": {"Two Bedroom apartment": ["101&102"], "Deluxe Apartment": ["103&104"], "Deluxe Double Room": ["203", "204", "205"], "Deluxe Triple Room": ["201", "202"], "Deluxe Family Room": ["206"], "Day Use": ["Day Use 1", "Day Use 2"], "No Show": ["No Show"]}
    }

def main():
    check_authentication()
    st.title("🏢 TIE Reservations")
    st.markdown("---")
    st.sidebar.title("Navigation")
    page_options = ["Direct Reservations", "View Reservations", "Edit Reservations", "Online Reservations", "Daily Status", "Daily Management Status", "Monthly Consolidation", "User Dashboard"]
    if st.session_state.role == "Management":
        page_options.append("Analytics")
    if edit_online_available:
        page_options.insert(4, "Edit Online Reservations")
    if st.session_state.role == "Admin":
        page_options.append("User Management")
        page_options.append("Log Report")

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
    elif page == "User Dashboard":
        show_user_dashboard(supabase)
        log_activity(supabase, st.session_state.username, "Accessed User Dashboard")

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
