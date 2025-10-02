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
    """Load online reservations, filtered by user properties."""
    try:
        query = supabase.table("online_reservations").select("*").order("check_in", desc=True)
        if st.session_state.role != "Management":
            query = query.in_("property", st.session_state.properties)
        response = query.execute()
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
    booking_ids = df["booking_id"].tolist()
    if selected_booking_id and selected_booking_id in booking_ids:
        edit_index = booking_ids.index(selected_booking_id)
    else:
        edit_index = st.selectbox("Select Booking ID", booking_ids, format_func=lambda x: x)
        edit_index = booking_ids.index(edit_index)
    
    reservation = st.session_state.online_reservations[edit_index]
    st.session_state.online_edit_mode = True
    st.session_state.online_edit_index = edit_index

    with st.form("edit_online_reservation_form"):
        col1, col2 = st.columns(2)
        with col1:
            property_name = st.selectbox("Property", st.session_state.properties, index=st.session_state.properties.index(reservation["property"]) if reservation["property"] in st.session_state.properties else 0)
            booking_id = st.text_input("Booking ID", value=reservation["booking_id"], disabled=True)
            booking_made_on = st.date_input("Booking Made On", value=parse_date(reservation.get("booking_made_on")) if reservation.get("booking_made_on") else None, min_value=date(2000, 1, 1))
            guest_name = st.text_input("Guest Name", value=reservation.get("guest_name", ""))
            guest_phone = st.text_input("Guest Phone", value=reservation.get("guest_phone", ""))
            check_in = st.date_input("Check-in Date", value=parse_date(reservation.get("check_in")) if reservation.get("check_in") else None)
            check_out = st.date_input("Check-out Date", value=parse_date(reservation.get("check_out")) if reservation.get("check_out") else None)
            room_no = st.text_input("Room Number", value=reservation.get("room_no", ""))
            room_type = st.text_input("Room Type", value=reservation.get("room_type", ""))
            rate_plans = st.text_input("Rate Plans", value=reservation.get("rate_plans", ""))
        with col2:
            no_of_adults = st.number_input("Number of Adults", value=safe_int(reservation.get("no_of_adults", 0)), min_value=0)
            no_of_children = st.number_input("Number of Children", value=safe_int(reservation.get("no_of_children", 0)), min_value=0)
            no_of_infant = st.number_input("Number of Infants", value=safe_int(reservation.get("no_of_infant", 0)), min_value=0)
            total_pax = no_of_adults + no_of_children + no_of_infant
            st.text(f"Total Pax: {total_pax}")
            booking_source = st.text_input("Booking Source", value=reservation.get("booking_source", ""))
            segment = st.text_input("Segment", value=reservation.get("segment", ""))
            staflexi_status = st.text_input("Staflexi Status", value=reservation.get("staflexi_status", ""))
            booking_confirmed_on = st.date_input("Booking Confirmed On", value=parse_date(reservation.get("booking_confirmed_on")) if reservation.get("booking_confirmed_on") else None, min_value=date(2000, 1, 1))
            booking_amount = st.number_input("Booking Amount", value=safe_float(reservation.get("booking_amount", 0.0)), min_value=0.0)
            total_payment_made = st.number_input("Total Payment Made", value=safe_float(reservation.get("total_payment_made", 0.0)), min_value=0.0)
            balance_due = st.number_input("Balance Due", value=safe_float(reservation.get("balance_due", 0.0)), min_value=0.0)
        col3, col4 = st.columns(2)
        with col3:
            mode_of_booking = st.text_input("Mode of Booking", value=reservation.get("mode_of_booking", ""))
            booking_status = st.selectbox("Booking Status", ["Pending", "Confirmed", "Cancelled", "Completed", "No Show"], index=["Pending", "Confirmed", "Cancelled", "Completed", "No Show"].index(reservation.get("booking_status", "Pending")))
            payment_status = st.selectbox("Payment Status", ["Not Paid", "Partially Paid", "Fully Paid"], index=["Not Paid", "Partially Paid", "Fully Paid"].index(reservation.get("payment_status", "Not Paid")))
            advance_mop = st.selectbox("Advance MOP", ["", "Cash", "Card", "UPI", "Bank Transfer", "Other"], index=["", "Cash", "Card", "UPI", "Bank Transfer", "Other"].index(reservation.get("advance_mop", "")) if reservation.get("advance_mop") else 0)
            custom_advance_mop = st.text_input("Custom Advance MOP (if Other)", value=reservation.get("advance_mop", "") if reservation.get("advance_mop") not in ["", "Cash", "Card", "UPI", "Bank Transfer"] else "")
        with col4:
            balance_mop = st.selectbox("Balance MOP", ["", "Cash", "Card", "UPI", "Bank Transfer", "Other"], index=["", "Cash", "Card", "UPI", "Bank Transfer", "Other"].index(reservation.get("balance_mop", "")) if reservation.get("balance_mop") else 0)
            custom_balance_mop = st.text_input("Custom Balance MOP (if Other)", value=reservation.get("balance_mop", "") if reservation.get("balance_mop") not in ["", "Cash", "Card", "UPI", "Bank Transfer"] else "")
            remarks = st.text_area("Remarks", value=reservation.get("remarks", ""), max_chars=500)
            submitted_by = st.text_input("Submitted By", value=reservation.get("submitted_by", ""))
            modified_by = st.text_input("Modified By", value=reservation.get("modified_by", ""))
        with st.expander("OTA and Revenue Details"):
            total_amount_with_services = st.number_input("Total Amount with Services", value=safe_float(reservation.get("total_amount_with_services", 0.0)), min_value=0.0)
            ota_gross_amount = st.number_input("OTA Gross Amount", value=safe_float(reservation.get("ota_gross_amount", 0.0)), min_value=0.0)
            ota_commission = st.number_input("OTA Commission", value=safe_float(reservation.get("ota_commission", 0.0)), min_value=0.0)
            ota_tax = st.number_input("OTA Tax", value=safe_float(reservation.get("ota_tax", 0.0)), min_value=0.0)
            ota_net_amount = st.number_input("OTA Net Amount", value=safe_float(reservation.get("ota_net_amount", 0.0)), min_value=0.0)
            room_revenue = st.number_input("Room Revenue", value=safe_float(reservation.get("room_revenue", 0.0)), min_value=0.0)
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.form_submit_button("💾 Save Reservation", use_container_width=True):
                updated_reservation = {
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
                    "mode_of_booking": mode_of_booking,
                    "booking_status": booking_status,
                    "payment_status": payment_status,
                    "advance_mop": custom_advance_mop if advance_mop == "Other" else advance_mop,
                    "balance_mop": custom_balance_mop if balance_mop == "Other" else balance_mop,
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
            if st.session_state.role == "Management" or ("Daily Management Status" in st.session_state.screens and "Analytics" in st.session_state.screens):
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
