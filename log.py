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

def parse_action(action):
    """Parse the action string to extract type, res_type, old_status, new_status."""
    if action.startswith("Added new direct reservation"):
        parts = action.split(" ")
        if len(parts) >= 8:
            return "add", "direct", None, parts[7]
    elif action.startswith("Added new online reservation"):
        parts = action.split(" ")
        if len(parts) >= 8:
            return "add", "online", None, parts[7]
    elif action.startswith("Updated direct reservation"):
        parts = action.split(" ")
        if len(parts) >= 9:
            return "update", "direct", parts[6], parts[8]
    elif action.startswith("Updated online reservation"):
        parts = action.split(" ")
        if len(parts) >= 9:
            return "update", "online", parts[6], parts[8]
    return None, None, None, None

def show_user_dashboard(supabase):
    """Display user dashboard with counts of added, confirmed, cancelled, and modified reservations."""
    st.subheader("User Dashboard")

    # Get all users
    users = supabase.table("users").select("username").execute().data
    if not users:
        st.info("No users found.")
        return
    user_names = sorted(list(set(u["username"] for u in users if u["username"])))

    if st.session_state.role in ["Management", "Admin"]:
        selected_user = st.selectbox("Select User", user_names)
    else:
        selected_user = st.session_state.username
        st.write(f"Viewing dashboard for: {selected_user}")

    if selected_user:
        current_year = datetime.now().year
        current_month = datetime.now().month
        month = st.selectbox("Select Month", range(1, 13), index=current_month - 1, format_func=lambda x: datetime(current_year, x, 1).strftime("%B"))
        
        start_date = datetime(current_year, month, 1).isoformat()
        end_date = datetime(current_year + (month // 12), (month % 12) + 1, 1).isoformat() if month < 12 else datetime(current_year + 1, 1, 1).isoformat()
        
        # Fetch logs for the selected user and month, excluding 'Accessed' actions
        logs = supabase.table("logs").select("*").eq("username", selected_user).gte("timestamp", start_date).lt("timestamp", end_date).not_.like("action", "%Accessed%").order("timestamp").execute().data
        
        if not logs:
            st.info("No relevant activity (Added, Confirmed, Cancelled, Modified) found for the selected user and month.")
            return
        
        # Compute counts
        new_added = 0
        cancelled = 0
        confirmed = 0
        modified = 0
        
        for log in logs:
            action = log["action"]
            type_, res_type, old_status, new_status = parse_action(action)
            if type_:
                if type_ == "add" and res_type == "direct":
                    new_added += 1
                if new_status == "Cancelled":
                    cancelled += 1
                if new_status == "Confirmed":
                    confirmed += 1
                if (type_ == "update" and old_status == "Confirmed") or (new_status not in ["Confirmed", "Cancelled"]):
                    modified += 1
        
        # Display counts
        month_name = datetime(current_year, month, 1).strftime("%B %Y")
        st.subheader(f"{selected_user}'s Activity Summary for {month_name}")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("New Reservations Added", new_added)
        with col2:
            st.metric("Confirmed", confirmed)
        with col3:
            st.metric("Cancelled", cancelled)
        with col4:
            st.metric("Modified", modified)
        
        # Display detailed logs
        st.subheader("Detailed Activity Log")
        df = pd.DataFrame(logs)
        df['date'] = pd.to_datetime(df['timestamp']).dt.date
        grouped = df.groupby("date")['action'].value_counts().reset_index(name='count')
        
        for day, group in grouped.groupby("date"):
            st.write(f"**{day}**")
            for action, count in group.groupby("action")["count"].sum().items():
                st.write(f"- {action}: {count}")

def show_log_report(supabase):
    """Display log report for admin users, excluding 'Accessed' actions."""
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
        
        # Fetch logs for the selected user and month, excluding 'Accessed' actions
        start_date = datetime(current_year, month, 1).isoformat()
        end_date = datetime(current_year, month + 1, 1).isoformat() if month < 12 else datetime(current_year + 1, 1, 1).isoformat()
        logs = supabase.table("logs").select("*").eq("username", selected_user).gte("timestamp", start_date).lt("timestamp", end_date).not_.like("action", "%Accessed%").order("timestamp").execute().data
        
        if not logs:
            st.info("No relevant activity (Added, Confirmed, Cancelled, Modified) found for the selected user and month.")
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
