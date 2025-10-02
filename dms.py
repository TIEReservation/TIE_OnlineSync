import streamlit as st
from supabase import create_client, Client
from datetime import date, timedelta
import pandas as pd
import calendar
from online_reservation import load_online_reservations_from_supabase
from directreservation import load_reservations_from_supabase

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

def filter_bookings_for_day(bookings, target_date, is_direct=False):
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

def create_online_bookings_table(bookings):
    """Create a DataFrame for online bookings with specified columns, including edit links."""
    columns = [
        "Booking ID", "Guest Name", "Check-in Date", "Check-out Date", "Room No",
        "Advance MOP", "Balance MOP", "Total Tariff", "Advance Amount", "Balance Due",
        "Booking Status", "Remarks"
    ]
    df_data = []
    for booking in bookings:
        booking_id = booking.get("booking_id", "")
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

def create_direct_bookings_table(bookings):
    """Create a DataFrame for direct bookings with specified columns, including edit links."""
    columns = [
        "Booking ID", "Guest Name", "Check-in Date", "Check-out Date", "Room Type",
        "Total Tariff", "Advance Amount", "Booking Status"
    ]
    df_data = []
    for booking in bookings:
        booking_id = booking.get("booking_id", "")
        booking_id_link = f'<a href="?page=Edit+Reservations&booking_id={booking_id}" target="_self">{booking_id}</a>'
        df_data.append({
            "Booking ID": booking_id_link,
            "Guest Name": booking.get("guest_name", ""),
            "Check-in Date": booking.get("check_in", ""),
            "Check-out Date": booking.get("check_out", ""),
            "Room Type": booking.get("room_type", ""),
            "Total Tariff": booking.get("tariff", 0.0),
            "Advance Amount": booking.get("advance", 0.0),
            "Booking Status": booking.get("booking_status", "")
        })
    return pd.DataFrame(df_data, columns=columns)

@st.cache_data
def cached_load_online_reservations():
    """Cache the loading of online reservations."""
    return load_online_reservations_from_supabase()

@st.cache_data
def cached_load_direct_reservations():
    """Cache the loading of direct reservations."""
    return load_reservations_from_supabase()

def show_dms():
    """Display Daily Management Status page with Pending and Follow-up bookings."""
    st.title("📋 Daily Management Status")
    if st.button("🔄 Refresh Bookings"):
        st.cache_data.clear()
        st.success("Cache cleared! Refreshing bookings...")
        st.rerun()
    
    current_year = date.today().year
    year = st.selectbox("Select Year", list(range(current_year - 5, current_year + 6)), index=5)
    month = st.selectbox("Select Month", list(range(1, 13)), index=date.today().month - 1)
    month_dates = generate_month_dates(year, month)
    selected_date = st.selectbox("Select Date", month_dates, index=month_dates.index(date.today()) if date.today() in month_dates else 0)
    
    # Load and cache reservations
    online_bookings = cached_load_online_reservations()
    direct_bookings = cached_load_direct_reservations()
    
    # Convert direct bookings to list of dicts for consistency
    direct_bookings = direct_bookings.to_dict('records') if not direct_bookings.empty else []
    
    if not online_bookings and not direct_bookings:
        st.info("No reservations (online or direct) available.")
        return
    
    # Get unique properties
    all_bookings = online_bookings + direct_bookings
    df = pd.DataFrame(all_bookings)
    properties = sorted(df.get("property", df.get("property_name", pd.Series())).dropna().unique().tolist())
    if not properties:
        st.info("No properties found in reservations.")
        return
    
    st.subheader("Pending and Follow-up Bookings by Property")
    st.markdown(TABLE_CSS, unsafe_allow_html=True)
    
    for prop in properties:
        with st.expander(f"{prop}"):
            # Filter online bookings
            prop_online_bookings = [b for b in online_bookings if b.get("property") == prop and b.get("booking_status") in ["Pending", "Follow-up"]]
            # Filter direct bookings
            prop_direct_bookings = [b for b in direct_bookings if b.get("property_name") == prop and b.get("booking_status") in ["Pending", "Follow-up"]]
            
            st.subheader(f"{prop} - {selected_date.strftime('%B %d, %Y')}")
            
            # Online Bookings
            st.write("**Online Reservations**")
            daily_online_bookings = filter_bookings_for_day(prop_online_bookings, selected_date)
            st.info(f"Total Pending and Follow-up online bookings: {len(daily_online_bookings)}")
            if daily_online_bookings:
                df_online = create_online_bookings_table(daily_online_bookings)
                tooltip_columns = ['Guest Name', 'Room No', 'Remarks']
                for col in tooltip_columns:
                    if col in df_online.columns:
                        df_online[col] = df_online[col].apply(lambda x: f'<span title="{x}">{x}</span>' if isinstance(x, str) else x)
                table_html = df_online.to_html(escape=False, index=False)
                st.markdown(f'<div class="custom-scrollable-table">{table_html}</div>', unsafe_allow_html=True)
            else:
                st.info("No Pending or Follow-up online bookings on this day.")
            
            # Direct Bookings
            st.write("**Direct Reservations**")
            daily_direct_bookings = filter_bookings_for_day(prop_direct_bookings, selected_date, is_direct=True)
            st.info(f"Total Pending and Follow-up direct bookings: {len(daily_direct_bookings)}")
            if daily_direct_bookings:
                df_direct = create_direct_bookings_table(daily_direct_bookings)
                tooltip_columns = ['Guest Name', 'Room Type']
                for col in tooltip_columns:
                    if col in df_direct.columns:
                        df_direct[col] = df_direct[col].apply(lambda x: f'<span title="{x}">{x}</span>' if isinstance(x, str) else x)
                table_html = df_direct.to_html(escape=False, index=False)
                st.markdown(f'<div class="custom-scrollable-table">{table_html}</div>', unsafe_allow_html=True)
            else:
                st.info("No Pending or Follow-up direct bookings on this day.")
