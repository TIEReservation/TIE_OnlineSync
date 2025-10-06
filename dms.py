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

# Property synonym mapping
property_mapping = {
    "La Millionaire Luxury Resort": "La Millionaire Resort",
    "Le Poshe Beach View": "Le Poshe Beach view",
}
reverse_mapping = {}
for variant, canonical in property_mapping.items():
    reverse_mapping.setdefault(canonical, []).append(variant)

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

def load_direct_reservations_from_supabase():
    """Load direct reservations from Supabase (equivalent to load_reservations_from_supabase in directreservation.py)."""
    try:
        response = supabase.table("reservations").select("*").order("check_in", desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error loading direct reservations: {e}")
        return []

def generate_month_dates(year, month):
    """Generate a list of dates for the given month and year."""
    _, num_days = calendar.monthrange(year, month)
    return [date(year, month, day) for day in range(1, num_days + 1)]

def filter_bookings_for_day(bookings, target_date):
    """Filter bookings active on the target date with status Pending, Follow-up, or Confirmed with Not Paid."""
    filtered_bookings = []
    for booking in bookings:
        check_in = date.fromisoformat(booking.get("check_in")) if booking.get("check_in") else None
        check_out = date.fromisoformat(booking.get("check_out")) if booking.get("check_out") else None
        if check_in and check_out and check_in <= target_date < check_out:
            booking_status = booking.get("booking_status")
            payment_status = booking.get("payment_status")
            if booking_status in ["Pending", "Follow-up"] or (booking_status == "Confirmed" and payment_status == "Not Paid"):
                filtered_bookings.append(booking)
    return filtered_bookings

def normalize_property(property):
    """Normalize property name using synonym mapping."""
    return property_mapping.get(property, property)

def create_bookings_table(daily_bookings):
    """Create a DataFrame for the daily bookings."""
    rows = []
    for booking in daily_bookings:
        source = "Online" if booking.get("property") else "Direct"
        guest_name = booking.get("guest_name", "")
        room_no = booking.get("room_no", "")
        remarks = booking.get("remarks", "")
        booking_id = booking.get("booking_id", "")
        row = {
            "Source": source,
            "Guest Name": guest_name,
            "Room No": room_no,
            "Remarks": remarks,
            "Booking ID": f'<a href="?page=Edit%20{source}%20Reservations&booking_id={booking_id}">{booking_id}</a>' if booking_id else ""
        }
        rows.append(row)
    return pd.DataFrame(rows)

def show_dms():
    """Display daily management status with pending and follow-up bookings."""
    st.title("📅 Daily Management Status")
    if st.button("🔄 Refresh Property List"):
        st.cache_data.clear()
        st.success("Cache cleared! Refreshing properties...")
        st.rerun()
    current_year = date.today().year
    year = st.selectbox("Select Year", list(range(current_year - 5, current_year + 6)), index=5)
    month = st.selectbox("Select Month", list(range(1, 13)), index=date.today().month - 1)
    online_bookings = load_online_reservations_from_supabase()
    direct_bookings = load_direct_reservations_from_supabase()
    
    # Normalize properties in bookings
    for booking in online_bookings:
        booking["property"] = normalize_property(booking.get("property", ""))
    for booking in direct_bookings:
        booking["property_name"] = normalize_property(booking.get("property_name", ""))
    
    online_df = pd.DataFrame(online_bookings)
    direct_df = pd.DataFrame(direct_bookings)
    online_properties = sorted(online_df["property"].dropna().unique().tolist())
    direct_properties = sorted(direct_df["property_name"].dropna().unique().tolist())
    all_properties = sorted(list(set(online_properties + direct_properties)))
    
    if not all_properties:
        st.info("No properties found in reservations.")
        return
    
    st.subheader("Pending, Follow-up, and Unpaid Confirmed Bookings by Property")
    st.markdown(TABLE_CSS, unsafe_allow_html=True)
    
    for prop in all_properties:
        with st.expander(f"{prop}"):
            month_dates = generate_month_dates(year, month)
            start_date = month_dates[0]
            end_date = month_dates[-1] + timedelta(days=1)
            
            # Filter online bookings for the property and relevant statuses
            prop_online_bookings = [b for b in online_bookings if b.get("property") == prop and (b.get("booking_status") in ["Pending", "Follow-up"] or (b.get("booking_status") == "Confirmed" and b.get("payment_status") == "Not Paid"))]
            # Filter direct bookings for the property and relevant statuses
            prop_direct_bookings = [b for b in direct_bookings if b.get("property_name") == prop and (b.get("booking_status") in ["Pending", "Follow-up"] or (b.get("booking_status") == "Confirmed" and b.get("payment_status") == "Not Paid"))]
            
            # Combine both
            prop_all_bookings = prop_online_bookings + prop_direct_bookings
            st.info(f"Total Pending, Follow-up, and Unpaid Confirmed bookings for {prop}: {len(prop_all_bookings)} (Online: {len(prop_online_bookings)}, Direct: {len(prop_direct_bookings)})")
            
            for day in month_dates:
                daily_bookings = filter_bookings_for_day(prop_all_bookings, day)
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
                    st.info("No Pending, Follow-up, or Unpaid Confirmed bookings on this day.")
