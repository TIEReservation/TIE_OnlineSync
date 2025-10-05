import streamlit as st
import pandas as pd
from datetime import date
from supabase import create_client, Client

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
        string_fields = ["booking_id", "guest_name", "room_no", "booking_status"]
        for field in string_fields:
            if field in truncated:
                truncated[field] = str(truncated[field])[:50] if truncated[field] else ""
        response = supabase.table("reservations").insert(truncated).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Error saving reservation: {e}")
        return False

@st.cache_data(ttl=300)
def update_reservation_in_supabase(booking_id, updated_reservation):
    """Update a reservation in Supabase."""
    try:
        truncated = updated_reservation.copy()
        string_fields = ["booking_id", "guest_name", "room_no", "booking_status"]
        for field in string_fields:
            if field in truncated:
                truncated[field] = str(truncated[field])[:50] if truncated[field] else ""
        response = supabase.table("reservations").update(truncated).eq("booking_id", booking_id).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Error updating reservation: {e}")
        return False

@st.cache_data(ttl=300)
def delete_reservation_in_supabase(booking_id):
    """Delete a reservation from Supabase."""
    try:
        response = supabase.table("reservations").delete().eq("booking_id", booking_id).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Error deleting reservation: {e}")
        return False

def show_new_reservation_form():
    """Display form for new direct reservations with validation."""
    st.title("➕ New Direct Reservation")
    st.write("### Add New Reservation")
    
    col1, col2 = st.columns(2)
    with col1:
        booking_id = st.text_input("Booking ID", value="", key="new_booking_id")
    with col2:
        guest_name = st.text_input("Guest Name", value="", key="new_guest_name")
    
    col1, col2 = st.columns(2)
    with col1:
        check_in = st.date_input("Check In", value=date.today(), key="new_check_in")
    with col2:
        check_out = st.date_input("Check Out", value=date.today(), key="new_check_out")
    
    room_no = st.text_input("Room No", value="", key="new_room_no")
    booking_status = st.selectbox("Booking Status", ["Pending", "Confirmed", "Cancelled"], index=0, key="new_booking_status")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Submit Reservation", use_container_width=True):
            if not (booking_id and guest_name):
                st.error("❌ Booking ID and Guest Name are required.")
                if st.session_state.get("debug_enabled", False):
                    st.write(f"Debug: Validation failed - booking_id: {booking_id}, guest_name: {guest_name}")
                return
            reservation = {
                "booking_id": booking_id,
                "guest_name": guest_name,
                "check_in": str(check_in) if check_in else None,
                "check_out": str(check_out) if check_out else None,
                "room_no": room_no,
                "booking_status": booking_status
            }
            if create_reservation_in_supabase(reservation):
                st.success("✅ Reservation created!")
                st.session_state.reservations = load_reservations_from_supabase()
                st.rerun()
            else:
                st.error("❌ Failed to create reservation")
                if st.session_state.get("debug_enabled", False):
                    st.write(f"Debug: Supabase insert failed for reservation: {reservation}")
    with col2:
        if st.button("🔄 Reset Form", use_container_width=True):
            st.session_state.new_booking_id = ""
            st.session_state.new_guest_name = ""
            st.session_state.new_check_in = date.today()
            st.session_state.new_check_out = date.today()
            st.session_state.new_room_no = ""
            st.session_state.new_booking_status = "Pending"
            st.rerun()

def show_reservations():
    """Display direct reservations page."""
    st.title("📋 Direct Reservations")
    reservations = load_reservations_from_supabase()
    if not reservations:
        st.info("No direct reservations available.")
        return
    st.write("### Direct Reservations")
    df = pd.DataFrame(reservations)
    st.dataframe(df, use_container_width=True)

def show_edit_reservations():
    """Display edit direct reservations page."""
    st.title("✏️ Edit Direct Reservations")
    reservations = load_reservations_from_supabase()
    if not reservations:
        st.info("No direct reservations available to edit.")
        return
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False
        st.session_state.edit_index = None
    df = pd.DataFrame(reservations)
    st.subheader("Select Reservation to Edit")
    booking_id_list = df["booking_id"].tolist()
    selected_booking_id = st.selectbox("Select Booking ID", booking_id_list, key="edit_booking_id")
    if selected_booking_id:
        edit_index = df[df["booking_id"] == selected_booking_id].index[0]
        reservation = reservations[edit_index]
        st.session_state.edit_index = edit_index
        st.session_state.edit_mode = True
    if st.session_state.edit_mode and st.session_state.edit_index is not None:
        edit_index = st.session_state.edit_index
        reservation = reservations[edit_index]
        st.subheader(f"Editing Reservation: {reservation['booking_id']}")
        col1, col2 = st.columns(2)
        with col1:
            booking_id = st.text_input("Booking ID", value=reservation.get("booking_id", ""), disabled=True, key="edit_booking_id_field")
        with col2:
            guest_name = st.text_input("Guest Name", value=reservation.get("guest_name", ""), key="edit_guest_name")
        col1, col2 = st.columns(2)
        with col1:
            check_in = st.date_input("Check In", value=date.fromisoformat(reservation.get("check_in")) if reservation.get("check_in") else None, key="edit_check_in")
        with col2:
            check_out = st.date_input("Check Out", value=date.fromisoformat(reservation.get("check_out")) if reservation.get("check_out") else None, key="edit_check_out")
        room_no = st.text_input("Room No", value=reservation.get("room_no", ""), key="edit_room_no")
        booking_status = st.selectbox("Booking Status", ["Pending", "Confirmed", "Cancelled"], index=["Pending", "Confirmed", "Cancelled"].index(reservation.get("booking_status", "Pending")), key="edit_booking_status")
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("💾 Update Reservation", use_container_width=True):
                updated_reservation = {
                    "booking_id": booking_id,
                    "guest_name": guest_name,
                    "check_in": str(check_in) if check_in else None,
                    "check_out": str(check_out) if check_out else None,
                    "room_no": room_no,
                    "booking_status": booking_status
                }
                if update_reservation_in_supabase(booking_id, updated_reservation):
                    st.session_state.reservations[edit_index] = {**reservation, **updated_reservation}
                    st.session_state.edit_mode = False
                    st.session_state.edit_index = None
                    st.success(f"✅ Reservation {booking_id} updated successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to update reservation")
        with col_btn2:
            if st.session_state.get("role") == "Management":
                if st.button("🗑️ Delete Reservation", use_container_width=True):
                    if delete_reservation_in_supabase(booking_id):
                        st.session_state.reservations.pop(edit_index)
                        st.session_state.edit_mode = False
                        st.session_state.edit_index = None
                        st.success(f"🗑️ Reservation {booking_id} deleted successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to delete reservation")

def show_analytics():
    """Display analytics page for Management."""
    st.title("📊 Analytics")
    reservations = load_reservations_from_supabase()
    if not reservations:
        st.info("No data available for analytics.")
        return
    st.write("### Reservation Analytics")
    df = pd.DataFrame(reservations)
    st.write("#### Booking Status Distribution")
    status_counts = df["booking_status"].value_counts()
    st.bar_chart(status_counts)
