import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
from supabase import create_client, Client
from inventory import PROPERTY_INVENTORY  # Add this import

# Initialize Supabase client
try:
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except KeyError as e:
    st.error(f"Missing Supabase secret: {e}. Please check Streamlit Cloud secrets configuration.")
    st.stop()

# ... (Remove load_property_room_map function)

def show_add_reservations():
    """Display add new reservation page."""
    st.title("➕ Add New Reservation")
    
    with st.form("add_reservation_form"):
        # Row 1: Property, Booking Date
        col1, col2 = st.columns(2)
        with col1:
            properties = sorted(load_properties())
            property_name = st.selectbox("Property Name", properties, key="add_property")
        with col2:
            booking_date = st.date_input("Booking Date", value=date.today())

        # Row 2: Guest Name, Mobile No
        col1, col2 = st.columns(2)
        with col1:
            guest_name = st.text_input("Guest Name", key="add_guest_name")
        with col2:
            mobile_no = st.text_input("Mobile Number", key="add_mobile_no")

        # Row 3: Check In, Check Out
        col1, col2 = st.columns(2)
        with col1:
            check_in = st.date_input("Check In", value=date.today(), key="add_check_in")
        with col2:
            check_out = st.date_input("Check Out", value=date.today() + timedelta(days=1), key="add_check_out")

        # Row 4: Room No, Room Type
        col1, col2 = st.columns(2)
        with col1:
            room_options = PROPERTY_INVENTORY.get(property_name, {"all": ["Unknown"]})["all"]
            room_no = st.selectbox("Room No", room_options, key="add_room_no")
        with col2:
            room_type = st.text_input("Room Type", key="add_room_type")

        # ... (Rest of the form: Number of Pax, Plan, etc., remains unchanged)
        # (Assuming fields like no_of_adults, no_of_children, plan, etc., follow as in original)

        if st.form_submit_button("➕ Add Reservation", use_container_width=True):
            # ... (Logic for adding reservation remains unchanged)
            pass

def show_edit_reservations():
    """Display edit reservations page."""
    st.title("✏️ Edit Reservations")
    
    if st.button("🔄 Refresh Reservations"):
        st.cache_data.clear()
        st.session_state.pop('reservations', None)
        st.success("Cache cleared! Refreshing reservations...")
        st.rerun()

    if 'reservations' not in st.session_state:
        st.session_state.reservations = load_reservations_from_supabase()
    
    if not st.session_state.reservations:
        st.info("No reservations available to edit.")
        return

    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False
        st.session_state.edit_index = None

    # ... (Previous code for displaying table, handling query params, etc., remains unchanged)

    if st.session_state.edit_mode and st.session_state.edit_index is not None:
        edit_index = st.session_state.edit_index
        reservation = st.session_state.reservations[edit_index]
        st.subheader(f"Edit Reservation: {reservation['Booking ID']}")
        
        with st.form(f"edit_form_{edit_index}"):
            # Row 1: Property, Booking Date
            col1, col2 = st.columns(2)
            with col1:
                properties = sorted(load_properties())
                property_name = st.selectbox("Property Name", properties, index=properties.index(reservation.get("Property Name", "")) if reservation.get("Property Name") in properties else 0)
            with col2:
                booking_date = st.date_input("Booking Date", value=date.fromisoformat(reservation["Booking Date"]) if reservation.get("Booking Date") else None)

            # Row 2: Guest Name, Mobile No
            col1, col2 = st.columns(2)
            with col1:
                guest_name = st.text_input("Guest Name", value=reservation.get("Guest Name", ""))
            with col2:
                mobile_no = st.text_input("Mobile Number", value=reservation.get("Mobile No", ""))

            # Row 3: Check In, Check Out
            col1, col2 = st.columns(2)
            with col1:
                check_in = st.date_input("Check In", value=date.fromisoformat(reservation["Check In"]) if reservation.get("Check In") else None)
            with col2:
                check_out = st.date_input("Check Out", value=date.fromisoformat(reservation["Check Out"]) if reservation.get("Check Out") else None)

            # Row 4: Room No, Room Type
            col1, col2 = st.columns(2)
            with col1:
                room_options = PROPERTY_INVENTORY.get(property_name, {"all": ["Unknown"]})["all"]
                room_no = st.selectbox("Room No", room_options, index=room_options.index(reservation.get("Room No", "")) if reservation.get("Room No") in room_options else 0)
            with col2:
                room_type = st.text_input("Room Type", value=reservation.get("Room Type", ""))

            # ... (Rest of the form: Number of Pax, Plan, etc., remains unchanged)
            # (Assuming fields like no_of_adults, no_of_children, plan, etc., follow as in original)

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.form_submit_button("💾 Update Reservation", use_container_width=True):
                    # ... (Logic for updating reservation remains unchanged)
                    pass
            with col_btn2:
                if st.session_state.get('role') == "Management":
                    if st.form_submit_button("🗑️ Delete Reservation", use_container_width=True):
                        # ... (Logic for deleting reservation remains unchanged)
                        pass
