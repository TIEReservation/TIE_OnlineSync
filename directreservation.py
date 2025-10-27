import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
from supabase import create_client, Client

# Booking source dropdown options
BOOKING_SOURCES = [
    "Booking", "Direct", "Bkg-Direct", "Agoda", "Go-MMT", "Walk-In",
    "TIE Group", "Stayflexi", "Airbnb", "Social Media", "Expedia",
    "Cleartrip", "Website"
]

# MOP (Mode of Payment) options - same as online reservations
MOP_OPTIONS = [
    "", "UPI", "Cash", "Go-MMT", "Agoda", "Not Paid", "Bank Transfer", 
    "Card Payment", "Expedia", "Cleartrip", "Website", "AIRBNB"
]

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
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        },
        "La Millionaire Resort": {
            "Double Room": ["101", "102", "103", "105"],
            "Deluex Double Room with Balcony": ["205", "304", "305"],
            "Deluex Triple Room with Balcony": ["201", "202", "203", "204", "301", "302", "303"],
            "Deluex Family Room with Balcony": ["206", "207", "208", "306", "307", "308"],
            "Deluex Triple Room": ["402"],
            "Deluex Family Room": ["401"],
            "Day Use": ["Day Use 1", "Day Use 2", "Day Use 3", "Day Use 5"],
            "No Show": ["No Show"],
            "Others": []
        },
        "Le Poshe Luxury": {
            "2BHA Appartment": ["101&102", "101", "102"],
            "2BHA Appartment with Balcony": ["201&202", "201", "202", "301&302", "301", "302", "401&402", "401", "402"],
            "3BHA Appartment": ["203to205", "203", "204", "205", "303to305", "303", "304", "305", "403to405", "403", "404", "405"],
            "Double Room with Private Terrace": ["501"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        },
        "Le Poshe Suite": {
            "2BHA Appartment": ["601&602", "601", "602", "603", "604", "703", "704"],
            "2BHA Appartment with Balcony": ["701&702", "701", "702"],
            "Double Room with Terrace": ["801"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        },
        "La Paradise Residency": {
            "Double Room": ["101", "102", "103", "301", "302", "304"],
            "Family Room": ["201", "203"],
            "Triple Room": ["202", "303"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        },
        "La Paradise Luxury": {
            "3BHA Appartment": ["101to103", "101", "102", "103", "201to203", "201", "202", "203"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        },
        "La Villa Heritage": {
            "Double Room": ["101", "102", "103"],
            "4BHA Appartment": ["201to203&301", "201", "202", "203", "301"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        },
        "Le Pondy Beach Side": {
            "Villa": ["101to104", "101", "102", "103", "104"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        },
        "Le Royce Villa": {
            "Villa": ["101to102&201to202", "101", "102", "201", "202"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        },
        "La Tamara Luxury": {
            "3BHA": ["101to103", "101", "102", "103", "104to106", "104", "105", "106", "201to203", "201", "202", "203", "204to206", "204", "205", "206", "301to303", "301", "302", "303", "304to306", "304", "305", "306"],
            "4BHA": ["401to404", "401", "402", "403", "404"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        },
        "La Antilia Luxury": {
            "Deluex Suite Room": ["101"],
            "Deluex Double Room": ["203", "204", "303", "304"],
            "Family Room": ["201", "202", "301", "302"],
            "Deluex suite Room with Tarrace": ["404"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        },
        "La Tamara Suite": {
            "Two Bedroom apartment": ["101&102"],
            "Deluxe Apartment": ["103&104"],
            "Deluxe Double Room": ["203", "204", "205"],
            "Deluxe Triple Room": ["201", "202"],
            "Deluxe Family Room": ["206"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        },
        "Le Park Resort": {
            "Villa with Swimming Pool View": ["555&666", "555", "666"],
            "Villa with Garden View": ["111&222", "111", "222"],
            "Family Retreate Villa": ["333&444", "333", "444"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        },
        "Villa Shakti": {
            "2BHA Studio Room": ["101&102"],
            "2BHA with Balcony": ["202&203", "302&303"],
            "Family Suite": ["201"],
            "Family Room": ["301"],
            "Terrace Room": ["401"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        },
        "Eden Beach Resort": {
            "Double Room": ["101", "102"],
            "Deluex Room": ["103", "202"],
            "Triple Room": ["201"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        }
    }

def show_new_reservation_form():
    """Display form to create a new direct reservation."""
    st.header("New Direct Reservation")
    form_key = "new_reservation_form"
    property_room_map = load_property_room_map()
    properties = sorted(property_room_map.keys())
    
    # Property selection OUTSIDE form for dynamic updates
    property_name = st.selectbox("Property Name", properties, key="property_select_outside_form")
    
    # Get room types for selected property
    room_types = list(property_room_map[property_name].keys())
    
    with st.form(key=form_key):
             
        # Row 1: Guest Name, Guest Phone
        col1, col2 = st.columns(2)
        with col1:
            guest_name = st.text_input("Guest Name", key=f"{form_key}_guest_name")
        with col2:
            guest_phone = st.text_input("Guest Phone", key=f"{form_key}_guest_phone")
        
        # Row 2: Check In, Check Out
        col1, col2 = st.columns(2)
        with col1:
            check_in = st.date_input("Check In", min_value=date.today(), key=f"{form_key}_check_in")
        with col2:
            check_out = st.date_input("Check Out", min_value=date.today(), key=f"{form_key}_check_out")
        
        # Row 3: Room Type, Room No (WITH EDITABLE ROOM NUMBER)
        col1, col2 = st.columns(2)
        with col2:
            room_type = st.selectbox("Room Type", room_types, key=f"{form_key}_room_type", help="Select the room type. Choose 'Others' to manually enter a custom room number.")
        
        with col1:
            if room_type == "Others":
                # For "Others", show text input
                room_no = st.text_input(
                    "Room No",
                    value="",
                    placeholder="Enter custom room number",
                    key=f"{form_key}_room_no",
                    help="Enter a custom room number for 'Others' room type."
                )
                if not room_no.strip():
                    st.warning("⚠️ Please enter a valid Room No for 'Others' room type.")
            else:
                # For predefined types, show editable text input with suggestions
                room_numbers = property_room_map[property_name][room_type]
                room_no = st.text_input(
                    "Room No",
                    value="",
                    placeholder="Enter or select room number",
                    key=f"{form_key}_room_no",
                    help="Enter or edit the room number. You can type any custom value or use suggestions below."
                )
                
                # Show helpful suggestions based on property
                suggestion_list = [r for r in room_numbers if r.strip()]
                if suggestion_list:
                    st.caption(f"💡 **Quick suggestions:** {', '.join(suggestion_list)}")
        
        # Row 4: No of Adults, Children, Infants
        col1, col2, col3 = st.columns(3)
        with col1:
            no_of_adults = st.number_input("No of Adults", min_value=0, value=1, step=1, key=f"{form_key}_adults")
        with col2:
            no_of_children = st.number_input("No of Children", min_value=0, value=0, step=1, key=f"{form_key}_children")
        with col3:
            no_of_infants = st.number_input("No of Infants", min_value=0, value=0, step=1, key=f"{form_key}_infants")
        
        # Row 5: Rate Plans, Booking Source
        col1, col2 = st.columns(2)
        with col1:
            rate_plans = st.selectbox("Rate Plans", [" ", "EP", "CP"], key=f"{form_key}_rate_plans", help="EP: European Plan, CP: Continental Plan")
        with col2:
            booking_source = st.selectbox("Booking Source", BOOKING_SOURCES, key=f"{form_key}_booking_source")
        
        # Row 6: Total Tariff, Advance Payment
        col1, col2 = st.columns(2)
        with col1:
            total_tariff = st.number_input("Total Tariff", min_value=0.0, step=0.01, key=f"{form_key}_total_tariff")
        with col2:
            advance_payment = st.number_input("Advance Payment", min_value=0.0, step=0.01, key=f"{form_key}_advance_payment")
        
        # Row 7: Balance (Auto-calculated), Advance MOP
        col1, col2 = st.columns(2)
        with col1:
            balance = total_tariff - advance_payment
            st.number_input("Balance", value=balance, disabled=True, key=f"{form_key}_balance", help="Auto-calculated: Total Tariff - Advance Payment")
        with col2:
            advance_mop = st.selectbox("Advance MOP", MOP_OPTIONS, key=f"{form_key}_advance_mop", help="Mode of Payment for advance amount")
        
        # Row 8: Balance MOP
        balance_mop = st.selectbox("Balance MOP", MOP_OPTIONS, key=f"{form_key}_balance_mop", help="Mode of Payment for balance amount")
        
        # Row 9: Booking Status, Payment Status
        col1, col2 = st.columns(2)
        with col1:
            booking_status = st.selectbox("Booking Status", ["Pending", "Confirmed", "Cancelled", "Follow-up", "Completed", "No Show"], key=f"{form_key}_booking_status")
        with col2:
            payment_status = st.selectbox("Payment Status", ["Not Paid", "Fully Paid", "Partially Paid"], key=f"{form_key}_payment_status")
        
        # Row 10: Submitted By, Modified By
        col1, col2 = st.columns(2)
        with col1:
            submitted_by = st.text_input("Submitted By", value=st.session_state.get("username", ""), disabled=True, key=f"{form_key}_submitted_by")
        with col2:
            modified_by = st.text_input("Modified By", value="", disabled=True, key=f"{form_key}_modified_by")
        
        # Row 11: Modified Comments, Remarks
        modified_comments = st.text_area("Modified Comments", key=f"{form_key}_modified_comments")
        remarks = st.text_area("Remarks", key=f"{form_key}_remarks")
        
        if st.form_submit_button("Submit Reservation"):
            # Validate room_no
            if not room_no or not room_no.strip():
                st.error("❌ Room No cannot be empty. Please enter a room number.")
            elif len(room_no) > 50:
                st.error("❌ Room No cannot exceed 50 characters.")
            else:
                new_reservation = {
                    "property_name": property_name,
                    "guest_name": guest_name,
                    "guest_phone": guest_phone,
                    "check_in": str(check_in),
                    "check_out": str(check_out),
                    "room_no": room_no.strip(),
                    "room_type": room_type,
                    "no_of_adults": no_of_adults,
                    "no_of_children": no_of_children,
                    "no_of_infants": no_of_infants,
                    "rate_plans": rate_plans,
                    "booking_source": booking_source,
                    "total_tariff": total_tariff,
                    "advance_payment": advance_payment,
                    "balance": balance,
                    "advance_mop": advance_mop,
                    "balance_mop": balance_mop,
                    "booking_status": booking_status,
                    "payment_status": payment_status,
                    "submitted_by": st.session_state.get("username", ""),
                    "modified_by": "",
                    "modified_comments": modified_comments,
                    "remarks": remarks
                }
                try:
                    response = supabase.table("reservations").insert(new_reservation).execute()
                    if response.data:
                        st.success("✅ Reservation created successfully!")
                        st.session_state.reservations.append({
                            "Property Name": property_name,
                            "Booking ID": booking_id,
                            "Guest Name": guest_name,
                            "Guest Phone": guest_phone,
                            "Check In": str(check_in),
                            "Check Out": str(check_out),
                            "Room No": room_no.strip(),
                            "Room Type": room_type,
                            "No of Adults": no_of_adults,
                            "No of Children": no_of_children,
                            "No of Infants": no_of_infants,
                            "Rate Plans": rate_plans,
                            "Booking Source": booking_source,
                            "Total Tariff": total_tariff,
                            "Advance Payment": advance_payment,
                            "Balance": balance,
                            "Advance MOP": advance_mop,
                            "Balance MOP": balance_mop,
                            "Booking Status": booking_status,
                            "Payment Status": payment_status,
                            "Submitted By": st.session_state.get("username", ""),
                            "Modified By": "",
                            "Modified Comments": modified_comments,
                            "Remarks": remarks
                        })
                        st.rerun()
                    else:
                        st.error("❌ Failed to create reservation in Supabase.")
                except Exception as e:
                    st.error(f"Error creating reservation: {e}")

def show_reservations():
    """Display all direct reservations with filters."""
    st.title("📋 View Direct Reservations")
    
    if st.button("🔄 Refresh Reservations"):
        st.cache_data.clear()
        st.session_state.pop('reservations', None)
        st.success("Cache cleared! Refreshing reservations...")
        st.rerun()
    
    if 'reservations' not in st.session_state:
        st.session_state.reservations = load_reservations_from_supabase()
    
    if not st.session_state.reservations:
        st.info("No reservations available to view.")
        return

    df = pd.DataFrame(st.session_state.reservations)
    display_columns = [
        "Property Name", "Booking ID", "Guest Name", "Check In", "Check Out",
        "Room No", "Room Type", "Booking Status", "Payment Status"
    ]
    st.subheader("Filters")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        start_date = st.date_input("Start Date", value=None, key="view_filter_start_date")
    with col2:
        end_date = st.date_input("End Date", value=None, key="view_filter_end_date")
    with col3:
        filter_status = st.selectbox("Filter by Status", ["All", "Confirmed", "Pending", "Cancelled", "Follow-up", "Completed", "No Show"], key="view_filter_status")
    with col4:
        filter_check_in_date = st.date_input("Check-in Date", value=None, key="view_filter_check_in_date")
    with col5:
        filter_check_out_date = st.date_input("Check-out Date", value=None, key="view_filter_check_out_date")
    with col6:
        filter_property = st.selectbox("Filter by Property", ["All"] + sorted(df["Property Name"].dropna().unique()), key="view_filter_property")
    
    filtered_df = display_filtered_analysis(df, start_date, end_date)
    
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
    else:
        st.dataframe(filtered_df[display_columns], use_container_width=True)

def show_edit_reservations():
    """Display edit direct reservations page."""
    st.title("✏️ Edit Direct Reservations")
    
    if st.button("🔄 Refresh Reservations"):
        st.cache_data.clear()
        st.session_state.pop('reservations', None)
        st.success("Cache cleared! Refreshing reservations...")
        st.rerun()

    if 'reservations' not in st.session_state:
        st.session_state.reservations = load_reservations_from_supabase()
    
    if not st.session_state.reservations:
        st.info("No reservations available to edit.")
        return

    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False
        st.session_state.edit_index = None

    df = pd.DataFrame(st.session_state.reservations)
    display_columns = ["Property Name", "Booking ID", "Guest Name", "Check In", "Check Out", "Room No", "Room Type", "Booking Status", "Payment Status"]
    st.dataframe(df[display_columns], use_container_width=True)
    
    st.subheader("Select Reservation to Edit")
    booking_id_options = df["Booking ID"].unique()
    selected_booking_id = st.selectbox("Select Booking ID", booking_id_options)
    
    if st.button("✏️ Edit Selected Reservation"):
        edit_index = df[df["Booking ID"] == selected_booking_id].index[0]
        st.session_state.edit_mode = True
        st.session_state.edit_index = edit_index
    
    if st.session_state.edit_mode and st.session_state.edit_index is not None:
        edit_index = st.session_state.edit_index
        reservation = st.session_state.reservations[edit_index]
        
        property_room_map = load_property_room_map()
        properties = sorted(property_room_map.keys())
        room_types = list(property_room_map[reservation["Property Name"]].keys()) if reservation["Property Name"] in property_room_map else []
        
        with st.form(key=f"edit_form_{reservation['Booking ID']}"):
            # Row 1: Property Name, Booking ID
            col1, col2 = st.columns(2)
            with col1:
                property_name = st.selectbox("Property Name", properties, index=properties.index(reservation["Property Name"]) if reservation["Property Name"] in properties else 0)
            with col2:
                booking_id = st.text_input("Booking ID", value=reservation["Booking ID"], disabled=True)
            
            # Row 2: Guest Name, Guest Phone
            col1, col2 = st.columns(2)
            with col1:
                guest_name = st.text_input("Guest Name", value=reservation["Guest Name"])
            with col2:
                guest_phone = st.text_input("Guest Phone", value=reservation["Guest Phone"])
            
            # Row 3: Check In, Check Out
            col1, col2 = st.columns(2)
            with col1:
                check_in = st.date_input("Check In", value=date.fromisoformat(reservation["Check In"]) if reservation["Check In"] else date.today())
            with col2:
                check_out = st.date_input("Check Out", value=date.fromisoformat(reservation["Check Out"]) if reservation["Check Out"] else date.today())
            
            # Row 4: Room Type, Room No (WITH EDITABLE ROOM NUMBER)
            fetched_room_no = str(reservation.get("Room No", "") or "")
            fetched_room_type = str(reservation.get("Room Type", "") or "")
            
            col1, col2 = st.columns(2)
            with col2:
                room_type = st.selectbox("Room Type", room_types, index=room_types.index(fetched_room_type) if fetched_room_type in room_types else 0, help="Select the room type. Choose 'Others' to manually enter a custom room number.")
            
            with col1:
                if room_type == "Others":
                    # For "Others", show text input
                    initial_value = fetched_room_no if fetched_room_type == "Others" else ""
                    room_no = st.text_input(
                        "Room No",
                        value=initial_value,
                        placeholder="Enter custom room number",
                        help="Enter a custom room number for 'Others' room type."
                    )
                    if not room_no.strip():
                        st.warning("⚠️ Please enter a valid Room No for 'Others' room type.")
                else:
                    # For predefined types, show editable text input with suggestions
                    room_numbers = property_room_map[property_name].get(room_type, [])
                    room_no = st.text_input(
                        "Room No",
                        value=fetched_room_no,
                        placeholder="Enter room number",
                        help="Enter or edit the room number. You can type any custom value or use suggestions below."
                    )
                    
                    # Show helpful suggestions based on property
                    suggestion_list = [r for r in room_numbers if r.strip()]
                    if suggestion_list:
                        st.caption(f"💡 **Quick suggestions:** {', '.join(suggestion_list)}")
            
            # Row 5: No of Adults, Children, Infants
            col1, col2, col3 = st.columns(3)
            with col1:
                no_of_adults = st.number_input("No of Adults", min_value=0, value=reservation["No of Adults"])
            with col2:
                no_of_children = st.number_input("No of Children", min_value=0, value=reservation["No of Children"])
            with col3:
                no_of_infants = st.number_input("No of Infants", min_value=0, value=reservation["No of Infants"])
            
            # Row 6: Rate Plans, Booking Source
            col1, col2 = st.columns(2)
            with col1:
                current_rate_plan = reservation.get("Rate Plans", " ")
                rate_plan_options = [" ", "EP", "CP"]
                rate_plan_index = rate_plan_options.index(current_rate_plan) if current_rate_plan in rate_plan_options else 0
                rate_plans = st.selectbox("Rate Plans", rate_plan_options, index=rate_plan_index, help="EP: European Plan, CP: Continental Plan")
            with col2:
                current_source = reservation.get("Booking Source", "")
                source_index = BOOKING_SOURCES.index(current_source) if current_source in BOOKING_SOURCES else 0
                booking_source = st.selectbox("Booking Source", BOOKING_SOURCES, index=source_index)
            
            # Row 7: Total Tariff, Advance Payment
            col1, col2 = st.columns(2)
            with col1:
                total_tariff = st.number_input("Total Tariff", min_value=0.0, value=reservation["Total Tariff"])
            with col2:
                advance_payment = st.number_input("Advance Payment", min_value=0.0, value=reservation["Advance Payment"])
            
            # Row 8: Balance (Auto-calculated), Advance MOP
            col1, col2 = st.columns(2)
            with col1:
                balance = total_tariff - advance_payment
                st.number_input("Balance", value=balance, disabled=True, help="Auto-calculated: Total Tariff - Advance Payment")
            with col2:
                current_advance_mop = reservation.get("Advance MOP", "")
                advance_mop_index = MOP_OPTIONS.index(current_advance_mop) if current_advance_mop in MOP_OPTIONS else 0
                advance_mop = st.selectbox("Advance MOP", MOP_OPTIONS, index=advance_mop_index, help="Mode of Payment for advance amount")
            
            # Row 9: Balance MOP
            current_balance_mop = reservation.get("Balance MOP", "")
            balance_mop_index = MOP_OPTIONS.index(current_balance_mop) if current_balance_mop in MOP_OPTIONS else 0
            balance_mop = st.selectbox("Balance MOP", MOP_OPTIONS, index=balance_mop_index, help="Mode of Payment for balance amount")
            
            # Row 10: Booking Status, Payment Status
            col1, col2 = st.columns(2)
            with col1:
                booking_status = st.selectbox("Booking Status", ["Pending", "Confirmed", "Cancelled", "Follow-up", "Completed", "No Show"], index=["Pending", "Confirmed", "Cancelled", "Follow-up", "Completed", "No Show"].index(reservation["Booking Status"]))
            with col2:
                payment_status = st.selectbox("Payment Status", ["Not Paid", "Fully Paid", "Partially Paid"], index=["Not Paid", "Fully Paid", "Partially Paid"].index(reservation["Payment Status"]))
            
            # Row 11: Submitted By, Modified By
            col1, col2 = st.columns(2)
            with col1:
                submitted_by = st.text_input("Submitted By", value=reservation["Submitted By"], disabled=True)
            with col2:
                modified_by = st.text_input("Modified By", value=st.session_state.username, disabled=True)
            
            # Row 12: Modified Comments, Remarks
            modified_comments = st.text_area("Modified Comments", value=reservation["Modified Comments"])
            remarks = st.text_area("Remarks", value=reservation["Remarks"])
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.form_submit_button("💾 Update Reservation", use_container_width=True):
                    # Validate room_no
                    if not room_no or not room_no.strip():
                        st.error("❌ Room No cannot be empty. Please enter a room number.")
                    elif len(room_no) > 50:
                        st.error("❌ Room No cannot exceed 50 characters.")
                    else:
                        updated_reservation = {
                            "property_name": property_name,
                            "booking_id": reservation["Booking ID"],
                            "guest_name": guest_name,
                            "guest_phone": guest_phone,
                            "check_in": str(check_in),
                            "check_out": str(check_out),
                            "room_no": room_no.strip(),
                            "room_type": room_type,
                            "no_of_adults": no_of_adults,
                            "no_of_children": no_of_children,
                            "no_of_infants": no_of_infants,
                            "rate_plans": rate_plans,
                            "booking_source": booking_source,
                            "total_tariff": total_tariff,
                            "advance_payment": advance_payment,
                            "balance": balance,
                            "advance_mop": advance_mop,
                            "balance_mop": balance_mop,
                            "booking_status": booking_status,
                            "payment_status": payment_status,
                            "submitted_by": reservation["Submitted By"],
                            "modified_by": st.session_state.username,
                            "modified_comments": modified_comments,
                            "remarks": remarks
                        }
                        if update_reservation_in_supabase(reservation["Booking ID"], updated_reservation):
                            st.session_state.reservations[edit_index] = {
                                "Property Name": property_name,
                                "Booking ID": reservation["Booking ID"],
                                "Guest Name": guest_name,
                                "Guest Phone": guest_phone,
                                "Check In": str(check_in),
                                "Check Out": str(check_out),
                                "Room No": room_no.strip(),
                                "Room Type": room_type,
                                "No of Adults": no_of_adults,
                                "No of Children": no_of_children,
                                "No of Infants": no_of_infants,
                                "Rate Plans": rate_plans,
                                "Booking Source": booking_source,
                                "Total Tariff": total_tariff,
                                "Advance Payment": advance_payment,
                                "Balance": balance,
                                "Advance MOP": advance_mop,
                                "Balance MOP": balance_mop,
                                "Booking Status": booking_status,
                                "Payment Status": payment_status,
                                "Submitted By": reservation["Submitted By"],
                                "Modified By": st.session_state.username,
                                "Modified Comments": modified_comments,
                                "Remarks": remarks
                            }
                            st.session_state.edit_mode = False
                            st.session_state.edit_index = None
                            st.success(f"✅ Reservation {reservation['Booking ID']} updated successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to update reservation")
            with col_btn2:
                if st.session_state.get('role') == "Management":
                    if st.form_submit_button("🗑️ Delete Reservation", use_container_width=True):
                        if delete_reservation_in_supabase(reservation["Booking ID"]):
                            st.session_state.reservations.pop(edit_index)
                            st.session_state.edit_mode = False
                            st.session_state.edit_index = None
                            st.success(f"🗑️ Reservation {reservation['Booking ID']} deleted successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to delete reservation")

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
                y="Total Tariff",
                title="Total Revenue by Property",
                height=400,
                labels={"Total Tariff": "Revenue (₹)"}
            )
            st.plotly_chart(fig_bar, use_container_width=True, key="analytics_bar_chart")
    except Exception as e:
        st.error(f"Error rendering analytics dashboard: {e}")

def load_reservations_from_supabase():
    """Load all direct reservations from Supabase."""
    try:
        response = supabase.table("reservations").select("*").order("check_in", desc=True).execute()
        if not response.data:
            st.warning("No reservations found in Supabase.")
            return []
        
        # Transform Supabase snake_case to title case for UI consistency
        transformed_data = []
        for record in response.data:
            transformed_record = {
                "Property Name": record.get("property_name", ""),
                "Booking ID": record.get("booking_id", ""),
                "Guest Name": record.get("guest_name", ""),
                "Guest Phone": record.get("guest_phone", ""),
                "Check In": record.get("check_in", ""),
                "Check Out": record.get("check_out", ""),
                "Room No": record.get("room_no", ""),
                "Room Type": record.get("room_type", ""),
                "No of Adults": record.get("no_of_adults", 0),
                "No of Children": record.get("no_of_children", 0),
                "No of Infants": record.get("no_of_infants", 0),
                "Rate Plans": record.get("rate_plans", ""),
                "Booking Source": record.get("booking_source", ""),
                "Total Tariff": record.get("total_tariff", 0.0),
                "Advance Payment": record.get("advance_payment", 0.0),
                "Balance": record.get("balance", 0.0),
                "Advance MOP": record.get("advance_mop", ""),
                "Balance MOP": record.get("balance_mop", ""),
                "Booking Status": record.get("booking_status", "Pending"),
                "Payment Status": record.get("payment_status", "Not Paid"),
                "Submitted By": record.get("submitted_by", ""),
                "Modified By": record.get("modified_by", ""),
                "Modified Comments": record.get("modified_comments", ""),
                "Remarks": record.get("remarks", "")
            }
            transformed_data.append(transformed_record)
        return transformed_data
    except Exception as e:
        st.error(f"Error loading reservations: {e}")
        return []

def update_reservation_in_supabase(booking_id, updated_reservation):
    """Update a reservation in Supabase."""
    try:
        # Transform to snake_case for Supabase
        supabase_reservation = {
            "property_name": updated_reservation["property_name"],
            "booking_id": updated_reservation["booking_id"],
            "guest_name": updated_reservation["guest_name"],
            "guest_phone": updated_reservation["guest_phone"],
            "check_in": updated_reservation["check_in"],
            "check_out": updated_reservation["check_out"],
            "room_no": updated_reservation["room_no"],
            "room_type": updated_reservation["room_type"],
            "no_of_adults": updated_reservation["no_of_adults"],
            "no_of_children": updated_reservation["no_of_children"],
            "no_of_infants": updated_reservation["no_of_infants"],
            "rate_plans": updated_reservation["rate_plans"],
            "booking_source": updated_reservation["booking_source"],
            "total_tariff": updated_reservation["total_tariff"],
            "advance_payment": updated_reservation["advance_payment"],
            "balance": updated_reservation["balance"],
            "advance_mop": updated_reservation["advance_mop"],
            "balance_mop": updated_reservation["balance_mop"],
            "booking_status": updated_reservation["booking_status"],
            "payment_status": updated_reservation["payment_status"],
            "submitted_by": updated_reservation["submitted_by"],
            "modified_by": updated_reservation["modified_by"],
            "modified_comments": updated_reservation["modified_comments"],
            "remarks": updated_reservation["remarks"]
        }
        response = supabase.table("reservations").update(supabase_reservation).eq("booking_id", booking_id).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Error updating reservation {booking_id}: {e}")
        return False

def delete_reservation_in_supabase(booking_id):
    """Delete a reservation from Supabase."""
    try:
        response = supabase.table("reservations").delete().eq("booking_id", booking_id).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Error deleting reservation {booking_id}: {e}")
        return False

def display_filtered_analysis(df, start_date, end_date, view_mode=True):
    """Helper function to filter dataframe for analytics or view."""
    filtered_df = df.copy()
    try:
        if start_date:
            filtered_df = filtered_df[pd.to_datetime(filtered_df["Check In"]) >= pd.to_datetime(start_date)]
        if end_date:
            filtered_df = filtered_df[pd.to_datetime(filtered_df["Check In"]) <= pd.to_datetime(end_date)]
    except Exception as e:
        st.error(f"Error filtering data: {e}")
    return filtered_df
