import streamlit as st
from datetime import datetime
import pandas as pd

def log_activity(supabase, username, action):
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

def show_log_report(supabase):
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
        
        # Process logs to categorize activities
        df = pd.DataFrame(logs)
        df['date'] = pd.to_datetime(df['timestamp']).dt.date
        
        # Group by day and categorize actions
        st.subheader(f"{selected_user}'s Activity Log for {datetime(current_year, month, 1).strftime('%B %Y')}")
        
        for day in sorted(df['date'].unique()):
            day_logs = df[df['date'] == day]
            
            # Count different activities
            newly_added = 0
            modified = 0
            cancelled = 0
            confirmed = 0
            
            for action in day_logs['action']:
                action_lower = action.lower()
                
                # Newly Added - Adding new reservation via direct
                if 'added' in action_lower and 'reservation' in action_lower:
                    newly_added += 1
                
                # Modified - Edit reservations (both direct and online)
                elif 'updated' in action_lower or 'modified' in action_lower or 'edit' in action_lower:
                    modified += 1
                
                # Cancelled - booking status changed to cancelled
                elif 'cancelled' in action_lower:
                    cancelled += 1
                
                # Confirmed - booking status changed to confirmed
                elif 'confirmed' in action_lower:
                    confirmed += 1
            
            # Display summary for the day
            st.write(f"**{day}**")
            if newly_added > 0:
                st.write(f"- Newly Added: {newly_added}")
            if modified > 0:
                st.write(f"- Modified: {modified}")
            if cancelled > 0:
                st.write(f"- Cancelled: {cancelled}")
            if confirmed > 0:
                st.write(f"- Confirmed: {confirmed}")
            
            # If no activities for the day, show a message
            if newly_added == 0 and modified == 0 and cancelled == 0 and confirmed == 0:
                st.write("- No tracked activities")
