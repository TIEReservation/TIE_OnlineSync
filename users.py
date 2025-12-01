# app.py
import streamlit as st
import os
import pandas as pd

# ──────────────────────────────────────────────────────────────
# 1. IMPORT USER FUNCTIONS FIRST – THIS FIXES THE NameError
# ──────────────────────────────────────────────────────────────
try:
    from users import (
        load_users,
        create_user,
        validate_user,
        load_properties
    )
except ImportError as e:
    st.error(f"Cannot find 'users.py' → {e}")
    st.stop()

# ──────────────────────────────────────────────────────────────
# 2. OTHER PAGE MODULES
# ──────────────────────────────────────────────────────────────
from directreservation import (
    show_new_reservation_form,
    show_reservations,
    show_edit_reservations,
    show_analytics,
    load_reservations_from_supabase
)
from online_reservation import show_online_reservations, load_online_reservations_from_supabase
from inventory import show_daily_status
from dms import show_dms
from monthlyconsolidation import show_monthly_consolidation
from dashboard import show_dashboard
from summary_report import show_summary_report
from log import show_log_report, log_activity

# Optional online edit module
try:
    from editOnline import show_edit_online_reservations
    edit_online_available = True
except ImportError:
    edit_online_available = False
    show_edit_online_reservations = None

# ──────────────────────────────────────────────────────────────
# 3. PAGE CONFIG & SUPABASE
# ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TIE Reservations",
    page_icon="https://github.com/TIEReservation/TIEReservation-System/raw/main/TIE_Logo_Icon.png",
    layout="wide"
)
st.image("https://github.com/TIEReservation/TIEReservation-System/raw/main/TIE_Logo_Icon.png", width=100)

from supabase import create_client, Client
supabase: Client = create_client(
    "https://oxbrezracnmazucnnqox.supabase.co",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im94YnJlenJhY25tYXp1Y25ucW94Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM3NjUxMTgsImV4cCI6MjA2OTM0MTExOH0.nqBK2ZxntesLY9qYClpoFPVnXOW10KrzF-UI_DKjbKo"
)

# ──────────────────────────────────────────────────────────────
# 4. AUTHENTICATION
# ──────────────────────────────────────────────────────────────
def check_authentication():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.role = None
        st.session_state.current_page = "Direct Reservations"

    if not st.session_state.authenticated:
        st.title("TIE Reservations – Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            # Hardcoded emergency accounts
            if username == "Admin" and password == "Admin2024":
                st.session_state.authenticated = True
                st.session_state.username = "Admin"
                st.session_state.role = "Admin"
                st.session_state.current_page = "User Management"
                st.rerun()

            elif username == "Management" and password == "TIE2024":
                st.session_state.authenticated = True
                st.session_state.username = "Management"
                st.session_state.role = "Management"
                st.session_state.current_page = "Inventory Dashboard"
                st.rerun()

            elif username == "ReservationTeam" and password == "TIE123":
                st.session_state.authenticated = True
                st.session_state.username = "ReservationTeam"
                st.session_state.role = "ReservationTeam"
                st.session_state.current_page = "Direct Reservations"
                st.rerun()

            # Real Supabase login (hashed passwords)
            user = validate_user(supabase, username, password)
            if user:
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.role = user["role"]
                st.session_state.current_page = "User Management" if user["role"] == "Admin" else "Inventory Dashboard"
                st.success(f"Welcome {username}!")
                st.rerun()
            else:
                st.error("Invalid credentials")
        st.stop()

# ──────────────────────────────────────────────────────────────
# 5. USER MANAGEMENT PAGE (Admin only)
# ──────────────────────────────────────────────────────────────
def show_user_management():
    if st.session_state.role != "Admin":
        st.error("Access denied – Admin only")
        return

    st.title("User Management")

    # THIS WILL NOW WORK – load_users is imported at the top
    users = load_users(supabase)

    if users:
        df = pd.DataFrame(users)[["username", "role", "properties", "screens"]]
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No users in database yet.")

    st.subheader("Create New User")
    c1, c2 = st.columns(2)
    with c1:
        new_username = st.text_input("Username", key="new_user")
        new_password = st.text_input("Password", type="password", key="new_pass")
        new_role = st.selectbox("Role", ["ReservationTeam", "Management", "Admin"], key="new_role")
    with c2:
        new_properties = st.multiselect("Properties", load_properties(), default=load_properties())
        new_screens = st.multiselect("Allowed Screens", [
            "Inventory Dashboard", "Direct Reservations", "View Reservations",
            "Edit Direct Reservation", "Online Reservations", "Edit Online Reservations",
            "Daily Status", "Daily Management Status", "Analytics",
            "Monthly Consolidation", "Summary Report"
        ])

    if st.button("Create User"):
        if create_user(supabase, new_username, new_password, new_role, new_properties, new_screens):
            st.success(f"User {new_username} created!")
            st.rerun()

# ──────────────────────────────────────────────────────────────
# 6. MAIN APP
# ──────────────────────────────────────────────────────────────
def main():
    check_authentication()

    pages = [
        "Inventory Dashboard", "Direct Reservations", "View Reservations",
        "Edit Direct Reservation", "Online Reservations", "Daily Status",
        "Daily Management Status", "Analytics", "Monthly Consolidation", "Summary Report"
    ]
    if edit_online_available:
        pages.insert(5, "Edit Online Reservations")
    if st.session_state.role == "Admin":
        pages += ["User Management", "Log Report"]

    page = st.sidebar.selectbox(
        "Navigate",
        pages,
        index=pages.index(st.session_state.current_page) if st.session_state.current_page in pages else 0
    )
    st.session_state.current_page = page

    if st.sidebar.button("Refresh Data"):
        st.cache_data.clear()
        st.success("Cache cleared")
        st.rerun()

    # ───── PAGE ROUTING ─────
    if page == "Inventory Dashboard":
        if st.session_state.role not in ["Admin", "Management"]:
            st.error("Access denied")
        else:
            show_dashboard()

    elif page == "Direct Reservations":
        show_new_reservation_form()

    elif page == "View Reservations":
        show_reservations()

    elif page == "Edit Direct Reservation":
        show_edit_reservations()

    elif page == "Online Reservations":
        show_online_reservations()

    elif page == "Edit Online Reservations" and edit_online_available:
        show_edit_online_reservations(st.session_state.get("selected_booking_id"))

    elif page == "Daily Status":
        show_daily_status()

    elif page == "Daily Management Status":
        show_dms()

    elif page == "Analytics":
        if st.session_state.role not in ["Admin", "Management"]:
            st.error("Access denied")
        else:
            show_analytics()

    elif page == "Monthly Consolidation":
        show_monthly_consolidation()

    elif page == "Summary Report":
        if st.session_state.role not in ["Admin", "Management"]:
            st.error("Access denied")
        else:
            show_summary_report()

    elif page == "User Management":
        show_user_management()
        log_activity(supabase, st.session_state.username, "Accessed User Management")

    elif page == "Log Report":
        show_log_report(supabase)

    # Footer
    st.sidebar.markdown(f"**Logged in as:** {st.session_state.username} ({st.session_state.role})")
    if st.sidebar.button("Log Out"):
        log_activity(supabase, st.session_state.username, "Logged out")
        st.session_state.clear()
        st.rerun()

if __name__ == "__main__":
    main()
