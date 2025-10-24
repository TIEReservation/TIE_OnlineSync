import streamlit as st
import os
import supabase
from supabase import Client, create_client
import bcrypt

# Initialize Supabase client
@st.cache_resource
def init_supabase():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    return create_client(url, key)

supabase = init_supabase()

# Session state for user management
if 'user' not in st.session_state:
    st.session_state.user = None

# Login function
def login(username, password):
    try:
        user_response = supabase.table("users").select("*").eq("username", username).single().execute()
        user = user_response.data
        if user and password == user["password_hash"]:  # Changed from bcrypt.checkpw
            st.session_state.user = user
            st.success("Login successful!")
            return True
        else:
            st.error("❌ Invalid username or password. Please try again.")
            return False
    except Exception as e:
        st.error(f"Login error: {e}")
        return False

# Logout function
def logout():
    st.session_state.user = None
    st.success("Logged out successfully!")
    st.rerun()

# Sidebar
st.sidebar.title("TIE Reservations")
if st.session_state.user:
    st.sidebar.button("Log Out", on_click=logout)
else:
    st.sidebar.title("Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("🔑 Login"):
        if login(username, password):
            st.rerun()

# Main content based on user role
if st.session_state.user:
    role = st.session_state.user.get("role")
    screens = st.session_state.user.get("screens", [])
    if role == "Admin" and "User Management" in screens:
        st.title("User Management")
        st.write("Manage users here (add, edit, delete).")
        # Add user management logic here if needed
    else:
        st.write("No access to any screens.")
else:
    st.title("Please Log In")
    st.write("Use the sidebar to log in with your credentials.")

# Debug mode (optional)
if os.environ.get("DEBUG_ENABLED", "false").lower() == "true":
    st.write("Debug Mode Enabled")
    st.write(f"Current user: {st.session_state.user}")
