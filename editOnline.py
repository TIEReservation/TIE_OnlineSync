import streamlit as st
import pandas as pd
from datetime import date
from supabase import create_client, Client
from utils import safe_int, safe_float

# Initialize Supabase client
try:
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except KeyError as e:
    st.error(f"Missing Supabase secret: {e}. Please check Streamlit Cloud secrets configuration.")
    st.stop()

def update_online_reservation_in_supabase(booking_id, updated_reservation):
    """Update an online reservation in Supabase."""
    try:
        # Truncate string fields to prevent database errors
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
        limit = 1000  # Supabase default max rows per request
        while True:
            response = supabase.table("online_reservations").select("*").range(offset, offset + limit - 1).execute()
            data = response.data if response.data else []
            all_data.extend(data)
            if len(data) < limit:  # If fewer rows than limit, we've reached the end
                break
            offset += limit
        if not all_data:
            st.warning("No online reservations found in the database.")
        return all_data
    except Exception as e:
        st.error(f"Error loading online reservations: {e}")
        return []

def show_edit_online_reservations(selected_booking_id=None):
    """Edit or view online reservations based on booking ID or selection."""
    if 'online_reservations' not in st.session_state:
        st.session_state.online_reservations = load_online_reservations_from_supabase()

    if not st.session_state.online_reservations:
        st.warning("No online reservations available to edit.")
        return

    # Determine the reservation to edit
    edit_index = None
    if selected_booking_id:
        for i, res in enumerate(st.session_state.online_reservations):
            if res.get("booking_id") == selected_booking_id:
                edit_index = i
                break
    elif st.session_state.get('online_edit_mode') and st.session_state.get('online_edit_index') is not None:
        edit_index = st.session_state.online_edit_index

    if edit_index is not None:
        reservation = st.session_state.online_reservations[edit_index]
        st.session_state.online_edit_mode = True
        st.session_state.online_edit_index = edit_index

        with st.form("edit_online_reservation_form"):
            st.subheader(f"Edit Reservation - {reservation['booking_id']}")
            
            # Non-editable fields
            submitted_by = st.session_state.username if 'username' in st.session_state else "Unknown"
            st.write(f"Submitted By: {submitted_by}")
            modified_by = st.session_state.username if 'username' in st.session_state else "Unknown"
            st.write(f"Modified By: {modified_by}")

            # Editable fields
            property = st.text_input("Property", value=reservation.get("property", ""))
            guest_name = st.text_input("Guest Name", value=reservation.get("guest_name", ""))
            guest_phone = st.text_input("Guest Phone", value=reservation.get("guest_phone", ""))
            check_in = st.date_input("Check-in Date", value=date.fromisoformat(reservation.get("check_in", date.today().isoformat())) if reservation.get("check_in") else date.today())
            check_out = st.date_input("Check-out Date", value=date.fromisoformat(reservation.get("check_out", date.today().isoformat())) if reservation.get("check_out") else date.today())
            no_of_adults = st.number_input("No. of Adults", min_value=0, value=safe_int(reservation.get("no_of_adults", 0)))
            no_of_children = st.number_input("No. of Children", min_value=0, value=safe_int(reservation.get("no_of_children", 0)))
            no_of_infant = st.number_input("No. of Infants", min_value=0, value=safe_int(reservation.get("no_of_infant", 0)))
            total_pax = st.number_input("Total Pax", min_value=0, value=safe_int(reservation.get("total_pax", no_of_adults + no_of_children + no_of_infant)))
            room_no = st.text_input("Room No.", value=reservation.get("room_no", ""))
            room_type = st.text_input("Room Type", value=reservation.get("room_type", ""))
            rate_plans = st.text_input("Rate Plans", value=reservation.get("rate_plans", ""))
            booking_source = st.text_input("Booking Source", value=reservation.get("booking_source", ""))
            segment = st.text_input("Segment", value=reservation.get("segment", ""))
            staflexi_status = st.text_input("StaFlexi Status", value=reservation.get("staflexi_status", ""))
            booking_confirmed_on = st.date_input("Booking Confirmed On", value=date.fromisoformat(reservation.get("booking_confirmed_on", date.today().isoformat())) if reservation.get("booking_confirmed_on") else date.today())
            booking_amount = st.number_input("Booking Amount", min_value=0.0, value=safe_float(reservation.get("booking_amount", 0.0)))
            total_payment_made = st.number_input("Total Payment Made", min_value=0.0, value=safe_float(reservation.get("total_payment_made", 0.0)))
            balance_due = st.number_input("Balance Due", min_value=0.0, value=safe_float(reservation.get("balance_due", 0.0)))
            advance_mop = st.text_input("Advance MOP", value=reservation.get("advance_mop", ""))
            balance_mop = st.text_input("Balance MOP", value=reservation.get("balance_mop", ""))
            mode_of_booking = st.text_input("Mode of Booking", value=reservation.get("mode_of_booking", ""))
            booking_status = st.text_input("Booking Status", value=reservation.get("booking_status", ""))
            payment_status = st.text_input("Payment Status", value=reservation.get("payment_status", ""))
            remarks = st.text_area("Remarks", value=reservation.get("remarks", ""))
            total_amount_with_services = st.number_input("Total Amount with Services", min_value=0.0, value=safe_float(reservation.get("total_amount_with_services", 0.0)))
            ota_gross_amount = st.number_input("OTA Gross Amount", min_value=0.0, value=safe_float(reservation.get("ota_gross_amount", 0.0)))
            ota_commission = st.number_input("OTA Commission", min_value=0.0, value=safe_float(reservation.get("ota_commission", 0.0)))
            ota_tax = st.number_input("OTA Tax", min_value=0.0, value=safe_float(reservation.get("ota_tax", 0.0)))
            ota_net_amount = st.number_input("OTA Net Amount", min_value=0.0, value=safe_float(reservation.get("ota_net_amount", 0.0)))
            room_revenue = st.number_input("Room Revenue", min_value=0.0, value=safe_float(reservation.get("room_revenue", 0.0)))

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.form_submit_button("💾 Save Changes", use_container_width=True):
                    updated_reservation = {
                        "property": property,
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
                        "submitted_by": submitted_by,  # Set from session state
                        "modified_by": modified_by,    # Set from session state
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
