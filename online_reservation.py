import streamlit as st
import pandas as pd
from datetime import datetime

def update_online_reservation_in_supabase(booking_id, reservation_data):
    """Update an online reservation in Supabase."""
    try:
        response = st.session_state.supabase.table("online_reservations").update(reservation_data).eq("booking_id", booking_id).execute()
        if response.data:
            st.write(f"Debug: Successfully updated online reservation {booking_id}")
            return True
        else:
            st.error(f"Debug: Failed to update online reservation {booking_id}")
            return False
    except Exception as e:
        st.error(f"Error updating online reservation {booking_id}: {e}")
        return False

def delete_online_reservation_in_supabase(booking_id):
    """Delete an online reservation from Supabase."""
    try:
        response = st.session_state.supabase.table("online_reservations").delete().eq("booking_id", booking_id).execute()
        if response.data:
            st.write(f"Debug: Successfully deleted online reservation {booking_id}")
            return True
        else:
            st.error(f"Debug: Failed to delete online reservation {booking_id}")
            return False
    except Exception as e:
        st.error(f"Error deleting online reservation {booking_id}: {e}")
        return False

def show_edit_online_reservations(selected_booking_id=None):
    """Display form to edit or delete online reservations."""
    st.title("✏️ Edit Online Reservations")
    reservations = st.session_state.online_reservations
    if not reservations.empty:
        booking_ids = reservations["booking_id"].tolist()
        if selected_booking_id and selected_booking_id in booking_ids:
            selected_booking = selected_booking_id
        else:
            selected_booking = st.selectbox("Select Booking ID", booking_ids)
        reservation = reservations[reservations["booking_id"] == selected_booking].iloc[0]
        
        with st.form("edit_online_reservation_form"):
            col1, col2 = st.columns(2)
            with col1:
                property_name = st.selectbox("Property Name", st.session_state.properties, index=st.session_state.properties.index(reservation["property_name"]) if reservation["property_name"] in st.session_state.properties else 0)
                guest_name = st.text_input("Guest Name", value=reservation["guest_name"])
                check_in = st.date_input("Check-in Date", value=datetime.fromisoformat(reservation["check_in"]))
                check_out = st.date_input("Check-out Date", value=datetime.fromisoformat(reservation["check_out"]))
                room_type = st.selectbox("Room Type", ["Standard", "Deluxe", "Suite"], index=["Standard", "Deluxe", "Suite"].index(reservation["room_type"]))
            with col2:
                num_guests = st.number_input("Number of Guests", value=int(reservation["num_guests"]), min_value=1, step=1)
                tariff = st.number_input("Tariff per Night", value=float(reservation["tariff"]), min_value=0.0, step=100.0)
                advance = st.number_input("Advance Paid", value=float(reservation["advance"]), min_value=0.0, step=100.0)
                mob = st.selectbox("Mode of Booking", ["OTA", "Stay-back"], index=["OTA", "Stay-back"].index(reservation["mob"]))
                # Set modified_by based on username
                restricted_users = ["reservationteam", "management", "admin", "Shyam", "Nabees", "Praveen"]
                modified_by = st.session_state.username if st.session_state.username and st.session_state.username.lower() not in restricted_users else st.text_input("Modified By", value=reservation.get("modified_by", ""))
                submitted_by = st.text_input("Submitted By", value=reservation.get("submitted_by", ""))
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("💾 Save Reservation"):
                    reservation_data = {
                        "property_name": property_name,
                        "guest_name": guest_name,
                        "check_in": check_in.isoformat(),
                        "check_out": check_out.isoformat(),
                        "room_type": room_type,
                        "num_guests": num_guests,
                        "tariff": tariff,
                        "advance": advance,
                        "mob": mob,
                        "submitted_by": submitted_by,
                        "modified_by": modified_by,
                        "modified_at": datetime.now().isoformat()
                    }
                    if update_online_reservation_in_supabase(selected_booking, reservation_data):
                        st.success(f"Online reservation {selected_booking} updated successfully!")
                        st.session_state.online_reservations = load_online_reservations_from_supabase()
                        st.rerun()
                    else:
                        st.error("Failed to update online reservation.")
            with col2:
                if st.session_state.role == "Management":
                    if st.form_submit_button("🗑️ Delete Reservation"):
                        if delete_online_reservation_in_supabase(selected_booking):
                            st.success(f"Online reservation {selected_booking} deleted successfully!")
                            st.session_state.online_reservations = load_online_reservations_from_supabase()
                            st.rerun()
                        else:
                            st.error("Failed to delete online reservation.")
    else:
        st.info("No online reservations available to edit.")
