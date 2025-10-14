import streamlit as st
import pandas as pd
from datetime import date
from supabase import create_client, Client
from inventory import PROPERTY_INVENTORY

# Initialize Supabase client
try:
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except KeyError as e:
    st.error(f"Missing Supabase secret: {e}. Please check Streamlit Cloud secrets configuration.")
    st.stop()

def load_properties() -> list:
    """Load unique properties from online_reservations table."""
    try:
        response = supabase.table("online_reservations").select("property").execute()
        properties = sorted(set([row["property"] for row in response.data if row["property"]]))
        return properties
    except Exception as e:
        st.error(f"Error loading properties: {e}")
        return []

def safe_int(value, default=0):
    """Safely convert value to int, return default if conversion fails."""
    try:
        return int(value) if value is not None else default
    except (ValueError, TypeError):
        return default

def safe_float(value, default=0.0):
    """Safely convert value to float, return default if conversion fails."""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default

def update_online_reservation_in_supabase(booking_id: str, data: dict) -> bool:
    """Update a reservation in the online_reservations table."""
    try:
        response = supabase.table("online_reservations").update(data).eq("booking_id", booking_id).execute()
        return len(response.data) > 0
    except Exception as e:
        st.error(f"Error updating reservation {booking_id}: {e}")
        return False

def delete_online_reservation_in_supabase(booking_id: str) -> bool:
    """Delete a reservation from the online_reservations table."""
    try:
        response = supabase.table("online_reservations").delete().eq("booking_id", booking_id).execute()
        return True
    except Exception as e:
        st.error(f"Error deleting reservation {booking_id}: {e}")
        return False

@st.cache_data
def load_online_reservations_from_supabase():
    """Load all online reservations from Supabase."""
    try:
        response = supabase.table("online_reservations").select("*").execute()
        return response.data
    except Exception as e:
        st.error(f"Error loading online reservations: {e}")
        return []

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

    # Convert reservations to DataFrame for display
    df = pd.DataFrame(st.session_state.online_reservations)
    columns_to_display = [
        "booking_id", "property", "guest_name", "check_in", "check_out",
        "room_no", "room_type", "booking_status", "payment_status"
    ]
    columns_to_display = [col for col in columns_to_display if col in df.columns]
    st.dataframe(df[columns_to_display], use_container_width=True)

    # Check for query parameter to auto-select a booking
    query_params = st.query_params
    if selected_booking_id or query_params.get("booking_id"):
        booking_id = selected_booking_id or query_params.get("booking_id")
        for idx, reservation in enumerate(st.session_state.online_reservations):
            if reservation.get("booking_id") == booking_id:
                st.session_state.online_edit_mode = True
                st.session_state.online_edit_index = idx
                break

    # Edit form for selected reservation
    if st.session_state.online_edit_mode and st.session_state.online_edit_index is not None:
        edit_index = st.session_state.online_edit_index
        reservation = st.session_state.online_reservations[edit_index]
        st.subheader(f"Edit Reservation: {reservation['booking_id']}")
        
        with st.form(f"edit_online_form_{edit_index}"):
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
                room_options = PROPERTY_INVENTORY.get(property_name, {"all": ["Unknown"]})["all"]
                room_no = st.selectbox("Room No", room_options, index=room_options.index(reservation.get("room_no", "")) if reservation.get("room_no") in room_options else 0)
            with col2:
                room_type = st.text_input("Room Type", value=reservation.get("room_type", ""))

            # Row 5: Number of Adults, Number of Children, Number of Infant
            col1, col2, col3 = st.columns(3)
            with col1:
                no_of_adults = st.number_input("Number of Adults", min_value=0, value=safe_int(reservation.get("no_of_adults", 0)))
            with col2:
                no_of_children = st.number_input("Number of Children", min_value=0, value=safe_int(reservation.get("no_of_children", 0)))
            with col3:
                no_of_infant = st.number_input("Number of Infant", min_value=0, value=safe_int(reservation.get("no_of_infant", 0)))

            # Calculate total pax
            total_pax = no_of_adults + no_of_children + no_of_infant

            # Row 6: Rate Plans, Booking Source, Segment
            col1, col2, col3 = st.columns(3)
            with col1:
                rate_plans = st.text_input("Rate Plans", value=reservation.get("rate_plans", ""))
            with col2:
                booking_source = st.text_input("Booking Source", value=reservation.get("booking_source", ""))
            with col3:
                segment = st.text_input("Segment", value=reservation.get("segment", ""))

            # Row 7: Staflexi Status, Booking Confirmed On, Booking Amount
            col1, col2, col3 = st.columns(3)
            with col1:
                staflexi_status = st.selectbox("Staflexi Status", ["Flexible", "Non-Flexible"], index=["Flexible", "Non-Flexible"].index(reservation.get("staflexi_status", "Flexible")) if reservation.get("staflexi_status") in ["Flexible", "Non-Flexible"] else 0)
            with col2:
                booking_confirmed_on = st.date_input("Booking Confirmed On", value=date.fromisoformat(reservation["booking_confirmed_on"]) if reservation.get("booking_confirmed_on") else None)
            with col3:
                booking_amount = st.number_input("Booking Amount", min_value=0.0, value=safe_float(reservation.get("booking_amount", 0.0)))

            # Row 8: Total Payment Made, Balance Due, Advance MOP, Balance MOP
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                total_payment_made = st.number_input("Total Payment Made", min_value=0.0, value=safe_float(reservation.get("total_payment_made", 0.0)))
            with col2:
                balance_due = st.number_input("Balance Due", min_value=0.0, value=safe_float(reservation.get("balance_due", 0.0)))
            with col3:
                advance_mop = st.text_input("Advance MOP", value=reservation.get("advance_mop", ""))
            with col4:
                balance_mop = st.text_input("Balance MOP", value=reservation.get("balance_mop", ""))

            # Row 9: Mode of Booking, Booking Status, Payment Status
            col1, col2, col3 = st.columns(3)
            with col1:
                mode_of_booking = st.text_input("Mode of Booking", value=reservation.get("mode_of_booking", ""))
            with col2:
                booking_status = st.selectbox("Booking Status", ["Confirmed", "Pending", "Cancelled"], index=["Confirmed", "Pending", "Cancelled"].index(reservation.get("booking_status", "Pending")) if reservation.get("booking_status") in ["Confirmed", "Pending", "Cancelled"] else 0)
            with col3:
                payment_status = st.selectbox("Payment Status", ["Fully Paid", "Partially Paid", "Not Paid"], index=["Fully Paid", "Partially Paid", "Not Paid"].index(reservation.get("payment_status", "Not Paid")) if reservation.get("payment_status") in ["Fully Paid", "Partially Paid", "Not Paid"] else 0)

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
