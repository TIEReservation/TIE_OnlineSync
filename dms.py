import streamlit as st
from supabase import create_client, Client
from datetime import date, timedelta
import pandas as pd
import calendar
from online_reservation import load_online_reservations_from_supabase

# Initialize Supabase client
try:
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except KeyError as e:
    st.error(f"Missing Supabase secret: {e}. Please check Streamlit Cloud secrets configuration.")
    st.stop()

# Table CSS for non-wrapping, scrollable table
TABLE_CSS = """
<style>
/* Styles for non-wrapping, scrollable table in DMS */
.custom-scrollable-table {
    overflow-x: auto;
    max-width: 100%;
    min-width: 800px;
}
.custom-scrollable-table table {
    table-layout: auto;
    border-collapse: collapse;
}
.custom-scrollable-table td, .custom-scrollable-table th {
    white-space: nowrap;
    text-overflow: ellipsis;
    overflow: hidden;
    max-width: 300px;
    padding: 8px;
    border: 1px solid #ddd;
}
.custom-scrollable-table a {
    color: #1E90FF;
    text-decoration: none;
}
.custom-scrollable-table a:hover {
    text-decoration: underline;
}
</style>
"""

def generate_month_dates(year, month):
    """Generate a list of dates for the given month and year."""
    _, num_days = calendar.monthrange(year, month)
    return [date(year, month, day) for day in range(1, num_days + 1)]

def filter_bookings_for_day(bookings, target_date):
    """Filter bookings active on the target date with status Pending or Follow-up."""
    filtered_bookings = []
    for booking in bookings:
        if booking.get("booking_status") not in ["Pending", "Follow-up"]:
            continue
        check_in = date.fromisoformat(booking["check_in"]) if booking.get("check_in") else None
        check_out = date.fromisoformat(booking["check_out"]) if booking.get("check_out") else None
        if check_in and check_out and check_in <= target_date < check_out:
            filtered_bookings.append(booking)
    return filtered_bookings

def create_bookings_table(bookings):
    """Create a DataFrame for bookings with specified columns, including edit links."""
    columns = [
        "Booking ID", "Guest Name", "Check-in Date", "Check-out Date", "Room No",
        "Advance MOP", "Balance MOP", "Total Tariff", "Advance Amount", "Balance Due",
        "Booking Status", "Remarks"
    ]
    df_data = []
    for booking in bookings:
        booking_id = booking.get("booking_id", "")
        # Create a clickable link for Booking ID
        booking_id_link = f'<a href="?page=Edit+Online+Reservations&booking_id={booking_id}" target="_self">{booking_id}</a>'
        df_data.append({
            "Booking ID": booking_id_link,
            "Guest Name": booking.get("guest_name", ""),
            "Check-in Date": booking.get("check_in", ""),
            "Check-out Date": booking.get("check_out", ""),
            "Room No": booking.get("room_no", ""),
            "Advance MOP": booking.get("advance_mop", ""),
            "Balance MOP": booking.get("balance_mop", ""),
            "Total Tariff": booking.get("booking_amount", 0.0),
            "Advance Amount": booking.get("total_payment_made", 0.0),
            "Balance Due": booking.get("balance_due", 0.0),
            "Booking Status": booking.get("booking_status", ""),
            "Remarks": booking.get("remarks", "")
        })
    return pd.DataFrame(df_data, columns=columns)

@st.cache_data
def cached_load_online_reservations():
    """Cache the loading of online reservations."""
    return load_online_reservations_from_supabase()

def show_dms():
    """Display Daily Management Status page with Pending and Follow-up online bookings."""
    st.title("📋 Daily Management Status")
    if st.button("🔄 Refresh Bookings"):
        st.cache_data.clear()
        st.success("Cache cleared! Refreshing bookings...")
        st.rerun()
    
    current_year = date.today().year
    year = st.selectbox("Select Year", list(range(current_year - 5, current_year + 6)), index=5)
    month = st.selectbox("Select Month", list(range(1, 13)), index=date.today().month - 1)
    
    # Load and cache online reservations
    bookings = cached_load_online_reservations()
    if not bookings:
        st.info("No online reservations available.")
        return
    
    # Get unique properties
    df = pd.DataFrame(bookings)
    properties = sorted(df["property"].dropna().unique().tolist())
    if not properties:
        st.info("No properties found in reservations.")
        return
    
    st.subheader("Pending and Follow-up Bookings by Property")
    st.markdown(TABLE_CSS, unsafe_allow_html=True)
    
    for prop in properties:
        with st.expander(f"{prop}"):
            month_dates = generate_month_dates(year, month)
            start_date = month_dates[0]
            end_date = month_dates[-1] + timedelta(days=1)
            
            # Filter bookings for the property and Pending or Follow-up status
            prop_bookings = [b for b in bookings if b.get("property") == prop and b.get("booking_status") in ["Pending", "Follow-up"]]
            st.info(f"Total Pending and Follow-up bookings for {prop}: {len(prop_bookings)}")
            
            for day in month_dates:
                daily_bookings = filter_bookings_for_day(prop_bookings, day)
                st.subheader(f"{prop} - {day.strftime('%B %d, %Y')}")
                if daily_bookings:
                    df = create_bookings_table(daily_bookings)
                    tooltip_columns = ['Guest Name', 'Room No', 'Remarks']
                    for col in tooltip_columns:
                        if col in df.columns:
                            df[col] = df[col].apply(lambda x: f'<span title="{x}">{x}</span>' if isinstance(x, str) else x)
                    table_html = df.to_html(escape=False, index=False)
                    st.markdown(f'<div class="custom-scrollable-table">{table_html}</div>', unsafe_allow_html=True)
                else:
                    st.info("No Pending or Follow-up bookings on this day.")
