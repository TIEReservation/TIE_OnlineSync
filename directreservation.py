import streamlit as st
from supabase import create_client, Client
from directreservation import show_new_reservation_form, show_reservations, show_edit_reservations, show_analytics
from online_reservation import show_online_reservations
from editOnline import show_edit_online_reservations
from inventory import show_daily_status

# Initialize Supabase client
try:
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except KeyError as e:
    st.error(f"Missing Supabase secret: {e}. Please check Streamlit Cloud secrets configuration.")
    st.stop()

def main():
    """Main function to handle page navigation."""
    st.set_page_config(page_title="Hotel Reservation System", layout="wide")
    
    # Initialize session state for role if not set
    if 'role' not in st.session_state:
        st.session_state.role = "Staff"  # Default role; replace with actual authentication logic
    
    # Sidebar for page navigation
    page = st.sidebar.selectbox(
        "Select Page",
        ["Daily Status", "Online Reservations", "Edit Online Reservations", 
         "Direct Reservations", "View Reservations", "Edit Reservations", "Analytics"]
    )
    
    # Store current page in session state
    st.session_state.current_page = page
    
    # Route to appropriate page
    if page == "Daily Status":
        show_daily_status()
    elif page == "Online Reservations":
        show_online_reservations()
    elif page == "Edit Online Reservations":
        show_edit_online_reservations()
    elif page == "Direct Reservations":
        show_new_reservation_form()
    elif page == "View Reservations":
        show_reservations()
    elif page == "Edit Reservations":
        show_edit_reservations()
    elif page == "Analytics":
        show_analytics()

if __name__ == "__main__":
    main()
