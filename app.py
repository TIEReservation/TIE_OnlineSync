import streamlit as st

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

# Import other libraries after authentication
import pandas as pd
from datetime import datetime, date, timedelta
import plotly.express as px
import plotly.graph_objects as go

# Page config
st.set_page_config(
    page_title="TIE Reservation System",
    page_icon="🏢",
    layout="wide"
)

# Initialize session state for reservations
if 'reservations' not in st.session_state:
    st.session_state.reservations = []

# Sample data for demonstration
if 'sample_data_loaded' not in st.session_state:
    st.session_state.reservations = [
        {
            'id': 1,
            'name': 'John Doe',
            'email': 'john@example.com',
            'room': 'Conference Room A',
            'date': date(2024, 1, 15),
            'start_time': '09:00',
            'end_time': '11:00',
            'purpose': 'Team Meeting',
            'status': 'Confirmed'
        },
        {
            'id': 2,
            'name': 'Jane Smith',
            'email': 'jane@example.com',
            'room': 'Conference Room B',
            'date': date(2024, 1, 16),
            'start_time': '14:00',
            'end_time': '16:00',
            'purpose': 'Client Presentation',
            'status': 'Confirmed'
        }
    ]
    st.session_state.sample_data_loaded = True

# Available rooms
ROOMS = [
    'Conference Room A',
    'Conference Room B',
    'Meeting Room 1',
    'Meeting Room 2',
    'Board Room',
    'Training Room',
    'Video Conference Room'
]

# Time slots
TIME_SLOTS = [
    '08:00', '08:30', '09:00', '09:30', '10:00', '10:30', '11:00', '11:30',
    '12:00', '12:30', '13:00', '13:30', '14:00', '14:30', '15:00', '15:30',
    '16:00', '16:30', '17:00', '17:30', '18:00', '18:30', '19:00', '19:30', '20:00'
]

def main():
    st.title("🏢 TIE Reservation System")
    st.write("Welcome to the TIE Organization Room Reservation System")
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Make Reservation", "View Reservations", "Dashboard", "Settings"])
    
    if page == "Make Reservation":
        make_reservation_page()
    elif page == "View Reservations":
        view_reservations_page()
    elif page == "Dashboard":
        dashboard_page()
    elif page == "Settings":
        settings_page()

def make_reservation_page():
    st.header("📅 Make a New Reservation")
    
    with st.form("reservation_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Full Name *", placeholder="Enter your full name")
            email = st.text_input("Email *", placeholder="Enter your email address")
            room = st.selectbox("Select Room *", ROOMS)
            reservation_date = st.date_input("Date *", min_value=date.today())
        
        with col2:
            start_time = st.selectbox("Start Time *", TIME_SLOTS)
            end_time = st.selectbox("End Time *", TIME_SLOTS)
            purpose = st.text_area("Purpose of Meeting *", placeholder="Brief description of the meeting")
            priority = st.selectbox("Priority", ["Normal", "High", "Urgent"])
        
        submitted = st.form_submit_button("Submit Reservation")
        
        if submitted:
            # Validation
            if not name or not email or not purpose:
                st.error("Please fill in all required fields marked with *")
            elif start_time >= end_time:
                st.error("End time must be after start time")
            else:
                # Check for conflicts
                conflict = check_room_conflict(room, reservation_date, start_time, end_time)
                if conflict:
                    st.error(f"Room {room} is already booked from {conflict['start_time']} to {conflict['end_time']} on {conflict['date']}")
                else:
                    # Add reservation
                    new_reservation = {
                        'id': len(st.session_state.reservations) + 1,
                        'name': name,
                        'email': email,
                        'room': room,
                        'date': reservation_date,
                        'start_time': start_time,
                        'end_time': end_time,
                        'purpose': purpose,
                        'priority': priority,
                        'status': 'Confirmed',
                        'created_at': datetime.now()
                    }
                    st.session_state.reservations.append(new_reservation)
                    st.success("✅ Reservation created successfully!")
                    st.balloons()

def check_room_conflict(room, date, start_time, end_time):
    for reservation in st.session_state.reservations:
        if (reservation['room'] == room and 
            reservation['date'] == date and
            reservation['status'] == 'Confirmed'):
            # Check time overlap
            if (start_time < reservation['end_time'] and end_time > reservation['start_time']):
                return reservation
    return None

def view_reservations_page():
    st.header("📋 View Reservations")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_room = st.selectbox("Filter by Room", ["All"] + ROOMS)
    with col2:
        filter_date = st.date_input("Filter by Date", value=None)
    with col3:
        filter_status = st.selectbox("Filter by Status", ["All", "Confirmed", "Cancelled", "Pending"])
    
    # Filter reservations
    filtered_reservations = st.session_state.reservations.copy()
    
    if filter_room != "All":
        filtered_reservations = [r for r in filtered_reservations if r['room'] == filter_room]
    
    if filter_date:
        filtered_reservations = [r for r in filtered_reservations if r['date'] == filter_date]
    
    if filter_status != "All":
        filtered_reservations = [r for r in filtered_reservations if r['status'] == filter_status]
    
    # Display reservations
    if filtered_reservations:
        for reservation in filtered_reservations:
            with st.expander(f"🏠 {reservation['room']} - {reservation['date']} ({reservation['start_time']} - {reservation['end_time']})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Name:** {reservation['name']}")
                    st.write(f"**Email:** {reservation['email']}")
                    st.write(f"**Purpose:** {reservation['purpose']}")
                
                with col2:
                    st.write(f"**Status:** {reservation['status']}")
                    st.write(f"**Priority:** {reservation.get('priority', 'Normal')}")
                    
                    # Action buttons
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button(f"Cancel", key=f"cancel_{reservation['id']}"):
                            cancel_reservation(reservation['id'])
                    with col_btn2:
                        if st.button(f"Edit", key=f"edit_{reservation['id']}"):
                            st.info("Edit functionality coming soon!")
    else:
        st.info("No reservations found matching the selected filters.")

def cancel_reservation(reservation_id):
    for reservation in st.session_state.reservations:
        if reservation['id'] == reservation_id:
            reservation['status'] = 'Cancelled'
            st.success("Reservation cancelled successfully!")
            st.rerun()

def dashboard_page():
    st.header("📊 Dashboard")
    
    # Statistics
    total_reservations = len(st.session_state.reservations)
    confirmed_reservations = len([r for r in st.session_state.reservations if r['status'] == 'Confirmed'])
    cancelled_reservations = len([r for r in st.session_state.reservations if r['status'] == 'Cancelled'])
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Reservations", total_reservations)
    with col2:
        st.metric("Confirmed", confirmed_reservations)
    with col3:
        st.metric("Cancelled", cancelled_reservations)
    with col4:
        st.metric("Active Rooms", len(ROOMS))
    
    # Charts
    if st.session_state.reservations:
        # Room usage chart
        room_usage = {}
        for reservation in st.session_state.reservations:
            if reservation['status'] == 'Confirmed':
                room = reservation['room']
                room_usage[room] = room_usage.get(room, 0) + 1
        
        if room_usage:
            fig_room = px.bar(
                x=list(room_usage.keys()),
                y=list(room_usage.values()),
                title="Room Usage Statistics",
                labels={'x': 'Room', 'y': 'Number of Reservations'}
            )
            st.plotly_chart(fig_room, use_container_width=True)
        
        # Weekly overview
        today = date.today()
        week_dates = [today + timedelta(days=i) for i in range(7)]
        daily_reservations = {}
        
        for d in week_dates:
            count = len([r for r in st.session_state.reservations 
                        if r['date'] == d and r['status'] == 'Confirmed'])
            daily_reservations[d.strftime('%Y-%m-%d')] = count
        
        fig_weekly = px.line(
            x=list(daily_reservations.keys()),
            y=list(daily_reservations.values()),
            title="Weekly Reservation Overview",
            labels={'x': 'Date', 'y': 'Number of Reservations'}
        )
        st.plotly_chart(fig_weekly, use_container_width=True)
    
    # Recent reservations
    st.subheader("Recent Reservations")
    recent_reservations = sorted(st.session_state.reservations, 
                               key=lambda x: x.get('created_at', datetime.now()), 
                               reverse=True)[:5]
    
    for reservation in recent_reservations:
        st.write(f"• **{reservation['name']}** - {reservation['room']} on {reservation['date']} ({reservation['status']})")

def settings_page():
    st.header("⚙️ Settings")
    
    st.subheader("System Configuration")
    
    # Room management
    st.write("**Room Management**")
    new_room = st.text_input("Add New Room")
    if st.button("Add Room"):
        if new_room and new_room not in ROOMS:
            ROOMS.append(new_room)
            st.success(f"Room '{new_room}' added successfully!")
        else:
            st.error("Room already exists or invalid name")
    
    # Current rooms
    st.write("**Current Rooms:**")
    for room in ROOMS:
        st.write(f"• {room}")
    
    # Data management
    st.subheader("Data Management")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Export Reservations"):
            if st.session_state.reservations:
                df = pd.DataFrame(st.session_state.reservations)
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"reservations_{date.today()}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No reservations to export")
    
    with col2:
        if st.button("Clear All Data"):
            st.session_state.reservations = []
            st.success("All reservation data cleared!")
    
    # System info
    st.subheader("System Information")
    st.write(f"**Total Reservations:** {len(st.session_state.reservations)}")
    st.write(f"**Available Rooms:** {len(ROOMS)}")
    st.write(f"**System Date:** {date.today()}")

if __name__ == "__main__":
    main()
