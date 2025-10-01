import streamlit as st
from supabase import Client

def validate_user(supabase: Client, username: str, role: str) -> dict:
    """Validate user by username and role, return user data if valid."""
    try:
        response = supabase.table("users").select("*").eq("username", username).eq("role", role).execute()
        if response.data:
            user = response.data[0]
            return {
                "username": user["username"],
                "role": user["role"],
                "properties": user["properties"],
                "screens": user["screens"]
            }
        return None
    except Exception as e:
        st.error(f"Error validating user: {e}")
        return None

def create_user(supabase: Client, username: str, role: str, properties: list, screens: list) -> bool:
    """Create a new user in Supabase."""
    try:
        user_data = {
            "username": username,
            "role": role,
            "properties": properties,
            "screens": screens
        }
        response = supabase.table("users").insert(user_data).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Error creating user: {e}")
        return False

def update_user(supabase: Client, username: str, role: str = None, properties: list = None, screens: list = None) -> bool:
    """Update an existing user in Supabase."""
    try:
        update_data = {}
        if role:
            update_data["role"] = role
        if properties is not None:
            update_data["properties"] = properties
        if screens is not None:
            update_data["screens"] = screens
        if update_data:
            response = supabase.table("users").update(update_data).eq("username", username).execute()
            return bool(response.data)
        return False
    except Exception as e:
        st.error(f"Error updating user: {e}")
        return False

def delete_user(supabase: Client, username: str) -> bool:
    """Delete a user from Supabase."""
    try:
        response = supabase.table("users").delete().eq("username", username).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Error deleting user: {e}")
        return False

def load_users(supabase: Client) -> list:
    """Load all users from Supabase."""
    try:
        response = supabase.table("users").select("*").execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error loading users: {e}")
        return []
