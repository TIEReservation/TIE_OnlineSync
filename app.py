import streamlit as st
import os
import pandas as pd
from supabase import create_client, Client
from directreservation import show_new_reservation_form, show_reservations, show_edit_reservations, show_analytics, load_reservations_from_supabase
from online_reservation import show_online_reservations, load_online_reservations_from_supabase
from editOnline import show_edit_online_reservations
from inventory import show_daily_status
from dms import show_dms
from users import validate_user, create_user, update_user, delete_user, load_users

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
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except Exception as e:
    st.error(f"Failed to initialize Supabase client: {e}")
    st.stop()

# Store Supabase client in session state for other modules
st.session_state.supabase = supabase

def show_admin_panel():
    """Display Admin Panel for managing user accounts."""
    st.title("🔧 Admin Panel")
    st.subheader("Manage Users")
    
    try:
        users = load_users(supabase)
        if not users:
            st.info("No users found.")
        else:
            st.write(f"Debug: Loaded {len(users)} users")
    except Exception as e:
        st.error(f"Error loading users: {e}")
        users = []
    
    # Display existing users
    st.subheader("Current Users")
    user_df = pd.DataFrame(users, columns=["username", "role", "properties", "screens"])
    st.dataframe(user_df)
    
    # Create new user
    st.subheader("Create New User")
    with st.form("create_user_form"):
        new_username = st.text_input("Username")
        new_password = st.text_input("Password", type="password")
        new_role = st.selectbox("Role", ["ReservationTeam", "Management"])
        all_properties = [
            "All",
            "Eden Beach Resort",
            "La Millionare Resort",
            "Le Poshe Beachview",
            "La Park Resort",
            "Le Poshe Luxury",
            "La Paradise Residency",
            "La Tamara Luxury",
            "Villa Shakti",
            "La Millionaire Luxury Resort",
            "Le Meridian Resort",
            "La Serenity Resort",
            "La Beachview Resort",
            "La Oceanview Resort",
            "La Grand Resort",
            "La Coastal Residency"
        ]
        selected_properties = st.multiselect("Properties", all_properties, default=[])
        all_screens = ["Direct Reservations", "View Reservations", "Edit Reservations", "Online Reservations", "Edit Online Reservations", "Daily Status", "Daily Management Status", "Analytics"]
        default_screens = all_screens if new_role == "Management" else ["Direct Reservations", "View Reservations", "Edit Reservations", "Online Reservations", "Edit Online Reservations", "Daily Status"]
        selected_screens = st.multiselect("Permitted Screens", all_screens, default=default_screens)
        if st.form_submit_button("Create User"):
            if new_username and new_password and len(new_password) >= 8:
                # Handle "All" option
                final_properties = all_properties[1:] if "All" in selected_properties else selected_properties
                try:
                    if create_user(supabase, new_username, new_password, new_role, final_properties, selected_screens):
                        st.success(f"User {new_username} created successfully!")
                        st.rerun()
                    else:
                        st.error(f"Failed to create user '{new_username}'. Username may already exist or there was a database error.")
                except Exception as e:
                    st.error(f"Error creating user '{new_username}': {e}")
            else:
                st.error("Username and password (minimum 8 characters) are required.")

    # Edit or delete user
    st.subheader("Edit or Delete User")
    usernames = [user["username"] for user in users if user["username"] != "admin"]
    if usernames:
        selected_username = st.selectbox("Select User to Edit/Delete", usernames)
        user = next((u for u in users if u["username"] == selected_username), None)
        if user:
            with st.form("edit_user_form"):
                edit_password = st.text_input("New Password (leave blank to keep unchanged)", type="password")
                edit_role = st.selectbox("Role", ["ReservationTeam", "Management"], index=["ReservationTeam", "Management"].index(user["role"]))
                edit_properties = st.multiselect("Properties", all_properties, default=user["properties"] or [])
                edit_screens = st.multiselect("Permitted Screens", all_screens, default=user["screens"] or [])
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Update User"):
                        # Handle "All" option
                        final_properties = all_properties[1:] if "All" in edit_properties else edit_properties
                        try:
                            if edit_password and len(edit_password) < 8:
                                st.error("Password must be at least 8 characters.")
                            elif update_user(supabase, selected_username, password=edit_password if edit_password else None, role=edit_role, properties=final_properties, screens=edit_screens):
                                st.success(f"User {selected_username} updated successfully!")
                                st.rerun()
                            else:
                                st.error(f"Failed to update user '{selected_username}'.")
                        except Exception as e:
                            st.error(f"Error updating user '{selected_username}': {e}")
                with col2:
                    if st.form_submit_button("Delete User"):
                        try:
                            if delete_user(supabase, selected_username):
                                st.success(f"User {selected_username} deleted successfully!")
                                st.rerun()
                            else:
                                st.error(f"Failed to delete user '{selected_username}'.")
                        except Exception as e:
                            st.error(f"Error deleting user '{selected_username}': {e}")
    else:
        st.info("No users available to edit or delete (excluding admin).")

def check_authentication():
    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.write("Debug: Initializing session state")
        st.session_state.authenticated = False
        st.session_state.role = None
        st.session_state.username = None
        st.session_state.properties = []
        st.session_state.screens = []
        st.session_state.reservations = []
        st.session_state.online_reservations = []
        st.session_state.edit_mode = False
        st.session_state.edit_index = None
        st.session_state.online_edit_mode = False
        st.session_state.online_edit_index = None
        st.session_state.current_page = "Direct Reservations"
        st.session_state.selected_booking_id = None

    # Preserve query parameters
    query_params = st.query_params
    if st.session_state.authenticated:
        query_page = query_params.get("page", [st.session_state.current_page])[0]
        allowed_pages = ["Direct Reservations", "View Reservations", "Edit Reservations", "Online Reservations", "Edit Online Reservations", "Daily Status", "Daily Management Status", "Analytics", "Admin Panel"]
        if query_page in allowed_pages:
            if st.session_state.role == "Admin" and query_page != "Admin Panel":
                st.session_state.current_page = "Admin Panel"
            elif query_page in st.session_state.screens:
                st.session_state.current_page = query_page
        query_booking_id = query_params.get("booking_id", [None])[0]
        if query_booking_id:
            st.session_state.selected_booking_id = query_booking_id

    if not st.session_state.authenticated:
        st.title("🔐 TIE Reservations Login")
        st.write("Please enter your username and password to access the system.")
        
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("🔑 Login"):
            st.write(f"Debug: Attempting login with username={username}")
            # Default logins
            if username == "admin" and password == "AdminTIE2025":
                st.session_state.authenticated = True
                st.session_state.role = "Admin"
                st.session_state.username = "admin"
                st.session_state.properties = []
                st.session_state.screens = ["Admin Panel"]
                st.session_state.current_page = "Admin Panel"
                try:
                    st.session_state.reservations = load_reservations_from_supabase()
                    st.session_state.online_reservations = load_online_reservations_from_supabase()
                    st.success("✅ Admin login successful!")
                except Exception as e:
                    st.session_state.reservations = []
                    st.session_state.online_reservations = []
                    st.warning(f"✅ Admin login successful, but failed to fetch reservations: {e}")
                st.rerun()
            elif username == "management" and password == "TIE2024":
                st.session_state.authenticated = True
                st.session_state.role = "Management"
                st.session_state.username = "management"
                st.session_state.properties = [
                    "Eden Beach Resort",
                    "La Millionare Resort",
                    "Le Poshe Beachview",
                    "La Park Resort",
                    "Le Poshe Luxury",
                    "La Paradise Residency",
                    "La Tamara Luxury",
                    "Villa Shakti",
                    "La Millionaire Luxury Resort",
                    "Le Meridian Resort",
                    "La Serenity Resort",
                    "La Beachview Resort",
                    "La Oceanview Resort",
                    "La Grand Resort",
                    "La Coastal Residency"
                ]
                st.session_state.screens = ["Direct Reservations", "View Reservations", "Edit Reservations", "Online Reservations", "Edit Online Reservations", "Daily Status", "Daily Management Status", "Analytics"]
                query_page = query_params.get("page", ["Direct Reservations"])[0]
                if query_page in st.session_state.screens:
                    st.session_state.current_page = query_page
                query_booking_id = query_params.get("booking_id", [None])[0]
                if query_booking_id:
                    st.session_state.selected_booking_id = query_booking_id
                try:
                    st.session_state.reservations = load_reservations_from_supabase()
                    st.session_state.online_reservations = load_online_reservations_from_supabase()
                    st.success("✅ Management login successful!")
                except Exception as e:
                    st.session_state.reservations = []
                    st.session_state.online_reservations = []
                    st.warning(f"✅ Management login successful, but failed to fetch reservations: {e}")
                st.rerun()
            elif username == "reservationteam" and password == "TIE123":
                st.session_state.authenticated = True
                st.session_state.role = "ReservationTeam"
                st.session_state.username = "reservationteam"
                st.session_state.properties = [
                    "Eden Beach Resort",
                    "La Millionare Resort",
                    "Le Poshe Beachview",
                    "La Park Resort",
                    "Le Poshe Luxury",
                    "La Paradise Residency",
                    "La Tamara Luxury",
                    "Villa Shakti",
                    "La Millionaire Luxury Resort",
                    "Le Meridian Resort",
                    "La Serenity Resort",
                    "La Beachview Resort",
                    "La Oceanview Resort",
                    "La Grand Resort",
                    "La Coastal Residency"
                ]
                st.session_state.screens = ["Direct Reservations", "View Reservations", "Edit Reservations", "Online Reservations", "Edit Online Reservations", "Daily Status"]
                query_page = query_params.get("page", ["Direct Reservations"])[0]
                if query_page in st.session_state.screens:
                    st.session_state.current_page = query_page
                query_booking_id = query_params.get("booking_id", [None])[0]
                if query_booking_id:
                    st.session_state.selected_booking_id = query_booking_id
                try:
                    st.session_state.reservations = load_reservations_from_supabase()
                    st.session_state.online_reservations = load_online_reservations_from_supabase()
                    st.success("✅ ReservationTeam login successful!")
                except Exception as e:
                    st.session_state.reservations = []
                    st.session_state.online_reservations = []
                    st.warning(f"✅ ReservationTeam login successful, but failed to fetch reservations: {e}")
                st.rerun()
            else:
                user = validate_user(supabase, username, password)
                if user:
                    st.session_state.authenticated = True
                    st.session_state.role = user["role"]
                    st.session_state.username = username
                    st.session_state.properties = user["properties"]
                    st.session_state.screens = user["screens"]
                    query_page = query_params.get("page", ["Direct Reservations"])[0]
                    if query_page in st.session_state.screens:
                        st.session_state.current_page = query_page
                    query_booking_id = query_params.get("booking_id", [None])[0]
                    if query_booking_id:
                        st.session_state.selected_booking_id = query_booking_id
                    try:
                        st.session_state.reservations = load_reservations_from_supabase()
                        st.session_state.online_reservations = load_online_reservations_from_supabase()
                        st.success(f"✅ {user['role']} login successful for {username}!")
                    except Exception as e:
                        st.session_state.reservations = []
                        st.session_state.online_reservations = []
                        st.warning(f"✅ {user['role']} login successful, but failed to fetch reservations: {e}")
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password.")
        st.stop()

def main():
    check_authentication()
    st.title("🏢 TIE Reservations")
    st.markdown("---")
    st.sidebar.title(f"Welcome, {st.session_state.username or st.session_state.role}")
    page_options = ["Direct Reservations", "View Reservations", "Edit Reservations", "Online Reservations", "Edit Online Reservations", "Daily Status", "Daily Management Status", "Analytics", "Admin Panel"]
    permitted_pages = []
    if st.session_state.role == "Admin":
        permitted_pages = ["Admin Panel"]
    elif st.session_state.role == "Management":
        permitted_pages = ["Direct Reservations", "View Reservations", "Edit Reservations", "Online Reservations", "Edit Online Reservations", "Daily Status", "Daily Management Status", "Analytics"]
    else:
        permitted_pages = [page for page in page_options if page in st.session_state.screens]
    
    page = st.sidebar.selectbox("Choose a page", permitted_pages, index=permitted_pages.index(st.session_state.current_page) if st.session_state.current_page in permitted_pages else 0, key="page_select")
    st.session_state.current_page = page

    if page == "Direct Reservations" and page in permitted_pages:
        show_new_reservation_form()
    elif page == "View Reservations" and page in permitted_pages:
        show_reservations()
    elif page == "Edit Reservations" and page in permitted_pages:
        show_edit_reservations()
    elif page == "Online Reservations" and page in permitted_pages:
        show_online_reservations()
    elif page == "Edit Online Reservations" and page in permitted_pages:
        show_edit_online_reservations(st.session_state.selected_booking_id)
        if st.session_state.selected_booking_id:
            st.session_state.selected_booking_id = None
            st.query_params.clear()
    elif page == "Daily Status" and page in permitted_pages:
        show_daily_status()
    elif page == "Daily Management Status" and page in permitted_pages:
        show_dms()
    elif page == "Analytics" and page in permitted_pages:
        show_analytics()
    elif page == "Admin Panel" and page in permitted_pages:
        show_admin_panel()

    # Logout button
    if st.sidebar.button("Log Out"):
        st.session_state.authenticated = False
        st.session_state.role = None
        st.session_state.username = None
        st.session_state.properties = []
        st.session_state.screens = []
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
