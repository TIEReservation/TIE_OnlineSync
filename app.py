import streamlit as st
import pandas as pd
import psycopg2
from datetime import datetime, date, timedelta
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
import requests
import uuid

# Page config
st.set_page_config(
    page_title="TIE Reservation System",
    page_icon="🏢",
    layout="wide"
)

def check_authentication():
    # Initialize authentication state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        
    # If not authenticated, show login page
    if not st.session_state.authenticated:
        st.title("🔐 TIE Reservation System - Organization Login")
        st.write("Please enter the organization password to access the system.")
        
        # Create password input
        password = st.text_input("Enter organization password:", type="password")
        
        # Login button
        if st.button("🔑 Login"):
            # Change "TIE2024" to your desired password
            if password == "TIE2024":
                st.session_state.authenticated = True
                st.success("✅ Login successful! Redirecting...")
                st.rerun()
            else:
                st.error("❌ Invalid password. Please try again.")
        
        # Stop the app here if not authenticated
        st.stop()

# Call the authentication check
check_authentication()

# Initialize session state for reservations
if 'reservations' not in st.session_state:
    st.session_state.reservations = []

# Initialize session state for edit mode
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False
    st.session_state.edit_index = None

# Helper function to generate booking ID
def generate_booking_id():
    return f"TIE{datetime.now().strftime('%Y%m%d')}{len(st.session_state.reservations) + 1:03d}"

# Helper function to check if guest already exists (excluding current edit)
def check_duplicate_guest(guest_name, mobile_no, room_no, exclude_index=None):
    for i, reservation in enumerate(st.session_state.reservations):
        if exclude_index is not None and i == exclude_index:
            continue
        if (reservation["Guest Name"].lower() == guest_name.lower() and 
            reservation["Mobile No"] == mobile_no and 
            reservation["Room No"] == room_no):
            return True, reservation["Booking ID"]
    return False, None

# Helper function to calculate days between dates (calendar days)
def calculate_days(check_in, check_out):
    if check_in and check_out and check_out > check_in:
        delta = check_out - check_in
        return delta.days
    return 0

# Helper function to safely convert to int with default
def safe_int(value, default=0):
    try:
        return int(value) if value is not None else default
    except (ValueError, TypeError):
        return default

# Helper function to safely convert to float with default
def safe_float(value, default=0.0):
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default

# Main App
def main():
    st.title("🏢 TIE Reservation System")
    st.markdown("---")
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Choose a page", ["Direct Reservations", "View Reservations", "Edit Reservations", "Analytics"])
    
    if page == "Direct Reservations":
        show_new_reservation_form()
    elif page == "View Reservations":
        show_reservations()
    elif page == "Edit Reservations":
        show_edit_reservations()
    elif page == "Analytics":
        show_analytics()

def show_new_reservation_form():
    st.header("📝 Direct Reservations")
    
    # Initialize form keys for real-time calculations
    form_key = "new_reservation"
    
    # Create columns for form layout
    col1, col2, col3 = st.columns(3)
    
    with col1:
        property_options = [
            "Eden Beach Resort",
            "La Paradise Luxury",
            "La Villa Heritage",
            "Le Pondy Beach Side",
            "Le Royce Villa",
            "Le Poshe Luxury",
            "Le Poshe Suite",
            "La Paradise Residency",
            "La Tamara Luxury",
            "Le Poshe Beachview",
            "La Antilia",
            "La Tamara Suite",
            "La Millionare Resort",
            "Le Park Resort"
        ]
        property_name = st.selectbox("Property Name", property_options, 
                                   placeholder="Select or type property name", 
                                   key=f"{form_key}_property")
        room_no = st.text_input("Room No", placeholder="e.g., 101, 202", 
                               key=f"{form_key}_room")
        guest_name = st.text_input("Guest Name", placeholder="Enter guest name", 
                                  key=f"{form_key}_guest")
        mobile_no = st.text_input("Mobile No", placeholder="Enter mobile number", 
                                 key=f"{form_key}_mobile")
        
    with col2:
        adults = st.number_input("No of Adults", min_value=0, value=1, 
                                key=f"{form_key}_adults")
        children = st.number_input("No of Children", min_value=0, value=0, 
                                  key=f"{form_key}_children")
        infants = st.number_input("No of Infants", min_value=0, value=0, 
                                 key=f"{form_key}_infants")
        
        # Real-time Total Pax calculation
        total_pax = safe_int(adults) + safe_int(children) + safe_int(infants)
        st.text_input("Total Pax", value=str(total_pax), disabled=True, 
                     help="Automatically calculated: Adults + Children + Infants")
        
    with col3:
        check_in = st.date_input("Check In", value=date.today(), 
                                key=f"{form_key}_checkin")
        check_out = st.date_input("Check Out", value=date.today() + timedelta(days=1), 
                                 key=f"{form_key}_checkout")
        
        # Real-time Days calculation
        no_of_days = calculate_days(check_in, check_out)
        st.text_input("No of Days", value=str(no_of_days), disabled=True, 
                     help="Automatically calculated: Check-out - Check-in dates")
        
        room_type = st.selectbox("Room Type", 
                               ["Double", "Triple", "Family", "1BHK", "2BHK", "3BHK", "4BHK", "Superior Villa"],
                               key=f"{form_key}_roomtype")
    
    col4, col5 = st.columns(2)
    
    with col4:
        tariff = st.number_input("Tariff (per day)", min_value=0.0, value=0.0, step=100.0,
                                key=f"{form_key}_tariff")
        
        # Real-time Total Tariff calculation
        total_tariff = safe_float(tariff) * max(0, no_of_days)
        st.text_input("Total Tariff", value=f"₹{total_tariff:.2f}", disabled=True, 
                     help="Automatically calculated: Tariff × No of Days")
        
        advance_mop = st.selectbox("Advance MOP", 
                                 ["Cash", "Card", "UPI", "Bank Transfer", "Agoda", "MMT", "Airbnb", "Expedia", "Staflexi", "Website"],
                                 key=f"{form_key}_advmop")
        balance_mop = st.selectbox("Balance MOP", 
                                 ["Cash", "Card", "UPI", "Bank Transfer", "Agoda", "MMT", "Airbnb", "Expedia", "Stayflexi", "Website", "Pending"],
                                 key=f"{form_key}_balmop")
        
    with col5:
        advance_amount = st.number_input("Advance Amount", min_value=0.0, value=0.0, step=100.0,
                                        key=f"{form_key}_advance")
        
        # Real-time Balance Amount calculation
        balance_amount = max(0, total_tariff - safe_float(advance_amount))
        st.text_input("Balance Amount", value=f"₹{balance_amount:.2f}", disabled=True, 
                     help="Automatically calculated: Total Tariff - Advance Amount")
        
        mob = st.text_input("MOB (Mode of Booking)", placeholder="e.g., Phone, Walk-in, Online", 
                           key=f"{form_key}_mob")
        invoice_no = st.text_input("Invoice No", placeholder="Enter invoice number", 
                                  key=f"{form_key}_invoice")
    
    col6, col7 = st.columns(2)
    
    with col6:
        enquiry_date = st.date_input("Enquiry Date", value=date.today(), 
                                    key=f"{form_key}_enquiry")
        booking_date = st.date_input("Booking Date", value=date.today(), 
                                    key=f"{form_key}_booking")
        booking_source = st.selectbox("Booking Source", 
                                    ["Direct", "Online", "Agent", "Walk-in", "Phone"],
                                    key=f"{form_key}_source")
        
    with col7:
        breakfast = st.selectbox("Breakfast", ["CP", "EP"], 
                                key=f"{form_key}_breakfast")
        plan_status = st.selectbox("Plan Status", 
                                 ["Confirmed", "Pending", "Cancelled", "Completed", "No Show"],
                                 key=f"{form_key}_status")
    
    # Form submission button
    if st.button("💾 Save Reservation", use_container_width=True, type="primary"):
        # Validation checks
        if not all([property_name, room_no, guest_name, mobile_no]):
            st.error("❌ Please fill in all required fields (Property Name, Room No, Guest Name, Mobile No)")
        elif check_out <= check_in:
            st.error("❌ Check-out date must be after check-in date")
        elif no_of_days <= 0:
            st.error("❌ Number of days must be greater than 0")
        else:
            # Check for duplicate guest
            is_duplicate, existing_booking_id = check_duplicate_guest(guest_name, mobile_no, room_no)
            
            if is_duplicate:
                st.error(f"❌ Guest '{guest_name}' with mobile '{mobile_no}' in room '{room_no}' already exists! Existing Booking ID: {existing_booking_id}")
            else:
                # Generate booking ID
                booking_id = generate_booking_id()
                
                # Create reservation record with calculated values
                reservation = {
                    "Property Name": property_name,
                    "Room No": room_no,
                    "Guest Name": guest_name,
                    "Mobile No": mobile_no,
                    "No of Adults": safe_int(adults),
                    "No of Children": safe_int(children),
                    "No of Infants": safe_int(infants),
                    "Total Pax": total_pax,
                    "Check In": check_in,
                    "Check Out": check_out,
                    "No of Days": no_of_days,
                    "Tariff": safe_float(tariff),
                    "Total Tariff": total_tariff,
                    "Advance Amount": safe_float(advance_amount),
                    "Balance Amount": balance_amount,
                    "Advance MOP": advance_mop,
                    "Balance MOP": balance_mop,
                    "MOB": mob,
                    "Invoice No": invoice_no,
                    "Enquiry Date": enquiry_date,
                    "Booking Date": booking_date,
                    "Booking ID": booking_id,
                    "Booking Source": booking_source,
                    "Room Type": room_type,
                    "Breakfast": breakfast,
                    "Plan Status": plan_status
                }
                
                # Add to session state
                st.session_state.reservations.append(reservation)
                
                st.success(f"✅ Reservation saved successfully! Booking ID: {booking_id}")
                st.balloons()
    
    # Display recent reservations for reference
    if st.session_state.reservations:
        st.markdown("---")
        st.subheader("📋 Recent Reservations")
        recent_df = pd.DataFrame(st.session_state.reservations[-5:])  # Show last 5 reservations
        st.dataframe(
            recent_df[["Booking ID", "Guest Name", "Mobile No", "Room No", "Check In", "Check Out", "Plan Status"]],
            use_container_width=True,
            hide_index=True
        )

def show_edit_reservations():
    st.header("✏️ Edit Reservations")
    
    if not st.session_state.reservations:
        st.info("No reservations found. Please add a new reservation from Direct Reservations.")
        return
    
    # Convert to DataFrame for display
    df = pd.DataFrame(st.session_state.reservations)
    
    # Search functionality
    search_term = st.text_input("🔍 Search by Booking ID, Guest Name, or Mobile No", placeholder="Enter search term")
    
    # Filter reservations based on search
    if search_term:
        filtered_indices = []
        for i, reservation in enumerate(st.session_state.reservations):
            if (search_term.lower() in reservation["Booking ID"].lower() or 
                search_term.lower() in reservation["Guest Name"].lower() or 
                search_term in reservation["Mobile No"]):
                filtered_indices.append(i)
    else:
        filtered_indices = list(range(len(st.session_state.reservations)))
    
    if not filtered_indices:
        st.info("No reservations match your search criteria.")
        return
    
    # Display reservations with edit buttons
    st.subheader("📋 Select Reservation to Edit")
    
    for idx in filtered_indices:
        reservation = st.session_state.reservations[idx]
        
        with st.expander(f"🏷️ {reservation['Booking ID']} - {reservation['Guest Name']} (Room: {reservation['Room No']})"):
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.write(f"**Check In:** {reservation['Check In']}")
                st.write(f"**Check Out:** {reservation['Check Out']}")
                st.write(f"**Mobile:** {reservation['Mobile No']}")
            
            with col2:
                st.write(f"**Total Tariff:** ₹{reservation['Total Tariff']:.2f}")
                st.write(f"**Balance:** ₹{reservation['Balance Amount']:.2f}")
                st.write(f"**Status:** {reservation['Plan Status']}")
            
            with col3:
                if st.button(f"✏️ Edit", key=f"edit_{idx}"):
                    st.session_state.edit_mode = True
                    st.session_state.edit_index = idx
                    st.rerun()
    
    # Edit form
    if st.session_state.edit_mode and st.session_state.edit_index is not None:
        show_edit_form(st.session_state.edit_index)

def show_edit_form(edit_index):
    st.markdown("---")
    st.subheader("✏️ Edit Reservation")
    
    # Get current reservation data
    current_reservation = st.session_state.reservations[edit_index]
    form_key = f"edit_{edit_index}"
    
    # Create columns for form layout
    col1, col2, col3 = st.columns(3)
    
    with col1:
        property_options = [
            "Eden Beach Resort",
            "La Paradise Luxury",
            "La Villa Heritage",
            "Le Pondy Beach Side",
            "Le Royce Villa",
            "Le Poshe Luxury",
            "Le Poshe Suite",
            "La Paradise Residency",
            "La Tamara Luxury",
            "Le Poshe Beachview",
            "La Antilia",
            "La Tamara Suite",
            "La Millionare Resort",
            "Le Park Resort"
        ]
        current_property = current_reservation["Property Name"]
        if current_property not in property_options:
            property_options.append(current_property)
        property_name = st.selectbox("Property Name", property_options, 
                                   index=property_options.index(current_property),
                                   key=f"{form_key}_property")
        room_no = st.text_input("Room No", value=current_reservation["Room No"],
                               key=f"{form_key}_room")
        guest_name = st.text_input("Guest Name", value=current_reservation["Guest Name"],
                                  key=f"{form_key}_guest")
        mobile_no = st.text_input("Mobile No", value=current_reservation["Mobile No"],
                                 key=f"{form_key}_mobile")
        
    with col2:
        adults = st.number_input("No of Adults", min_value=0, 
                                value=current_reservation["No of Adults"],
                                key=f"{form_key}_adults")
        children = st.number_input("No of Children", min_value=0, 
                                  value=current_reservation["No of Children"],
                                  key=f"{form_key}_children")
        infants = st.number_input("No of Infants", min_value=0, 
                                 value=current_reservation["No of Infants"],
                                 key=f"{form_key}_infants")
        
        # Real-time Total Pax calculation
        total_pax = safe_int(adults) + safe_int(children) + safe_int(infants)
        st.text_input("Total Pax", value=str(total_pax), disabled=True, 
                     help="Automatically calculated: Adults + Children + Infants")
        
    with col3:
        check_in = st.date_input("Check In", value=current_reservation["Check In"],
                                key=f"{form_key}_checkin")
        check_out = st.date_input("Check Out", value=current_reservation["Check Out"],
                                 key=f"{form_key}_checkout")
        
        # Real-time Days calculation
        no_of_days = calculate_days(check_in, check_out)
        st.text_input("No of Days", value=str(no_of_days), disabled=True, 
                     help="Automatically calculated: Check-out - Check-in dates")
        
        room_type_options = ["Double", "Triple", "Family", "1BHK", "2BHK", "3BHK", "4BHK", "Superior Villa"]
        current_room_type = current_reservation["Room Type"]
        if current_room_type not in room_type_options:
            room_type_options.append(current_room_type)
        room_type = st.selectbox("Room Type", room_type_options, 
                               index=room_type_options.index(current_room_type),
                               key=f"{form_key}_roomtype")
    
    col4, col5 = st.columns(2)
    
    with col4:
        tariff = st.number_input("Tariff (per day)", min_value=0.0, 
                                value=current_reservation["Tariff"], step=100.0,
                                key=f"{form_key}_tariff")
        
        # Real-time Total Tariff calculation
        total_tariff = safe_float(tariff) * max(0, no_of_days)
        st.text_input("Total Tariff", value=f"₹{total_tariff:.2f}", disabled=True, 
                     help="Automatically calculated: Tariff × No of Days")
        
        advance_mop_options = ["Cash", "Card", "UPI", "Bank Transfer", "Agoda", "MMT", "Airbnb", "Expedia", "Staflexi", "Website"]
        current_advance_mop = current_reservation["Advance MOP"]
        if current_advance_mop not in advance_mop_options:
            advance_mop_options.append(current_advance_mop)
        advance_mop = st.selectbox("Advance MOP", advance_mop_options, 
                                 index=advance_mop_options.index(current_advance_mop),
                                 key=f"{form_key}_advmop")
        
        balance_mop_options = ["Cash", "Card", "UPI", "Bank Transfer", "Agoda", "MMT", "Airbnb", "Expedia", "Stayflexi", "Website", "Pending"]
        current_balance_mop = current_reservation["Balance MOP"]
        if current_balance_mop not in balance_mop_options:
            balance_mop_options.append(current_balance_mop)
        balance_mop = st.selectbox("Balance MOP", balance_mop_options, 
                                 index=balance_mop_options.index(current_balance_mop),
                                 key=f"{form_key}_balmop")
        
    with col5:
        advance_amount = st.number_input("Advance Amount", min_value=0.0, 
                                        value=current_reservation["Advance Amount"], step=100.0,
                                        key=f"{form_key}_advance")
        
        # Real-time Balance Amount calculation
        balance_amount = max(0, total_tariff - safe_float(advance_amount))
        st.text_input("Balance Amount", value=f"₹{balance_amount:.2f}", disabled=True, 
                     help="Automatically calculated: Total Tariff - Advance Amount")
        
        mob = st.text_input("MOB (Mode of Booking)", value=current_reservation["MOB"],
                           key=f"{form_key}_mob")
        invoice_no = st.text_input("Invoice No", value=current_reservation["Invoice No"],
                                  key=f"{form_key}_invoice")
    
    col6, col7 = st.columns(2)
    
    with col6:
        enquiry_date = st.date_input("Enquiry Date", value=current_reservation["Enquiry Date"],
                                    key=f"{form_key}_enquiry")
        booking_date = st.date_input("Booking Date", value=current_reservation["Booking Date"],
                                    key=f"{form_key}_booking")
        booking_source_options = ["Direct", "Online", "Agent", "Walk-in", "Phone"]
        booking_source = st.selectbox("Booking Source", booking_source_options, 
                                    index=booking_source_options.index(current_reservation["Booking Source"]),
                                    key=f"{form_key}_source")
        
    with col7:
        breakfast_options = ["CP", "EP"]
        breakfast = st.selectbox("Breakfast", breakfast_options, 
                               index=breakfast_options.index(current_reservation["Breakfast"]),
                               key=f"{form_key}_breakfast")
        
        plan_status_options = ["Confirmed", "Pending", "Cancelled", "Completed", "No Show"]
        plan_status = st.selectbox("Plan Status", plan_status_options, 
                                 index=plan_status_options.index(current_reservation["Plan Status"]),
                                 key=f"{form_key}_status")
    
    # Form buttons
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("✅ Update Reservation", use_container_width=True, type="primary"):
            # Validation checks
            if not all([property_name, room_no, guest_name, mobile_no]):
                st.error("❌ Please fill in all required fields (Property Name, Room No, Guest Name, Mobile No)")
            elif check_out <= check_in:
                st.error("❌ Check-out date must be after check-in date")
            elif no_of_days <= 0:
                st.error("❌ Number of days must be greater than 0")
            else:
                # Check for duplicate guest (excluding current reservation)
                is_duplicate, existing_booking_id = check_duplicate_guest(guest_name, mobile_no, room_no, exclude_index=edit_index)
                
                if is_duplicate:
                    st.error(f"❌ Guest '{guest_name}' with mobile '{mobile_no}' in room '{room_no}' already exists! Existing Booking ID: {existing_booking_id}")
                else:
                    # Update reservation record with calculated values
                    updated_reservation = {
                        "Property Name": property_name,
                        "Room No": room_no,
                        "Guest Name": guest_name,
                        "Mobile No": mobile_no,
                        "No of Adults": safe_int(adults),
                        "No of Children": safe_int(children),
                        "No of Infants": safe_int(infants),
                        "Total Pax": total_pax,
                        "Check In": check_in,
                        "Check Out": check_out,
                        "No of Days": no_of_days,
                        "Tariff": safe_float(tariff),
                        "Total Tariff": total_tariff,
                        "Advance Amount": safe_float(advance_amount),
                        "Balance Amount": balance_amount,
                        "Advance MOP": advance_mop,
                        "Balance MOP": balance_mop,
                        "MOB": mob,
                        "Invoice No": invoice_no,
                        "Enquiry Date": enquiry_date,
                        "Booking Date": booking_date,
                        "Booking ID": current_reservation["Booking ID"],  # Keep original booking ID
                        "Booking Source": booking_source,
                        "Room Type": room_type,
                        "Breakfast": breakfast,
                        "Plan Status": plan_status
                    }
                    
                    # Update the reservation in session state
                    st.session_state.reservations[edit_index] = updated_reservation
                    
                    st.success(f"✅ Reservation updated successfully! Booking ID: {current_reservation['Booking ID']}")
                    st.balloons()
                    
                    # Reset edit mode
                    st.session_state.edit_mode = False
                    st.session_state.edit_index = None
                    st.rerun()
    
    with col_btn2:
        if st.button("❌ Cancel Edit", use_container_width=True):
            st.session_state.edit_mode = False
            st.session_state.edit_index = None
            st.rerun()

def show_reservations():
    st.header("📋 View Reservations")
    
    if not st.session_state.reservations:
        st.info("No reservations found. Please add a new reservation from Direct Reservations.")
        return
    
    # Convert to DataFrame for better display
    df = pd.DataFrame(st.session_state.reservations)
    
    # Search and filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_guest = st.text_input("🔍 Search by Guest Name", placeholder="Enter guest name")
    with col2:
        filter_status = st.selectbox("Filter by Status", ["All", "Confirmed", "Pending", "Cancelled", "Completed"])
    with col3:
        filter_property = st.selectbox("Filter by Property", ["All"] + list(df["Property Name"].unique()))
    
    # Apply filters
    filtered_df = df.copy()
    
    if search_guest:
        filtered_df = filtered_df[filtered_df["Guest Name"].str.contains(search_guest, case=False, na=False)]
    
    if filter_status != "All":
        filtered_df = filtered_df[filtered_df["Plan Status"] == filter_status]
    
    if filter_property != "All":
        filtered_df = filtered_df[filtered_df["Property Name"] == filter_property]
    
    # Display statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Reservations", len(filtered_df))
    with col2:
        st.metric("Total Revenue", f"₹{filtered_df['Total Tariff'].sum():,.2f}")
    with col3:
        st.metric("Average Tariff", f"₹{df['Tariff'].mean():,.2f}")
    with col4:
        st.metric("Average Stay", f"{df['No of Days'].mean():.1f} days")
    
    st.markdown("---")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Booking Status Distribution
        status_counts = df['Plan Status'].value_counts()
        fig_status = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="Booking Status Distribution"
        )
        st.plotly_chart(fig_status, use_container_width=True)
        
        # Room Type Distribution
        room_counts = df['Room Type'].value_counts()
        fig_room = px.bar(
            x=room_counts.index,
            y=room_counts.values,
            title="Room Type Distribution"
        )
        st.plotly_chart(fig_room, use_container_width=True)
    
    with col2:
        # Booking Source Distribution
        source_counts = df['Booking Source'].value_counts()
        fig_source = px.pie(
            values=source_counts.values,
            names=source_counts.index,
            title="Booking Source Distribution"
        )
        st.plotly_chart(fig_source, use_container_width=True)
        
        # Revenue by Property
        property_revenue = df.groupby('Property Name')['Total Tariff'].sum()
        fig_revenue = px.bar(
            x=property_revenue.index,
            y=property_revenue.values,
            title="Revenue by Property"
        )
        st.plotly_chart(fig_revenue, use_container_width=True)
    
    # Monthly booking trends (if date range is available)
    if len(df) > 0:
        df['Booking Month'] = pd.to_datetime(df['Booking Date']).dt.to_period('M')
        monthly_bookings = df.groupby('Booking Month').size()
        
        if len(monthly_bookings) > 1:
            fig_trend = px.line(
                x=monthly_bookings.index.astype(str),
                y=monthly_bookings.values,
                title="Monthly Booking Trends"
            )
            st.plotly_chart(fig_trend, use_container_width=True)

if __name__ == "__main__":
    main()Advance Collected", f"₹{filtered_df['Advance Amount'].sum():,.2f}")
    with col4:
        st.metric("Balance Pending", f"₹{filtered_df['Balance Amount'].sum():,.2f}")
    
    st.markdown("---")
    
    # Display reservations
    if not filtered_df.empty:
        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Check In": st.column_config.DateColumn("Check In"),
                "Check Out": st.column_config.DateColumn("Check Out"),
                "Total Tariff": st.column_config.NumberColumn("Total Tariff", format="₹%.2f"),
                "Advance Amount": st.column_config.NumberColumn("Advance Amount", format="₹%.2f"),
                "Balance Amount": st.column_config.NumberColumn("Balance Amount", format="₹%.2f"),
            }
        )
        
        # Download CSV
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name=f"reservations_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No reservations match your search criteria.")
def show_analytics():
    st.header("📊 Analytics Dashboard")
    
    if not st.session_state.reservations:
        st.info("No data available for analytics. Please add some reservations.")
        return
    
    df = pd.DataFrame(st.session_state.reservations)
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Bookings", len(df))
    with col2:
        st.metric("Total Revenue", f"₹{df['Total Tariff'].sum():,.2f}")
    with col3:
        st.metric("Average Tariff", f"₹{df['Tariff'].mean():,.2f}")
    with col4:
        st.metric("Average Stay", f"{df['No of Days'].mean():.1f} days")
    
    st.markdown("---")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Booking Status Distribution
        status_counts = df['Plan Status'].value_counts()
        fig_status = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="Booking Status Distribution"
        )
        st.plotly_chart(fig_status, use_container_width=True)
        
        # Room Type Distribution
        room_counts = df['Room Type'].value_counts()
        fig_room = px.bar(
            x=room_counts.index,
            y=room_counts.values,
            title="Room Type Distribution"
        )
        st.plotly_chart(fig_room, use_container_width=True)
    
    with col2:
        # Booking Source Distribution
        source_counts = df['Booking Source'].value_counts()
        fig_source = px.pie(
            values=source_counts.values,
            names=source_counts.index,
            title="Booking Source Distribution"
        )
        st.plotly_chart(fig_source, use_container_width=True)
        
        # Revenue by Property
        property_revenue = df.groupby('Property Name')['Total Tariff'].sum()
        fig_revenue = px.bar(
            x=property_revenue.index,
            y=property_revenue.values,
            title="Revenue by Property"
        )
        st.plotly_chart(fig_revenue, use_container_width=True)
    
    # Monthly booking trends (if date range is available)
    if len(df) > 0:
        df['Booking Month'] = pd.to_datetime(df['Booking Date']).dt.to_period('M')
        monthly_bookings = df.groupby('Booking Month').size()
        
        if len(monthly_bookings) > 1:
            fig_trend = px.line(
                x=monthly_bookings.index.astype(str),
                y=monthly_bookings.values,
                title="Monthly Booking Trends"
            )
            st.plotly_chart(fig_trend, use_container_width=True)

if __name__ == "__main__":
    main()
