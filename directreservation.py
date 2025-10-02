import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from supabase import Client
import random
import string

def generate_booking_id():
    """Generate a unique booking ID."""
    date_str = datetime.now().strftime("%Y%m%d")
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"DIR_{date_str}_{random_str}"

def load_reservations_from_supabase():
    """Load reservations from Supabase."""
    try:
        response = st.session_state.supabase.table("reservations").select("*").execute()
        if response.data:
            return pd.DataFrame(response.data)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading reservations: {e}")
        return pd.DataFrame()

def save_reservation_to_supabase(reservation_data):
    """Save a reservation to Supabase."""
    try:
        response = st.session_state.supabase.table("reservations").insert(reservation_data).execute()
        if response.data:
            st.write(f"Debug: Successfully saved reservation {reservation_data['booking_id']}")
            return True
        else:
            st.error(f"Debug: Failed to save reservation {reservation_data['booking_id']}")
            return False
    except Exception as e:
        st.error(f"Error saving reservation: {e}")
        return False

def update_reservation_in_supabase(booking_id, reservation_data):
    """Update a reservation in Supabase."""
    try:
        response = st.session_state.supabase.table("reservations").update(reservation_data).eq("booking_id", booking_id).execute()
        if response.data:
            st.write(f"Debug: Successfully updated reservation {booking_id}")
            return True
        else:
            st.error(f"Debug: Failed to update reservation {booking_id}")
            return False
    except Exception as e:
        st.error(f"Error updating reservation {booking_id}: {e}")
        return False

def delete_reservation_in_supabase(booking_id):
    """Delete a reservation from Supabase."""
    try:
        response = st.session_state.supabase.table("reservations").delete().eq("booking_id", booking_id).execute()
        if response.data:
            st.write(f"Debug: Successfully deleted reservation {booking_id}")
            return True
        else:
            st.error(f"Debug: Failed to delete reservation {booking_id}")
            return False
    except Exception as e:
        st.error(f"Error deleting reservation {booking_id}: {e}")
        return False

def show_new_reservation_form():
    """Display form for new direct reservations."""
    st.title("📝 New Direct Reservation")
    with st.form("new_reservation_form"):
        col1, col2 = st.columns(2)
        with col1:
            property_name = st.selectbox("Property Name", st.session_state.properties)
            guest_name = st.text_input("Guest Name")
            check_in = st.date_input("Check-in Date", min_value=datetime.today())
            check_out = st.date_input("Check-out Date", min_value=check_in + timedelta(days=1))
            room_type = st.selectbox("Room Type", ["Standard", "Deluxe", "Suite"])
        with col2:
            num_guests = st.number_input("Number of Guests", min_value=1, step=1)
            tariff = st.number_input("Tariff per Night", min_value=0.0, step=100.0)
            advance = st.number_input("Advance Paid", min_value=0.0, step=100.0)
            mob = st.selectbox("Mode of Booking", ["Direct", "OTA", "Stay-back"])
            submitted_by = st.text_input("Submitted By")
        
        if st.form_submit_button("💾 Save Reservation"):
            if guest_name and property_name:
                booking_id = generate_booking_id()
                reservation_data = {
                    "booking_id": booking_id,
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
                    "booking_status": "Pending",
                    "created_at": datetime.now().isoformat()
                }
                if save_reservation_to_supabase(reservation_data):
                    st.success(f"Reservation {booking_id} created successfully!")
                    st.session_state.reservations = load_reservations_from_supabase()
                    st.rerun()
                else:
                    st.error("Failed to save reservation.")
            else:
                st.error("Guest Name and Property Name are required.")

def show_reservations():
    """Display all reservations."""
    st.title("📋 View Reservations")
    reservations = st.session_state.reservations
    if not reservations.empty:
        st.dataframe(reservations[["booking_id", "property_name", "guest_name", "check_in", "check_out", "booking_status", "submitted_by"]])
    else:
        st.info("No reservations found.")

def show_edit_reservations():
    """Display form to edit or delete reservations."""
    st.title("✏️ Edit Reservations")
    reservations = st.session_state.reservations
    if not reservations.empty:
        booking_ids = reservations["booking_id"].tolist()
        selected_booking_id = st.selectbox("Select Booking ID", booking_ids)
        reservation = reservations[reservations["booking_id"] == selected_booking_id].iloc[0]
        
        with st.form("edit_reservation_form"):
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
                mob = st.selectbox("Mode of Booking", ["Direct", "OTA", "Stay-back"], index=["Direct", "OTA", "Stay-back"].index(reservation["mob"]))
                booking_status = st.selectbox("Booking Status", ["Pending", "Follow-up", "Confirmed", "Cancelled", "Completed", "No Show"], index=["Pending", "Follow-up", "Confirmed", "Cancelled", "Completed", "No Show"].index(reservation.get("booking_status", "Pending")))
                modified_by = st.text_input("Modified By", value=reservation.get("modified_by", ""))
            
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
                        "booking_status": booking_status,
                        "modified_by": modified_by
                    }
                    if update_reservation_in_supabase(selected_booking_id, reservation_data):
                        st.success(f"Reservation {selected_booking_id} updated successfully!")
                        st.session_state.reservations = load_reservations_from_supabase()
                        st.rerun()
                    else:
                        st.error("Failed to update reservation.")
            with col2:
                if st.session_state.role == "Management":
                    if st.form_submit_button("🗑️ Delete Reservation"):
                        if delete_reservation_in_supabase(selected_booking_id):
                            st.success(f"Reservation {selected_booking_id} deleted successfully!")
                            st.session_state.reservations = load_reservations_from_supabase()
                            st.rerun()
                        else:
                            st.error("Failed to delete reservation.")
    else:
        st.info("No reservations available to edit.")

def show_analytics():
    """Display analytics for reservations."""
    st.title("📊 Analytics")
    reservations = st.session_state.reservations
    if not reservations.empty:
        total_reservations = len(reservations)
        total_revenue = reservations["tariff"].sum()
        avg_tariff = reservations["tariff"].mean()
        st.metric("Total Reservations", total_reservations)
        st.metric("Total Revenue", f"₹{total_revenue:,.2f}")
        st.metric("Average Tariff", f"₹{avg_tariff:,.2f}")
    else:
        st.info("No data available for analytics.")
