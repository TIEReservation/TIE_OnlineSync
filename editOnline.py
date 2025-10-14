import streamlit as st
import pandas as pd
from datetime import date
from supabase import create_client, Client
from utils import safe_int, safe_float
from inventory import PROPERTY_INVENTORY  # Add this import

# ... (Previous imports and functions like update_online_reservation_in_supabase, delete_online_reservation_in_supabase, load_online_reservations_from_supabase, load_properties remain unchanged)

def show_edit_online_reservations(selected_booking_id=None):
    """Display edit online reservations page."""
    st.title("✏️ Edit Online Reservations")
    
    # Add refresh button to clear cache and reload data
    if st.button("🔄 Refresh Reservations"):
        st.cache_data.clear()
        st.session_state.pop('online_reservations', None)
        st.success("Cache cleared! Refreshing reservations...")
        st.rerun()

    # Load reservations if not in session state
    if 'online_reservations' not in st.session_state:
        st.session_state.online_reservations = load_online_reservations_from_supabase()
    
    if not st.session_state.online_reservations:
        st.info("No online reservations available to edit.")
        return

    if 'online_edit_mode' not in st.session_state:
        st.session_state.online_edit_mode = False
        st.session_state.online_edit_index = None

    df = pd.DataFrame(st.session_state.online_reservations)
    # ... (Previous code for displaying table, handling query params, etc., remains unchanged)

    # Edit form for selected reservation
    if st.session_state.online_edit_mode and st.session_state.online_edit_index is not None:
        edit_index = st.session_state.online_edit_index
        reservation = st.session_state.online_reservations[edit_index]
        st.subheader(f"Edit Reservation: {reservation['booking_id']}")
        
        # Row 1: Property, Booking Made On
        col1, col2 = st.columns(2)
        with col1:
            properties = load_properties()
            property_name = st.selectbox("Property", properties, index=properties.index(reservation.get("property", "")) if reservation.get("property") in properties else 0)
        with col2:
            booking_made_on = st.date_input("Booking Made On", value=date.fromisoformat(reservation["booking_made_on"]) if reservation.get("booking_made_on") else None)

        # Row 2: Guest Name, Guest Phone
        col1, col2 = st.columns(2)
        with col1:
            guest_name = st.text_input("Guest Name", value=reservation.get("guest_name", ""))
        with col2:
            guest_phone = st.text_input("Guest Phone", value=reservation.get("guest_phone", ""))

        # Row 3: Check In, Check Out
        col1, col2 = st.columns(2)
        with col1:
            check_in = st.date_input("Check In", value=date.fromisoformat(reservation["check_in"]) if reservation.get("check_in") else None)
        with col2:
            check_out = st.date_input("Check Out", value=date.fromisoformat(reservation["check_out"]) if reservation.get("check_out") else None)

        # Row 4: Room No, Room Type
        col1, col2 = st.columns(2)
        with col1:
            # Use dropdown for room number based on selected property
            room_options = PROPERTY_INVENTORY.get(property_name, {"all": ["Unknown"]})["all"]
            room_no = st.selectbox("Room No", room_options, index=room_options.index(reservation.get("room_no", "")) if reservation.get("room_no") in room_options else 0)
        with col2:
            room_type = st.text_input("Room Type", value=reservation.get("room_type", ""))

        # ... (Rest of the form: Rate Plans, Booking Source, Segment, etc., remains unchanged)

        # Row 8: Remarks
        remarks = st.text_area("Remarks", value=reservation.get("remarks", ""))

        # Row 9: Submitted by, Modified by
        col1, col2 = st.columns(2)
        with col1:
            submitted_by = st.text_input("Submitted by", value=reservation.get("submitted_by", ""))
        with col2:
            modified_by = st.text_input("Modified by", value=reservation.get("modified_by", ""))

        # Hidden/Other fields
        total_amount_with_services = safe_float(reservation.get("total_amount_with_services", 0.0))
        ota_gross_amount = safe_float(reservation.get("ota_gross_amount", 0.0))
        ota_commission = safe_float(reservation.get("ota_commission", 0.0))
        ota_tax = safe_float(reservation.get("ota_tax", 0.0))
        ota_net_amount = safe_float(reservation.get("ota_net_amount", 0.0))
        room_revenue = safe_float(reservation.get("room_revenue", 0.0))

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("💾 Update Reservation", use_container_width=True):
                updated_reservation = {
                    "property": property_name,
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
                    "modified_by": modified_by,
                    "total_amount_with_services": total_amount_with_services,
                    "ota_gross_amount": ota_gross_amount,
                    "ota_commission": ota_commission,
                    "ota_tax": ota_tax,
                    "ota_net_amount": ota_net_amount,
                    "room_revenue": room_revenue
                }
                if update_online_reservation_in_supabase(reservation["booking_id"], updated_reservation):
                    st.session_state.online_reservations[edit_index] = {**reservation, **updated_reservation}
                    st.session_state.online_edit_mode = False
                    st.session_state.online_edit_index = None
                    st.query_params.clear()
                    st.success(f"✅ Reservation {reservation['booking_id']} updated successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to update reservation")
        with col_btn2:
            if st.session_state.get('role') == "Management":
                if st.button("🗑️ Delete Reservation", use_container_width=True):
                    if delete_online_reservation_in_supabase(reservation["booking_id"]):
                        st.session_state.online_reservations.pop(edit_index)
                        st.session_state.online_edit_mode = False
                        st.session_state.online_edit_index = None
                        st.query_params.clear()
                        st.success(f"🗑️ Reservation {reservation['booking_id']} deleted successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to delete reservation")
