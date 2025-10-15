import streamlit as st
import pandas as pd
from datetime import date
from supabase import create_client, Client
from utils import safe_int, safe_float

# Try to import PROPERTY_INVENTORY, use fallback if not available
try:
    from inventory import PROPERTY_INVENTORY
except ImportError:
    PROPERTY_INVENTORY = {
        "La Millionaire Resort": {"all": ["Day Use 1", "Day Use 2", "Day Use 3", "Day Use 4", "Day Use 5", "No Show"]},
        "default": {"all": ["Day Use 1", "Day Use 2", "No Show"]}
    }

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
        st.info(f"Loaded {len(all_data)} online reservations from Supabase")
        if not all_data:
            st.warning("No online reservations found in the database.")
        return all_data
    except Exception as e:
        st.error(f"Error loading online reservations: {e}")
        return []

def load_properties():
    """Load unique properties from reservations and online_reservations tables."""
    try:
        res_direct = supabase.table("reservations").select("property_name").execute().data
        res_online = supabase.table("online_reservations").select("property").execute().data
        properties = set()
        for r in res_direct:
            prop = r['property_name']
            if prop:
                properties.add(prop)
        for r in res_online:
            prop = r['property']
            if prop:
                properties.add(prop)
        return sorted(properties)
    except Exception as e:
        st.error(f"Error loading properties: {e}")
        return []

def process_and_sync_excel(file):
    """Placeholder for Excel sync function."""
    return 0, 0  # Replace with actual implementation if available

def show_edit_online_reservations(selected_booking_id=None):
    """Display edit online reservations page with upload and view."""
    st.title("✏️ Edit Online Reservations")
    if 'online_reservations' not in st.session_state:
        st.session_state.online_reservations = load_online_reservations_from_supabase()

    # Upload and Sync section
    st.subheader("Upload and Sync Excel File")
    uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx")
    if uploaded_file is not None:
        if st.button("🔄 Sync to Database"):
            with st.spinner("Processing and syncing..."):
                inserted, skipped = process_and_sync_excel(uploaded_file)
                st.success(f"✅ Synced successfully! Inserted: {inserted}, Skipped (duplicates): {skipped}")
                # Reload to reflect changes
                st.session_state.online_reservations = load_online_reservations_from_supabase()

    # View section
    st.subheader("View Online Reservations")
    if not st.session_state.online_reservations:
        st.info("No online reservations available.")
        return

    df = pd.DataFrame(st.session_state.online_reservations)
    # Enhanced filters
    st.subheader("Filters")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        start_date = st.date_input("Start Date (Check-In)", value=None)
    with col2:
        end_date = st.date_input("End Date (Check-In)", value=None)
    with col3:
        filter_status = st.selectbox("Filter by Booking Status", ["All", "Pending", "Confirmed", "Cancelled", "Completed", "No Show"])
    with col4:
        properties = ["All"] + sorted(df["property"].dropna().unique().tolist())
        filter_property = st.selectbox("Filter by Property", properties)

    # Sorting option
    sort_order = st.radio("Sort by Check-In Date", ["Descending (Newest First)", "Ascending (Oldest First)"], index=0)

    filtered_df = df.copy()
    # Apply filters
    if start_date:
        filtered_df = filtered_df[pd.to_datetime(filtered_df["check_in"]) >= pd.to_datetime(start_date)]
    if end_date:
        filtered_df = filtered_df[pd.to_datetime(filtered_df["check_in"]) <= pd.to_datetime(end_date)]
    if filter_status != "All":
        filtered_df = filtered_df[filtered_df["booking_status"] == filter_status]
    if filter_property != "All":
        filtered_df = filtered_df[filtered_df["property"] == filter_property]

    # Apply sorting
    if sort_order == "Ascending (Oldest First)":
        filtered_df = filtered_df.sort_values(by="check_in", ascending=True)
    else:
        filtered_df = filtered_df.sort_values(by="check_in", ascending=False)

    if filtered_df.empty:
        st.warning("No reservations match the selected filters.")
    else:
        # Display selected columns
        display_columns = [
            "property", "booking_id", "guest_name", "check_in", "check_out", "room_no", "room_type",
            "booking_status", "payment_status", "booking_amount", "total_payment_made", "balance_due"
        ]
        st.dataframe(filtered_df[display_columns], use_container_width=True)

    # Edit mode
    if 'online_edit_mode' not in st.session_state:
        st.session_state.online_edit_mode = False
        st.session_state.online_edit_index = None

    if selected_booking_id:
        for idx, res in enumerate(st.session_state.online_reservations):
            if res["booking_id"] == selected_booking_id:
                st.session_state.online_edit_mode = True
                st.session_state.online_edit_index = idx
                break
        if not st.session_state.online_edit_mode:
            st.error(f"Booking ID {selected_booking_id} not found.")
            return

    if st.session_state.online_edit_mode and st.session_state.online_edit_index is not None:
        edit_index = st.session_state.online_edit_index
        reservation = st.session_state.online_reservations[edit_index]
        st.subheader(f"Edit Reservation: {reservation['booking_id']}")

        with st.form("edit_online_form"):
            # Row 1: Property, Booking Made On
            col1, col2 = st.columns(2)
            with col1:
                properties = load_properties()
                property_name = st.selectbox("Property", properties, index=properties.index(reservation["property"]) if reservation["property"] in properties else 0)
            with col2:
                booking_made_on = st.date_input("Booking Made On", value=date.fromisoformat(reservation["booking_made_on"]) if reservation["booking_made_on"] else None)

            # Row 2: Guest Name, Guest Phone
            col1, col2 = st.columns(2)
            with col1:
                guest_name = st.text_input("Guest Name", value=reservation["guest_name"])
            with col2:
                guest_phone = st.text_input("Guest Phone", value=reservation["guest_phone"])

            # Row 3: Check In, Check Out
            col1, col2 = st.columns(2)
            with col1:
                check_in = st.date_input("Check In", value=date.fromisoformat(reservation["check_in"]) if reservation["check_in"] else None)
            with col2:
                check_out = st.date_input("Check Out", value=date.fromisoformat(reservation["check_out"]) if reservation["check_out"] else None)

            # Row 4: No of Adults, No of Children, No of Infant
            col1, col2, col3 = st.columns(3)
            with col1:
                no_of_adults = st.number_input("No of Adults", min_value=0, value=safe_int(reservation["no_of_adults"]))
            with col2:
                no_of_children = st.number_input("No of Children", min_value=0, value=safe_int(reservation["no_of_children"]))
            with col3:
                no_of_infant = st.number_input("No of Infant", min_value=0, value=safe_int(reservation["no_of_infant"]))

            total_pax = no_of_adults + no_of_children + no_of_infant

            # Row 5: Room No, Room Type
            col1, col2 = st.columns(2)
            with col1:
                # Define room options based on property
                if property_name == "La Millionaire Resort":
                    room_options = ["Day Use 1", "Day Use 2", "Day Use 3", "Day Use 4", "Day Use 5", "No Show"]
                else:
                    room_options = ["Day Use 1", "Day Use 2", "No Show"]
                # Use PROPERTY_INVENTORY if available and contains valid options
                inventory_options = PROPERTY_INVENTORY.get(property_name, {"all": room_options})["all"]
                if set(inventory_options).issuperset(room_options):
                    room_options = inventory_options
                # Default to fetched room_no if valid, else first option (Day Use 1)
                default_room_no = reservation["room_no"] if reservation["room_no"] and reservation["room_no"] in room_options else room_options[0]
                room_no = st.selectbox("Room No", room_options, index=room_options.index(default_room_no), key="room_no_select")
            with col2:
                room_type_options = ["Day Use", "No Show"]
                # Default to fetched room_type if valid, else Day Use
                default_room_type = (
                    reservation["room_type"] if reservation["room_type"] and reservation["room_type"] in room_type_options
                    else "Day Use"
                )
                room_type = st.selectbox("Room Type", room_type_options, index=room_type_options.index(default_room_type), key="room_type_select")

            # Row 6: Rate Plans, Booking Source, Segment
            col1, col2, col3 = st.columns(3)
            with col1:
                rate_plans = st.text_input("Rate Plans", value=reservation["rate_plans"])
            with col2:
                booking_source = st.text_input("Booking Source", value=reservation["booking_source"])
            with col3:
                segment = st.text_input("Segment", value=reservation["segment"])

            # Row 7: Staflexi Status, Booking Confirmed On, Booking Amount
            col1, col2, col3 = st.columns(3)
            with col1:
                staflexi_status = st.text_input("Staflexi Status", value=reservation["staflexi_status"])
            with col2:
                booking_confirmed_on = st.date_input("Booking Confirmed On", value=date.fromisoformat(reservation["booking_confirmed_on"]) if reservation["booking_confirmed_on"] else None)
            with col3:
                booking_amount = st.number_input("Booking Amount", min_value=0.0, value=safe_float(reservation["booking_amount"]))

            # Row 8: Total Payment Made, Balance Due, Advance MOP, Balance MOP
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                total_payment_made = st.number_input("Total Payment Made", min_value=0.0, value=safe_float(reservation["total_payment_made"]))
            with col2:
                balance_due = st.number_input("Balance Due", min_value=0.0, value=safe_float(reservation["balance_due"]))
            with col3:
                advance_mop = st.text_input("Advance MOP", value=reservation["advance_mop"])
            with col4:
                balance_mop = st.text_input("Balance MOP", value=reservation["balance_mop"])

            # Row 9: Mode of Booking, Booking Status, Payment Status
            col1, col2, col3 = st.columns(3)
            with col1:
                mode_of_booking = st.text_input("Mode of Booking", value=reservation["mode_of_booking"])
            with col2:
                booking_status = st.selectbox("Booking Status", ["Pending", "Confirmed", "Cancelled", "Completed", "No Show"], index=["Pending", "Confirmed", "Cancelled", "Completed", "No Show"].index(reservation["booking_status"]) if reservation["booking_status"] in ["Pending", "Confirmed", "Cancelled", "Completed", "No Show"] else 0)
            with col3:
                payment_status = st.selectbox("Payment Status", ["Fully Paid", "Partially Paid", "Not Paid"], index=["Fully Paid", "Partially Paid", "Not Paid"].index(reservation["payment_status"]) if reservation["payment_status"] in ["Fully Paid", "Partially Paid", "Not Paid"] else 0)

            # Row 10: Remarks
            remarks = st.text_area("Remarks", value=reservation["remarks"])

            # Row 11: Submitted by, Modified by
            col1, col2 = st.columns(2)
            with col1:
                submitted_by = st.text_input("Submitted by", value=reservation["submitted_by"])
            with col2:
                modified_by = st.text_input("Modified by", value=reservation["modified_by"])

            # Hidden/Other fields
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

            if st.form_submit_button("Cancel Edit"):
                st.session_state.online_edit_mode = False
                st.session_state.online_edit_index = None
                st.rerun()

    if not st.session_state.online_edit_mode:
        col1, col2 = st.columns([3, 1])
        with col2:
            selected_id = st.text_input("Enter Booking ID to Edit")
            if st.button("Edit"):
                for idx, res in enumerate(st.session_state.online_reservations):
                    if res["booking_id"] == selected_id:
                        st.session_state.online_edit_mode = True
                        st.session_state.online_edit_index = idx
                        st.rerun()
                st.error("Booking ID not found")
