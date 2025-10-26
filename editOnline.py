import streamlit as st
import pandas as pd
from datetime import date
from supabase import create_client, Client
from utils import safe_int, safe_float
from log import log_activity

# Initialize Supabase client
try:
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except KeyError as e:
    st.error(f"Missing Supabase secret: {e}. Please check Streamlit Cloud secrets configuration.")
    st.stop()

def update_online_reservation_in_supabase(booking_id, updated_reservation):
    """Update an online reservation in Supabase."""
    try:
        truncated_reservation = updated_reservation.copy()
        string_fields_50 = [
            "property", "booking_id", "guest_name", "guest_phone", "room_no", 
            "room_type", "rate_plans", "booking_source", "segment", "staflexi_status",
            "mode_of_booking", "booking_status", "payment_status", "submitted_by", 
            "modified_by", "advance_mop", "balance_mop"
        ]
        for field in string_fields_50:
            if field in truncated_reservation:
                truncated_reservation[field] = str(truncated_reservation[field])[:50] if truncated_reservation[field] else ""
        if "remarks" in truncated_reservation:
            truncated_reservation["remarks"] = str(truncated_reservation["remarks"])[:500] if truncated_reservation["remarks"] else ""
        response = supabase.table("online_reservations").update(truncated_reservation).eq("booking_id", booking_id).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Error updating online reservation {booking_id}: {e}")
        return False

def delete_online_reservation_in_supabase(booking_id):
    """Delete an online reservation from Supabase."""
    try:
        response = supabase.table("online_reservations").delete().eq("booking_id", booking_id).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Error deleting online reservation {booking_id}: {e}")
        return False

@st.cache_data
def load_online_reservations_from_supabase():
    """Load all online reservations from Supabase without limit."""
    try:
        all_data = []
        offset = 0
        limit = 1000
        while True:
            response = supabase.table("online_reservations").select("*").range(offset, offset + limit - 1).execute()
            data = response.data if response.data else []
            all_data.extend(data)
            if len(data) < limit:
                break
            offset += limit
        if not all_data:
            st.warning("No online reservations found in the database.")
        return all_data
    except Exception as e:
        st.error(f"Error loading online reservations: {e}")
        return []

def load_properties():
    """Load unique properties from reservations table (direct reservations)."""
    try:
        res_direct = supabase.table("reservations").select("property_name").execute().data
        properties = set()
        for r in res_direct:
            prop = r['property_name']
            if prop:
                properties.add(prop)
        return sorted(properties)
    except Exception as e:
        st.error(f"Error loading properties: {e}")
        return []

def get_room_options(property_name):
    """Return room number and room type options based on property."""
    if property_name == "Millionaire":
        room_numbers = ["Day Use 1", "Day Use 2", "Day Use 3", "Day Use 4", "Day Use 5", "No Show"]
    else:
        room_numbers = ["Day Use 1", "Day Use 2", "No Show"]
    
    def get_room_type(room_no):
        return "No Show" if room_no == "No Show" else "Day Use"
    
    room_types = ["Day Use", "No Show", "Others"]
    return room_numbers, room_types, get_room_type

def show_edit_online_reservations(selected_booking_id=None):
    """Display edit online reservations page."""
    st.title("✏️ Edit Online Reservations")
    
    if st.button("🔄 Refresh Reservations"):
        st.cache_data.clear()
        st.session_state.pop('online_reservations', None)
        st.success("Cache cleared! Refreshing reservations...")
        st.rerun()

    if 'online_reservations' not in st.session_state:
        st.session_state.online_reservations = load_online_reservations_from_supabase()
    
    if not st.session_state.online_reservations:
        st.info("No online reservations available to edit.")
        return

    if 'online_edit_mode' not in st.session_state:
        st.session_state.online_edit_mode = False
        st.session_state.online_edit_index = None

    df = pd.DataFrame(st.session_state.online_reservations)
    display_columns = ["property", "booking_id", "guest_name", "check_in", "check_out", "room_no", "room_type", "booking_status", "payment_status"]
    st.dataframe(df[display_columns], use_container_width=True)
    
    st.subheader("Select Reservation to Edit")
    booking_id_options = df["booking_id"].unique()
    selected_booking_id = st.selectbox("Select Booking ID", booking_id_options, index=booking_id_options.tolist().index(selected_booking_id) if selected_booking_id in booking_id_options else 0)
    
    if st.button("✏️ Edit Selected Reservation"):
        edit_index = df[df["booking_id"] == selected_booking_id].index[0]
        st.session_state.online_edit_mode = True
        st.session_state.online_edit_index = edit_index
        st.query_params["booking_id"] = selected_booking_id
    
    if st.session_state.online_edit_mode and st.session_state.online_edit_index is not None:
        edit_index = st.session_state.online_edit_index
        reservation = st.session_state.online_reservations[edit_index]
        
        with st.form(key=f"edit_online_form_{reservation['booking_id']}"):
            col1, col2 = st.columns(2)
            with col1:
                properties = load_properties()
                property_name = st.selectbox("Property", properties, index=properties.index(reservation.get("property", "")) if reservation.get("property") in properties else 0)
            with col2:
                booking_id = st.text_input("Booking ID", value=reservation.get("booking_id", ""), disabled=True)
            
            col1, col2 = st.columns(2)
            with col1:
                guest_name = st.text_input("Guest Name", value=reservation.get("guest_name", ""))
            with col2:
                guest_phone = st.text_input("Guest Phone", value=reservation.get("guest_phone", ""))
            
            col1, col2 = st.columns(2)
            with col1:
                check_in = st.date_input("Check In", value=date.fromisoformat(reservation.get("check_in")) if reservation.get("check_in") else date.today())
            with col2:
                check_out = st.date_input("Check Out", value=date.fromisoformat(reservation.get("check_out")) if reservation.get("check_out") else date.today())
            
            room_numbers, room_types, get_room_type = get_room_options(property_name)
            col1, col2 = st.columns(2)
            with col1:
                room_no = st.selectbox("Room No", room_numbers, index=room_numbers.index(reservation.get("room_no", "")) if reservation.get("room_no") in room_numbers else 0)
            with col2:
                room_type = st.selectbox("Room Type", room_types, index=room_types.index(reservation.get("room_type", "")) if reservation.get("room_type") in room_types else 0)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                no_of_adults = st.number_input("No of Adults", min_value=0, value=safe_int(reservation.get("no_of_adults", 1)))
            with col2:
                no_of_children = st.number_input("No of Children", min_value=0, value=safe_int(reservation.get("no_of_children", 0)))
            with col3:
                no_of_infant = st.number_input("No of Infants", min_value=0, value=safe_int(reservation.get("no_of_infant", 0)))
            
            col1, col2 = st.columns(2)
            with col1:
                rate_plans = st.text_input("Rate Plans", value=reservation.get("rate_plans", ""))
            with col2:
                booking_source = st.text_input("Booking Source", value
