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
        st.session_state.users = []  # Initialize users list

    # Preserve exact login page look
    if not st.session_state.authenticated:
        st.title("🔐 TIE Reservations Login")
        st.write("Please select your role and enter the password to access the system.")
        role = st.selectbox("Select Role", ["Admin", "Management", "ReservationTeam"])
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            # Simulated authentication
            users = st.session_state.get("users", [])
            user = next((u for u in users if u.get("role") == role and u.get("password") == password), None)
            if not user:
                # Add default users if none exist
                if not users:
                    st.session_state.users = [
                        {"role": "Admin", "password": "admin2024"},
                        {"role": "Management", "password": "mgmt2024"},
                        {"role": "ReservationTeam", "password": "res2024"}
                    ]
                    users = st.session_state.users
                    user = next((u for u in users if u.get("role") == role and u.get("password") == password), None)
            if user:
                st.session_state.authenticated = True
                st.session_state.role = role
                st.rerun()
            else:
                st.error("Invalid role or password")
        st.stop()

def show_user_management():
    st.subheader("Admin User Management")
    
    # Get reservations data for property names
    reservations = load_reservations_from_supabase()
    all_properties = sorted(list(set(res["Property Name"] for res in reservations if res and "Property Name" in res))) if reservations else []
    
    if not all_properties:
        st.warning("No properties found in reservations. Using fallback list.")
        all_properties = ["Le Poshe Beach view", "La Millionaire Resort", "Le Poshe Luxury", "Le Poshe Suite", "Eden Beach Resort"]  # Fallback

    all_screens = ["Direct Reservations", "View Reservations", "Analytics", "Reports"]
    all_access = ["Add", "Edit", "Delete"]

    all_users = st.session_state.get("users", [])

    # Admin can create a new user or modify existing
    action = st.radio("Action", ["Create New User", "Modify Existing User"], key="user_action")

    if action == "Create New User":
        with st.form(key="create_user_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            role = st.selectbox("Role", ["Management", "ReservationTeam"])  # Admin role managed separately
            visible_properties = st.multiselect("Visible Properties", all_properties)
            visible_screens = st.multiselect("Visible Screens", all_screens)
            access_levels = st.multiselect("Access Levels", all_access)
            
            if st.form_submit_button("Create User"):
                new_user = {
                    "username": username,
                    "password": password,  # Note: Hash in production
                    "role": role,
                    "properties": visible_properties,
                    "screens": visible_screens,
                    "permissions": access_levels
                }
                all_users.append(new_user)
                st.session_state.users = all_users
                st.success(f"User {username} created successfully!")
                st.rerun()

    elif action == "Modify Existing User":
        if not all_users:
            st.warning("No users available to modify.")
            return
        
        user_to_modify = st.selectbox("Select User to Modify", [user["username"] for user in all_users if user["username"]])
        user_index = next(i for i, user in enumerate(all_users) if user["username"] == user_to_modify)
        
        with st.form(key="modify_user_form"):
            username = st.text_input("Username", value=user_to_modify, disabled=True)
            password = st.text_input("New Password (leave blank to keep current)", type="password")
            role = st.selectbox("Role", ["Management", "ReservationTeam"], index=["Management", "ReservationTeam"].index(all_users[user_index]["role"]) if all_users[user_index]["role"] in ["Management", "ReservationTeam"] else 0)
            
            # Filter default properties to only those in all_properties
            default_properties = [prop for prop in all_users[user_index].get("properties", []) if prop in all_properties]
            mod_properties = st.multiselect("Visible Properties", all_properties, default=default_properties if default_properties else [])
            
            mod_screens = st.multiselect("Visible Screens", all_screens, default=[s for s in all_users[user_index].get("screens", []) if s in all_screens])
            mod_access = st.multiselect("Access Levels", all_access, default=[a for a in all_users[user_index].get("permissions", []) if a in all_access])
            
            if st.form_submit_button("Update User"):
                updated_user = {
                    "username": username,
                    "password": password if password else all_users[user_index]["password"],
                    "role": role,
                    "properties": mod_properties,
                    "screens": mod_screens,
                    "permissions": mod_access
                }
                all_users[user_index] = updated_user
                st.session_state.users = all_users
                st.success(f"User {username} updated successfully!")
                st.rerun()

    # Display current users (for admin view)
    if all_users:
        st.subheader("Current Users")
        for user in all_users:
            st.write(f"Username: {user['username']}, Role: {user['role']}, Properties: {', '.join(user.get('properties', []))}, Screens: {', '.join(user.get('screens', []))}, Access: {', '.join(user.get('permissions', []))}")

def main():
    check_authentication()

    if st.session_state.authenticated:
        st.sidebar.write(f"Welcome, {st.session_state.role}")
        page_options = ["Direct Reservations", "View Reservations", "Edit Reservations", "Online Reservations"]
        if edit_online_available:
            page_options.append("Edit Online Reservations")
        page_options.append("Daily Status")
        if st.session_state.role == "Management":
            page_options.extend(["Daily Management Status", "Analytics"])
        page_options.append("Monthly Consolidation")
        if st.session_state.role == "Admin":
            page_options.append("User Management")
        
        page = st.sidebar.selectbox("Choose a page", page_options, index=page_options.index(st.session_state.current_page) if st.session_state.current_page in page_options else 0, key="page_select")
        st.session_state.current_page = page

        # Add global refresh button in sidebar above Log Out
        if st.sidebar.button("🔄 Refresh All Data"):
            st.cache_data.clear()
            try:
                st.session_state.reservations = load_reservations_from_supabase()
                st.session_state.online_reservations = load_online_reservations_from_supabase()
                st.success("✅ Data refreshed from database!")
            except Exception as e:
                st.warning(f"⚠️ Data refresh partially failed: {e}")
            st.rerun()

        if page == "Direct Reservations":
            show_new_reservation_form()
        elif page == "View Reservations":
            show_reservations()
        elif page == "Edit Reservations":
            show_edit_reservations()
        elif page == "Online Reservations":
            show_online_reservations()
        elif page == "Edit Online Reservations" and edit_online_available:
            show_edit_online_reservations(st.session_state.selected_booking_id)
            if st.session_state.selected_booking_id:
                st.session_state.selected_booking_id = None
                st.query_params.clear()
        elif page == "Daily Status":
            show_daily_status()
        elif page == "Daily Management Status" and st.session_state.role == "Management":
            show_dms()
        elif page == "Analytics" and st.session_state.role == "Management":
            show_analytics()
        elif page == "Monthly Consolidation":
            show_monthly_consolidation()
        elif page == "User Management" and st.session_state.role == "Admin":
            show_user_management()

        if st.sidebar.button("Log Out"):
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
