import streamlit as st
from supabase import Client
import bcrypt

# ============================================================================
# FIXED USER MANAGEMENT FUNCTIONS (working with password_hash column)
# ============================================================================

def hash_password(password: str) -> str:
    try:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    except Exception as e:
        st.error(f"Error hashing password: {e}")
        return None

def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception as e:
        st.error(f"Error verifying password: {e}")
        return False

def validate_user(supabase: Client, username: str, password: str) -> dict | None:
    try:
        response = supabase.table("users").select("*").eq("username", username).execute()
        if not response.data or not response.data[0].get("password_hash"):
            return None
        if verify_password(password, response.data[0]["password_hash"]):
            user = response.data[0]
            return {
                "username": user["username"],
                "role": user["role"],
                "properties": user.get("properties") or [],
                "screens": user.get("screens") or []
            }
        return None
    except Exception as e:
        st.error(f"Login error: {e}")
        return None

def create_user(supabase: Client, username: str, password: str, role: str, properties: list, screens: list) -> bool:
    try:
        hashed = hash_password(password)
        if not hashed:
            return False
        user_data = {
            "username": username,
            "password_hash": hashed,   # ← FIXED
            "role": role,
            "properties": properties,
            "screens": screens
        }
        response = supabase.table("users").insert(user_data).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Failed to create user: {e}")
        return False

def update_user(supabase: Client, username: str, password: str = None, role: str = None, properties: list = None, screens: list = None) -> bool:
    try:
        update_data = {}
        if password:
            update_data["password_hash"] = hash_password(password)  # ← FIXED
        if role:
            update_data["role"] = role
        if properties is not None:
            update_data["properties"] = properties
        if screens is not None:
            update_data["screens"] = screens
        if update_data:
            response = supabase.table("users").update(update_data).eq("username", username).execute()
            return bool(response.data)
        return True
    except Exception as e:
        st.error(f"Update failed: {e}")
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
