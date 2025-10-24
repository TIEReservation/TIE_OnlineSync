import streamlit as st
import os
from supabase import create_client, Client
from directreservation import show_new_reservation_form, show_reservations, show_edit_reservations, show_analytics, load_reservations_from_supabase, load_property_room_map
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
import bcrypt
import pandas as pd

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

# Initialize users table with initial users if empty
try:
    response = supabase.table("users").select("count", count="exact").execute()
    if response.count == 0:
        all_properties = list(load_property_room_map().keys())
        initial_users = [
            {
                "username": "Admin",
                "password_hash": bcrypt.hashpw(b"TIE2024", bcrypt.gensalt()).decode(),
                "role": "Admin",
                "properties": [],
                "screens": ["User Management"],
                "permissions": {"add": True, "edit": True, "delete": True}
            },
            {
                "username": "Management",
                "password_hash": bcrypt.hashpw(b"TIE2024", bcrypt.gensalt()).decode(),
                "role": "Management",
                "properties": all_properties,
                "screens": ["Direct Reservations", "View Reservations", "Edit Reservations", "Online Reservations", "Edit Online Reservations", "Daily Status", "Daily Management Status", "Analytics", "Monthly Consolidation"],
                "permissions": {"add": True, "edit": True, "delete": True}
            },
            {
                "username": "ReservationTeam",
                "password_hash": bcrypt.hashpw(b"TIE123", bcrypt.gensalt()).decode(),
                "role": "ReservationTeam",
                "properties": all_properties,
                "screens": ["Direct Reservations", "View Reservations", "Edit Reservations", "Online Reservations", "Edit Online Reservations", "Daily Status", "Monthly Consolidation"],
                "permissions": {"add": True, "edit": True, "delete": True}
            }
        ]
        supabase.table("users").insert(initial_users).execute()
        st.info("Initial users created: Admin, Management, ReservationTeam")
except Exception as e:
    st.warning(f"Failed to initialize users: {e}")

def check_authentication():
    # Initialize session state if not already set
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.role = None
        st.session_state.username = None
        st.session_state.properties = []
        st.session_state.screens = []
        st.session_state.permissions = {"add": False, "edit": False, "delete": False}
        st.session_state.reservations = []
        st.session_state.online_reservations = []
        st.session_state.edit_mode = False
        st.session_state.edit_index = None
        st.session_state.online_edit_mode = False
        st.session_state.online_edit_index = None
        st.session_state.current_page = "Direct Reservations"
        st.session_state.selected_booking_id = None

    # If not authenticated, show login page and stop
    if not st.session_state.authenticated:
        st.title("🔐 TIE Reservations Login")
        st.write("Please enter your username and password to access the system.")
        username = st.text_input("Username")
        password = st.text_input("Enter password:", type="password")
        if st.button("🔑 Login"):
            try:
                user_response = supabase.table("users").select("*").eq("username", username).single().execute()
                user = user_response.data
                if user and password == user["password_hash"]:  # Updated for plain-text comparison
                    st.session_state.authenticated = True
                    st.session_state.role = user["role"]
                    st.session_state.username = username
                    st.session_state.properties = user.get("properties", [])
                    st.session_state.screens = user.get("screens", [])
                    st.session_state.permissions = user.get("permissions", {"add": True, "edit": True, "delete": True})
                    query_params = st.query_params
                    query_page = query_params.get("page", [st.session_state.current_page])[0]
                    if query_page in st.session_state.screens:
                        st.session_state.current_page = query_page
                    query_booking_id = query_params.get("booking_id", [None])[0]
                    if query_booking_id:
                        st.session_state.selected_booking_id = query_booking_id
                    try:
                        st.session_state.reservations = load_reservations_from_supabase(st.session_state.properties)
                        st.session_state.online_reservations = load_online_reservations_from_supabase(st.session_state.properties)
                        st.success(f"✅ Login successful as {st.session_state.role}! Data fetched.")
                    except Exception as e:
                        st.session_state.reservations = []
                        st.session_state.online_reservations = []
                        st.warning(f"✅ Login successful, but failed to fetch data: {e}")
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password. Please try again.")
            except Exception as e:
                st.error(f"Login error: {e}")
        st.stop()
    else:
        # Preserve query params for authenticated users
        query_params = st.query_params
        if st.session_state.current_page not in st.session_state.screens:
            st.session_state.current_page = st.session_state.screens[0] if st.session_state.screens else "Direct Reservations"
        query_page = query_params.get("page", [st.session_state.current_page])[0]
        if query_page in st.session_state.screens:
            st.session_state.current_page = query_page
        query_booking_id = query_params.get("booking_id", [None])[0]
        if query_booking_id:
            st.session_state.selected_booking_id = query_booking_id

def show_user_management():
    if st.session_state.role != "Admin":
        st.error("❌ Access Denied: User Management is available only for Admin.")
        return
    st.header("👥 User Management")

    # Load all users
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
        all_properties = sorted(list(load_property_room_map().keys()))
        new_properties = st.multiselect("Visible Properties", all_properties, default=all_properties)
        all_screens = ["Direct Reservations", "View Reservations", "Edit Reservations", "Online Reservations", "Edit Online Reservations", "Daily Status", "Daily Management Status", "Analytics", "Monthly Consolidation"]
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
                hash_pw = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
                new_user = {
                    "username": new_username,
                    "password_hash": hash_pw,
                    "role": new_role,
                    "properties": new_properties,
                    "screens": new_screens,
                    "permissions": {"add": add_perm, "edit": edit_perm, "delete": delete_perm}
                }
                supabase.table("users").insert(new_user).execute()
                st.success(f"User {new_username} created successfully!")
                st.rerun()

    # Modify user
    st.subheader("Modify User")
    modify_username = st.selectbox("Select User to Modify", [u["username"] for u in users if u["username"] != "Admin"])
    if modify_username:
        user_to_modify = next(u for u in users if u["username"] == modify_username)
        with st.form("modify_user_form"):
            mod_role = st.selectbox("Role", ["Management", "ReservationTeam"], index=0 if user_to_modify["role"] == "Management" else 1)
            all_properties = sorted(list(load_property_room_map().keys()))
            mod_properties = st.multiselect("Visible Properties", all_properties, default=user_to_modify["properties"])
            all_screens = ["Direct Reservations", "View Reservations", "Edit Reservations", "Online Reservations", "Edit Online Reservations", "Daily Status", "Daily Management Status", "Analytics", "Monthly Consolidation"]
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
                supabase.table("users").update(updated_user).eq("username", modify_username).execute()
                st.success(f"User {modify_username} updated successfully!")
                st.rerun()

    # Delete user
    st.subheader("Delete User")
    delete_username = st.selectbox("Select User to Delete", [u["username"] for u in users if u["username"] not in ["Admin", "Management", "ReservationTeam"]])
    if delete_username and st.button("Delete User"):
        supabase.table("users").delete().eq("username", delete_username).execute()
        st.success(f"User {delete_username} deleted successfully!")
        st.rerun()

def main():
    check_authentication()
    st.title("🏢 TIE Reservations")
    st.markdown("---")
    st.sidebar.title("Navigation")
    page_options = st.session_state.screens
    if edit_online_available and "Edit Online Reservations" in page_options:
        pass
    
    page = st.sidebar.selectbox("Choose a page", page_options, index=page_options.index(st.session_state.current_page) if st.session_state.current_page in page_options else 0, key="page_select")
    st.session_state.current_page = page

    # Add global refresh button in sidebar above Log Out
    if st.sidebar.button("🔄 Refresh All Data"):
        st.cache_data.clear()
        try:
            st.session_state.reservations = load_reservations_from_supabase(st.session_state.properties)
            st.session_state.online_reservations = load_online_reservations_from_supabase(st.session_state.properties)
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
    elif page == "Daily Management Status":
        show_dms()
    elif page == "Analytics":
        show_analytics()
    elif page == "Monthly Consolidation":
        show_monthly_consolidation()
    elif page == "User Management":
        show_user_management()

    if st.sidebar.button("Log Out"):
        st.cache_data.clear()
        st.cache_resource.clear()
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.session_state.authenticated = False
        st.query_params.clear()
        st.rerun()

if __name__ == "__main__":
    main()
