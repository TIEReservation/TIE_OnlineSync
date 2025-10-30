# directreservation.py
import streamlit as st
from datetime import date, timedelta
from supabase import create_client, Client
from typing import List, Dict

# ----------------------------------------------------------------------
# Supabase client (reuse the same secrets as in other modules)
# ----------------------------------------------------------------------
try:
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except Exception as e:
    st.error(f"Supabase init error: {e}")
    st.stop()

# ----------------------------------------------------------------------
# 1. NEW RESERVATION FORM (with instant “Number of Days”)
# ----------------------------------------------------------------------
def show_new_reservation_form() -> None:
    """Streamlit form to create a new direct reservation."""
    st.subheader("Add New Direct Reservation")

    with st.form(key="new_reservation_form", clear_on_submit=True):
        # ---- Layout: 3 columns (dates + days display) ----
        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            check_in = st.date_input(
                "Check-In",
                value=date.today(),
                min_value=date.today(),
                key="new_check_in"
            )
        with col2:
            check_out = st.date_input(
                "Check-Out",
aurants                value=date.today() + timedelta(days=1),
                min_value=date.today() + timedelta(days=1),
                key="new_check_out"
            )
        with col3:
            # ---- Instant days calculation ----
            days = (check_out - check_in).days
            if days <= 0:
                days_display = "Invalid"
                st.markdown("<p style='color:red; font-weight:bold; margin-top:30px;'>Invalid</p>", unsafe_allow_html=True)
            else:
                days_display = f"**{days} night{'s' if days > 1 else ''}**"
                st.markdown(f"<p style='margin-top:30px; text-align:center;'>{days_display}</p>", unsafe_allow_html=True)

        # ---- Rest of the fields ----
        col_a, col_b = st.columns(2)
        with col_a:
            guest_name = st.text_input("Guest Name *", placeholder="Full name")
            mobile_no  = st.text_input("Mobile No *", placeholder="10-digit number")
            property   = st.selectbox(
                "Property *",
                options=[
                    "Le Poshe Beach view", "La Millionaire Resort", "Le Poshe Luxury",
                    "Le Poshe Suite", "La Paradise Residency", "La Paradise Luxury",
                    "La Villa Heritage", "Le Pondy Beach Side", "Le Royce Villa",
                    "La Tamara Luxury", "La Antilia Luxury", "La Tamara Suite",
                    "Le Park Resort", "Villa Shakti", "Eden Beach Resort"
                ]
            )
        with col_b:
            total_pax = st.number_input("Total Pax *", min_value=1, step=1, value=1)
            room_no   = st.text_input("Room No (comma-separated if multiple)", placeholder="101, 102")
            plan      = st.selectbox("Plan *", options=["CP", "MAP", "AP"])

        col_c, col_d = st.columns(2)
        with col_c:
            total_tariff = st.number_input("Total Tariff (INR) *", min_value=0.0, format="%.2f")
            advance      = st.number_input("Advance Paid (INR)", min_value=0.0, format="%.2f")
            advance_mop  = st.selectbox("Advance MOP", options=["Cash", "UPI", "Bank Transfer", "Card Payment"])
        with col_d:
            submitted_by = st.text_input("Submitted By *", placeholder="Your name")
            remarks      = st.text_area("Remarks (optional)")

        submit = st.form_submit_button("Save Reservation")

        if submit:
            # ---- Basic validation ----
            required = [guest_name, mobile_no, property, plan, submitted_by, check_in, check_out, total_tariff]
            if any(not x for x in required) or days <= 0:
                st.error("Please fill all required fields and ensure check-out is after check-in.")
            else:
                # ---- Insert into Supabase ----
                payload = {
                    "property_name": property,
                    "guest_name": guest_name,
                    "mobile_no": mobile_no,
                    "check_in": str(check_in),
                    "check_out": str(check_out),
                    "total_pax": total_pax,
                    "room_no": room_no,
                    "plan": plan,
                    "total_tariff": total_tariff,
                    "advance_amount": advance,
                    "advance_mop": advance_mop,
                    "submitted_by": submitted_by,
                    "remarks": remarks,
                    "payment_status": "Partially Paid" if advance < total_tariff else "Fully Paid",
                    "plan_status": "Confirmed"
                }
                try:
                    supabase.table("reservations").insert(payload).execute()
                    st.success(f"Reservation saved! {days} night(s) booked.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to save: {e}")

# ----------------------------------------------------------------------
# 2. LIST OF RESERVATIONS (minimal placeholder – replace with your real logic)
# ----------------------------------------------------------------------
def show_reservations_list() -> None:
    """Display a simple table of direct reservations (placeholder)."""
    st.subheader("Direct Reservations List")
    try:
        data = supabase.table("reservations").select("*").execute().data
        if data:
            import pandas as pd
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No direct reservations yet.")
    except Exception as e:
        st.error(f"Error loading list: {e}")

# ----------------------------------------------------------------------
# (Optional) Export the functions for `app.py`
# ----------------------------------------------------------------------
__all__ = ["show_new_reservation_form", "show_reservations_list"]
