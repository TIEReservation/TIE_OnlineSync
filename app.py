import streamlit as st
from directreservation import load_reservations_from_supabase
from datetime import date

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None
    st.session_state.users = []  # List to store users

def show_login():
    st.title("Hotel Reservation System - Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        users = st.session_state.get("users", [])
        user = next((u for u in users if u["username"] == username and u["password"] == password), None)
        if user:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = user["role"]
            st.rerun()
        else:
            st.error("Invalid credentials")

def show_user_management():
    st.subheader("Admin User Management")
    
    # Get reservations data for property names
    reservations = load_reservations_from_supabase()
    all_properties = sorted(list(set(res["Property Name"] for res in reservations if res and "Property Name" in res))) if reservations else []
    
    if not all_properties:
        st.warning("No properties found in reservations. Using fallback list.")
        all_properties = ["Le Poshe Beach view", "La Millionaire Resort", "Le Poshe Luxury", "Le Poshe Suite", "Eden Beach Resort"]  # Fallback with 'Eden Beach Resort'

    all_screens = ["Direct Reservations", "View Reservations", "Analytics", "Reports"]
    all_access = ["Add", "Edit", "Delete"]

    all_users = st.session_state.get("users", [])

    # Admin can create a new user or modify existing
    action = st.radio("Action", ["Create New User", "Modify Existing User"], key="user_action")

    if action == "Create New User":
        with st.form(key="create_user_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            role = st.selectbox("Role", ["Management", "Reservation Team"])
            visible_properties = st.multiselect("Visible Properties", all_properties)
            visible_screens = st.multiselect("Visible Screens", all_screens)
            access_levels = st.multiselect("Access Levels", all_access)
            
            if st.form_submit_button("Create User"):
                new_user = {
                    "username": username,
                    "password": password,  # Note: Hash password in production
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
        
        user_to_modify = st.selectbox("Select User to Modify", [user["username"] for user in all_users])
        user_index = next(i for i, user in enumerate(all_users) if user["username"] == user_to_modify)
        
        with st.form(key="modify_user_form"):
            username = st.text_input("Username", value=user_to_modify, disabled=True)
            password = st.text_input("New Password (leave blank to keep current)", type="password")
            role = st.selectbox("Role", ["Management", "Reservation Team"], index=["Management", "Reservation Team"].index(all_users[user_index]["role"]))
            
            # Filter default properties to only those in all_properties
            default_properties = [prop for prop in all_users[user_index]["properties"] if prop in all_properties]
            mod_properties = st.multiselect("Visible Properties", all_properties, default=default_properties)
            
            mod_screens = st.multiselect("Visible Screens", all_screens, default=[s for s in all_users[user_index]["screens"] if s in all_screens])
            mod_access = st.multiselect("Access Levels", all_access, default=[a for a in all_users[user_index]["permissions"] if a in all_access])
            
            if st.form_submit_button("Update User"):
                updated_user = {
                    "username": username,
                    "password": password if password else all_users[user_index]["password"],  # Keep old password if blank
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
            st.write(f"Username: {user['username']}, Role: {user['role']}, Properties: {', '.join(user['properties'])}, Screens: {', '.join(user['screens'])}, Access: {', '.join(user['permissions'])}")

def show_monthly_consolidation():
    st.subheader("Monthly Consolidation")
    st.write("This is a placeholder for monthly consolidation data.")
    # Add your consolidation logic here

def main():
    st.title("Hotel Reservation System")
    
    if not st.session_state.logged_in:
        show_login()
    else:
        st.sidebar.write(f"Welcome, {st.session_state.username} ({st.session_state.role})")
        page = st.sidebar.selectbox("Navigate", ["Reservations", "Monthly Consolidation", "User Management"])
        if page == "Reservations":
            st.write("Reservations page content goes here.")
            # Add reservation logic
        elif page == "Monthly Consolidation":
            show_monthly_consolidation()
        elif page == "User Management" and st.session_state.role == "Admin":
            show_user_management()
        
        if st.sidebar.button("Log Out"):
            st.cache_data.clear()
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.role = None
            st.rerun()

if __name__ == "__main__":
    main()
