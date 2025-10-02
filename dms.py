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
    """Filter bookings active on the target date with status Pending or Follow-up."""
    filtered_bookings = []
    for booking in bookings:
        if booking.get("booking_status") not in ["Pending", "Follow-up"]:
            continue
        check_in = date.fromisoformat(booking["check_in"]) if booking.get("check_in") else None
        check_out = date.fromisoformat(booking["check_out"]) if booking.get("check_out") else None
        if check_in and check_out and check_in <= target_date < check_out:
            # Add source identifier for unified display
            booking["source"] = "direct" if "property_name" in booking else "online"
            filtered_bookings.append(booking)
    return filtered_bookings

def create_bookings_table(bookings):
    """Create a DataFrame for bookings with specified columns, including edit links and unified fields for online/direct."""
    columns = [
        "Source", "Booking ID", "Guest Name", "Check-in Date", "Check-out Date", "Room No",
        "Advance MOP", "Balance MOP", "Total Tariff", "Advance Amount", "Balance Due",
        "Booking Status", "Remarks"
    ]
    df_data = []
    for booking in bookings:
        booking_id = booking.get("booking_id", "")
        source = booking.get("source", "online")  # From filter_bookings_for_day
        # Create a clickable link for Booking ID (route to appropriate edit page)
        edit_page = "Edit+Online+Reservations" if source == "online" else "Edit+Reservations"
        booking_id_link = f'<a href="?page={edit_page}&booking_id={booking_id}" target="_self">{booking_id}</a>'
        
        # Unified field mapping for online vs. direct
        total_tariff = booking.get("booking_amount", booking.get("total_tariff", 0.0))
        advance_amount = booking.get("total_payment_made", booking.get("advance_amount", 0.0))
        balance_due = booking.get("balance_due", booking.get("balance_amount", 0.0))
        advance_mop = booking.get("mode_of_booking", booking.get("advance_mop", ""))  # Fallback for online
        balance_mop = booking.get("balance_mop", "")  # Online may not have this; leave blank
        
        df_data.append({
            "Source": source.upper(),
            "Booking ID": booking_id_link,
            "Guest Name": booking.get("guest_name", ""),
            "Check-in Date": booking.get("check_in", ""),
            "Check-out Date": booking.get("check_out", ""),
            "Room No": booking.get("room_no", ""),
            "Advance MOP": advance_mop,
            "Balance MOP": balance_mop,
            "Total Tariff": total_tariff,
            "Advance Amount": advance_amount,
            "Balance Due": balance_due,
            "Booking Status": booking.get("booking_status", ""),
            "Remarks": booking.get("remarks", "")
        })
    return pd.DataFrame(df_data, columns=columns)

@st.cache_data
def cached_load_online_reservations():
    """Cache the loading of online reservations."""
    return load_online_reservations_from_supabase()

@st.cache_data
def cached_load_direct_reservations():
    """Cache the loading of direct reservations."""
    return load_direct_reservations_from_supabase()

def show_dms():
    """Display Daily Management Status page with Pending and Follow-up bookings from both online and direct sources."""
    st.title("📋 Daily Management Status")
    
    if st.button("🔄 Refresh Bookings"):
        st.cache_data.clear()
        st.success("Cache cleared! Refreshing bookings...")
        st.rerun()
    
    current_year = date.today().year
    year = st.selectbox("Select Year", list(range(current_year - 5, current_year + 6)), index=5)
    month = st.selectbox("Select Month", list(range(1, 13)), index=date.today().month - 1)
    
    # Load and cache both online and direct reservations
    online_bookings = cached_load_online_reservations()
    direct_bookings = cached_load_direct_reservations()
    
    # Normalize property names using the mapping
    for b in online_bookings:
        if "property" in b:
            b["property"] = property_mapping.get(b["property"], b["property"])
    for b in direct_bookings:
        if "property_name" in b:
            b["property_name"] = property_mapping.get(b["property_name"], b["property_name"])
    
    if not online_bookings and not direct_bookings:
        st.info("No reservations available.")
        return
    
    # Get unique properties from both sources (now normalized)
    online_df = pd.DataFrame(online_bookings)
    direct_df = pd.DataFrame(direct_bookings)
    online_properties = sorted(online_df["property"].dropna().unique().tolist())
    direct_properties = sorted(direct_df["property_name"].dropna().unique().tolist())
    all_properties = sorted(list(set(online_properties + direct_properties)))
    
    if not all_properties:
        st.info("No properties found in reservations.")
        return
    
    st.subheader("Pending and Follow-up Bookings by Property")
    st.markdown(TABLE_CSS, unsafe_allow_html=True)
    
    for prop in all_properties:
        with st.expander(f"{prop}"):
            month_dates = generate_month_dates(year, month)
            start_date = month_dates[0]
            end_date = month_dates[-1] + timedelta(days=1)
            
            # Filter online bookings for the property and Pending or Follow-up status
            prop_online_bookings = [b for b in online_bookings if b.get("property") == prop and b.get("booking_status") in ["Pending", "Follow-up"]]
            # Filter direct bookings for the property and Pending or Follow-up status
            prop_direct_bookings = [b for b in direct_bookings if b.get("property_name") == prop and b.get("booking_status") in ["Pending", "Follow-up"]]
            
            # Combine both
            prop_all_bookings = prop_online_bookings + prop_direct_bookings
            st.info(f"Total Pending and Follow-up bookings for {prop}: {len(prop_all_bookings)} (Online: {len(prop_online_bookings)}, Direct: {len(prop_direct_bookings)})")
            
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
                    st.info("No Pending or Follow-up bookings on this day.")
