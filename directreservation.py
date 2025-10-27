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
            "No Show": ["No Show"]
        },
        "La Millionaire Resort": {
            "Double Room": ["101", "102", "103", "105"],
            "Deluex Double Room with Balcony": ["205", "304", "305"],
            "Deluex Triple Room with Balcony": ["201", "202", "203", "204", "301", "302", "303"],
            "Deluex Family Room with Balcony": ["206", "207", "208", "306", "307", "308"],
            "Deluex Triple Room": ["402"],
            "Deluex Family Room": ["401"],
            "Day Use": ["Day Use 1", "Day Use 2", "Day Use 3", "Day Use 5"],
            "No Show": ["No Show"]
        },
        "Le Poshe Luxury": {
            "2BHA Appartment": ["101&102", "101", "102"],
            "2BHA Appartment with Balcony": ["201&202", "201", "202", "301&302", "301", "302", "401&402", "401", "402"],
            "3BHA Appartment": ["203to205", "203", "204", "205", "303to305", "303", "304", "305", "403to405", "403", "404", "405"],
            "Double Room with Private Terrace": ["501"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"]
        },
        "Le Poshe Suite": {
            "2BHA Appartment": ["601&602", "601", "602", "603", "604", "703", "704"],
            "2BHA Appartment with Balcony": ["701&702", "701", "702"],
            "Double Room with Terrace": ["801"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"]
        },
        "La Paradise Residency": {
            "Double Room": ["101", "102", "103", "301", "302", "304"],
            "Family Room": ["201", "203"],
            "Triple Room": ["202", "303"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"]
        },
        "La Paradise Luxury": {
            "3BHA Appartment": ["101to103", "101", "102", "103", "201to203", "201", "202", "203"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"]
        },
        "La Villa Heritage": {
            "Double Room": ["101", "102", "103"],
            "4BHA Appartment": ["201to203&301", "201", "202", "203", "301"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"]
        },
        "Le Pondy Beach Side": {
            "Villa": ["101to104", "101", "102", "103", "104"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"]
        },
        "Le Royce Villa": {
            "Villa": ["101to102&201to202", "101", "102", "201", "202"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"]
        },
        "La Tamara Luxury": {
            "3BHA": ["101to103", "101", "102", "103", "104to106", "104", "105", "106", "201to203", "201", "202", "203", "204to206", "204", "205", "206", "301to303", "301", "302", "303", "304to306", "304", "305", "306"],
            "4BHA": ["401to404", "401", "402", "403", "404"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"]
        },
        "La Antilia Luxury": {
            "Deluex Suite Room": ["101"],
            "Deluex Double Room": ["203", "204", "303", "304"],
            "Family Room": ["201", "202", "301", "302"],
            "Deluex suite Room with Tarrace": ["404"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"]
        },
        "La Tamara Suite": {
            "Two Bedroom apartment": ["101&102"],
            "Deluxe Apartment": ["103&104"],
            "Deluxe Double Room": ["203", "204", "205"],
            "Deluxe Triple Room": ["201", "202"],
            "Deluxe Family Room": ["206"]
        }
    }

def generate_booking_id():
    """
    Generate a unique booking ID by checking existing IDs in Supabase.
    """
    try:
        today = datetime.now().strftime('%Y%m%d')
        response = supabase.table("reservations").select("bookingId").like("bookingId", f"TIE{today}%").execute()
        existing_ids = [record["bookingId"] for record in response.data]
        sequence = 1
        while f"TIE{today}{sequence:03d}" in existing_ids:
            sequence += 1
        return f"TIE{today}{sequence:03d}"
    except Exception as e:
        st.error(f"Error generating booking ID: {e}")
        return None

def insert_reservation_in_supabase(reservation):
    """Insert a new reservation into Supabase."""
    try:
        response = supabase.table("reservations").insert(reservation).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Error inserting reservation: {e}")
        return False

def show_new_reservation_form():
    """Display form to create a new direct reservation."""
    st.header("🏠 New Direct Reservation")
    
    # Form layout
    with st.form(key="new_reservation_form"):
        col1, col2 = st.columns(2)
        
        # Column 1
        with col1:
            property_name = st.selectbox(
                "Property Name", 
                sorted(load_property_room_map().keys()),
                key="new_property_name"
            )
            # Get room types for selected property
            room_types = sorted(load_property_room_map()[property_name].keys())
            room_type = st.selectbox(
                "Room Type",
                room_types,
                key="new_room_type"
            )
            # Get room numbers for selected room type
            room_numbers = load_property_room_map()[property_name][room_type]
            room_no = st.selectbox(
                "Room No",
                room_numbers,
                key="new_room_no"
            )
            guest_name = st.text_input("Guest Name", key="new_guest_name")
            guest_phone = st.text_input("Guest Phone", key="new_guest_phone")
            check_in = st.date_input(
                "Check In",
                value=date.today(),
                key="new_check_in"
            )
            check_out = st.date_input(
                "Check Out",
                value=date.today() + timedelta(days=1),
                key="new_check_out"
            )
        
        # Column 2
        with col2:
            no_of_adults = st.number_input(
                "No of Adults",
                min_value=0,
                value=1,
                step=1,
                key="new_no_of_adults"
            )
            no_of_children = st.number_input(
                "No of Children",
                min_value=0,
                value=0,
                step=1,
                key="new_no_of_children"
            )
            no_of_infants = st.number_input(
                "No of Infants",
                min_value=0,
                value=0,
                step=1,
                key="new_no_of_infants"
            )
            rate_plans = st.text_input("Rate Plans", key="new_rate_plans")
            booking_source = st.selectbox(
                "Booking Source",
                BOOKING_SOURCES,
                key="new_booking_source"
            )
            total_tariff = st.number_input(
                "Total Tariff",
                min_value=0.0,
                step=100.0,
                key="new_total_tariff"
            )
            advance_payment = st.number_input(
                "Advance Payment",
                min_value=0.0,
                step=100.0,
                key="new_advance_payment"
            )
            balance = st.number_input(
                "Balance",
                min_value=0.0,
                step=100.0,
                value=total_tariff - advance_payment,
                key="new_balance"
            )
            advance_mop = st.selectbox(
                "Advance MOP",
                MOP_OPTIONS,
                key="new_advance_mop"
            )
            balance_mop = st.selectbox(
                "Balance MOP",
                MOP_OPTIONS,
                key="new_balance_mop"
            )
            booking_status = st.selectbox(
                "Booking Status",
                ["Pending", "Confirmed", "Cancelled", "Completed", "No Show"],
                key="new_booking_status"
            )
            payment_status = st.selectbox(
                "Payment Status",
                ["Not Paid", "Partially Paid", "Fully Paid"],
                key="new_payment_status"
            )
            submitted_by = st.text_input(
                "Submitted By",
                value=st.session_state.username if st.session_state.get('username') else "",
                key="new_submitted_by"
            )
            remarks = st.text_area("Remarks", key="new_remarks")
        
        # Submit button
        submitted = st.form_submit_button("Submit Reservation")
        
        if submitted:
            # Generate booking ID
            booking_id = generate_booking_id()
            if not booking_id:
                st.error("Failed to generate booking ID. Please try again.")
                return
            
            # Prepare reservation data for Supabase
            reservation = {
                "propertyName": property_name,
                "bookingId": booking_id,
                "guestName": guest_name,
                "guestPhone": guest_phone,
                "checkIn": check_in.isoformat(),
                "checkOut": check_out.isoformat(),
                "roomNo": room_no,
                "roomType": room_type,
                "noOfAdults": int(no_of_adults),
                "noOfChildren": int(no_of_children),
                "noOfInfants": int(no_of_infants),
                "ratePlans": rate_plans,
                "bookingSource": booking_source,
                "totalTariff": float(total_tariff),
                "advancePayment": float(advance_payment),
                "balance": float(balance),
                "advanceMop": advance_mop,
                "balanceMop": balance_mop,
                "bookingStatus": booking_status,
                "paymentStatus": payment_status,
                "submittedBy": submitted_by,
                "modifiedBy": "",
                "modifiedComments": "",
                "remarks": remarks
            }
            
            # Insert reservation into Supabase
            if insert_reservation_in_supabase(reservation):
                st.success(f"✅ Reservation {booking_id} created successfully!")
                st.session_state.reservations.append({
                    "Property Name": property_name,
                    "Booking ID": booking_id,
                    "Guest Name": guest_name,
                    "Guest Phone": guest_phone,
                    "Check In": check_in.isoformat(),
                    "Check Out": check_out.isoformat(),
                    "Room No": room_no,
                    "Room Type": room_type,
                    "No of Adults": int(no_of_adults),
                    "No of Children": int(no_of_children),
                    "No of Infants": int(no_of_infants),
                    "Rate Plans": rate_plans,
                    "Booking Source": booking_source,
                    "Total Tariff": float(total_tariff),
                    "Advance Payment": float(advance_payment),
                    "Balance": float(balance),
                    "Advance MOP": advance_mop,
                    "Balance MOP": balance_mop,
                    "Booking Status": booking_status,
                    "Payment Status": payment_status,
                    "Submitted By": submitted_by,
                    "Modified By": "",
                    "Modified Comments": "",
                    "Remarks": remarks
                })
                st.rerun()
            else:
                st.error("❌ Failed to create reservation. Please try again.")

def show_reservations():
    """Display a table of all reservations."""
    st.header("📋 View Reservations")
    
    if not st.session_state.get('reservations'):
        st.session_state.reservations = load_reservations_from_supabase()
    
    if not st.session_state.reservations:
        st.info("No reservations available to display.")
        return
    
    df = pd.DataFrame(st.session_state.reservations)
    
    # Display filters
    st.subheader("Filters")
    col1, col2, col3 = st.columns(3)
    with col1:
        start_date = st.date_input("Start Date", value=None, key="view_filter_start_date")
    with col2:
        end_date = st.date_input("End Date", value=None, key="view_filter_end_date")
    with col3:
        property_filter = st.selectbox(
            "Filter by Property",
            ["All"] + sorted(df["Property Name"].unique()),
            key="view_filter_property"
        )
    
    # Apply filters
    filtered_df = display_filtered_analysis(df, start_date, end_date)
    if property_filter != "All":
        filtered_df = filtered_df[filtered_df["Property Name"] == property_filter]
    
    if filtered_df.empty:
        st.warning("No reservations match the selected filters.")
        return
    
    # Display table
    st.dataframe(
        filtered_df,
        use_container_width=True,
        column_config={
            "Total Tariff": st.column_config.NumberColumn(format="₹%.2f"),
            "Advance Payment": st.column_config.NumberColumn(format="₹%.2f"),
            "Balance": st.column_config.NumberColumn(format="₹%.2f")
        }
    )

def show_edit_reservations():
    """Display a form to edit existing reservations."""
    st.header("✏️ Edit Reservations")
    
    if not st.session_state.get('reservations'):
        st.session_state.reservations = load_reservations_from_supabase()
    
    if not st.session_state.reservations:
        st.info("No reservations available to edit.")
        return
    
    # Check permissions
    if not st.session_state.get('permissions', {}).get('edit', False):
        st.error("❌ Access Denied: You do not have permission to edit reservations.")
        return
    
    df = pd.DataFrame(st.session_state.reservations)
    
    # Filter selection
    st.subheader("Select Reservation to Edit")
    booking_id = st.selectbox(
        "Select Booking ID",
        options=df["Booking ID"].tolist(),
        key="edit_booking_id"
    )
    
    if not booking_id:
        return
    
    # Get the reservation to edit
    reservation = df[df["Booking ID"] == booking_id].iloc[0]
    edit_index = df[df["Booking ID"] == booking_id].index[0]
    
    # Edit form
    with st.form(key=f"edit_reservation_{booking_id}"):
        col1, col2 = st.columns(2)
        
        # Column 1
        with col1:
            property_name = st.selectbox(
                "Property Name",
                sorted(load_property_room_map().keys()),
                index=sorted(load_property_room_map().keys()).index(reservation["Property Name"]),
                key=f"edit_property_name_{booking_id}"
            )
            room_types = sorted(load_property_room_map()[property_name].keys())
            room_type = st.selectbox(
                "Room Type",
                room_types,
                index=room_types.index(reservation["Room Type"]) if reservation["Room Type"] in room_types else 0,
                key=f"edit_room_type_{booking_id}"
            )
            room_numbers = load_property_room_map()[property_name][room_type]
            room_no = st.selectbox(
                "Room No",
                room_numbers,
                index=room_numbers.index(reservation["Room No"]) if reservation["Room No"] in room_numbers else 0,
                key=f"edit_room_no_{booking_id}"
            )
            guest_name = st.text_input("Guest Name", value=reservation["Guest Name"], key=f"edit_guest_name_{booking_id}")
            guest_phone = st.text_input("Guest Phone", value=reservation["Guest Phone"], key=f"edit_guest_phone_{booking_id}")
            check_in = st.date_input(
                "Check In",
                value=datetime.fromisoformat(reservation["Check In"]).date() if reservation["Check In"] else date.today(),
                key=f"edit_check_in_{booking_id}"
            )
            check_out = st.date_input(
                "Check Out",
                value=datetime.fromisoformat(reservation["Check Out"]).date() if reservation["Check Out"] else date.today() + timedelta(days=1),
                key=f"edit_check_out_{booking_id}"
            )
        
        # Column 2
        with col2:
            no_of_adults = st.number_input(
                "No of Adults",
                min_value=0,
                value=int(reservation["No of Adults"]),
                step=1,
                key=f"edit_no_of_adults_{booking_id}"
            )
            no_of_children = st.number_input(
                "No of Children",
                min_value=0,
                value=int(reservation["No of Children"]),
                step=1,
                key=f"edit_no_of_children_{booking_id}"
            )
            no_of_infants = st.number_input(
                "No of Infants",
                min_value=0,
                value=int(reservation["No of Infants"]),
                step=1,
                key=f"edit_no_of_infants_{booking_id}"
            )
            rate_plans = st.text_input("Rate Plans", value=reservation["Rate Plans"], key=f"edit_rate_plans_{booking_id}")
            booking_source = st.selectbox(
                "Booking Source",
                BOOKING_SOURCES,
                index=BOOKING_SOURCES.index(reservation["Booking Source"]) if reservation["Booking Source"] in BOOKING_SOURCES else 0,
                key=f"edit_booking_source_{booking_id}"
            )
            total_tariff = st.number_input(
                "Total Tariff",
                min_value=0.0,
                value=float(reservation["Total Tariff"]),
                step=100.0,
                key=f"edit_total_tariff_{booking_id}"
            )
            advance_payment = st.number_input(
                "Advance Payment",
                min_value=0.0,
                value=float(reservation["Advance Payment"]),
                step=100.0,
                key=f"edit_advance_payment_{booking_id}"
            )
            balance = st.number_input(
                "Balance",
                min_value=0.0,
                value=float(total_tariff - advance_payment),
                step=100.0,
                key=f"edit_balance_{booking_id}"
            )
            advance_mop = st.selectbox(
                "Advance MOP",
                MOP_OPTIONS,
                index=MOP_OPTIONS.index(reservation["Advance MOP"]) if reservation["Advance MOP"] in MOP_OPTIONS else 0,
                key=f"edit_advance_mop_{booking_id}"
            )
            balance_mop = st.selectbox(
                "Balance MOP",
                MOP_OPTIONS,
                index=MOP_OPTIONS.index(reservation["Balance MOP"]) if reservation["Balance MOP"] in MOP_OPTIONS else 0,
                key=f"edit_balance_mop_{booking_id}"
            )
            booking_status = st.selectbox(
                "Booking Status",
                ["Pending", "Confirmed", "Cancelled", "Completed", "No Show"],
                index=["Pending", "Confirmed", "Cancelled", "Completed", "No Show"].index(reservation["Booking Status"]) if reservation["Booking Status"] in ["Pending", "Confirmed", "Cancelled", "Completed", "No Show"] else 0,
                key=f"edit_booking_status_{booking_id}"
            )
            payment_status = st.selectbox(
                "Payment Status",
                ["Not Paid", "Partially Paid", "Fully Paid"],
                index=["Not Paid", "Partially Paid", "Fully Paid"].index(reservation["Payment Status"]) if reservation["Payment Status"] in ["Not Paid", "Partially Paid", "Fully Paid"] else 0,
                key=f"edit_payment_status_{booking_id}"
            )
            submitted_by = st.text_input(
                "Submitted By",
                value=reservation["Submitted By"],
                key=f"edit_submitted_by_{booking_id}"
            )
            modified_by = st.text_input(
                "Modified By",
                value=st.session_state.username if st.session_state.get('username') else "",
                key=f"edit_modified_by_{booking_id}"
            )
            modified_comments = st.text_area(
                "Modified Comments",
                value=reservation["Modified Comments"],
                key=f"edit_modified_comments_{booking_id}"
            )
            remarks = st.text_area("Remarks", value=reservation["Remarks"], key=f"edit_remarks_{booking_id}")
        
        # Buttons
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.form_submit_button("💾 Update Reservation", use_container_width=True):
                updated_reservation = {
                    "propertyName": property_name,
                    "bookingId": booking_id,
                    "guestName": guest_name,
                    "guestPhone": guest_phone,
                    "checkIn": check_in.isoformat(),
                    "checkOut": check_out.isoformat(),
                    "roomNo": room_no,
                    "roomType": room_type,
                    "noOfAdults": int(no_of_adults),
                    "noOfChildren": int(no_of_children),
                    "noOfInfants": int(no_of_infants),
                    "ratePlans": rate_plans,
                    "bookingSource": booking_source,
                    "totalTariff": float(total_tariff),
                    "advancePayment": float(advance_payment),
                    "balance": float(balance),
                    "advanceMop": advance_mop,
                    "balanceMop": balance_mop,
                    "bookingStatus": booking_status,
                    "paymentStatus": payment_status,
                    "submittedBy": submitted_by,
                    "modifiedBy": modified_by,
                    "modifiedComments": modified_comments,
                    "remarks": remarks
                }
                if update_reservation_in_supabase(booking_id, updated_reservation):
                    st.session_state.reservations[edit_index] = {
                        "Property Name": property_name,
                        "Booking ID": booking_id,
                        "Guest Name": guest_name,
                        "Guest Phone": guest_phone,
                        "Check In": check_in.isoformat(),
                        "Check Out": check_out.isoformat(),
                        "Room No": room_no,
                        "Room Type": room_type,
                        "No of Adults": int(no_of_adults),
                        "No of Children": int(no_of_children),
                        "No of Infants": int(no_of_infants),
                        "Rate Plans": rate_plans,
                        "Booking Source": booking_source,
                        "Total Tariff": float(total_tariff),
                        "Advance Payment": float(advance_payment),
                        "Balance": float(balance),
                        "Advance MOP": advance_mop,
                        "Balance MOP": balance_mop,
                        "Booking Status": booking_status,
                        "Payment Status": payment_status,
                        "Submitted By": submitted_by,
                        "Modified By": modified_by,
                        "Modified Comments": modified_comments,
                        "Remarks": remarks
                    }
                    st.session_state.edit_mode = False
                    st.session_state.edit_index = None
                    st.success(f"✅ Reservation {booking_id} updated successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to update reservation")
        with col_btn2:
            if st.session_state.get('role') == "Management" and st.session_state.get('permissions', {}).get('delete', False):
                if st.form_submit_button("🗑️ Delete Reservation", use_container_width=True):
                    if delete_reservation_in_supabase(booking_id):
                        st.session_state.reservations.pop(edit_index)
                        st.session_state.edit_mode = False
                        st.session_state.edit_index = None
                        st.success(f"🗑️ Reservation {booking_id} deleted successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to delete reservation")

def show_analytics():
    """Display analytics dashboard for reservations (Management only)."""
    st.header("📊 Reservation Analytics")
    
    if st.session_state.get('role') != "Management":
        st.error("❌ Access Denied: Only Management can view analytics.")
        return
    
    if not st.session_state.get('reservations'):
        st.session_state.reservations = load_reservations_from_supabase()
    
    if not st.session_state.reservations:
        st.info("No reservations available for analytics.")
        return
    
    df = pd.DataFrame(st.session_state.reservations)
    
    # Filters
    st.subheader("Filters")
    col1, col2, col3 = st.columns(3)
    with col1:
        start_date = st.date_input("Start Date", value=None, key="analytics_filter_start_date")
    with col2:
        end_date = st.date_input("End Date", value=None, key="analytics_filter_end_date")
    with col3:
        property_filter = st.selectbox(
            "Filter by Property",
            ["All"] + sorted(df["Property Name"].unique()),
            key="analytics_filter_property"
        )
    
    # Apply filters
    filtered_df = display_filtered_analysis(df, start_date, end_date, view_mode=False)
    if property_filter != "All":
        filtered_df = filtered_df[filtered_df["Property Name"] == property_filter]
    
    if filtered_df.empty:
        st.warning("No data available for the selected filters.")
        return
    
    # Summary Metrics
    st.subheader("Summary Metrics")
    col_metric1, col_metric2, col_metric3 = st.columns(3)
    with col_metric1:
        total_bookings = len(filtered_df)
        st.metric("Total Bookings", total_bookings)
    with col_metric2:
        total_revenue = filtered_df["Total Tariff"].sum()
        st.metric("Total Revenue", f"₹{total_revenue:,.2f}")
    with col_metric3:
        avg_tariff = filtered_df["Total Tariff"].mean()
        st.metric("Average Tariff", f"₹{avg_tariff:,.2f}")
    
    # Charts
    st.subheader("Visualizations")
    
    # Booking Source Distribution
    booking_source_counts = filtered_df["Booking Source"].value_counts().reset_index()
    booking_source_counts.columns = ["Booking Source", "Count"]
    
    # Create bar chart for Booking Source Distribution
    chartjs
    {
        "type": "bar",
        "data": {
            "labels": ${booking_source_counts["Booking Source"].tolist()},
            "datasets": [{
                "label": "Number of Bookings",
                "data": ${booking_source_counts["Count"].tolist()},
                "backgroundColor": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"],
                "borderColor": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"],
                "borderWidth": 1
            }]
        },
        "options": {
            "scales": {
                "y": {
                    "beginAtZero": true,
                    "title": {"display": true, "text": "Number of Bookings"}
                },
                "x": {
                    "title": {"display": true, "text": "Booking Source"}
                }
            },
            "plugins": {
                "legend": {"display": false},
                "title": {"display": true, "text": "Booking Source Distribution"}
            }
        }
    }
