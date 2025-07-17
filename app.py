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

# Define user roles and permissions
USER_CREDENTIALS = {
    # Property-specific logins
    "eden_beach": {
        "password": "eden2024",
        "role": "property",
        "property_access": ["Eden Beach Resort"],
        "name": "Eden Beach Resort"
    },
    "la_paradise_luxury": {
        "password": "paradise2024",
        "role": "property",
        "property_access": ["La Paradise Luxury"],
        "name": "La Paradise Luxury"
    },
    "la_villa": {
        "password": "villa2024",
        "role": "property",
        "property_access": ["La Villa Heritage"],
        "name": "La Villa Heritage"
    },
    "le_pondy": {
        "password": "pondy2024",
        "role": "property",
        "property_access": ["Le Pondy Beach Side"],
        "name": "Le Pondy Beach Side"
    },
    "le_royce": {
        "password": "royce2024",
        "role": "property",
        "property_access": ["Le Royce Villa"],
        "name": "Le Royce Villa"
    },
    "le_poshe_luxury": {
        "password": "poshelux2024",
        "role": "property",
        "property_access": ["Le Poshe Luxury"],
        "name": "Le Poshe Luxury"
    },
    "le_poshe_suite": {
        "password": "poshesuite2024",
        "role": "property",
        "property_access": ["Le Poshe Suite"],
        "name": "Le Poshe Suite"
    },
    "la_paradise_residency": {
        "password": "residency2024",
        "role": "property",
        "property_access": ["La Paradise Residency"],
        "name": "La Paradise Residency"
    },
    "la_tamara_luxury": {
        "password": "tamaralux2024",
        "role": "property",
        "property_access": ["La Tamara Luxury"],
        "name": "La Tamara Luxury"
    },
    "le_poshe_beachview": {
        "password": "poshebeach2024",
        "role": "property",
        "property_access": ["Le Poshe Beachview"],
        "name": "Le Poshe Beachview"
    },
    "la_antilia": {
        "password": "antilia2024",
        "role": "property",
        "property_access": ["La Antilia"],
        "name": "La Antilia"
    },
    "la_tamara_suite": {
        "password": "tamarasuite2024",
        "role": "property",
        "property_access": ["La Tamara Suite"],
        "name": "La Tamara Suite"
    },
    "la_millionare": {
        "password": "millionare2024",
        "role": "property",
        "property_access": ["La Millionare Resort"],
        "name": "La Millionare Resort"
    },
    "le_park": {
        "password": "park2024",
        "role": "property",
        "property_access": ["Le Park Resort"],
        "name": "Le Park Resort"
    },
    
    # Management logins with full access
    "reservation_team": {
        "password": "reservations2024",
        "role": "reservation_team",
        "property_access": "all",
        "name": "Reservation Team"
    },
    "ceo": {
        "password": "ceo2024",
        "role": "ceo",
        "property_access": "all",
        "name": "CEO"
    },
    "md": {
        "password": "md2024",
        "role": "md",
        "property_access": "all",
        "name": "Managing Director"
    },
    "gm": {
        "password": "gm2024",
        "role": "gm",
        "property_access": "all",
        "name": "General Manager"
    }
}

ALL_PROPERTIES = [
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

def check_authentication():
    # Initialize authentication state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.user_role = None
        st.session_state.user_name = None
        st.session_state.property_access = None
        
    # If not authenticated, show login page
    if not st.session_state.authenticated:
        st.title("🔐 TIE Reservation System - Login")
        st.write("Please enter your credentials to access the system.")
        
        # Create login form
        with st.form("login_form"):
            username = st.text_input("Username:", placeholder="Enter your username")
            password = st.text_input("Password:", type="password", placeholder="Enter your password")
            
            login_button = st.form_submit_button("🔑 Login", use_container_width=True)
            
            if login_button:
                if username in USER_CREDENTIALS and USER_CREDENTIALS[username]["password"] == password:
                    user_info = USER_CREDENTIALS[username]
                    st.session_state.authenticated = True
                    st.session_state.user_role = user_info["role"]
                    st.session_state.user_name = user_info["name"]
                    st.session_state.property_access = user_info["property_access"]
                    st.success(f"✅ Welcome {user_info['name']}! Redirecting...")
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password. Please try again.")
        
        # Show login instructions
        with st.expander("📋 Login Instructions"):
            st.write("**Property Logins:**")
            st.write("- Each property has its own username and password")
            st.write("- Property users can only access their own property data")
            st.write("")
            st.write("**Management Logins:**")
            st.write("- **reservation_team**: Access to all properties")
            st.write("- **ceo**: Full access to all properties")
            st.write("- **md**: Full access to all properties")
            st.write("- **gm**: Full access to all properties")
        
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

# Helper function to get accessible properties
def get_accessible_properties():
    if st.session_state.property_access == "all":
        return ALL_PROPERTIES
    else:
        return st.session_state.property_access

# Helper function to filter reservations by access
def filter_reservations_by_access(reservations):
    if st.session_state.property_access == "all":
        return reservations
    else:
        return [r for r in reservations if r["Property Name"] in st.session_state.property_access]

# Helper function to generate booking ID
def generate_booking_id():
    return f"TIE{datetime.now().strftime('%Y%m%d')}{len(st.session_state.reservations) + 1:03d}"

# Helper function to check if guest already exists (excluding current edit)
def check_duplicate_guest(guest_name, mobile_no, room_no, exclude_index=None):
    accessible_reservations = filter_reservations_by_access(st.session_state.reservations)
    for i, reservation in enumerate(st.session_state.reservations):
        if exclude_index is not None and i == exclude_index:
            continue
        if reservation not in accessible_reservations:
            continue
        if (reservation["Guest Name"].lower() == guest_name.lower() and 
            reservation["Mobile No"] == mobile_no and 
            reservation["Room No"] == room_no):
            return True, reservation["Booking ID"]
    return False, None

# Helper function to calculate days between dates (calendar days)
def calculate_days(check_in, check_out):
    if check_in and check_out:
        # Calculate the difference in calendar days
        delta = check_out - check_in
        return delta.days
    return 0

# Main App
def main():
    # Display header with user info
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.title("🏢 TIE Reservation System")
    
    with col2:
        st.write(f"**User:** {st.session_state.user_name}")
        st.write(f"**Role:** {st.session_state.user_role.replace('_', ' ').title()}")
    
    with col3:
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_role = None
            st.session_state.user_name = None
            st.session_state.property_access = None
            st.rerun()
    
    st.markdown("---")
    
    # Show accessible properties
    accessible_properties = get_accessible_properties()
    if st.session_state.property_access != "all":
        st.info(f"🏨 You have access to: {', '.join(accessible_properties)}")
    else:
        st.info("🏨 You have access to all properties")
    
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
    
    # Get accessible properties for dropdown
    accessible_properties = get_accessible_properties()
    
    # Initialize form submission state
    if 'form_submitted' not in st.session_state:
        st.session_state.form_submitted = False
    
    with st.form("reservation_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Property dropdown based on user access
            if len(accessible_properties) == 1:
                property_name = st.selectbox("Property Name", accessible_properties, disabled=True)
            else:
                property_name = st.selectbox("Property Name", accessible_properties, placeholder="Select property")
            
            room_no = st.text_input("Room No", placeholder="e.g., 101, 202")
            guest_name = st.text_input("Guest Name", placeholder="Enter guest name")
            mobile_no = st.text_input("Mobile No", placeholder="Enter mobile number")
            
        with col2:
            adults = st.number_input("No of Adults", min_value=0, value=1)
            children = st.number_input("No of Children", min_value=0, value=0)
            infants = st.number_input("No of Infants", min_value=0, value=0)
            total_pax = adults + children + infants
            st.text_input("Total Pax", value=str(total_pax), disabled=True)
            
        with col3:
            check_in = st.date_input("Check In", value=date.today())
            check_out = st.date_input("Check Out", value=date.today() + timedelta(days=1))
            no_of_days = calculate_days(check_in, check_out)
            st.text_input("No of Days", value=str(max(0, no_of_days)), disabled=True)
            room_type = st.selectbox("Room Type", ["Standard", "Deluxe", "Suite", "Presidential"])
        
        col4, col5 = st.columns(2)
        
        with col4:
            tariff = st.number_input("Tariff (per day)", min_value=0.0, value=0.0, step=100.0)
            total_tariff = tariff * max(0, no_of_days)
            st.text_input("Total Tariff", value=f"₹{total_tariff:.2f}", disabled=True)
            advance_mop = st.selectbox("Advance MOP", ["Cash", "Card", "UPI", "Bank Transfer", "Online"])
            balance_mop = st.selectbox("Balance MOP", ["Cash", "Card", "UPI", "Bank Transfer", "Online", "Pending"])
            
        with col5:
            advance_amount = st.number_input("Advance Amount", min_value=0.0, value=0.0, step=100.0)
            balance_amount = max(0, total_tariff - advance_amount)
            st.text_input("Balance Amount", value=f"₹{balance_amount:.2f}", disabled=True)
            mob = st.text_input("MOB (Mode of Booking)", placeholder="e.g., Phone, Walk-in, Online")
            invoice_no = st.text_input("Invoice No", placeholder="Enter invoice number")
        
        col6, col7 = st.columns(2)
        
        with col6:
            enquiry_date = st.date_input("Enquiry Date", value=date.today())
            booking_date = st.date_input("Booking Date", value=date.today())
            booking_source = st.selectbox("Booking Source", ["Direct", "Online", "Agent", "Walk-in", "Phone"])
            
        with col7:
            breakfast = st.selectbox("Breakfast", ["Included", "Not Included", "Paid"])
            plan_status = st.selectbox("Plan Status", ["Confirmed", "Pending", "Cancelled", "Completed"])
        
        # Form submission button
        submitted = st.form_submit_button("💾 Save Reservation", use_container_width=True)
        
        if submitted:
            # Reset form submission state
            st.session_state.form_submitted = True
            
            # Validation checks
            if not all([property_name, room_no, guest_name, mobile_no]):
                st.error("❌ Please fill in all required fields (Property Name, Room No, Guest Name, Mobile No)")
                st.session_state.form_submitted = False
            elif check_out <= check_in:
                st.error("❌ Check-out date must be after check-in date")
                st.session_state.form_submitted = False
            elif property_name not in accessible_properties:
                st.error("❌ You don't have access to this property")
                st.session_state.form_submitted = False
            else:
                # Check for duplicate guest
                is_duplicate, existing_booking_id = check_duplicate_guest(guest_name, mobile_no, room_no)
                
                if is_duplicate:
                    st.error(f"❌ Guest '{guest_name}' with mobile '{mobile_no}' in room '{room_no}' already exists! Existing Booking ID: {existing_booking_id}")
                    st.session_state.form_submitted = False
                else:
                    # Generate booking ID
                    booking_id = generate_booking_id()
                    
                    # Calculate final values
                    no_of_days = calculate_days(check_in, check_out)
                    total_tariff = tariff * max(0, no_of_days)
                    balance_amount = max(0, total_tariff - advance_amount)
                    
                    # Create reservation record
                    reservation = {
                        "Property Name": property_name,
                        "Room No": room_no,
                        "Guest Name": guest_name,
                        "Mobile No": mobile_no,
                        "No of Adults": adults,
                        "No of Children": children,
                        "No of Infants": infants,
                        "Total Pax": total_pax,
                        "Check In": check_in,
                        "Check Out": check_out,
                        "No of Days": no_of_days,
                        "Tariff": tariff,
                        "Total Tariff": total_tariff,
                        "Advance Amount": advance_amount,
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
                        "Plan Status": plan_status,
                        "Created By": st.session_state.user_name,
                        "Created At": datetime.now()
                    }
                    
                    # Add to session state
                    st.session_state.reservations.append(reservation)
                    
                    st.success(f"✅ Reservation saved successfully! Booking ID: {booking_id}")
                    st.balloons()
                    
                    # Reset form submission state after successful save
                    st.session_state.form_submitted = False
    
    # Display recent reservations for reference (filtered by access)
    accessible_reservations = filter_reservations_by_access(st.session_state.reservations)
    if accessible_reservations:
        st.markdown("---")
        st.subheader("📋 Recent Reservations")
        recent_df = pd.DataFrame(accessible_reservations[-5:])  # Show last 5 accessible reservations
        st.dataframe(
            recent_df[["Booking ID", "Property Name", "Guest Name", "Mobile No", "Room No", "Check In", "Check Out", "Plan Status"]],
            use_container_width=True,
            hide_index=True
        )

def show_edit_reservations():
    st.header("✏️ Edit Reservations")
    
    # Filter reservations by access
    accessible_reservations = filter_reservations_by_access(st.session_state.reservations)
    
    if not accessible_reservations:
        st.info("No reservations found for your accessible properties.")
        return
    
    # Search functionality
    search_term = st.text_input("🔍 Search by Booking ID, Guest Name, or Mobile No", placeholder="Enter search term")
    
    # Filter reservations based on search
    if search_term:
        filtered_reservations = []
        for reservation in accessible_reservations:
            if (search_term.lower() in reservation["Booking ID"].lower() or 
                search_term.lower() in reservation["Guest Name"].lower() or 
                search_term in reservation["Mobile No"]):
                filtered_reservations.append(reservation)
    else:
        filtered_reservations = accessible_reservations
    
    if not filtered_reservations:
        st.info("No reservations match your search criteria.")
        return
    
    # Display reservations with edit buttons
    st.subheader("📋 Select Reservation to Edit")
    
    for reservation in filtered_reservations:
        # Find the original index in the full reservations list
        original_index = st.session_state.reservations.index(reservation)
        
        with st.expander(f"🏷️ {reservation['Booking ID']} - {reservation['Guest Name']} ({reservation['Property Name']} - Room: {reservation['Room No']})"):
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
                if st.button(f"✏️ Edit", key=f"edit_{original_index}"):
                    st.session_state.edit_mode = True
                    st.session_state.edit_index = original_index
                    st.rerun()
    
    # Edit form
    if st.session_state.edit_mode and st.session_state.edit_index is not None:
        show_edit_form(st.session_state.edit_index)

def show_edit_form(edit_index):
    st.markdown("---")
    st.subheader("✏️ Edit Reservation")
    
    # Get current reservation data
    current_reservation = st.session_state.reservations[edit_index]
    
    # Check if user has access to this property
    accessible_properties = get_accessible_properties()
    if current_reservation["Property Name"] not in accessible_properties:
        st.error("❌ You don't have access to edit this reservation.")
        st.session_state.edit_mode = False
        st.session_state.edit_index = None
        return
    
    with st.form("edit_reservation_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Property dropdown based on user access
            if len(accessible_properties) == 1:
                property_name = st.selectbox("Property Name", accessible_properties, 
                                           index=accessible_properties.index(current_reservation["Property Name"]),
                                           disabled=True)
            else:
                property_name = st.selectbox("Property Name", accessible_properties, 
                                           index=accessible_properties.index(current_reservation["Property Name"]))
            
            room_no = st.text_input("Room No", value=current_reservation["Room No"])
            guest_name = st.text_input("Guest Name", value=current_reservation["Guest Name"])
            mobile_no = st.text_input("Mobile No", value=current_reservation["Mobile No"])
            
        with col2:
            adults = st.number_input("No of Adults", min_value=0, value=current_reservation["No of Adults"])
            children = st.number_input("No of Children", min_value=0, value=current_reservation["No of Children"])
            infants = st.number_input("No of Infants", min_value=0, value=current_reservation["No of Infants"])
            total_pax = adults + children + infants
            st.text_input("Total Pax", value=str(total_pax), disabled=True)
            
        with col3:
            check_in = st.date_input("Check In", value=current_reservation["Check In"])
            check_out = st.date_input("Check Out", value=current_reservation["Check Out"])
            no_of_days = calculate_days(check_in, check_out)
            st.text_input("No of Days", value=str(max(0, no_of_days)), disabled=True)
            room_type = st.selectbox("Room Type", ["Standard", "Deluxe", "Suite", "Presidential"], 
                                   index=["Standard", "Deluxe", "Suite", "Presidential"].index(current_reservation["Room Type"]))
        
        col4, col5 = st.columns(2)
        
        with col4:
            tariff = st.number_input("Tariff (per day)", min_value=0.0, value=current_reservation["Tariff"], step=100.0)
            total_tariff = tariff * max(0, no_of_days)
            st.text_input("Total Tariff", value=f"₹{total_tariff:.2f}", disabled=True)
            advance_mop_options = ["Cash", "Card", "UPI", "Bank Transfer", "Online"]
            advance_mop = st.selectbox("Advance MOP", advance_mop_options, 
                                     index=advance_mop_options.index(current_reservation["Advance MOP"]))
            balance_mop_options = ["Cash", "Card", "UPI", "Bank Transfer", "Online", "Pending"]
            balance_mop = st.selectbox("Balance MOP", balance_mop_options, 
                                     index=balance_mop_options.index(current_reservation["Balance MOP"]))
            
        with col5:
            advance_amount = st.number_input("Advance Amount", min_value=0.0, value=current_reservation["Advance Amount"], step=100.0)
            balance_amount = max(0, total_tariff - advance_amount)
            st.text_input("Balance Amount", value=f"₹{balance_amount:.2f}", disabled=True)
            mob = st.text_input("MOB (Mode of Booking)", value=current_reservation["MOB"])
            invoice_no = st.text_input("Invoice No", value=current_reservation["Invoice No"])
        
        col6, col7 = st.columns(2)
        
        with col6:
            enquiry_date = st.date_input("Enquiry Date", value=current_reservation["Enquiry Date"])
            booking_date = st.date_input("Booking Date", value=current_reservation["Booking Date"])
            booking_source_options = ["Direct", "Online", "Agent", "Walk-in", "Phone"]
            booking_source = st.selectbox("Booking Source", booking_source_options, 
                                        index=booking_source_options.index(current_reservation["Booking Source"]))
            
        with col7:
            breakfast_options = ["Included", "Not Included", "Paid"]
            breakfast = st.selectbox("Breakfast", breakfast_options, 
                                   index=breakfast_options.index(current_reservation["Breakfast"]))
            plan_status_options = ["Confirmed", "Pending", "Cancelled", "Completed"]
            plan_status = st.selectbox("Plan Status", plan_status_options, 
                                     index=plan_status_options.index(current_reservation["Plan Status"]))
        
        # Form buttons
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            update_submitted = st.form_submit_button("✅ Update Reservation", use_container_width=True, type="primary")
        
        with col_btn2:
            cancel_edit = st.form_submit_button("❌ Cancel Edit", use_container_width=True)
        
        if cancel_edit:
            st.session_state.edit_mode = False
            st.session_state.edit_index = None
            st.rerun()
        
        if update_submitted:
            # Validation checks
            if not all([property_name, room_no, guest_name, mobile_no]):
                st.error("❌ Please fill in all required fields (Property Name, Room No, Guest Name, Mobile No)")
            elif check_out <= check_in:
                st.error("❌ Check-out date must be after check-in date")
            elif property_name not in accessible_properties:
                st.error("❌ You don't have access to this property")
            else:
                # Check for duplicate guest (excluding current reservation)
                is_duplicate, existing_booking_id = check_duplicate_guest(guest_name, mobile_no, room_no, exclude_index=edit_index)
                
                if is_duplicate:
                    st.error(f"❌ Guest '{guest_name}' with mobile '{mobile_no}' in room '{room_no}' already exists! Existing Booking ID: {existing_booking_id}")
                else:
                    # Calculate final values
                    no_of_days = calculate_days(check_in, check_out)
                    total_tariff = tariff * max(0, no_of_days)
                    balance_amount = max(0, total_tariff - advance_amount)
                    
                    # Update reservation record
                    updated_reservation = {
                        "Property Name": property_name,
                        "Room No": room_no,
                        "Guest Name": guest_name,
                        "Mobile No": mobile_no,
                        "No of Adults": adults,
                        "No of Children": children,
                        "No of Infants": infants,
                        "Total Pax": total_pax,
                        "Check In": check_in,
                        "Check Out": check_out,
                        "No of Days": no_of_days,
                        "Tariff": tariff,
                        "Total Tariff": total_tariff,
                        "Advance Amount": advance_amount,
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
                        "Plan Status": plan_status,
                        "Created By": current_reservation.get("Created By", "Unknown"),
                        "Created At": current_reservation.get("Created At", datetime.now()),
                        "Updated By": st.session_state.user_name,
                        "Updated At": datetime.now()
                    }
                    
                    # Update the reservation in session state
                    st.session_state.reservations[edit_index] = updated_reservation
                    
                    st.success(f"✅ Reservation updated successfully! Booking ID: {current_reservation['Booking ID']}")
                    st.balloons()
                    
                    # Reset edit mode
                    st.session_state.edit_mode = False
                    st.session_state.edit_index = None
                    st.rerun()

def show_reservations():
    st.header("📋 View Reservations")
    
    # Filter reservations by access
    accessible_reservations = filter_reservations_by_access(st.session_state.reservations)
    
    if not accessible_reservations:
        st.info("No reservations found for your accessible properties.")
        return
    
    # Convert to DataFrame for better display
    df = pd.DataFrame(accessible_reservations)
    
    # Search and filter options
    col1, col2, col3 = st
