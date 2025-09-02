import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from supabase import create_client, Client
from utils import safe_int, safe_float

# Initialize Supabase client
try:
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except KeyError as e:
    st.error(f"Missing Supabase secret: {e}. Please check Streamlit Cloud secrets configuration.")
    st.stop()

def load_all_reservations():
    """Load both direct and online reservations."""
    try:
        # Load direct reservations
        direct_response = supabase.table("reservations").select("*").execute()
        direct_reservations = []
        
        for record in direct_response.data:
            reservation = {
                "booking_id": record["booking_id"],
                "guest_name": record["guest_name"] or "",
                "mobile_no": record["mobile_no"] or "",
                "enquiry_date": datetime.strptime(record["enquiry_date"], "%Y-%m-%d").date() if record["enquiry_date"] else None,
                "room_no": record["room_no"] or "",
                "mob": record["mob"] or "",
                "check_in": datetime.strptime(record["check_in"], "%Y-%m-%d").date() if record["check_in"] else None,
                "check_out": datetime.strptime(record["check_out"], "%Y-%m-%d").date() if record["check_out"] else None,
                "booking_status": record["booking_status"] or "Pending",
                "payment_status": record.get("payment_status", "Not Paid"),
                "remarks": record.get("remarks", "")
            }
            direct_reservations.append(reservation)
        
        # Load online reservations
        online_response = supabase.table("online_reservations").select("*").execute()
        online_reservations = []
        
        for record in online_response.data:
            reservation = {
                "booking_id": record["booking_id"],
                "guest_name": record["guest_name"] or "",
                "mobile_no": record["guest_phone"] or "",
                "enquiry_date": datetime.strptime(record["enquiry_date"], "%Y-%m-%d").date() if record["enquiry_date"] else None,
                "room_no": record["room_no"] or "",
                "mob": "Online" if record.get("source") == "online" else "Direct",
                "check_in": datetime.strptime(record["check_in"], "%Y-%m-%d").date() if record["check_in"] else None,
                "check_out": datetime.strptime(record["check_out"], "%Y-%m-%d").date() if record["check_out"] else None,
                "booking_status": record["booking_status"] or "Pending",
                "payment_status": record.get("payment_status", "Not Paid"),
                "remarks": record.get("remarks", "")
            }
            online_reservations.append(reservation)
        
        return direct_reservations + online_reservations
    
    except Exception as e:
        st.error(f"Error loading reservations: {e}")
        return []

def show_calendar_navigation():
    """Show year and month calendar navigation."""
    st.title("🏨 Daily Status Dashboard")
    st.markdown("---")
    
    current_year = datetime.now().year
    col1, col2 = st.columns([1, 3])
    
    with col1:
        selected_year = st.selectbox("Year", [current_year - 1, current_year, current_year + 1], index=1)
    
    with col2:
        st.write("### Select Month")
        months = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        
        month_cols = st.columns(4)
        selected_month = None
        
        for i, month in enumerate(months):
            col_index = i % 4
            with month_cols[col_index]:
                if st.button(f"📆 {month}", key=f"month_{i}", use_container_width=True):
                    selected_month = i + 1
                    st.session_state.selected_month = selected_month
                    st.session_state.selected_year = selected_year
    
    if hasattr(st.session_state, 'selected_month') and hasattr(st.session_state, 'selected_year'):
        show_monthly_daily_status(st.session_state.selected_year, st.session_state.selected_month)

def show_monthly_daily_status(year, month):
    """Show daily status for the selected month."""
    st.subheader(f"Daily Status for {calendar.month_name[month]} {year}")

    # Load reservations
    if 'all_reservations' not in st.session_state:
        st.session_state.all_reservations = load_all_reservations()

    reservations = st.session_state.all_reservations

    # Get days in month
    _, num_days = calendar.monthrange(year, month)
    days = [date(year, month, day) for day in range(1, num_days + 1)]

    selected_day = st.selectbox("Select Day", days, format_func=lambda x: x.strftime("%d-%b-%Y"), key="day_select")

    # Filter reservations for the selected day
    filtered = [
        res for res in reservations
        if res["check_in"] and res["check_out"] and res["check_in"] <= selected_day < res["check_out"]
    ]

    if not filtered:
        st.info(f"No bookings for {selected_day.strftime('%d-%b-%Y')}")
        return

    st.subheader(f"Booking Details for {selected_day.strftime('%d-%b-%Y')}")

    # Display table
    headers = ["Booking ID", "Guest Name", "Mobile No", "Enquiry Date", "Room No", "MOB", "Check In", "Check Out", "Booking Status", "Payment Status", "Remarks"]
    header_cols = st.columns(len(headers))
    for col, header in zip(header_cols, headers):
        col.write(f"**{header}**")

    for res in sorted(filtered, key=lambda x: x.get("booking_id", "")):
        row_cols = st.columns(len(headers))
        with row_cols[0]:
            unique_key = f"edit_{res['booking_id']}_{selected_day}_{id(res)}"
            if st.button(str(res["booking_id"]), key=unique_key):
                st.session_state.edit_booking_id = res["booking_id"]
                st.session_state.edit_booking_source = "direct"  # Adjust based on source if needed
                st.rerun()
        row_cols[1].write(res.get("guest_name", ""))
        row_cols[2].write(res.get("mobile_no", ""))
        row_cols[3].write(res["enquiry_date"].strftime("%d-%m-%Y") if res["enquiry_date"] else "")
        row_cols[4].write(res.get("room_no", ""))
        row_cols[5].write(res.get("mob", ""))
        row_cols[6].write(res["check_in"].strftime("%d-%m-%Y") if res["check_in"] else "")
        row_cols[7].write(res["check_out"].strftime("%d-%m-%Y") if res["check_out"] else "")
        row_cols[8].write(res.get("booking_status", ""))
        row_cols[9].write(res.get("payment_status", ""))
        row_cols[10].write(res.get("remarks", ""))

def main():
    """Main function for daily status."""
    st.set_page_config(
        page_title="Hotel Daily Status",
        page_icon="🏨",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    if hasattr(st.session_state, 'edit_booking_id'):
        st.write("Edit Reservation screen would open here with pre-filled details.")
        if st.button("Back to Daily Status"):
            del st.session_state.edit_booking_id
            del st.session_state.edit_booking_source
            st.rerun()
        return
    
    show_calendar_navigation()

if __name__ == "__main__":
    main()
