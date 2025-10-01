import streamlit as st
import os
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

# Display logo in top-left corner
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
        is_admin = st.checkbox("Admin Privileges", value=False)
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
    usernames = [user["username"] for user in users]
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
        if query_page in ["Direct Reservations", "View Reservations", "Edit Reservations", "Online Reservations", "Edit Online Reservations", "Daily Status", "Daily Management Status", "Analytics", "Admin Panel"]:
            st.session_state.current_page = query_page
        query_booking_id = query_params.get("booking_id", [None])[0]
        if query_booking_id:
            st.session_state.selected_booking_id = query_booking_id

    if not st.session_state.authenticated:
        st.title("🔐 TIE Reservations Login")
        st.write("Please enter your credentials to access the system.")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("🔑 Login"):
            user = validate_user(supabase, username, password)
            if user:
                st.session_state.authenticated = True
                st.session_state.username = user["username"]
                st.session_state.properties = user["properties"]
                st.session_state.screens = user["screens"]
                st.session_state.is_admin = user["is_admin"]
                query_page = query_params.get("page", ["Direct Reservations"])[0]
                if query_page in st.session_state.screens or st.session_state.is_admin:
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
        st.stop()

def main():
    check_authentication()
    st.title("🏢 TIE Reservations")
    st.markdown("---")
    st.sidebar.title(f"Welcome, {st.session_state.username}")
    page_options = ["Direct Reservations", "View Reservations", "Edit Reservations", "Online Reservations", "Edit Online Reservations", "Daily Status", "Daily Management Status", "Analytics"]
    if st.session_state.is_admin:
        page_options.append("Admin Panel")
    # Filter page options based on user permissions
    permitted_pages = [page for page in page_options if page in st.session_state.screens or st.session_state.is_admin]
    
    page = st.sidebar.selectbox("Choose a page", permitted_pages, index=permitted_pages.index(st.session_state.current_page) if st.session_state.current_page in permitted_pages else 0, key="page_select")
    st.session_state.current_page = page

    if page == "Direct Reservations" and (page in st.session_state.screens or st.session_state.is_admin):
        show_new_reservation_form()
    elif page == "View Reservations" and (page in st.session_state.screens or st.session_state.is_admin):
        show_reservations()
    elif page == "Edit Reservations" and (page in st.session_state.screens or st.session_state.is_admin):
        show_edit_reservations()
    elif page == "Online Reservations" and (page in st.session_state.screens or st.session_state.is_admin):
        show_online_reservations()
    elif page == "Edit Online Reservations" and (page in st.session_state.screens or st.session_state.is_admin):
        show_edit_online_reservations(st.session_state.selected_booking_id)
        if st.session_state.selected_booking_id:
            st.session_state.selected_booking_id = None
            st.query_params.clear()
    elif page == "Daily Status" and (page in st.session_state.screens or st.session_state.is_admin):
        show_daily_status()
    elif page == "Daily Management Status" and (page in st.session_state.screens or st.session_state.is_admin):
        show_dms()
    elif page == "Analytics" and (page in st.session_state.screens or st.session_state.is_admin):
        show_analytics()
    elif page == "Admin Panel" and st.session_state.is_admin:
        show_admin_panel()

    # Logout button
    if st.sidebar.button("Log Out"):
        st.session_state.authenticated = False
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
