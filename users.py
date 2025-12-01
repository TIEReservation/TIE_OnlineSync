import streamlit as st
from supabase import Client
import bcrypt

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
