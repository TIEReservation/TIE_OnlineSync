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
            "modified_by"
        ]
        for field in string_fields_50:
            if field in truncated_reservation:
                truncated_reservation[field] = str(truncated_reservation[field])[:50] if truncated_reservation[field] else ""
        if "remarks" in truncated_reservation:
            truncated_reservation["remarks"] = str(truncated_reservation["remarks"])[:500] if truncated_reservation["remarks"] else ""
        response = supabase.table("online_reservations").update(truncated_reservation).eq("booking_id", booking_id).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Error updating online reservation: {e}")
        return False

def delete_online_reservation_in_supabase(booking_id):
    """Delete an online reservation from Supabase."""
    try:
        response = supabase.table("online_reservations").delete().eq("booking_id", booking_id).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Error deleting online reservation: {e}")
        return False

def load_online_reservations_from_supabase():
    """Load online reservations from Supabase."""
    try:
        response = supabase.table("online_reservations").select("*").order("check_in", desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error loading online reservations: {e}")
        return []

def show_edit_online_reservations(selected_booking_id=None):
    """Display edit online reservations page."""
    st.title("✏️ Edit Online Reservations")
    
    if 'online_reservations' not in st.session_state:
        st.session_state.online_reservations = load_online_reservations_from_supabase()
    
    if not st.session_state.online_reservations:
        st.info("No online reservations available to edit.")
        return

    if 'online_edit_mode' not in st.session_state:
        st.session_state.online_edit_mode = False
        st.session_state.online_edit_index = None

    df = pd.DataFrame(st.session_state.online_reservations)
    display_columns = ["property", "booking_id", "guest_name", "check_in", "check_out", "room_no", "room_type", "booking_status"]
    
    st.subheader("Select Reservation to Edit")
    booking_id_list = df["booking_id"].tolist()
    default_index = booking_id_list.index(selected_booking_id) if selected_booking_id in booking_id_list else 0
    selected_booking_id = st.selectbox("Select Booking ID", booking_id_list, index=default_index)
    
    if selected_booking_id:
        edit_index = df[df["booking_id"] == selected_booking_id].index[0]
        reservation = st.session_state.online_reservations[edit_index]
        st.session_state.online_edit_index = edit_index
        st.session_state.online_edit_mode = True

    if st.session_state.online_edit_mode and st.session_state.online_edit_index is not None:
        edit_index = st.session_state.online_edit_index
        reservation = st.session_state.online_reservations[edit_index]
        
        st.subheader(f"Editing Reservation: {reservation['booking_id']}")
        
        # Row 1: Property Name, Booking ID, Booking Made On
        col1, col2, col3 = st.columns(3)
        with col1:
            property_name = st.text_input("Property Name", value=reservation.get("property", ""), disabled=True)
        with col2:
            booking_id = st.text_input("Booking ID", value=reservation.get("booking_id", ""), disabled=True)
        with col3:
            booking_made_on = st.date_input("Booking Made On", value=date.fromisoformat(reservation.get("booking_made_on")) if reservation.get("booking_made_on") else None)

        # Row 2: Guest Name, Mobile No, Check In, Check Out
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            guest_name = st.text_input("Guest Name", value=reservation.get("guest_name", ""))
        with col2:
            guest_phone = st.text_input("Mobile No", value=reservation.get("guest_phone", ""))
        with col3:
            check_in = st.date_input("Check In", value=date.fromisoformat(reservation.get("check_in")) if reservation.get("check_in") else None)
        with col4:
            check_out = st.date_input("Check Out", value=date.fromisoformat(reservation.get("check_out")) if reservation.get("check_out") else None)

        # Row 3: No of Adults, No of Children, No of Infant, Total Pax
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            no_of_adults = st.number_input("No of Adults", value=safe_int(reservation.get("no_of_adults", 0)), min_value=0)
        with col2:
            no_of_children = st.number_input("No of Children", value=safe_int(reservation.get("no_of_children", 0)), min_value=0)
        with col3:
            no_of_infant = st.number_input("No of Infant", value=safe_int(reservation.get("no_of_infant", 0)), min_value=0)
        with col4:
            total_pax = no_of_adults + no_of_children + no_of_infant
            st.text_input("Total Pax", value=total_pax, disabled=True)

        # Row 4: Room No, Room Type, Breakfast (rate_plans), Booking Source
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            room_no = st.text_input("Room No", value=reservation.get("room_no", ""))
        with col2:
            room_type = st.text_input("Room Type", value=reservation.get("room_type", ""))
        with col3:
            rate_plans = st.text_input("Breakfast", value=reservation.get("rate_plans", ""))
        with col4:
            booking_source = st.text_input("Booking Source", value=reservation.get("booking_source", ""))

        # Row 5: Segment, Staflexi Status, Booking Confirmed on
        col1, col2, col3 = st.columns(3)
        with col1:
            segment = st.text_input("Segment", value=reservation.get("segment", ""))
        with col2:
            staflexi_status = st.text_input("Staflexi Status", value=reservation.get("staflexi_status", ""))
        with col3:
            booking_confirmed_on = st.date_input("Booking Confirmed on", value=date.fromisoformat(reservation.get("booking_confirmed_on")) if reservation.get("booking_confirmed_on") else None)

        # Row 6: Total Tariff (booking_amount), Advance Amount, Balance Due
        col1, col2, col3 = st.columns(3)
        with col1:
            booking_amount = st.number_input("Total Tariff", value=safe_float(reservation.get("booking_amount", 0.0)))
        with col2:
            total_payment_made = st.number_input("Advance Amount", value=safe_float(reservation.get("total_payment_made", 0.0)))
        with col3:
            balance_due = booking_amount - total_payment_made
            st.text_input("Balance Due", value=balance_due, disabled=True)

        # Row 7: MOB (mode_of_booking), Booking Status, Payment Status
        col1, col2, col3 = st.columns(3)
        with col1:
            current_mob = reservation.get("mode_of_booking", "") or reservation.get("booking_source", "")
            mob_options = [booking_source, "Booking-Dir"] if booking_source else ["Booking-Dir"]
            if current_mob and current_mob not in mob_options:
                mob_options.insert(0, current_mob)
            mob_options = list(dict.fromkeys(mob_options))
            try:
                mob_index = mob_options.index(current_mob) if current_mob in mob_options else 0
            except ValueError:
                mob_index = 0
            mode_of_booking = st.selectbox("MOB", mob_options, index=mob_index)
        with col2:
            booking_status_options = ["Pending", "Follow-up", "Confirmed", "Cancelled", "Completed", "No Show"]
            current_status = reservation.get("booking_status", "Pending")
            try:
                status_index = booking_status_options.index(current_status)
            except ValueError:
                status_index = 0
            booking_status = st.selectbox("Booking Status", booking_status_options, index=status_index)
        with col3:
            payment_status = st.selectbox("Payment Status", ["Not Paid", "Fully Paid", "Partially Paid"], index=["Not Paid", "Fully Paid", "Partially Paid"].index(reservation.get("payment_status", "Not Paid")))

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
            if st.session_state.role == "Management":
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
