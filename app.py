# app.py - FULLY WORKING VERSION - DECEMBER 2025
import streamlit as st
import os
import pandas as pd
import bcrypt
from supabase import create_client, Client

# =========================== IMPORTS ===========================
from directreservation import (
    show_new_reservation_form, show_reservations,
    show_edit_reservations, show_analytics, load_reservations_from_supabase
)
from online_reservation import show_online_reservations, load_online_reservations_from_supabase
from inventory import show_daily_status
from dms import show_dms
from monthlyconsolidation import show_monthly_consolidation
from dashboard import show_dashboard
from summary_report import show_summary_report
from log import show_log_report, log_activity

# Optional online edit
try:
    from editOnline import show_edit_online_reservations
    edit_online_available = True
except:
    edit_online_available = False

# =========================== PAGE CONFIG ===========================
st.set_page_config(
    page_title="TIE Reservations",
    page_icon="https://github.com/TIEReservation/TIEReservation-System/raw/main/TIE_Logo_Icon.png",
    layout="wide"
)
st.image("https://github.com/TIEReservation/TIEReservation-System/raw/main/TIE_Logo_Icon.png", width=100)

# =========================== SUPABASE ===========================
supabase: Client = create_client(
    "https://oxbrezracnmazucnnqox.supabase.co",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im94YnJlenJhY25tYXp1Y25ucW94Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM3NjUxMTgsImV4cCI6MjA2OTM0MTExOH0.nqBK2ZxntesLY9qYClpoFPVnXOW10KrzF-UI_DKjbKo"
)

# =========================== USER FUNCTIONS (FIXED) ===========================
def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))

def validate_user(supabase: Client, username: str, password: str) -> dict | None:
    try:
        resp = supabase.table("users").select("*").eq("username", username).execute()
        if not resp.data:
            return None
        user = resp.data[0]
        if not user.get("password_hash") or not verify_password(password, user["password_hash"]):
            return None
        return {
            "username": user["username"],
            "role": user["role"],
            "properties": user.get("properties") or [],
            "screens": user.get("screens") or []
        }
    except:
        return None

def create_user(supabase: Client, username: str, password: str, role: str, properties: list, screens: list) -> bool:
    try:
        data = {
            "username": username,
            "password_hash": hash_password(password),  # CORRECT COLUMN
            "role": role,
            "properties": properties or [],
            "screens": screens or []
        }
        result = supabase.table("users").insert(data).execute()
        if result.data:
            st.success(f"User '{username}' created successfully!")
            log_activity(supabase, st.session_state.username, f"Created user: {username}")
            return True
        st.error("Failed to create user")
        return False
    except Exception as e:
        st.error(f"Error: {e}")
        return False

def update_user(supabase: Client, username: str, password: str = None, role: str = None,
                properties: list = None, screens: list = None) -> bool:
    try:
        data = {}
        if password:
            data["password_hash"] = hash_password(password)  # CORRECT COLUMN
        if role: data["role"] = role
        if properties is not None: data["properties"] = properties
        if screens is not None: data["screens"] = screens
        if data:
            result = supabase.table("users").update(data).eq("username", username).execute()
            if result.data:
                st.success("User updated!")
                log_activity(supabase, st.session_state.username, f"Updated user: {username}")
                return True
        return False
    except Exception as e:
        st.error(f"Update failed: {e}")
        return False

def load_users(supabase: Client) -> list:
    try:
        resp = supabase.table("users").select("*").execute()
        return resp.data or []
    except Exception as e:
        st.error(f"Load users error: {e}")
        return []

def load_properties() -> list:
    tie_properties = [
        "Eden Beach Resort","Villa Shakti","La Villa Heritage","La Paradise Luxury",
        "Le Poshe Luxury","La Paradise Residency","Le Pondy Beachside","Le Poshe Beachview",
        "Le Park Resort","Le Terra Resort","La Tamara Suite","La Antilia Luxury",
        "La Tamara Luxury","Le Royce Villa","La Millionaire Resort","Le Poshe Suite",
        "La Coromandel Luxury"
    ]
    try:
        resp = supabase.table("reservations").select("property").execute()
        extra = [r["property"] for r in resp.data if r.get("property")]
        return sorted(list(set(tie_properties + extra)))
    except:
        return sorted(tie_properties)

# =========================== AUTHENTICATION ===========================
def check_authentication():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.role = None
        st.session_state.current_page = "Direct Reservations"

    if not st.session_state.authenticated:
        st.title("TIE Reservations - Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            # Hardcoded emergency accounts
            if username == "Admin" and password == "TIE2024":
                st.session_state.update(authenticated=True, username="Admin", role="Admin", current_page="User Management")
                st.rerun()
            elif username == "Management" and password == "TIE2024":
                st.session_state.update(authenticated=True, username="Management", role="Management", current_page="Inventory Dashboard")
                st.rerun()
            elif username == "ReservationTeam" and password == "TIE123":
                st.session_state.update(authenticated=True, username="ReservationTeam", role="ReservationTeam", current_page="Direct Reservations")
                st.rerun()

            # Database users
            user = validate_user(supabase, username, password)
            if user:
                st.session_state.update(
                    authenticated=True,
                    username=username,
                    role=user["role"],
                    current_page="User Management" if user["role"] == "Admin" else "Inventory Dashboard"
                )
                st.rerun()
            else:
                st.error("Invalid username or password")
        st.stop()

# =========================== USER MANAGEMENT PAGE ===========================
def show_user_management():
    if st.session_state.role != "Admin":
        st.error("Access Denied - Admin Only")
        return

    st.title("User Management")
    users = load_users(supabase)

    if users:
        df = pd.DataFrame(users)
        st.dataframe(
            df[["username", "role", "properties", "screens"]],
            width="stretch",
            hide_index=True
        )
    else:
        st.info("No users found in database.")

    tab1, tab2, tab3 = st.tabs(["Create User", "Modify User", "Delete User"])

    with tab1:
        st.subheader("Create New User")
        nu = st.text_input("Username", key="nu")
        np = st.text_input("Password", type="password", key="np")
        nr = st.selectbox("Role", ["ReservationTeam", "Management", "Admin"], key="nr")
        nprop = st.multiselect("Properties", load_properties(), key="nprop")
        nscr = st.multiselect("Allowed Screens", [
            "Inventory Dashboard","Direct Reservations","View Reservations","Edit Direct Reservation",
            "Online Reservations","Edit Online Reservations","Daily Status","Daily Management Status",
            "Analytics","Monthly Consolidation","Summary Report"
        ], key="nscr")

        if st.button("Create User", type="primary"):
            if nu and np:
                create_user(supabase, nu, np, nr, nprop, nscr)
                st.rerun()
            else:
                st.error("Username and password required")

    with tab2:
        if users:
            sel = st.selectbox("Select user to edit", [u["username"] for u in users])
            user = next(u for u in users if u["username"] == sel)
            new_pass = st.text_input("New Password (leave blank to keep)", type="password")
            new_role = st.selectbox("Role", ["ReservationTeam", "Management", "Admin"],
                                   index=["ReservationTeam", "Management", "Admin"].index(user["role"]))
            new_prop = st.multiselect("Properties", load_properties(), default=user.get("properties",[]))
            new_scr = st.multiselect("Screens", [
                "Inventory Dashboard","Direct Reservations","View Reservations","Edit Direct Reservation",
                "Online Reservations","Edit Online Reservations","Daily Status","Daily Management Status",
                "Analytics","Monthly Consolidation","Summary Report"
            ], default=user.get("screens", []))

            if st.button("Update User"):
                update_user(supabase, sel, new_pass or None, new_role, new_prop, new_scr)
                st.rerun()

    with tab3:
        if users:
            del_user = st.selectbox("User to delete", [u["username"] for u in users], key="delu")
            confirm = st.text_input("Type username to confirm deletion")
            if st.button("Delete User", type="primary") and confirm == del_user:
                supabase.table("users").delete().eq("username", del_user).execute()
                st.success("User deleted")
                log_activity(supabase, st.session_state.username, f"Deleted user: {del_user}")
                st.rerun()

# =========================== MAIN APP ===========================
def main():
    check_authentication()

    # Navigation
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
        "Navigation",
        pages,
        index=pages.index(st.session_state.current_page) if st.session_state.current_page in pages else 0
    )
    st.session_state.current_page = page

    if st.sidebar.button("Refresh All Data"):
        st.cache_data.clear()
        st.success("Cache cleared")
        st.rerun()

    # Page routing
    if page == "User Management":
        show_user_management()

    elif page == "Inventory Dashboard":
        if st.session_state.role in ["Admin", "Management"]:
            show_dashboard()
            log_activity(supabase, st.session_state.username, "Accessed Inventory Dashboard")
        else:
            st.error("Access denied")

    elif page == "Direct Reservations":
        show_new_reservation_form()
        log_activity(supabase, st.session_state.username, "Accessed Direct Reservations")

    elif page == "View Reservations":
        show_reservations()
        log_activity(supabase, st.session_state.username, "Accessed View Reservations")

    elif page == "Edit Direct Reservation":
        show_edit_reservations()
        log_activity(supabase, st.session_state.username, "Accessed Edit Direct Reservation")

    elif page == "Online Reservations":
        show_online_reservations()
        log_activity(supabase, st.session_state.username, "Accessed Online Reservations")

    elif page == "Edit Online Reservations" and edit_online_available:
        show_edit_online_reservations(st.session_state.get("selected_booking_id"))

    elif page == "Daily Status":
        show_daily_status()

    elif page == "Daily Management Status":
        show_dms()

    elif page == "Analytics":
        if st.session_state.role in ["Admin", "Management"]:
            show_analytics()
        else:
            st.error("Access denied")

    elif page == "Monthly Consolidation":
        show_monthly_consolidation()

    elif page == "Summary Report":
        if st.session_state.role in ["Admin", "Management"]:
            show_summary_report()
        else:
            st.error("Access denied")

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
