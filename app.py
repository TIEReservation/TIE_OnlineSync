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
from summary_report import show_summary_report  # NEW IMPORT
import pandas as pd
from log import show_log_report, log_activity
from users import validate_user, create_user, update_user, delete_user, load_users

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
        st.title("TIE Reservations Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            # First check hardcoded credentials
            if username == "Admin" and password == "Admin2024":
                st.session_state.authenticated = True
                st.session_state.username = "Admin"
                st.session_state.role = "Admin"
                st.session_state.current_page = "User Management"
                st.session_state.permissions = {"add": True, "edit": True, "delete": True}
                st.session_state.user_data = None
            elif username == "Management" and password == "Admin2024":
                st.session_state.authenticated = True
                st.session_state.username = "Management"
                st.session_state.role = "Management"
                st.session_state.current_page = "Inventory Dashboard"
                st.session_state.permissions = {"add": True, "edit": True, "delete": False}
                st.session_state.user_data = None
            elif username == "ReservationTeam" and password == "Admin2024":
                st.session_state.authenticated = True
                st.session_state.username = "ReservationTeam"
                st.session_state.role = "ReservationTeam"
                st.session_state.current_page = "Direct Reservations"
                st.session_state.permissions = {"add": True, "edit": False, "delete": False}
                st.session_state.user_data = None
            elif username == "ReservationHead" and password == "Admin2024":
                st.session_state.authenticated = True
                st.session_state.username = "ReservationHead"
                st.session_state.role = "ReservationHead"
                st.session_state.current_page = "Direct Reservations"
                st.session_state.permissions = {"add": True, "edit": False, "delete": False}
                st.session_state.user_data = None
            else:
                # Try database authentication with proper password hashing
                try:
                    user_data = validate_user(supabase, username, password)
                    if user_data:
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.role = user_data["role"]
                        st.session_state.user_data = user_data
                        st.session_state.permissions = user_data.get("permissions", {"add": False, "edit": False, "delete": False})
                        
                        valid_screens = ["Inventory Dashboard", "Direct Reservations", "View Reservations", "Edit Direct Reservation", "Online Reservations", "Edit Online Reservations", "Daily Status", "Daily Management Status", "Analytics", "Monthly Consolidation", "Summary Report"]
                        
                        if st.session_state.role == "Admin":
                            valid_screens.append("User Management")
                        elif st.session_state.role == "Management":
                            valid_screens = [s for s in valid_screens if s not in ["User Management"]]
                        
                        user_screens = user_data.get("screens", ["Direct Reservations"])
                        st.session_state.current_page = next((s for s in valid_screens if s in user_screens), "Direct Reservations")
                    else:
                        st.error("Invalid username or password.")
                except Exception as e:
                    st.error(f"Database authentication failed: {e}")
                    st.error("Invalid username or password.")
            
            if st.session_state.authenticated:
                query_params = st.query_params
                query_booking_id = query_params.get("booking_id", [None])[0]
                if query_booking_id:
                    st.session_state.selected_booking_id = query_booking_id
                try:
                    if st.session_state.role != "Admin":
                        st.session_state.reservations = load_reservations_from_supabase()
                        st.session_state.online_reservations = load_online_reservations_from_supabase()
                    st.success(f"{username} login successful!")
                except Exception as e:
                    st.session_state.reservations = []
                    st.session_state.online_reservations = []
                    st.warning(f"{username} login successful, but failed to fetch data: {e}")
                st.rerun()
        st.stop()
    else:
        query_params = st.query_params
        query_page = query_params.get("page", [st.session_state.current_page])[0]
        
        valid_screens = ["Inventory Dashboard", "Direct Reservations", "View Reservations", "Edit Direct Reservation", "Online Reservations", "Edit Online Reservations", "Daily Status", "Daily Management Status", "Analytics", "Monthly Consolidation", "Summary Report"]
        
        if st.session_state.role == "Admin":
            valid_screens = ["User Management"]
        elif st.session_state.role == "Management":
            valid_screens = [s for s in valid_screens if s not in ["User Management"]]
        
        if st.session_state.user_data and query_page not in st.session_state.user_data.get("screens", valid_screens):
            st.error(f"Access Denied: You do not have permission to view {query_page}.")
            st.session_state.current_page = valid_screens[0] if valid_screens else "Direct Reservations"
        elif query_page in valid_screens:
            st.session_state.current_page = query_page
        
        query_booking_id = query_params.get("booking_id", [None])[0]
        if query_booking_id:
            st.session_state.selected_booking_id = query_booking_id

def show_user_management():
    if st.session_state.role != "Admin":
        st.error("Access Denied: User Management is available only for Admin.")
        return
    
    st.header("User Management")

    users = load_users(supabase)
    if not users:
        st.info("No users found in database.")
    else:
        st.subheader("Existing Users")
        df = pd.DataFrame(users)
        display_columns = ["username", "role"]
        if "properties" in df.columns:
            display_columns.append("properties")
        if "screens" in df.columns:
            display_columns.append("screens")
        if "permissions" in df.columns:
            display_columns.append("permissions")
        st.dataframe(df[display_columns])

    st.markdown("---")

    # Create new user
    st.subheader("Create New User")
    with st.form("create_user_form", clear_on_submit=False):
        new_username = st.text_input("Username", key="create_username")
        new_password = st.text_input("Password", type="password", key="create_password")
        new_role = st.selectbox("Role", ["Management", "ReservationTeam", "ReservationHead"], key="create_role")
        
        all_properties = [
            "Le Poshe Beachview", "La Millionaire Resort", "Le Poshe Luxury", "Le Poshe Suite",
            "La Paradise Residency", "La Paradise Luxury", "La Villa Heritage", "Le Pondy Beach Side",
            "Le Royce Villa", "La Tamara Luxury", "La Antilia Luxury", "La Tamara Suite",
            "Le Park Resort", "Villa Shakti", "Eden Beach Resort", "La Coromandel Luxury",
            "Le Terra", "Happymates Forest Retreat"
        ]
        new_properties = st.multiselect("Visible Properties", all_properties, default=all_properties, key="create_properties")
        
        all_screens = ["Inventory Dashboard", "Direct Reservations", "View Reservations", "Edit Direct Reservation", "Online Reservations", "Edit Online Reservations", "Daily Status", "Daily Management Status", "Analytics", "Monthly Consolidation", "Summary Report"]
        
        # Default screens based on role
        if new_role == "Management":
            default_screens = all_screens
        elif new_role == "ReservationHead":
            default_screens = ["Direct Reservations", "View Reservations", "Edit Direct Reservation", "Online Reservations", "Edit Online Reservations", "Daily Status", "Monthly Consolidation", "Summary Report"]
        else:
            default_screens = [s for s in all_screens if s not in ["Daily Management Status", "Analytics", "Inventory Dashboard", "Summary Report"]]
        
        new_screens = st.multiselect("Visible Screens", all_screens, default=default_screens, key="create_screens")
        
        add_perm = st.checkbox("Add Permission", value=True, key="create_add_perm")
        edit_perm = st.checkbox("Edit Permission", value=True, key="create_edit_perm")
        delete_perm = st.checkbox("Delete Permission", value=False, key="create_delete_perm")
        
        submit_create = st.form_submit_button("Create User")
        
        if submit_create:
            if not new_username or not new_password:
                st.error("Username and Password are required!")
            else:
                # Check if user already exists
                existing = supabase.table("users").select("*").eq("username", new_username).execute().data
                if existing:
                    st.error(f"Username '{new_username}' already exists.")
                else:
                    new_permissions = {"add": add_perm, "edit": edit_perm, "delete": delete_perm}
                    success = create_user(supabase, new_username, new_password, new_role, new_properties, new_screens, new_permissions)
                    if success:
                        log_activity(supabase, st.session_state.username, f"Created user {new_username}")
                        st.rerun()

    st.markdown("---")

    # Modify existing user
    st.subheader("Modify Existing User")
    if users:
        modifiable_users = [u["username"] for u in users if u["username"] not in ["Admin", "Management", "ReservationTeam"]]
        
        if not modifiable_users:
            st.info("No modifiable users found. Protected users (Admin, Management, ReservationTeam) cannot be modified.")
        else:
            modify_username = st.selectbox("Select User to Modify", modifiable_users, key="modify_username_select")
            
            if modify_username:
                user_to_modify = next((u for u in users if u["username"] == modify_username), None)
                
                if user_to_modify:
                    with st.form("modify_user_form", clear_on_submit=False):
                        st.write(f"**Modifying User: {modify_username}**")
                        
                        mod_password = st.text_input("New Password (leave blank to keep current)", type="password", key="modify_password")
                        
                        current_role = user_to_modify.get("role", "ReservationTeam")
                        mod_role = st.selectbox("Role", ["Management", "ReservationTeam", "ReservationHead"], 
                                              index=["Management", "ReservationTeam", "ReservationHead"].index(current_role) if current_role in ["Management", "ReservationTeam", "ReservationHead"] else 1, 
                                              key="modify_role")
                        
                        all_properties = [
                            "Le Poshe Beachview", "La Millionaire Resort", "Le Poshe Luxury", "Le Poshe Suite",
                            "La Paradise Residency", "La Paradise Luxury", "La Villa Heritage", "Le Pondy Beach Side",
                            "Le Royce Villa", "La Tamara Luxury", "La Antilia Luxury", "La Tamara Suite",
                            "Le Park Resort", "Villa Shakti", "Eden Beach Resort", "La Coromandel Luxury",
                            "Le Terra", "Happymates Forest Retreat"
                        ]
                        current_properties = user_to_modify.get("properties", [])
                        default_properties = [prop for prop in current_properties if prop in all_properties]
                        if not default_properties:
                            default_properties = all_properties
                        mod_properties = st.multiselect("Visible Properties", all_properties, default=default_properties, key="modify_properties")
                        
                        all_screens = ["Inventory Dashboard", "Direct Reservations", "View Reservations", "Edit Direct Reservation", "Online Reservations", "Edit Online Reservations", "Daily Status", "Daily Management Status", "Analytics", "Monthly Consolidation", "Summary Report"]
                        current_screens = user_to_modify.get("screens", [])
                        # Filter out any screens that don't exist in all_screens to avoid the error
                        valid_current_screens = [screen for screen in current_screens if screen in all_screens]
                        mod_screens = st.multiselect("Visible Screens", all_screens, default=valid_current_screens, key="modify_screens")
                        
                        current_perms = user_to_modify.get("permissions", {"add": False, "edit": False, "delete": False})
                        mod_add = st.checkbox("Add Permission", value=current_perms.get("add", False), key="modify_add_perm")
                        mod_edit = st.checkbox("Edit Permission", value=current_perms.get("edit", False), key="modify_edit_perm")
                        mod_delete = st.checkbox("Delete Permission", value=current_perms.get("delete", False), key="modify_delete_perm")
                        
                        submit_modify = st.form_submit_button("Update User")
                        
                        if submit_modify:
                            mod_permissions = {"add": mod_add, "edit": mod_edit, "delete": mod_delete}
                            success = update_user(
                                supabase, 
                                modify_username, 
                                password=mod_password if mod_password else None,
                                role=mod_role,
                                properties=mod_properties,
                                screens=mod_screens,
                                permissions=mod_permissions
                            )
                            if success:
                                log_activity(supabase, st.session_state.username, f"Modified user {modify_username}")
                                st.rerun()

    st.markdown("---")

    # Delete user
    st.subheader("Delete User")
    if users:
        deletable_users = [u["username"] for u in users if u["username"] not in ["Admin", "Management", "ReservationTeam"]]
        
        if not deletable_users:
            st.info("No deletable users found. Protected users (Admin, Management, ReservationTeam) cannot be deleted.")
        else:
            delete_username = st.selectbox("Select User to Delete", deletable_users, key="delete_username_select")
            
            if delete_username:
                st.warning(f"⚠️ You are about to delete user: **{delete_username}**")
                st.write("This action cannot be undone!")
                
                if st.button("🗑️ Confirm Delete User", key="delete_user_button"):
                    success = delete_user(supabase, delete_username)
                    if success:
                        log_activity(supabase, st.session_state.username, f"Deleted user {delete_username}")
                        st.rerun()

def main():
    check_authentication()
    st.title("TIE Reservations")
    st.markdown("---")
    st.sidebar.title("Navigation")

    # === Build page options based on role ===
    if st.session_state.role == "Admin":
        page_options = ["User Management", "Log Report"]
    elif st.session_state.role == "Management":
        page_options = [
            "Inventory Dashboard", "Direct Reservations", "View Reservations", "Edit Direct Reservation",
            "Online Reservations", "Daily Status", "Daily Management Status", "Analytics", "Monthly Consolidation", "Summary Report"
        ]
        if edit_online_available:
            page_options.insert(page_options.index("Daily Status"), "Edit Online Reservations")
    elif st.session_state.role == "ReservationHead":
        page_options = [
            "Direct Reservations", "View Reservations", "Edit Direct Reservation",
            "Online Reservations", "Daily Status", "Monthly Consolidation", "Summary Report"
        ]
        if edit_online_available:
            page_options.insert(page_options.index("Daily Status"), "Edit Online Reservations")
    elif st.session_state.role == "ReservationTeam":
        page_options = [
            "Direct Reservations", "View Reservations", "Edit Direct Reservation",
            "Online Reservations", "Daily Status", "Monthly Consolidation"
        ]
        if edit_online_available:
            page_options.insert(page_options.index("Daily Status"), "Edit Online Reservations")
    else:
        # Custom user with specific screens
        if st.session_state.user_data:
            allowed_screens = st.session_state.user_data.get("screens", [])
            page_options = allowed_screens
        else:
            page_options = ["Direct Reservations"]

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

    # === Refresh Button (not for Admin) ===
    if st.session_state.role != "Admin":
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
    if page == "User Management" and st.session_state.role == "Admin":
        show_user_management()
        log_activity(supabase, st.session_state.username, "Accessed User Management")

    elif page == "Log Report" and st.session_state.role == "Admin":
        show_log_report(supabase)
        log_activity(supabase, st.session_state.username, "Accessed Log Report")

    elif page == "Inventory Dashboard":
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
        if st.session_state.role not in ["Management", "ReservationHead", "Admin"]:
            st.error("Access Denied: Summary Report is only available to Management and ReservationHead.")
            log_activity(supabase, st.session_state.username, "Unauthorized Summary Report access attempt")
        else:
            show_summary_report()
            log_activity(supabase, st.session_state.username, "Accessed Summary Report")

    # === Footer: User Info & Logout ===
    if st.session_state.authenticated:
        st.sidebar.write(f"Logged in as: **{st.session_state.username}**")
        st.sidebar.write(f"Role: **{st.session_state.role}**")

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
