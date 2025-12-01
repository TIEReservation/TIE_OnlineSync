# app.py — FULLY WORKING FINAL VERSION (December 2025)
import streamlit as st
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

try:
    from editOnline import show_edit_online_reservations
    edit_online_available = True
except:
    edit_online_available = False

# =========================== CONFIG ===========================
st.set_page_config(page_title="TIE Reservations", layout="wide",
                   page_icon="https://github.com/TIEReservation/TIEReservation-System/raw/main/TIE_Logo_Icon.png")
st.image("https://github.com/TIEReservation/TIEReservation-System/raw/main/TIE_Logo_Icon.png", width=100)

# =========================== SUPABASE ===========================
supabase: Client = create_client(
    "https://oxbrezracnmazucnnqox.supabase.co",
    "eyJhbGciOiJIUzI1IyIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im94YnJlenJhY25tYXp1Y25ucW94Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM3NjUxMTgsImV4cCI6MjA2OTM0MTExOH0.nqBK2ZxntesLY9qYClpoFPVnXOW10KrzF-UI_DKjbKo"
)

# =========================== USER FUNCTIONS ===========================
def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())

def validate_user(username: str, password: str) -> dict | None:
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

def create_user(username: str, password: str, role: str, properties: list, screens: list) -> bool:
    try:
        data = {
            "username": username,
            "password_hash": hash_password(password),
            "role": role,
            "properties": properties,
            "screens": screens
        }
        result = supabase.table("users").insert(data).execute()
        if result.data:
            st.success(f"User '{username}' created!")
            log_activity(supabase, st.session_state.username, f"Created user: {username}")
            return True
        return False
    except Exception as e:
        st.error(f"Error: {e}")
        return False

def update_user(username: str, password: str = None, role: str = None,
                properties: list = None, screens: list = None) -> bool:
    try:
        data = {}
        if password:
            data["password_hash"] = hash_password(password)
        if role: data["role"] = role
        if properties is not None: data["properties"] = properties
        if screens is not None: data["screens"] = screens
        if data:
            result = supabase.table("users").update(data).eq("username", username).execute()
            return bool(result.data)
        return True
    except Exception as e:
        st.error(f"Update error: {e}")
        return False

def load_users() -> list:
    try:
        return supabase.table("users").select("*").execute().data or []
    except:
        return []

def load_properties() -> list:
    base = ["Eden Beach Resort","Villa Shakti","La Villa Heritage","La Paradise Luxury",
            "Le Poshe Luxury","La Paradise Residency","Le Pondy Beachside","Le Poshe Beachview",
            "Le Park Resort","Le Terra Resort","La Tamara Suite","La Antilia Luxury",
            "La Tamara Luxury","Le Royce Villa","La Millionaire Resort","Le Poshe Suite",
            "La Coromandel Luxury"]
    try:
        extra = [r["property"] for r in supabase.table("reservations").select("property").execute().data if r.get("property")]
        return sorted(list(set(base + extra)))
    except:
        return sorted(base)

# List of screens that non-admin users can have
COMMON_SCREENS = [
    "Inventory Dashboard", "Direct Reservations", "View Reservations",
    "Edit Direct Reservation", "Online Reservations", "Edit Online Reservations",
    "Daily Status", "Daily Management Status", "Analytics",
    "Monthly Consolidation", "Summary Report"
]

# =========================== AUTH ===========================
def check_authentication():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.role = None
        st.session_state.current_page = "Direct Reservations"

    if not st.session_state.authenticated:
        st.title("TIE Reservations – Login")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            if u == "Admin" and p == "TIE2024":
                st.session_state.update(authenticated=True, username="Admin", role="Admin", current_page="User Management")
            elif u == "Management" and p == "TIE2024":
                st.session_state.update(authenticated=True, username="Management", role="Management", current_page="Inventory Dashboard")
            elif u == "ReservationTeam" and p == "TIE123":
                st.session_state.update(authenticated=True, username="ReservationTeam", role="ReservationTeam", current_page="Direct Reservations")
            else:
                user = validate_user(u, p)
                if user:
                    st.session_state.update(authenticated=True, username=u, role=user["role"],
                                          current_page="User Management" if user["role"]=="Admin" else "Inventory Dashboard")
                else:
                    st.error("Invalid credentials")
            st.rerun()
        st.stop()

# =========================== USER MANAGEMENT ===========================
def show_user_management():
    if st.session_state.role != "Admin":
        st.error("Access denied – Admin only")
        return

    st.title("User Management")
    users = load_users()

    if users:
        df = pd.DataFrame(users)
        st.dataframe(df[["username", "role", "properties", "screens"]], width="stretch", hide_index=True)
    else:
        st.info("No users in database yet.")

    t1, t2, t3 = st.tabs(["Create User", "Edit User", "Delete User"])

    # CREATE
    with t1:
        nu = st.text_input("Username", key="create_u")
        np = st.text_input("Password", type="password", key="create_p")
        nr = st.selectbox("Role", ["ReservationTeam", "Management", "Admin"], key="create_r")
        props = st.multiselect("Properties", load_properties(), key="create_prop")
        scr = st.multiselect("Allowed Screens", COMMON_SCREENS, key="create_scr")

        if st.button("Create User", type="primary"):
            if nu and np:
                create_user(nu, np, nr, props, scr)
                st.rerun()
            else:
                st.error("Username and password required")

    # EDIT
    with t2:
        if users:
            name = st.selectbox("Select user", [u["username"] for u in users], key="edit_sel")
            user = next(u for u in users if u["username"] == name)

            new_p = st.text_input("New Password (leave blank to keep)", type="password")
            new_r = st.selectbox("Role", ["ReservationTeam", "Management", "Admin"],
                                index=["ReservationTeam","Management","Admin"].index(user["role"]))

            curr_prop = [p for p in user.get("properties", []) if p in load_properties()]
            new_prop = st.multiselect("Properties", load_properties(), default=curr_prop)

            curr_scr = [s for s in user.get("screens", []) if s in COMMON_SCREENS]
            new_scr = st.multiselect("Screens", COMMON_SCREENS, default=curr_scr)

            if st.button("Update User"):
                update_user(name, new_p or None, new_r, new_prop, new_scr)
                st.success("Updated!")
                st.rerun()

    # DELETE
    with t3:
        if users:
            del_name = st.selectbox("User to delete", [u["username"] for u in users], key="del_sel")
            confirm = st.text_input("Type username to confirm")
            if st.button("Delete User", type="primary") and confirm == del_name:
                supabase.table("users").delete().eq("username", del_name).execute()
                st.success("Deleted")
                log_activity(supabase, st.session_state.username, f"Deleted user: {del_name}")
                st.rerun()

# =========================== MAIN ===========================
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

    page = st.sidebar.selectbox("Navigate", pages,
              index=pages.index(st.session_state.current_page) if st.session_state.current_page in pages else 0)

    st.session_state.current_page = page

    if st.sidebar.button("Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    # ROUTING
    if page == "User Management":
        show_user_management()
    elif page == "Inventory Dashboard" and st.session_state.role in ["Admin", "Management"]:
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
    elif page == "Analytics" and st.session_state.role in ["Admin", "Management"]:
        show_analytics()
    elif page == "Monthly Consolidation":
        show_monthly_consolidation()
    elif page == "Summary Report" and st.session_state.role in ["Admin", "Management"]:
        show_summary_report()
    elif page == "Log Report":
        show_log_report(supabase)

    st.sidebar.markdown(f"**{st.session_state.username}** ({st.session_state.role})")
    if st.sidebar.button("Log Out"):
        log_activity(supabase, st.session_state.username, "Logged out")
        st.session_state.clear()
        st.rerun()

if __name__ == "__main__":
    main()
