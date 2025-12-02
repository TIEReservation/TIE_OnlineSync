import streamlit as st
from supabase import Client

def validate_user(supabase: Client, username: str, password: str):
    """Validate user credentials against database with plain text password"""
    try:
        # Fetch user from database
        response = supabase.table("users").select("*").eq("username", username).execute()
        
        if not response.data or len(response.data) == 0:
            print(f"Debug: User '{username}' not found in database")
            return None
        
        user = response.data[0]
        stored_password = user.get("password")
        
        if not stored_password:
            print(f"Debug: No password found for user '{username}'")
            return None
        
        # Direct plain text password comparison
        if password == stored_password:
            return user
        else:
            print(f"Debug: Password verification failed for username '{username}'")
            return None
                
    except Exception as e:
        st.error(f"Database error during authentication: {e}")
        print(f"Debug: Database error for user '{username}': {e}")
        return None

def create_user(supabase: Client, username: str, password: str, role: str, 
                properties: list, screens: list, permissions: dict) -> bool:
    """Create a new user in the database with plain text password"""
    try:
        # Insert user into database with plain text password
        user_data = {
            "username": username,
            "password": password,  # Store as plain text
            "role": role,
            "properties": properties,
            "screens": screens,
            "permissions": permissions
        }
        
        response = supabase.table("users").insert(user_data).execute()
        
        if response.data:
            st.success(f"User '{username}' created successfully!")
            return True
        else:
            st.error("Failed to create user")
            return False
            
    except Exception as e:
        st.error(f"Error creating user: {e}")
        print(f"Debug: Error creating user '{username}': {e}")
        return False

def update_user(supabase: Client, username: str, password: str = None, 
                role: str = None, properties: list = None, 
                screens: list = None, permissions: dict = None) -> bool:
    """Update an existing user in the database"""
    try:
        # Build update dictionary
        update_data = {}
        
        if password:
            update_data["password"] = password  # Store as plain text
        
        if role is not None:
            update_data["role"] = role
        
        if properties is not None:
            update_data["properties"] = properties
        
        if screens is not None:
            update_data["screens"] = screens
        
        if permissions is not None:
            update_data["permissions"] = permissions
        
        if not update_data:
            st.warning("No changes to update")
            return False
        
        # Update user in database
        response = supabase.table("users").update(update_data).eq("username", username).execute()
        
        if response.data:
            st.success(f"User '{username}' updated successfully!")
            return True
        else:
            st.error("Failed to update user")
            return False
            
    except Exception as e:
        st.error(f"Error updating user: {e}")
        print(f"Debug: Error updating user '{username}': {e}")
        return False

def delete_user(supabase: Client, username: str) -> bool:
    """Delete a user from the database"""
    try:
        response = supabase.table("users").delete().eq("username", username).execute()
        
        if response.data:
            st.success(f"User '{username}' deleted successfully!")
            return True
        else:
            st.error("Failed to delete user")
            return False
            
    except Exception as e:
        st.error(f"Error deleting user: {e}")
        print(f"Debug: Error deleting user '{username}': {e}")
        return False

def load_users(supabase: Client) -> list:
    """Load all users from the database"""
    try:
        response = supabase.table("users").select("*").execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error loading users: {e}")
        print(f"Debug: Error loading users: {e}")
        return []
