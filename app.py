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
from log import show_log_report, log_activity
from summary_report import show_summary_report
import bcrypt

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

# ============================================================================
# USER MANAGEMENT FUNCTIONS (from users.py)
# ============================================================================

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    try:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    except Exception as e:
        st.error(f"Error hashing password: {e}")
        return None

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception as e:
        st.error(f"Error verifying password: {e}")
        return False

def validate_user(supabase: Client, username: str, password: str) -> dict:
    """Validate user by username and password, return user data if valid."""
    try:
        response = supabase.table("users").select("*").eq("username", username).execute()
        if not response.data:
            st.error(f"Debug: No user found with username '{username}'")
            return None
        if not response.data[0]["password"]:
            st.error(f"Debug: User '{username}' has no password set")
            return None
        if verify_password(password, response.data[0]["password"]):
            user = response.data[0]
            return {
                "username": user["username"],
                "role": user["role"],
                "properties": user["properties"] or [],
                "screens": user["screens"] or []
            }
        else:
            st.error(f"Debug: Password verification failed for username '{username}'")
            return None
    except Exception as e:
        st.error(f"Error validating user '{username}': {e}")
        return None

def create_user(supabase: Client, username: str, password: str, role: str, properties: list, screens: list) -> bool:
    """Create a new user in Supabase with hashed password."""
    try:
        hashed_password = hash_password(password)
        if not hashed_password:
            return False
        user_data = {
            "username": username,
            "password": hashed_password,
            "role": role,
            "properties": properties,
            "screens": screens
        }
        response = supabase.table("users").insert(user_data).execute()
        if response.data:
            st.write(f"Debug: Successfully created user '{username}'")
            return True
        else:
            st.error(f"Debug: Failed to create user '{username}' - no data returned")
            return False
    except Exception as e:
        st.error(f"Error creating user '{username}': {e}")
        return False

def update_user(supabase: Client, username: str, password: str = None, role: str = None, properties: list = None, screens: list = None) -> bool:
    """Update an existing user in Supabase."""
    try:
        update_data = {}
        if password:
            hashed_password = hash_password(password)
            if not hashed_password:
                return False
            update_data["password"] = hashed_password
        if role:
            update_data["role"] = role
        if properties is not None:
            update_data["properties"] = properties
        if screens is not None:
            update_data["screens"] = screens
        if update_data:
            response = supabase.table("users").update(update_data).eq("username", username).execute()
            if response.data:
                st.write(f"Debug: Successfully updated user '{username}'")
                return True
            else:
                st.error(f"Debug: Failed to update user '{username}' - no data returned")
                return False
        return False
    except Exception as e:
        st.error(f"Error updating user '{username}': {e}")
        return False

def delete_user(supabase: Client, username: str) -> bool:
    """Delete a user from Supabase."""
    try:
        response = supabase.table("users").delete().eq("username", username).execute()
        if response.data:
            st.write(f"Debug: Successfully deleted user '{username}'")
            return True
        else:
            st.error(f"Debug: Failed to delete user '{username}' - no data returned")
            return False
    except Exception as e:
        st.error(f"Error deleting user '{username}': {e}")
        return False

def load_users(supabase: Client) -> list:
    """Load all users from Supabase."""
    try:
        response = supabase.table("users").select("*").execute()
        if response.data:
            st.write(f"Debug: Loaded {len(response.data)} users from Supabase")
            return response.data
        else:
            st.info("Debug: No users found in Supabase")
            return []
    except Exception as e:
        st.error(f"Error loading users: {e}")
        return []

# ============================================================================
# END USER MANAGEMENT FUNCTIONS
# ============================================================================

def load_properties():
    """Load available properties from TIE Hotels & Resorts."""
    # Complete list of TIE Hotels & Resorts properties in Pondicherry
    tie_properties = [
        "Eden Beach Resort",
        "Villa Shakti",
        "La Villa Heritage",
        "La Paradise Luxury",
        "Le Poshe Luxury",
        "La Paradise Residency",
        "Le Pondy Beachside",
        "Le Poshe Beachview",
        "Le Park Resort",
        "Le Terra Resort",
        "La Tamara Suite",
        "La Antilia Luxury",
        "La Tamara Luxury",
        "Le Royce Villa",
        "La Millionaire Resort",
        "Le Poshe Suite",
        "La Coromandel Luxury"
    ]
    
    try:
        # Also get any additional properties from reservations table
        response = supabase.table("reservations").select("property").execute()
        if response.data:
            db_properties = list(set([r["property"] for r in response.data if r.get("property")]))
            # Merge and remove duplicates
            all_properties = list(set(tie_properties + db_properties))
            return sorted(all_properties)
        else:
            return sorted(tie_properties)
    except Exception:
        return sorted(tie_properties)

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
            if username == "Admin" and password == "TIE2024":
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
                    # Use the validate_user function
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
    
    # Load and display users
    users = load_users(supabase)
    if not users:
        st.info("No users found.")
    else:
        df = pd.DataFrame(users)
        st.dataframe(
            df[["username", "role", "properties", "screens"]],
            width="stretch",           # ← FIXED: no more warnings
            hide_index=True           # optional: looks cleaner
    )

    # Create tabs for different operations
    tab1, tab2, tab3 = st.tabs(["➕ Create User", "✏️ Modify User", "🗑️ Delete User"])
    
    # TAB 1: CREATE NEW USER
    with tab1:
        st.subheader("Create New User")
        new_username = st.text_input("New Username", key="create_username")
        new_password = st.text_input("New Password", type="password", key="create_password")
        new_role = st.selectbox("Role", ["ReservationTeam", "Management"], key="create_role")
        new_properties = st.multiselect("Properties", load_properties(), key="create_properties")
        new_screens = st.multiselect("Screens", ["Inventory Dashboard", "Direct Reservations", "View Reservations", "Edit Direct Reservation", "Online Reservations", "Edit Online Reservations", "Daily Status", "Daily Management Status", "Analytics", "Monthly Consolidation", "Summary Report"], key="create_screens")
        
        if st.button("Create User", key="btn_create"):
            if not new_username or not new_password:
                st.error("Username and password are required!")
            elif create_user(supabase, new_username, new_password, new_role, new_properties, new_screens):
                st.success(f"User '{new_username}' created successfully!")
                log_activity(supabase, st.session_state.username, f"Created user: {new_username}")
                st.rerun()
    
    # TAB 2: MODIFY USER
    with tab2:
        st.subheader("Modify Existing User")
        if users:
            usernames = [u["username"] for u in users]
            selected_user = st.selectbox("Select User to Modify", usernames, key="modify_select")
            
            # Get current user data
            current_user = next((u for u in users if u["username"] == selected_user), None)
            
            if current_user:
                st.info(f"Current Role: {current_user['role']}")
                
                modify_password = st.text_input("New Password (leave empty to keep current)", type="password", key="modify_password")
                modify_role = st.selectbox("Role", ["ReservationTeam", "Management"], 
                                          index=0 if current_user["role"] == "ReservationTeam" else 1, 
                                          key="modify_role")
                
                # Load properties and filter current user's properties
                available_properties = load_properties()
                current_properties = current_user.get("properties", [])
                # Filter to only include properties that exist in available_properties
                filtered_properties = [p for p in current_properties if p in available_properties]
                
                modify_properties = st.multiselect("Properties", available_properties, 
                                                  default=filtered_properties, 
                                                  key="modify_properties")
                
                # Available screens for non-admin users
                available_screens = ["Inventory Dashboard", "Direct Reservations", "View Reservations", 
                                    "Edit Direct Reservation", "Online Reservations", "Edit Online Reservations", 
                                    "Daily Status", "Daily Management Status", "Analytics", 
                                    "Monthly Consolidation", "Summary Report"]
                
                # Filter current user's screens to only include available screens (exclude admin-only screens)
                current_screens = current_user.get("screens", [])
                filtered_screens = [s for s in current_screens if s in available_screens]
                
                modify_screens = st.multiselect("Screens", available_screens,
                                               default=filtered_screens,
                                               key="modify_screens")
                
                if st.button("Update User", key="btn_modify"):
                    update_pwd = modify_password if modify_password else None
                    if update_user(supabase, selected_user, update_pwd, modify_role, modify_properties, modify_screens):
                        st.success(f"User '{selected_user}' updated successfully!")
                        log_activity(supabase, st.session_state.username, f"Modified user: {selected_user}")
                        st.rerun()
        else:
            st.info("No users available to modify.")
    
    # TAB 3: DELETE USER
    with tab3:
        st.subheader("Delete User")
        st.warning("⚠️ This action cannot be undone!")
        
        if users:
            usernames = [u["username"] for u in users]
            delete_username = st.selectbox("Select User to Delete", usernames, key="delete_select")
            
            confirm_delete = st.text_input("Type username to confirm deletion", key="delete_confirm")
            
            if st.button("Delete User", key="btn_delete", type="primary"):
                if confirm_delete == delete_username:
                    if delete_user(supabase, delete_username):
                        st.success(f"User '{delete_username}' deleted successfully!")
                        log_activity(supabase, st.session_state.username, f"Deleted user: {delete_username}")
                        st.rerun()
                else:
                    st.error("Username confirmation does not match. Deletion cancelled.")
        else:
            st.info("No users available to delete.")

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
