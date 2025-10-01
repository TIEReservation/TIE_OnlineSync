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

def show_admin_panel():
    """Display Admin Panel for managing user accounts."""
    st.title("🔧 Admin Panel")
    st.subheader("Manage Users")
    
    users = load_users(supabase)
    if not users:
        st.info("No users found.")
    
    # Display existing users
    st.subheader("Current Users")
    user_df = pd.DataFrame(users, columns=["username", "properties", "screens", "is_admin"])
    st.dataframe(user_df)
    
    # Create new user
    st.subheader("Create New User")
    with st.form("create_user_form"):
        new_username = st.text_input("Username")
        new_password = st.text_input("Password", type="password")
        all_properties = ["Eden Beach Resort", "La Millionare Resort", "Le Poshe Beachview", "La Park Resort"]
        selected_properties = st.multiselect("Properties", all_properties, default=[])
        all_screens = ["Direct Reservations", "View Reservations", "Edit Reservations", "Online Reservations", "Edit Online Reservations", "Daily Status", "Daily Management Status", "Analytics"]
        selected_screens = st.multiselect("Permitted Screens", all_screens, default=[])
        is_admin = st.checkbox("Admin Privileges (User Management Only)", value=False)
        if st.form_submit_button("Create User"):
            if new_username and new_password:
                if create_user(supabase, new_username, new_password, selected_properties, selected_screens, is_admin):
                    st.success(f"User {new_username} created successfully!")
                    st.rerun()
                else:
                    st.error("Failed to create user. Username may already exist.")
            else:
                st.error("Username and password are required.")

    # Edit or delete user
    st.subheader("Edit or Delete User")
    usernames = [user["username"] for user in users if user["username"] != st.session_state.username]
    if usernames:
        selected_username = st.selectbox("Select User to Edit/Delete", usernames)
        user = next((u for u in users if u["username"] == selected_username), None)
        if user:
            with st.form("edit_user_form"):
                edit_password = st.text_input("New Password (leave blank to keep unchanged)", type="password")
                edit_properties = st.multiselect("Properties", all_properties, default=user["properties"])
                edit_screens = st.multiselect("Permitted Screens", all_screens, default=user["screens"])
                edit_is_admin = st.checkbox("Admin Privileges", value=user["is_admin"])
                col1, col2 = st.form.columns(2)
                with col1:
                    if st.form_submit_button("Update User"):
                        if update_user(supabase, selected_username, edit_password or None, edit_properties, edit_screens, edit_is_admin):
                            st.success(f"User {selected_username} updated successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to update user.")
                with col2:
                    if st.form_submit_button("Delete User"):
                        if delete_user(supabase, selected_username):
                            st.success(f"User {selected_username} deleted successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to delete user.")

def check_authentication():
    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.role = None
        st.session_state.username = None
        st.session_state.properties = []
        st.session_state.screens = []
        st.session_state.is_admin = False
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
            if st.session_state.is_admin and query_page != "Admin Panel":
                st.session_state.current_page = "Admin Panel"
            elif not st.session_state.is_admin and (query_page in st.session_state.screens or st.session_state.role == "Management"):
                st.session_state.current_page = query_page
        query_booking_id = query_params.get("booking_id", [None])[0]
        if query_booking_id:
            st.session_state.selected_booking_id = query_booking_id

    if not st.session_state.authenticated:
        st.title("🔐 TIE Reservations Login")
        st.write("Log in with role-based credentials (ReservationTeam/Management) or username/password (Admin/Custom User).")
        
        # Role-based login
        st.subheader("Role-Based Login")
        role = st.selectbox("Select Role", ["ReservationTeam", "Management"])
        role_password = st.text_input("Role Password", type="password", key="role_password")
        
        # Username/password login
        st.subheader("User Login")
        username = st.text_input("Username")
        user_password = st.text_input("Password", type="password", key="user_password")
        
        if st.button("🔑 Login"):
            # Try role-based authentication
            if role_password:
                if role == "Management" and role_password == "TIE2024":
                    st.session_state.authenticated = True
                    st.session_state.role = "Management"
                    st.session_state.username = None
                    st.session_state.properties = ["Eden Beach Resort", "La Millionare Resort", "Le Poshe Beachview", "La Park Resort"]
                    st.session_state.screens = ["Direct Reservations", "View Reservations", "Edit Reservations", "Online Reservations", "Edit Online Reservations", "Daily Status", "Daily Management Status", "Analytics"]
                    st.session_state.is_admin = False
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
                elif role == "ReservationTeam" and role_password == "TIE123":
                    st.session_state.authenticated = True
                    st.session_state.role = "ReservationTeam"
                    st.session_state.username = None
                    st.session_state.properties = ["Eden Beach Resort", "La Millionare Resort", "Le Poshe Beachview", "La Park Resort"]
                    st.session_state.screens = ["Direct Reservations", "View Reservations", "Edit Reservations", "Online Reservations", "Edit Online Reservations", "Daily Status"]
                    st.session_state.is_admin = False
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
                    st.error("❌ Invalid role password.")
            # Try user-based authentication
            elif username and user_password:
                user = validate_user(supabase, username, user_password)
                if user:
                    st.session_state.authenticated = True
                    st.session_state.role = None
                    st.session_state.username = user["username"]
                    st.session_state.properties = user["properties"]
                    st.session_state.screens = user["screens"]
                    st.session_state.is_admin = user["is_admin"]
                    query_page = query_params.get("page", ["Admin Panel" if user["is_admin"] else "Direct Reservations"])[0]
                    if user["is_admin"] and query_page != "Admin Panel":
                        st.session_state.current_page = "Admin Panel"
                    elif not user["is_admin"] and query_page in user["screens"]:
                        st.session_state.current_page = query_page
                    query_booking_id = query_params.get("booking_id", [None])[0]
                    if query_booking_id:
                        st.session_state.selected_booking_id = query_booking_id
                    try:
                        st.session_state.reservations = load_reservations_from_supabase()
                        st.session_state.online_reservations = load_online_reservations_from_supabase()
                        st.success(f"✅ Login successful for {username}!")
                    except Exception as e:
                        st.session_state.reservations = []
                        st.session_state.online_reservations = []
                        st.warning(f"✅ Login successful, but failed to fetch reservations: {e}")
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password.")
            else:
                st.error("❌ Please provide either role-based or user-based credentials.")
        st.stop()

def main():
    check_authentication()
    st.title("🏢 TIE Reservations")
    st.markdown("---")
    st.sidebar.title(f"Welcome, {st.session_state.username or st.session_state.role}")
    page_options = ["Direct Reservations", "View Reservations", "Edit Reservations", "Online Reservations", "Edit Online Reservations", "Daily Status", "Daily Management Status", "Analytics", "Admin Panel"]
    permitted_pages = []
    if st.session_state.is_admin:
        permitted_pages = ["Admin Panel"]
    elif st.session_state.role == "Management":
        permitted_pages = ["Direct Reservations", "View Reservations", "Edit Reservations", "Online Reservations", "Edit Online Reservations", "Daily Status", "Daily Management Status", "Analytics"]
    elif st.session_state.role == "ReservationTeam":
        permitted_pages = ["Direct Reservations", "View Reservations", "Edit Reservations", "Online Reservations", "Edit Online Reservations", "Daily Status"]
    else:
        permitted_pages = [page for page in page_options if page in st.session_state.screens]
    
    page = st.sidebar.selectbox("Choose a page", permitted_pages, index=permitted_pages.index(st.session_state.current_page) if st.session_state.current_page in permitted_pages else 0, key="page_select")
    st.session_state.current_page = page

    if page == "Direct Reservations" and (page in st.session_state.screens or st.session_state.role in ["ReservationTeam", "Management"]):
        show_new_reservation_form()
    elif page == "View Reservations" and (page in st.session_state.screens or st.session_state.role in ["ReservationTeam", "Management"]):
        show_reservations()
    elif page == "Edit Reservations" and (page in st.session_state.screens or st.session_state.role in ["ReservationTeam", "Management"]):
        show_edit_reservations()
    elif page == "Online Reservations" and (page in st.session_state.screens or st.session_state.role in ["ReservationTeam", "Management"]):
        show_online_reservations()
    elif page == "Edit Online Reservations" and (page in st.session_state.screens or st.session_state.role in ["ReservationTeam", "Management"]):
        show_edit_online_reservations(st.session_state.selected_booking_id)
        if st.session_state.selected_booking_id:
            st.session_state.selected_booking_id = None
            st.query_params.clear()
    elif page == "Daily Status" and (page in st.session_state.screens or st.session_state.role in ["ReservationTeam", "Management"]):
        show_daily_status()
    elif page == "Daily Management Status" and (page in st.session_state.screens or st.session_state.role == "Management"):
        show_dms()
    elif page == "Analytics" and (page in st.session_state.screens or st.session_state.role == "Management"):
        show_analytics()
    elif page == "Admin Panel" and st.session_state.is_admin:
        show_admin_panel()

    # Logout button
    if st.sidebar.button("Log Out"):
        st.session_state.authenticated = False
        st.session_state.role = None
        st.session_state.username = None
        st.session_state.properties = []
        st.session_state.screens = []
        st.session_state.is_admin = False
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
