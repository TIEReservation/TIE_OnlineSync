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
        if st.session_state.properties:
            all_data = [r for r in all_data if r.get("property", "") in st.session_state.properties]
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
    
    room_types = ["Day Use", "No Show"]
    return room_numbers, room_types

def show_edit_online_reservations(selected_booking_id=None):
    """Display and edit online reservations."""
    st.header("✏️ Edit Online Reservations")
    if not st.session_state.online_reservations:
        st.info("No online reservations available to edit.")
        return
    df = pd.DataFrame(st.session_state.online_reservations)
    if selected_booking_id:
        df = df[df["booking_id"] == selected_booking_id]
    if df.empty:
        st.warning("No matching online reservation found.")
        return
    for edit_index, reservation in df.iterrows():
        with st.expander(f"Booking ID: {reservation['booking_id']}"):
            col1, col2 = st.columns(2)
            with col1:
                property_name = st.selectbox("Property", load_properties(), index=load_properties().index(reservation["property"]) if reservation["property"] in load_properties() else 0, key=f"property_{edit_index}")
                booking_made_on = st.date_input("Booking Made On", value=date.fromisoformat(reservation["booking_made_on"]) if reservation["booking_made_on"] else date.today(), key=f"booking_made_on_{edit_index}")
                guest_name = st.text_input("Guest Name", value=reservation["guest_name"], key=f"guest_name_{edit_index}")
                guest_phone = st.text_input("Guest Phone", value=reservation["guest_phone"], key=f"guest_phone_{edit_index}")
                check_in = st.date_input("Check In", value=date.fromisoformat(reservation["check_in"]) if reservation["check_in"] else date.today(), key=f"check_in_{edit_index}")
                check_out = st.date_input("Check Out", value=date.fromisoformat(reservation["check_out"]) if reservation["check_out"] else date.today() + timedelta(days=1), key=f"check_out_{edit_index}")
                no_of_adults = st.number_input("No. of Adults", min_value=0, value=safe_int(reservation["no_of_adults"]), key=f"no_of_adults_{edit_index}")
                no_of_children = st.number_input("No. of Children", min_value=0, value=safe_int(reservation["no_of_children"]), key=f"no_of_children_{edit_index}")
                no_of_infant = st.number_input("No. of Infants", min_value=0, value=safe_int(reservation["no_of_infant"]), key=f"no_of_infant_{edit_index}")
                total_pax = no_of_adults + no_of_children + no_of_infant
                st.write(f"Total Pax: {total_pax}")
            with col2:
                room_no, room_types = get_room_options(property_name)
                room_no = st.selectbox("Room No", room_no, index=room_no.index(reservation["room_no"]) if reservation["room_no"] in room_no else 0, key=f"room_no_{edit_index}")
                room_type = st.selectbox("Room Type", room_types, index=room_types.index(get_room_type(reservation["room_no"])) if get_room_type(reservation["room_no"]) in room_types else 0, key=f"room_type_{edit_index}")
                rate_plans = st.text_input("Rate Plans", value=reservation["rate_plans"], key=f"rate_plans_{edit_index}")
                booking_source = st.selectbox("Booking Source", ["Direct", "OTA", "Phone"], index=["Direct", "OTA", "Phone"].index(reservation["booking_source"]) if reservation["booking_source"] in ["Direct", "OTA", "Phone"] else 0, key=f"booking_source_{edit_index}")
                segment = st.selectbox("Segment", ["Leisure", "Corporate", "Group"], index=["Leisure", "Corporate", "Group"].index(reservation["segment"]) if reservation["segment"] in ["Leisure", "Corporate", "Group"] else 0, key=f"segment_{edit_index}")
                staflexi_status = st.selectbox("Staflexi Status", ["Confirmed", "Pending", "Cancelled"], index=["Confirmed", "Pending", "Cancelled"].index(reservation["staflexi_status"]) if reservation["staflexi_status"] in ["Confirmed", "Pending", "Cancelled"] else 0, key=f"staflexi_status_{edit_index}")
                booking_confirmed_on = st.date_input("Booking Confirmed On", value=date.fromisoformat(reservation["booking_confirmed_on"]) if reservation["booking_confirmed_on"] else None, key=f"booking_confirmed_on_{edit_index}")
                booking_amount = st.number_input("Booking Amount", min_value=0.0, value=safe_float(reservation["booking_amount"]), key=f"booking_amount_{edit_index}")
                total_payment_made = st.number_input("Total Payment Made", min_value=0.0, value=safe_float(reservation["total_payment_made"]), key=f"total_payment_made_{edit_index}")
                balance_due = booking_amount - total_payment_made
                st.write(f"Balance Due: ₹{balance_due}")
                advance_mop = st.text_input("Advance MOP", value=reservation["advance_mop"], key=f"advance_mop_{edit_index}")
                balance_mop = st.text_input("Balance MOP", value=reservation["balance_mop"], key=f"balance_mop_{edit_index}")
                mode_of_booking = st.selectbox("Mode of Booking", ["Online", "Offline"], index=["Online", "Offline"].index(reservation["mode_of_booking"]) if reservation["mode_of_booking"] in ["Online", "Offline"] else 0, key=f"mode_of_booking_{edit_index}")
                booking_status = st.selectbox("Booking Status", ["Confirmed", "Pending", "Cancelled", "Follow-up", "Completed", "No Show"], index=["Confirmed", "Pending", "Cancelled", "Follow-up", "Completed", "No Show"].index(reservation["booking_status"]) if reservation["booking_status"] in ["Confirmed", "Pending", "Cancelled", "Follow-up", "Completed", "No Show"] else 0, key=f"booking_status_{edit_index}")
                payment_status = st.selectbox("Payment Status", ["Paid", "Pending", "Partial"], index=["Paid", "Pending", "Partial"].index(reservation["payment_status"]) if reservation["payment_status"] in ["Paid", "Pending", "Partial"] else 0, key=f"payment_status_{edit_index}")
                remarks = st.text_area("Remarks", value=reservation["remarks"], key=f"remarks_{edit_index}")
                submitted_by = st.text_input("Submitted By", value=reservation["submitted_by"], key=f"submitted_by_{edit_index}")
                modified_by = st.text_input("Modified By", value=st.session_state.username if st.session_state.username else "Unknown", key=f"modified_by_{edit_index}")
                total_amount_with_services = st.number_input("Total Amount with Services", min_value=0.0, value=safe_float(reservation["total_amount_with_services"]), key=f"total_amount_with_services_{edit_index}")
                ota_gross_amount = st.number_input("OTA Gross Amount", min_value=0.0, value=safe_float(reservation["ota_gross_amount"]), key=f"ota_gross_amount_{edit_index}")
                ota_commission = st.number_input("OTA Commission", min_value=0.0, value=safe_float(reservation["ota_commission"]), key=f"ota_commission_{edit_index}")
                ota_tax = st.number_input("OTA Tax", min_value=0.0, value=safe_float(reservation["ota_tax"]), key=f"ota_tax_{edit_index}")
                ota_net_amount = st.number_input("OTA Net Amount", min_value=0.0, value=safe_float(reservation["ota_net_amount"]), key=f"ota_net_amount_{edit_index}")
                room_revenue = st.number_input("Room Revenue", min_value=0.0, value=safe_float(reservation["room_revenue"]), key=f"room_revenue_{edit_index}")

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("💾 Update Reservation", use_container_width=True) and st.session_state.permissions["edit"]:
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
                elif not st.session_state.permissions["edit"]:
                    st.warning("You do not have permission to edit reservations.")
            with col_btn2:
                if st.session_state.get('role') == "Management" and st.button("🗑️ Delete Reservation", use_container_width=True) and st.session_state.permissions["delete"]:
                    if delete_online_reservation_in_supabase(reservation["booking_id"]):
                        st.session_state.online_reservations.pop(edit_index)
                        st.session_state.online_edit_mode = False
                        st.session_state.online_edit_index = None
                        st.query_params.clear()
                        st.success(f"🗑️ Reservation {reservation['booking_id']} deleted successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to delete reservation")
                elif not st.session_state.permissions["delete"]:
                    st.warning("You do not have permission to delete reservations.")
