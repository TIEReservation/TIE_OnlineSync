import streamlit as st
import os  # Added to resolve NameError
from supabase import create_client, Client
from datetime import datetime
import pandas as pd

# Initialize Supabase client (using environment variables from app.py)
try:
    supabase: Client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
except Exception as e:
    st.error(f"Failed to initialize Supabase client: {e}")
    st.stop()

def log_activity(username, action):
    """Log user activity to Supabase."""
    log_entry = {
        "username": username,
        "action": action,
        "timestamp": datetime.now().isoformat()
    }
    try:
        supabase.table("logs").insert(log_entry).execute()
    except Exception as e:
        st.error(f"Failed to log activity: {e}")

def show_log_report():
    st.subheader("Log Report")
    
    # Get all users from users table
    users = supabase.table("users").select("username").execute().data
    if not users:
        st.info("No users found.")
        return
    user_names = sorted(list(set(u["username"] for u in users if u["username"])))
    
    # Display list of users
    selected_user = st.selectbox("Select User", user_names)
    
    if selected_user:
        # Month selection
        current_year = datetime.now().year
        current_month = datetime.now().month
        month = st.selectbox("Select Month", range(1, 13), index=current_month - 1, format_func=lambda x: datetime(current_year, x, 1).strftime("%B"))
        
        # Fetch logs for the selected user and month
        start_date = datetime(current_year, month, 1).isoformat()
        end_date = datetime(current_year, month + 1, 1).isoformat() if month < 12 else datetime(current_year + 1, 1, 1).isoformat()
        logs = supabase.table("logs").select("*").eq("username", selected_user).gte("timestamp", start_date).lt("timestamp", end_date).order("timestamp").execute().data
        
        if not logs:
            st.info("No logs found for the selected user and month.")
            return
        
        # Group by day
        df = pd.DataFrame(logs)
        df['date'] = pd.to_datetime(df['timestamp']).dt.date
        grouped = df.groupby("date")['action'].value_counts().reset_index(name='count')
        
        # Display summaries in point form
        st.subheader(f"{selected_user}'s Activity Log for {datetime(current_year, month, 1).strftime('%B %Y')}")
        for day, group in grouped.groupby("date"):
            st.write(f"**{day}**")
            for action, count in group.groupby("action")["count"].sum().items():
                st.write(f"- {action}: {count}")
