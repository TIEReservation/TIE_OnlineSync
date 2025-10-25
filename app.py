import streamlit as st

def show_user_management():
    st.subheader("Admin User Management")
    
    # Simulated user list and properties (replace with your data source)
    all_users = st.session_state.get("users", [])
    all_properties = ["Le Poshe Beach view", "La Millionaire Resort", "Le Poshe Luxury", "Le Poshe Suite"]
    all_screens = ["Reservations", "Analytics", "Reports"]
    all_access = ["Add", "Edit", "Delete"]

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
                    "password": password,  # Note: In production, hash the password
                    "role": role,
                    "properties": visible_properties,
                    "screens": visible_screens,
                    "access": access_levels
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
            # Pre-fill existing data
            username = st.text_input("Username", value=user_to_modify, disabled=True)
            password = st.text_input("New Password (leave blank to keep current)", type="password")
            role = st.selectbox("Role", ["Management", "Reservation Team"], index=["Management", "Reservation Team"].index(all_users[user_index]["role"]))
            mod_properties = st.multiselect("Visible Properties", all_properties, default=all_users[user_index]["properties"])
            mod_screens = st.multiselect("Visible Screens", all_screens, default=all_users[user_index]["screens"])
            mod_access = st.multiselect("Access Levels", all_access, default=all_users[user_index]["access"])
            
            if st.form_submit_button("Update User"):
                updated_user = {
                    "username": username,
                    "password": password if password else all_users[user_index]["password"],  # Keep old password if blank
                    "role": role,
                    "properties": mod_properties,
                    "screens": mod_screens,
                    "access": mod_access
                }
                all_users[user_index] = updated_user
                st.session_state.users = all_users
                st.success(f"User {username} updated successfully!")
                st.rerun()

    # Display current users (for admin view)
    if all_users:
        st.subheader("Current Users")
        for user in all_users:
            st.write(f"Username: {user['username']}, Role: {user['role']}, Properties: {', '.join(user['properties'])}, Screens: {', '.join(user['screens'])}, Access: {', '.join(user['access'])}")
