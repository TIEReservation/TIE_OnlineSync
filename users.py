import streamlit as st
from supabase import Client
import bcrypt

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def validate_user(supabase: Client, username: str, password: str) -> dict:
    """Validate user credentials and return user data if valid."""
    try:
        response = supabase.table("users").select("*").eq("username", username).execute()
        if response.data:
            user = response.data[0]
            if bcrypt.checkpw(password.encode('utf-8'), user["password"].encode('utf-8')):
                return {
                    "username": user["username"],
                    "properties": user["properties"],
                    "screens": user["screens"],
                    "is_admin": user["is_admin"]
                }
        return None
    except Exception as e:
        st.error(f"Error validating user: {e}")
        return None

def create_user(supabase: Client, username: str, password: str, properties: list, screens: list, is_admin: bool = False) -> bool:
    """Create a new user in Supabase."""
    try:
        hashed_password = hash_password(password)
        user_data = {
            "username": username,
            "password": hashed_password,
            "properties": properties,
            "screens": screens,
            "is_admin": is_admin
        }
        response = supabase.table("users").insert(user_data).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Error creating user: {e}")
        return False

def update_user(supabase: Client, username: str, password: str = None, properties: list = None, screens: list = None, is_admin: bool = None) -> bool:
    """Update an existing user in Supabase."""
    try:
        update_data = {}
        if password:
            update_data["password"] = hash_password(password)
        if properties is not None:
            update_data["properties"] = properties
        if screens is not None:
            update_data["screens"] = screens
        if is_admin is not None:
            update_data["is_admin"] = is_admin
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
