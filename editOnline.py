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
            "room_type", "rate_plans", "segment", "staflexi_status",
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
            # Row 1: Property, Transfer Property Option
            col1, col2 = st.columns(2)
            with col1:
                properties = load_properties()
                original_property = reservation.get("property", "")
                property_name = st.selectbox(
                    "Property",
                    properties,
                    index=properties.index(original_property) if original_property in properties else 0,
                    disabled=True
                )
            with col2:
                transfer_property = st.checkbox("Transfer to Another Property", help="Check to change the property for this reservation.")
                new_property = property_name
                if transfer_property:
                    new_property = st.selectbox(
                        "New Property",
                        properties,
                        index=properties.index(original_property) if original_property in properties else 0,
                        key="new_property",
                        help="Select the new property for the guest."
                    )
            
            # Row 2: Booking ID, Guest Name
            col1, col2 = st.columns(2)
            with col1:
                booking_id = st.text_input("Booking ID", value=reservation.get("booking_id", ""), disabled=True)
            with col2:
                guest_name = st.text_input("Guest Name", value=reservation.get("guest_name", ""))
            
            # Row 3: Guest Phone, Check In
            col1, col2 = st.columns(2)
            with col1:
                guest_phone = st.text_input("Guest Phone", value=reservation.get("guest_phone", ""))
            with col2:
                check_in = st.date_input("Check In", value=date.fromisoformat(reservation.get("check_in")) if reservation.get("check_in") else date.today())
            
            # Row 4: Check Out, Room No
            room_numbers, room_types, get_room_type = get_room_options(new_property)
            col1, col2 = st.columns(2)
            with col1:
                check_out = st.date_input("Check Out", value=date.fromisoformat(reservation.get("check_out")) if reservation.get("check_out") else date.today())
            with col2:
                room_no = st.selectbox(
                    "Room No",
                    room_numbers,
                    index=room_numbers.index(reservation.get("room_no", "")) if reservation.get("room_no", "") in room_numbers else 0
                )
            
            # Row 5: Room Type, No of Adults
            col1, col2 = st.columns(2)
            with col1:
                room_type = st.selectbox(
                    "Room Type",
                    room_types,
                    index=room_types.index(reservation.get("room_type", "")) if reservation.get("room_type", "") in room_types else 0
                )
            with col2:
                no_of_adults = st.number_input("No of Adults", min_value=0, value=safe_int(reservation.get("no_of_adults", 1)))
            
            # Row 6: No of Children, No of Infants
            col1, col2 = st.columns(2)
            with col1:
                no_of_children = st.number_input("No of Children", min_value=0, value=safe_int(reservation.get("no_of_children", 0)))
            with col2:
                no_of_infant = st.number_input("No of Infants", min_value=0, value=safe_int(reservation.get("no_of_infant", 0)))
            
            # Row 7: Rate Plans, Segment
            col1, col2 = st.columns(2)
            with col1:
                rate_plans = st.text_input("Rate Plans", value=reservation.get("rate_plans", ""))
            with col2:
                segment = st.text_input("Segment", value=reservation.get("segment", ""))
            
            # Row 8: Staflexi Status, Mode of Booking
            col1, col2 = st.columns(2)
            with col1:
                staflexi_status = st.text_input("Staflexi Status", value=reservation.get("staflexi_status", ""))
            with col2:
                current_mob = str(reservation.get("mode_of_booking", "") or "")
                mob_options = [current_mob, "Bkg-Direct"] if current_mob else ["", "Bkg-Direct"]
                mode_of_booking = st.selectbox(
                    "Mode of Booking",
                    mob_options,
                    index=0,
                    help="Select 'Bkg-Direct' if the guest canceled their online booking and rebooked directly. This is used for Daily Status statistics."
                )
            
            # Row 9: Booking Confirmed On, Booking Amount
            col1, col2 = st.columns(2)
            with col1:
                booking_confirmed_on = st.date_input("Booking Confirmed On", value=date.fromisoformat(reservation.get("booking_confirmed_on")) if reservation.get("booking_confirmed_on") else None, min_value=None)
            with col2:
                booking_amount = st.number_input("Booking Amount", min_value=0.0, value=safe_float(reservation.get("booking_amount", 0.0)))
            
            # Row 10: Total Payment Made, Balance Due
            col1, col2 = st.columns(2)
            with col1:
                total_payment_made = st.number_input("Total Payment Made", min_value=0.0, value=safe_float(reservation.get("total_payment_made", 0.0)))
            with col2:
                balance_due = st.number_input("Balance Due", min_value=0.0, value=safe_float(reservation.get("balance_due", 0.0)))
            
            # Row 11: Advance MOP, Balance MOP
            col1, col2 = st.columns(2)
            with col1:
                advance_mop = st.text_input("Advance MOP", value=reservation.get("advance_mop", ""))
            with col2:
                balance_mop = st.text_input("Balance MOP", value=reservation.get("balance_mop", ""))
            
            # Row 12: Booking Status, Payment Status
            col1, col2 = st.columns(2)
            with col1:
                booking_status_options = ["Pending", "Confirmed", "Cancelled", "Completed", "No Show"]
                current_status = reservation.get("booking_status", "Pending")
                try:
                    status_index = booking_status_options.index(current_status)
                except ValueError:
                    status_index = 0
                booking_status = st.selectbox("Booking Status", booking_status_options, index=status_index)
            with col2:
                payment_status = st.selectbox("Payment Status", ["Not Paid", "Fully Paid", "Partially Paid"], index=["Not Paid", "Fully Paid", "Partially Paid"].index(reservation.get("payment_status", "Not Paid")))
            
            # Row 13: Remarks
            remarks = st.text_area("Remarks", value=reservation.get("remarks", ""))
            
            # Row 14: Submitted by, Modified by
            col1, col2 = st.columns(2)
            with col1:
                submitted_by = st.text_input("Submitted by", value=reservation.get("submitted_by", ""), disabled=True)
            with col2:
                modified_by = st.text_input("Modified by", value=st.session_state.username, disabled=True)
            
            # Row 15: Hidden/Other fields
            total_amount_with_services = safe_float(reservation.get("total_amount_with_services", 0.0))
            ota_gross_amount = safe_float(reservation.get("ota_gross_amount", 0.0))
            ota_commission = safe_float(reservation.get("ota_commission", 0.0))
            ota_tax = safe_float(reservation.get("ota_tax", 0.0))
            ota_net_amount = safe_float(reservation.get("ota_net_amount", 0.0))
            room_revenue = safe_float(reservation.get("room_revenue", 0.0))
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.form_submit_button("💾 Update Reservation", use_container_width=True):
                    updated_reservation = {
                        "property": new_property,  # Use new_property if transferred, else original
                        "booking_made_on": str(reservation.get("booking_made_on")) if reservation.get("booking_made_on") else None,
                        "guest_name": guest_name,
                        "guest_phone": guest_phone,
                        "check_in": str(check_in) if check_in else None,
                        "check_out": str(check_out) if check_out else None,
                        "no_of_adults": no_of_adults,
                        "no_of_children": no_of_children,
                        "no_of_infant": no_of_infant,
                        "total_pax": no_of_adults + no_of_children + no_of_infant,
                        "room_no": room_no,
                        "room_type": room_type,
                        "rate_plans": rate_plans,
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
                        "submitted_by": reservation.get("submitted_by", ""),  # Retain original
                        "modified_by": st.session_state.username,  # Set to logged-in user
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
                    if st.form_submit_button("🗑️ Delete Reservation", use_container_width=True):
                        if delete_online_reservation_in_supabase(reservation["booking_id"]):
                            st.session_state.online_reservations.pop(edit_index)
                            st.session_state.online_edit_mode = False
                            st.session_state.online_edit_index = None
                            st.query_params.clear()
                            st.success(f"🗑️ Reservation {reservation['booking_id']} deleted successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to delete reservation")
