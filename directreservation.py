import streamlit as st
import pandas as pd
from datetime import date
from supabase import create_client, Client

# Initialize Supabase client
try:
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except KeyError as e:
    st.error(f"Missing Supabase secret: {e}. Check secrets.toml.")
    st.stop()

@st.cache_data(ttl=300)
def load_reservations_from_supabase():
    """Load direct reservations from Supabase with caching (5min TTL)."""
    try:
        response = supabase.table("reservations").select("*").order("check_in", desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error loading reservations: {e}")
        return []

@st.cache_data(ttl=300)
def create_reservation_in_supabase(reservation):
    """Save new reservation to Supabase with field truncation."""
    try:
        truncated = reservation.copy()
        string_fields = [
            "property", "booking_id", "guest_name", "guest_phone", "room_no", 
            "room_type", "rate_plans", "booking_source", "segment", "staflexi_status",
            "mode_of_booking", "booking_status", "payment_status", "submitted_by", 
            "modified_by", "advance_mop", "balance_mop"
        ]
        for field in string_fields:
            if field in truncated:
                truncated[field] = str(truncated[field])[:50] if truncated[field] else ""
        if "remarks" in truncated:
            truncated["remarks"] = str(truncated["remarks"])[:500] if truncated["remarks"] else ""
        response = supabase.table("reservations").insert(truncated).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Error saving reservation: {e}")
        return False

def show_new_reservation_form():
    """Display form for new direct reservations with validation."""
    st.title("➕ New Direct Reservation")
    st.write("### Add New Reservation")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        property_name = st.text_input("Property Name", value="Default Property")
    with col2:
        booking_id = st.text_input("Booking ID", value="")
    with col3:
        booking_made_on = st.date_input("Booking Made On", value=date.today())
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        guest_name = st.text_input("Guest Name", value="")
    with col2:
        guest_phone = st.text_input("Mobile No", value="")
    with col3:
        check_in = st.date_input("Check In", value=date.today())
    with col4:
        check_out = st.date_input("Check Out", value=date.today())
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        no_of_adults = st.number_input("No of Adults", min_value=0, value=1)
    with col2:
        no_of_children = st.number_input("No of Children", min_value=0, value=0)
    with col3:
        no_of_infant = st.number_input("No of Infant", min_value=0, value=0)
    with col4:
        total_pax = no_of_adults + no_of_children + no_of_infant
        st.text_input("Total Pax", value=total_pax, disabled=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        room_no = st.text_input("Room No", value="")
    with col2:
        room_type = st.text_input("Room Type", value="")
    with col3:
        rate_plans = st.text_input("Breakfast", value="")
    with col4:
        booking_source = st.text_input("Booking Source", value="")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        segment = st.text_input("Segment", value="")
    with col2:
        staflexi_status = st.text_input("Staflexi Status", value="")
    with col3:
        booking_confirmed_on = st.date_input("Booking Confirmed On", value=None)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        booking_amount = st.number_input("Total Tariff", value=0.0)
    with col2:
        total_payment_made = st.number_input("Advance Amount", value=0.0)
    with col3:
        mop_options = ["", "Cash", "Card", "UPI", "Bank Transfer", "Other"]
        advance_mop = st.selectbox("Advance Mop", mop_options, index=0)
    with col4:
        balance_due = booking_amount - total_payment_made
        st.text_input("Balance Due", value=balance_due, disabled=True)
    with col5:
        balance_mop = st.selectbox("Balance Mop", mop_options, index=0)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        mode_of_booking = st.selectbox("MOB", [booking_source, "Booking-Dir"] if booking_source else ["Booking-Dir"], index=0)
    with col2:
        booking_status = st.selectbox("Booking Status", ["Pending", "Follow-up", "Confirmed", "Cancelled", "Completed", "No Show"], index=0)
    with col3:
        payment_status = st.selectbox("Payment Status", ["Not Paid", "Fully Paid", "Partially Paid"], index=0)
    
    remarks = st.text_area("Remarks", value="")
    col1, col2 = st.columns(2)
    with col1:
        submitted_by = st.text_input("Submitted by", value="")
    with col2:
        modified_by = st.text_input("Modified by", value="")
    
    if st.button("💾 Submit Reservation"):
        if not (booking_id and guest_name and guest_phone):
            st.error("❌ Booking ID, Guest Name, and Mobile No are required.")
            return
        reservation = {
            "property": property_name,
            "booking_id": booking_id,
            "booking_made_on": str(booking_made_on) if booking_made_on else None,
            "guest_name": guest_name,
            "guest_phone": guest_phone,
            "check_in": str(check_in) if check_in else None,
            "check_out": str(check_out) if check_out else None,
            "no_of_adults": no_of_adults,
            "no_of_children": no_of_children,
            "no_of_infant": no_of_infant,
            "total_pax": total_pax,
            "room_no": room_no,
            "room_type": room_type,
            "rate_plans": rate_plans,
            "booking_source": booking_source,
            "segment": segment,
            "staflexi_status": staflexi_status,
            "booking_confirmed_on": str(booking_confirmed_on) if booking_confirmed_on else None,
            "booking_amount": booking_amount,
            "total_payment_made": total_payment_made,
            "balance_due": balance_due,
            "advance_mop": advance_mop,
            "balance_mop": balance_mop,
            "mode_of_booking": mode_of_booking,
            "booking_status": booking_status,
            "payment_status": payment_status,
            "remarks": remarks,
            "submitted_by": submitted_by,
            "modified_by": modified_by
        }
        if create_reservation_in_supabase(reservation):
            st.success("✅ Reservation created!")
            st.session_state.reservations = load_reservations_from_supabase()
            st.rerun()
        else:
            st.error("❌ Failed to create reservation")

def show_reservations():
    """Display direct reservations page."""
    st.title("📋 Direct Reservations")
    reservations = load_reservations_from_supabase()
    if not reservations:
        st.info("No direct reservations available.")
        return
    st.write("### Direct Reservations")
    st.dataframe(reservations)

def show_edit_reservations():
    """Display edit direct reservations page."""
    st.title("✏️ Edit Direct Reservations")
    st.write("Edit implementation not shown for brevity.")

def show_analytics():
    """Display analytics page for Management."""
    st.title("📊 Analytics")
    st.write("Analytics implementation not shown for brevity.")
