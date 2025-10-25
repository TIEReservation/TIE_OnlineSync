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
    """Return room number and room type options based on property, including 'Others'."""
    # Modified: Added "Others" to room_types
    room_types = ["Day Use", "No Show", "Others"]
    
    # Room numbers based on property
    if property_name == "Millionaire":
        room_numbers = ["Day Use 1", "Day Use 2", "Day Use 3", "Day Use 4", "Day Use 5", "No Show"]
    else:
        room_numbers = ["Day Use 1", "Day Use 2", "No Show"]
    
    def get_room_type(room_no):
        """Map room number to room type, default to 'Others' for non-standard rooms."""
        if room_no == "No Show":
            return "No Show"
        elif room_no in room_numbers and room_no.startswith("Day Use"):
            return "Day Use"
        else:
            return "Others"
    
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
    display_columns = ["property", "booking_id", "guest_name", "check_in", "check_out", "room_no", "room_type", "booking_status"]
    
    st.subheader("Select Reservation to Edit")
    booking_id_list = df["booking_id"].tolist()
    default_index = booking_id_list.index(selected_booking_id) if selected_booking_id in booking_id_list else 0
    selected_booking_id = st.selectbox("Select Booking ID", booking_id_list, index=default_index, key="booking_id_select")
    
    edit_index = booking_id_list.index(selected_booking_id) if selected_booking_id in booking_id_list else None
    if edit_index is None:
        st.error("Selected reservation not found.")
        return
    
    reservation = st.session_state.online_reservations[edit_index]
    form_key = f"edit_online_form_{reservation['booking_id']}"
    
    try:
        with st.form(key=form_key):
            properties = load_properties()
            property_name = st.selectbox("Property", properties, index=properties.index(reservation.get("property", "")) if reservation.get("property") in properties else 0)
            
            room_numbers, room_types, get_room_type = get_room_options(property_name)
            current_room_no = reservation.get("room_no", "")
            current_room_type = get_room_type(current_room_no)
            
            col1, col2 = st.columns(2)
            with col1:
                # Modified: Updated room type dropdown to include "Others"
                room_type_index = room_types.index(current_room_type) if current_room_type in room_types else 0
                room_type = st.selectbox("Room Type", room_types, index=room_type_index)
            with col2:
                # Modified: Show text input for room_no if "Others" is selected, else show dropdown
                if room_type == "Others":
                    room_no = st.text_input("Room No (Custom)", value=current_room_no)
                else:
                    room_no_index = room_numbers.index(current_room_no) if current_room_no in room_numbers else 0
                    room_no = st.selectbox("Room No", room_numbers, index=room_no_index)
            
            # Row 2: Guest details
            col1, col2 = st.columns(2)
            with col1:
                guest_name = st.text_input("Guest Name", value=reservation.get("guest_name", ""))
            with col2:
                guest_phone = st.text_input("Guest Phone", value=reservation.get("guest_phone", ""))
            
            # Row 3: Check-in, Check-out
            col1, col2 = st.columns(2)
            with col1:
                check_in = st.date_input("Check In", value=date.fromisoformat(reservation["check_in"]) if reservation.get("check_in") else None)
            with col2:
                check_out = st.date_input("Check Out", value=date.fromisoformat(reservation["check_out"]) if reservation.get("check_out") else None)
            
            # Row 4: Pax details
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                no_of_adults = st.number_input("No. of Adults", min_value=0, value=safe_int(reservation.get("no_of_adults", 0)))
            with col2:
                no_of_children = st.number_input("No. of Children", min_value=0, value=safe_int(reservation.get("no_of_children", 0)))
            with col3:
                no_of_infant = st.number_input("No. of Infants", min_value=0, value=safe_int(reservation.get("no_of_infant", 0)))
            with col4:
                total_pax = no_of_adults + no_of_children + no_of_infant
                st.number_input("Total Pax", value=total_pax, disabled=True)
            
            # Row 5: Financial details
            col1, col2, col3 = st.columns(3)
            with col1:
                booking_amount = st.number_input("Booking Amount", min_value=0.0, value=safe_float(reservation.get("booking_amount", 0.0)))
            with col2:
                total_payment_made = st.number_input("Total Payment Made", min_value=0.0, value=safe_float(reservation.get("total_payment_made", 0.0)))
            with col3:
                balance_due = st.number_input("Balance Due", value=safe_float(reservation.get("balance_due", booking_amount - total_payment_made)))
            
            # Row 6: Rate plans, Booking source, Segment
            col1, col2, col3 = st.columns(3)
            with col1:
                rate_plans = st.text_input("Rate Plans", value=reservation.get("rate_plans", ""))
            with col2:
                booking_source = st.text_input("Booking Source", value=reservation.get("booking_source", ""))
            with col3:
                segment = st.text_input("Segment", value=reservation.get("segment", ""))
            
            # Row 7: Advance MOP, Balance MOP, Staflexi status
            col1, col2, col3 = st.columns(3)
            with col1:
                advance_mop = st.text_input("Advance MOP", value=reservation.get("advance_mop", ""))
            with col2:
                balance_mop = st.text_input("Balance MOP", value=reservation.get("balance_mop", ""))
            with col3:
                staflexi_status = st.text_input("Staflexi Status", value=reservation.get("staflexi_status", ""))
            
            # Row 8: Booking made on, Booking confirmed on
            col1, col2 = st.columns(2)
            with col1:
                booking_made_on = st.date_input("Booking Made On", value=date.fromisoformat(reservation["booking_made_on"]) if reservation.get("booking_made_on") else None)
            with col2:
                booking_confirmed_on = st.date_input("Booking Confirmed On", value=date.fromisoformat(reservation["booking_confirmed_on"]) if reservation.get("booking_confirmed_on") else None)
            
            # Row 9: Mode of Booking, Booking Status, Payment Status
            col1, col2, col3 = st.columns(3)
            with col1:
                mob_options = ["Direct", "OTA", "Corporate", "Travel Agent"]
                current_mob = reservation.get("mode_of_booking", "")
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
            
            # Row 10: Remarks
            remarks = st.text_area("Remarks", value=reservation.get("remarks", ""))
            
            # Row 11: Submitted by, Modified by
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
    except Exception as e:
        st.error(f"Error rendering edit form: {e}")
