import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
from supabase import create_client, Client

# Initialize Supabase client
try:
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except KeyError as e:
    st.error(f"Missing Supabase secret: {e}. Please check Streamlit Cloud secrets configuration.")
    st.stop()

def load_property_room_map():
    """
    Loads the property to room type to room numbers mapping based on provided data.
    Keys and values are kept as-is from the user's input, including typos and combined rooms.
    Returns a nested dictionary: {"Property": {"Room Type": ["Room No", ...], ...}, ...}
    """
    return {
        "Le Poshe Beach view": {
            "Double Room": ["101", "102", "202", "203", "204"],
            "Standard Room": ["201"],
            "Deluex Double Room Seaview": ["301", "302", "303", "304"],
            "Day Use" : ["Day Use 1", "Day Use 2"],
            "No Show" : ["No Show"]
        },
        "La Millionaire Resort": {
            "Double Room": ["101", "102", "103", "105"],
            "Deluex Double Room with Balcony": ["205", "304", "305"],
            "Deluex Triple Room with Balcony": ["201", "202", "203", "204", "301", "302", "303"],
            "Deluex Family Room with Balcony": ["206", "207", "208", "306", "307", "308"],
            "Deluex Triple Room": ["402"],
            "Deluex Family Room": ["401"],
            "Day Use" : ["Day Use 1", "Day Use 2", "Day Use 3", "Day Use 5"],
            "No Show" : ["No Show"]
        },
        "Le Poshe Luxury": {
            "2BHA Appartment": ["101&102", "101", "102"],
            "2BHA Appartment with Balcony": ["201&202", "201", "202", "301&302", "301", "302", "401&402", "401", "402"],
            "3BHA Appartment": ["203to205", "203", "204", "205", "303to305", "303", "304", "305", "403to405", "403", "404", "405"],
            "Double Room with Private Terrace": ["501"],
            "Day Use" : ["Day Use 1", "Day Use 2"],
            "No Show" : ["No Show"]
        },
        "Le Poshe Suite": {
            "2BHA Appartment": ["601&602", "601", "602", "603", "604", "703", "704"],
            "2BHA Appartment with Balcony": ["701&702", "701", "702"],
            "Double Room with Terrace": ["801"],
            "Day Use" : ["Day Use 1", "Day Use 2"],
            "No Show" : ["No Show"]
        },
        "La Paradise Residency": {
            "Double Room": ["101", "102", "103", "301", "302", "304"],
            "Family Room": ["201", "203"],
            "Triple Room": ["202", "303"],
            "Day Use" : ["Day Use 1", "Day Use 2"],
            "No Show" : ["No Show"]
        },
        "La Paradise Luxury": {
            "3BHA Appartment": ["101to103", "101", "102", "103", "201to203", "201", "202", "203"],
            "Day Use" : ["Day Use 1", "Day Use 2"],
            "No Show" : ["No Show"]
        },
        "La Villa Heritage": {
            "Double Room": ["101", "102", "103"],
            "4BHA Appartment": ["201to203&301", "201", "202", "203", "301"],
            "Day Use" : ["Day Use 1", "Day Use 2"],
            "No Show" : ["No Show"]
        },
        "Le Pondy Beach Side": {
            "Villa": ["101to104", "101", "102", "103", "104"],
            "Day Use" : ["Day Use 1", "Day Use 2"],
            "No Show" : ["No Show"]
        },
        "Le Royce Villa": {
            "Villa": ["101to102&201to202", "101", "102", "201", "202"],
            "Day Use" : ["Day Use 1", "Day Use 2"],
            "No Show" : ["No Show"]
        },
        "La Tamara Luxury": {
            "3BHA": ["101to103", "101", "102", "103", "104to106", "104", "105", "106", "201to203", "201", "202", "203", "204to206", "204", "205", "206", "301to303", "301", "302", "303", "304to306", "304", "305", "306"],
            "4BHA": ["401to404", "401", "402", "403", "404"],
            "Day Use" : ["Day Use 1", "Day Use 2"],
            "No Show" : ["No Show"]
        },
        "La Antilia Luxury": {
            "Deluex Suite Room": ["101"],
            "Deluex Double Room": ["203", "204", "303", "304"],
            "Family Room": ["201", "202", "301", "302"],
            "Deluex suite Room with Tarrace": ["404"],
            "Day Use" : ["Day Use 1", "Day Use 2"],
            "No Show" : ["No Show"]
        },
        "La Tamara Suite": {
            "Two Bedroom apartment": ["101&102"],
            "Deluxe Apartment": ["103&104"],
            "Deluxe Double Room": ["203", "204", "205"],
            "Deluxe Triple Room": ["201", "202"],
            "Deluxe Family Room": ["206"],
            "Day Use" : ["Day Use 1", "Day Use 2"],
            "No Show" : ["No Show"]
        }
    }

def show_new_reservation_form():
    """Display form to create a new direct reservation."""
    st.header("New Direct Reservation")
    form_key = "new_reservation_form"
    property_room_map = load_property_room_map()
    properties = sorted(property_room_map.keys())
    
    with st.form(key=form_key):
        # Row 1: Property Name, Booking ID
        col1, col2 = st.columns(2)
        with col1:
            property_name = st.selectbox("Property Name", properties, key=f"{form_key}_property")
        with col2:
            booking_id = st.text_input("Booking ID", key=f"{form_key}_booking_id")
        
        # Row 2: Guest Name, Guest Phone
        col1, col2 = st.columns(2)
        with col1:
            guest_name = st.text_input("Guest Name", key=f"{form_key}_guest_name")
        with col2:
            guest_phone = st.text_input("Guest Phone", key=f"{form_key}_guest_phone")
        
        # Row 3: Check In, Check Out
        col1, col2 = st.columns(2)
        with col1:
            check_in = st.date_input("Check In", min_value=date.today(), key=f"{form_key}_check_in")
        with col2:
            check_out = st.date_input("Check Out", min_value=date.today(), key=f"{form_key}_check_out")
        
        # Row 4: Room No, Room Type
        room_types = sorted(property_room_map[property_name].keys())
        col1, col2 = st.columns(2)
        with col1:
            room_type = st.selectbox("Room Type", room_types, key=f"{form_key}_room_type")
        with col2:
            room_numbers = property_room_map[property_name][room_type]
            room_no = st.selectbox("Room No", room_numbers, key=f"{form_key}_room_no")
        
        # Row 5: No of Adults, Children, Infants
        col1, col2, col3 = st.columns(3)
        with col1:
            no_of_adults = st.number_input("No of Adults", min_value=0, value=1, step=1, key=f"{form_key}_adults")
        with col2:
            no_of_children = st.number_input("No of Children", min_value=0, value=0, step=1, key=f"{form_key}_children")
        with col3:
            no_of_infants = st.number_input("No of Infants", min_value=0, value=0, step=1, key=f"{form_key}_infants")
        
        # Row 6: Rate Plans, Booking Source
        col1, col2 = st.columns(2)
        with col1:
            rate_plans = st.text_input("Rate Plans", key=f"{form_key}_rate_plans")
        with col2:
            booking_source = st.text_input("Booking Source", key=f"{form_key}_booking_source")
        
        # Row 7: Total Tariff, Advance Payment
        col1, col2 = st.columns(2)
        with col1:
            total_tariff = st.number_input("Total Tariff", min_value=0.0, step=0.01, key=f"{form_key}_total_tariff")
        with col2:
            advance_payment = st.number_input("Advance Payment", min_value=0.0, step=0.01, key=f"{form_key}_advance_payment")
        
        # Row 8: Booking Status, Payment Status
        col1, col2 = st.columns(2)
        with col1:
            booking_status = st.selectbox("Booking Status", ["Pending", "Confirmed", "Cancelled", "Follow-up", "Completed", "No Show"], key=f"{form_key}_booking_status")
        with col2:
            payment_status = st.selectbox("Payment Status", ["Not Paid", "Fully Paid", "Partially Paid"], key=f"{form_key}_payment_status")
        
        # Row 9: Submitted By, Modified By
        col1, col2 = st.columns(2)
        with col1:
            submitted_by = st.text_input("Submitted By", value=st.session_state.get("username", ""), disabled=True, key=f"{form_key}_submitted_by")
        with col2:
            modified_by = st.text_input("Modified By", value="", disabled=True, key=f"{form_key}_modified_by")
        
        # Row 10: Modified Comments, Remarks
        modified_comments = st.text_area("Modified Comments", key=f"{form_key}_modified_comments")
        remarks = st.text_area("Remarks", key=f"{form_key}_remarks")
        
        if st.form_submit_button("✅ Submit Reservation"):
            reservation = {
                "property_name": property_name,
                "booking_id": booking_id,
                "guest_name": guest_name,
                "guest_phone": guest_phone,
                "check_in": str(check_in),
                "check_out": str(check_out),
                "room_no": room_no,
                "room_type": room_type,
                "no_of_adults": no_of_adults,
                "no_of_children": no_of_children,
                "no_of_infants": no_of_infants,
                "rate_plans": rate_plans,
                "booking_source": booking_source,
                "total_tariff": total_tariff,
                "advance_payment": advance_payment,
                "booking_status": booking_status,
                "payment_status": payment_status,
                "submitted_by": st.session_state.get("username", ""),
                "modified_by": "",
                "modified_comments": modified_comments,
                "remarks": remarks
            }
            # Insert into Supabase
            try:
                response = supabase.table("reservations").insert(reservation).execute()
                if response.data:
                    # Transform to title case for session state
                    reservation_transformed = {
                        "Property Name": reservation["property_name"],
                        "Booking ID": reservation["booking_id"],
                        "Guest Name": reservation["guest_name"],
                        "Guest Phone": reservation["guest_phone"],
                        "Check In": reservation["check_in"],
                        "Check Out": reservation["check_out"],
                        "Room No": reservation["room_no"],
                        "Room Type": reservation["room_type"],
                        "No of Adults": reservation["no_of_adults"],
                        "No of Children": reservation["no_of_children"],
                        "No of Infants": reservation["no_of_infants"],
                        "Rate Plans": reservation["rate_plans"],
                        "Booking Source": reservation["booking_source"],
                        "Total Tariff": reservation["total_tariff"],
                        "Advance Payment": reservation["advance_payment"],
                        "Booking Status": reservation["booking_status"],
                        "Payment Status": reservation["payment_status"],
                        "Submitted By": reservation["submitted_by"],
                        "Modified By": reservation["modified_by"],
                        "Modified Comments": reservation["modified_comments"],
                        "Remarks": reservation["remarks"]
                    }
                    st.session_state.reservations = st.session_state.get('reservations', []) + [reservation_transformed]
                    st.success(f"✅ Reservation {booking_id} created successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to create reservation: No data returned from Supabase")
            except Exception as e:
                st.error(f"Error creating reservation: {e}")

def show_reservations():
    """Display direct reservations page with view and filters."""
    st.title("📋 View Direct Reservations")
    
    # Ensure session state is initialized
    if 'reservations' not in st.session_state:
        st.session_state.reservations = []
    
    # Load reservations from Supabase
    try:
        reservations = load_reservations_from_supabase()
        if reservations:
            st.session_state.reservations = reservations
        else:
            st.warning("No reservations found in Supabase.")
    except Exception as e:
        st.error(f"Error loading reservations from Supabase: {e}")
        st.session_state.reservations = []

    # Refresh button
    if st.button("🔄 Refresh Reservations"):
        try:
            st.session_state.reservations = load_reservations_from_supabase()
            st.success("✅ Reservations refreshed!")
            st.rerun()
        except Exception as e:
            st.error(f"Error refreshing reservations: {e}")

    if not st.session_state.reservations:
        st.info("No direct reservations available.")
        return

    try:
        df = pd.DataFrame(st.session_state.reservations)
        if df.empty:
            st.info("No direct reservations available after processing.")
            return
        
        # Ensure required columns exist
        required_columns = [
            "Property Name", "Booking ID", "Guest Name", "Check In", "Check Out", 
            "Room No", "Room Type", "Booking Status", "Payment Status", "Total Tariff", 
            "Advance Payment"
        ]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            st.warning(f"Missing columns in data: {', '.join(missing_columns)}")
            return

        # Filters
        st.subheader("Filters")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            start_date = st.date_input("Start Date (Check-In)", value=None, key="view_filter_start_date")
        with col2:
            end_date = st.date_input("End Date (Check-In)", value=None, key="view_filter_end_date")
        with col3:
            filter_status = st.selectbox("Filter by Booking Status", ["All", "Pending", "Confirmed", "Cancelled", "Follow-up", "Completed", "No Show"], key="view_filter_status")
        with col4:
            properties = ["All"] + sorted(df["Property Name"].dropna().unique().tolist())
            filter_property = st.selectbox("Filter by Property", properties, key="view_filter_property")

        # Sorting option
        sort_order = st.radio("Sort by Check-In Date", ["Descending (Newest First)", "Ascending (Oldest First)"], index=0, key="view_sort_order")

        filtered_df = df.copy()
        # Apply filters
        try:
            if start_date:
                filtered_df = filtered_df[pd.to_datetime(filtered_df["Check In"]) >= pd.to_datetime(start_date)]
            if end_date:
                filtered_df = filtered_df[pd.to_datetime(filtered_df["Check In"]) <= pd.to_datetime(end_date)]
            if filter_status != "All":
                filtered_df = filtered_df[filtered_df["Booking Status"] == filter_status]
            if filter_property != "All":
                filtered_df = filtered_df[filtered_df["Property Name"] == filter_property]

            # Apply sorting
            if sort_order == "Ascending (Oldest First)":
                filtered_df = filtered_df.sort_values(by="Check In", ascending=True)
            else:
                filtered_df = filtered_df.sort_values(by="Check In", ascending=False)
        except Exception as e:
            st.error(f"Error applying filters or sorting: {e}")
            return

        if filtered_df.empty:
            st.warning("No reservations match the selected filters.")
        else:
            st.dataframe(filtered_df[required_columns], use_container_width=True)
    except Exception as e:
        st.error(f"Error rendering reservations table: {e}")

def show_edit_reservations():
    """Display edit reservations page."""
    st.title("✏️ Edit Reservations")
    
    # Ensure session state is initialized
    if 'reservations' not in st.session_state:
        st.session_state.reservations = []
    
    # Load reservations from Supabase
    try:
        reservations = load_reservations_from_supabase()
        if reservations:
            st.session_state.reservations = reservations
        else:
            st.warning("No reservations found in Supabase.")
    except Exception as e:
        st.error(f"Error loading reservations from Supabase: {e}")
        st.session_state.reservations = []
    
    if not st.session_state.reservations:
        st.info("No reservations available to edit.")
        return
    
    try:
        df = pd.DataFrame(st.session_state.reservations)
        if df.empty:
            st.info("No reservations available after processing.")
            return
        
        # Ensure required columns exist
        display_columns = ["Property Name", "Booking ID", "Guest Name", "Check In", "Check Out", "Room No", "Room Type", "Booking Status", "Payment Status"]
        missing_columns = [col for col in display_columns if col not in df.columns]
        if missing_columns:
            st.warning(f"Missing columns in data: {', '.join(missing_columns)}")
            return

        if 'edit_mode' not in st.session_state:
            st.session_state.edit_mode = False
            st.session_state.edit_index = None
        
        st.dataframe(df[display_columns], use_container_width=True)
        
        if st.button("🔄 Refresh Reservations"):
            try:
                st.session_state.reservations = load_reservations_from_supabase()
                st.success("✅ Reservations refreshed!")
                st.rerun()
            except Exception as e:
                st.error(f"Error refreshing reservations: {e}")
        
        st.subheader("Select Reservation to Edit")
        booking_id = st.selectbox("Select Booking ID", df["Booking ID"].dropna().unique(), key="edit_booking_id")
        if st.button("✏️ Edit Selected Reservation"):
            try:
                edit_index = df[df["Booking ID"] == booking_id].index[0]
                st.session_state.edit_mode = True
                st.session_state.edit_index = edit_index
            except IndexError:
                st.error(f"Reservation with Booking ID {booking_id} not found.")
                st.session_state.edit_mode = False
                st.session_state.edit_index = None
        
        if st.session_state.edit_mode and st.session_state.edit_index is not None:
            try:
                edit_index = st.session_state.edit_index
                reservation = st.session_state.reservations[edit_index]
                form_key = f"edit_form_{reservation['Booking ID']}"
                property_room_map = load_property_room_map()
                properties = sorted(property_room_map.keys())
                
                # Validate Submitted By
                if not reservation.get("Submitted By"):
                    st.warning(f"⚠️ Reservation {reservation['Booking ID']} has no 'Submitted By' value. Please check Supabase data.")
                
                with st.form(key=form_key):
                    # Row 1: Property Name, Booking ID
                    col1, col2 = st.columns(2)
                    with col1:
                        property_name = st.selectbox("Property Name", properties, index=properties.index(reservation.get("Property Name", "")) if reservation.get("Property Name") in properties else 0, key=f"{form_key}_property")
                    with col2:
                        booking_id = st.text_input("Booking ID", value=reservation.get("Booking ID", ""), disabled=True, key=f"{form_key}_booking_id")
                    
                    # Row 2: Guest Name, Guest Phone
                    col1, col2 = st.columns(2)
                    with col1:
                        guest_name = st.text_input("Guest Name", value=reservation.get("Guest Name", ""), key=f"{form_key}_guest_name")
                    with col2:
                        guest_phone = st.text_input("Guest Phone", value=reservation.get("Guest Phone", ""), key=f"{form_key}_guest_phone")
                    
                    # Row 3: Check In, Check Out
                    col1, col2 = st.columns(2)
                    with col1:
                        try:
                            check_in = st.date_input("Check In", value=datetime.strptime(reservation.get("Check In", str(date.today())), "%Y-%m-%d").date(), key=f"{form_key}_check_in")
                        except ValueError:
                            check_in = st.date_input("Check In", value=date.today(), key=f"{form_key}_check_in")
                    with col2:
                        try:
                            check_out = st.date_input("Check Out", value=datetime.strptime(reservation.get("Check Out", str(date.today())), "%Y-%m-%d").date(), key=f"{form_key}_check_out")
                        except ValueError:
                            check_out = st.date_input("Check Out", value=date.today(), key=f"{form_key}_check_out")
                    
                    # Row 4: Room No, Room Type
                    room_types = sorted(property_room_map[property_name].keys())
                    col1, col2 = st.columns(2)
                    with col1:
                        current_room_type = reservation.get("Room Type", room_types[0])
                        room_type_index = room_types.index(current_room_type) if current_room_type in room_types else 0
                        room_type = st.selectbox("Room Type", room_types, index=room_type_index, key=f"{form_key}_room_type")
                    with col2:
                        room_numbers = property_room_map[property_name][room_type]
                        current_room_no = reservation.get("Room No", room_numbers[0])
                        room_no_index = room_numbers.index(current_room_no) if current_room_no in room_numbers else 0
                        room_no = st.selectbox("Room No", room_numbers, index=room_no_index, key=f"{form_key}_room_no")
                    
                    # Row 5: No of Adults, Children, Infants
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        no_of_adults = st.number_input("No of Adults", min_value=0, value=int(reservation.get("No of Adults", 1)), step=1, key=f"{form_key}_adults")
                    with col2:
                        no_of_children = st.number_input("No of Children", min_value=0, value=int(reservation.get("No of Children", 0)), step=1, key=f"{form_key}_children")
                    with col3:
                        no_of_infants = st.number_input("No of Infants", min_value=0, value=int(reservation.get("No of Infants", 0)), step=1, key=f"{form_key}_infants")
                    
                    # Row 6: Rate Plans, Booking Source
                    col1, col2 = st.columns(2)
                    with col1:
                        rate_plans = st.text_input("Rate Plans", value=reservation.get("Rate Plans", ""), key=f"{form_key}_rate_plans")
                    with col2:
                        booking_source = st.text_input("Booking Source", value=reservation.get("Booking Source", ""), key=f"{form_key}_booking_source")
                    
                    # Row 7: Total Tariff, Advance Payment
                    col1, col2 = st.columns(2)
                    with col1:
                        total_tariff = st.number_input("Total Tariff", min_value=0.0, value=float(reservation.get("Total Tariff", 0.0)), step=0.01, key=f"{form_key}_total_tariff")
                    with col2:
                        advance_payment = st.number_input("Advance Payment", min_value=0.0, value=float(reservation.get("Advance Payment", 0.0)), step=0.01, key=f"{form_key}_advance_payment")
                    
                    # Row 8: Booking Status, Payment Status
                    col1, col2 = st.columns(2)
                    with col1:
                        booking_status_options = ["Pending", "Confirmed", "Cancelled", "Follow-up", "Completed", "No Show"]
                        current_booking_status = reservation.get("Booking Status", "Pending")
                        booking_status_index = booking_status_options.index(current_booking_status) if current_booking_status in booking_status_options else 0
                        booking_status = st.selectbox("Booking Status", booking_status_options, index=booking_status_index, key=f"{form_key}_booking_status")
                    with col2:
                        payment_status_options = ["Not Paid", "Fully Paid", "Partially Paid"]
                        current_payment_status = reservation.get("Payment Status", "Not Paid")
                        payment_status_index = payment_status_options.index(current_payment_status) if current_payment_status in payment_status_options else 0
                        payment_status = st.selectbox("Payment Status", payment_status_options, index=payment_status_index, key=f"{form_key}_payment_status")
                    
                    # Row 9: Submitted By, Modified By
                    col1, col2 = st.columns(2)
                    with col1:
                        submitted_by = st.text_input("Submitted By", value=reservation.get("Submitted By", ""), disabled=True, key=f"{form_key}_submitted_by")
                    with col2:
                        modified_by = st.text_input("Modified By", value=st.session_state.get("username", ""), disabled=True, key=f"{form_key}_modified_by")
                    
                    # Row 10: Modified Comments, Remarks
                    modified_comments = st.text_area("Modified Comments", value=reservation.get("Modified Comments", ""), key=f"{form_key}_modified_comments")
                    remarks = st.text_area("Remarks", value=reservation.get("Remarks", ""), key=f"{form_key}_remarks")
                    
                    # Ensure submit buttons are always rendered
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        submit_button = st.form_submit_button("💾 Update Reservation", use_container_width=True)
                    with col_btn2:
                        delete_button = None
                        if st.session_state.get('role') == "Management":
                            delete_button = st.form_submit_button("🗑️ Delete Reservation", use_container_width=True)
                    
                    # Handle form submission
                    if submit_button:
                        updated_reservation = {
                            "property_name": property_name,
                            "booking_id": reservation.get("Booking ID", ""),
                            "guest_name": guest_name,
                            "guest_phone": guest_phone,
                            "check_in": str(check_in),
                            "check_out": str(check_out),
                            "room_no": room_no,
                            "room_type": room_type,
                            "no_of_adults": no_of_adults,
                            "no_of_children": no_of_children,
                            "no_of_infants": no_of_infants,
                            "rate_plans": rate_plans,
                            "booking_source": booking_source,
                            "total_tariff": total_tariff,
                            "advance_payment": advance_payment,
                            "booking_status": booking_status,
                            "payment_status": payment_status,
                            "submitted_by": reservation.get("Submitted By", ""),
                            "modified_by": st.session_state.get("username", ""),
                            "modified_comments": modified_comments,
                            "remarks": remarks
                        }
                        if update_reservation_in_supabase(reservation["Booking ID"], updated_reservation):
                            # Transform to title case for session state
                            updated_reservation_transformed = {
                                "Property Name": updated_reservation["property_name"],
                                "Booking ID": updated_reservation["booking_id"],
                                "Guest Name": updated_reservation["guest_name"],
                                "Guest Phone": updated_reservation["guest_phone"],
                                "Check In": updated_reservation["check_in"],
                                "Check Out": updated_reservation["check_out"],
                                "Room No": updated_reservation["room_no"],
                                "Room Type": updated_reservation["room_type"],
                                "No of Adults": updated_reservation["no_of_adults"],
                                "No of Children": updated_reservation["no_of_children"],
                                "No of Infants": updated_reservation["no_of_infants"],
                                "Rate Plans": updated_reservation["rate_plans"],
                                "Booking Source": updated_reservation["booking_source"],
                                "Total Tariff": updated_reservation["total_tariff"],
                                "Advance Payment": updated_reservation["advance_payment"],
                                "Booking Status": updated_reservation["booking_status"],
                                "Payment Status": updated_reservation["payment_status"],
                                "Submitted By": updated_reservation["submitted_by"],
                                "Modified By": updated_reservation["modified_by"],
                                "Modified Comments": updated_reservation["modified_comments"],
                                "Remarks": updated_reservation["remarks"]
                            }
                            st.session_state.reservations[edit_index] = updated_reservation_transformed
                            st.session_state.edit_mode = False
                            st.session_state.edit_index = None
                            st.success(f"✅ Reservation {reservation['Booking ID']} updated successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to update reservation")
                    
                    if delete_button and st.session_state.get('role') == "Management":
                        if delete_reservation_in_supabase(reservation["Booking ID"]):
                            st.session_state.reservations.pop(edit_index)
                            st.session_state.edit_mode = False
                            st.session_state.edit_index = None
                            st.success(f"🗑️ Reservation {reservation['Booking ID']} deleted successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to delete reservation")
            except Exception as e:
                st.error(f"Error rendering edit form: {e}")
                st.session_state.edit_mode = False
                st.session_state.edit_index = None
    except Exception as e:
        st.error(f"Error rendering edit reservations page: {e}")

def show_analytics():
    """Display analytics dashboard for Management users."""
    if st.session_state.get('role') != "Management":
        st.error("❌ Access Denied: Analytics is available only for Management users.")
        return
    st.header("📊 Analytics Dashboard")
    
    if 'reservations' not in st.session_state:
        st.session_state.reservations = []
    
    try:
        reservations = load_reservations_from_supabase()
        if reservations:
            st.session_state.reservations = reservations
        else:
            st.warning("No reservations found in Supabase.")
    except Exception as e:
        st.error(f"Error loading reservations from Supabase: {e}")
        st.session_state.reservations = []

    if not st.session_state.reservations:
        st.info("No reservations available for analysis.")
        return
    
    try:
        df = pd.DataFrame(st.session_state.reservations)
        if df.empty:
            st.info("No reservations available after processing.")
            return
        
        st.subheader("Filters")
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1:
            start_date = st.date_input("Start Date", value=None, key="analytics_filter_start_date", help="Filter by Check In date range (optional)")
        with col2:
            end_date = st.date_input("End Date", value=None, key="analytics_filter_end_date", help="Filter by Check In date range (optional)")
        with col3:
            filter_status = st.selectbox("Filter by Status", ["All", "Confirmed", "Pending", "Cancelled", "Follow-up", "Completed", "No Show"], key="analytics_filter_status")
        with col4:
            filter_check_in_date = st.date_input("Check-in Date", value=None, key="analytics_filter_check_in_date")
        with col5:
            filter_check_out_date = st.date_input("Check-out Date", value=None, key="analytics_filter_check_out_date")
        with col6:
            filter_property = st.selectbox("Filter by Property", ["All"] + sorted(df["Property Name"].dropna().unique()), key="analytics_filter_property")
        
        filtered_df = display_filtered_analysis(df, start_date, end_date, view_mode=False)
        
        if filter_status != "All":
            filtered_df = filtered_df[filtered_df["Booking Status"] == filter_status]
        if filter_check_in_date:
            filtered_df = filtered_df[filtered_df["Check In"] == str(filter_check_in_date)]
        if filter_check_out_date:
            filtered_df = filtered_df[filtered_df["Check Out"] == str(filter_check_out_date)]
        if filter_property != "All":
            filtered_df = filtered_df[filtered_df["Property Name"] == filter_property]
        
        if filtered_df.empty:
            st.warning("No reservations match the selected filters.")
            return
        
        st.subheader("Visualizations")
        col1, col2 = st.columns(2)
        with col1:
            property_counts = filtered_df["Property Name"].value_counts().reset_index()
            property_counts.columns = ["Property Name", "Reservation Count"]
            fig_pie = px.pie(
                property_counts,
                values="Reservation Count",
                names="Property Name",
                title="Reservation Distribution by Property",
                height=400
            )
            st.plotly_chart(fig_pie, use_container_width=True, key="analytics_pie_chart")
        with col2:
            revenue_by_property = filtered_df.groupby("Property Name")["Total Tariff"].sum().reset_index()
            fig_bar = px.bar(
                revenue_by_property,
                x="Property Name",
                y="Total
