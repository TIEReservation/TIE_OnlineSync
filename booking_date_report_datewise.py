# booking_date_report.py - Date-wise Booking Made Report (All Properties)
import streamlit as st
from supabase import create_client, Client
from datetime import date, datetime
import pandas as pd
import calendar

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
    "Le Poshe Beach view": "Le Poshe Beach view",
    "Le Poshe Beach VIEW": "Le Poshe Beach view",
    "Le Poshe Beachview": "Le Poshe Beach view",
    "Millionaire": "La Millionaire Resort",
    "Le Pondy Beach Side": "Le Pondy Beachside",
    "Le Teera": "Le Terra"
}

# Table CSS with frozen columns till Guest Name
TABLE_CSS = """
<style>
.custom-scrollable-table {
    overflow-x: auto;
    max-width: 100%;
    position: relative;
}
.custom-scrollable-table table {
    table-layout: auto;
    border-collapse: collapse;
    min-width: 100%;
}
.custom-scrollable-table td, .custom-scrollable-table th {
    white-space: nowrap;
    text-overflow: ellipsis;
    overflow: hidden;
    max-width: 300px;
    padding: 8px;
    border: 1px solid #ddd;
    background-color: white;
}
/* Freeze first 5 columns: Source, Property, Booking ID, Booking Date, Guest Name */
.custom-scrollable-table th:nth-child(1),
.custom-scrollable-table td:nth-child(1) {
    position: sticky;
    left: 0;
    z-index: 10;
    background-color: #f8f9fa;
    box-shadow: 2px 0 5px rgba(0,0,0,0.1);
}
.custom-scrollable-table th:nth-child(2),
.custom-scrollable-table td:nth-child(2) {
    position: sticky;
    left: 80px;
    z-index: 10;
    background-color: #f8f9fa;
    box-shadow: 2px 0 5px rgba(0,0,0,0.1);
}
.custom-scrollable-table th:nth-child(3),
.custom-scrollable-table td:nth-child(3) {
    position: sticky;
    left: 250px;
    z-index: 10;
    background-color: #f8f9fa;
    box-shadow: 2px 0 5px rgba(0,0,0,0.1);
}
.custom-scrollable-table th:nth-child(4),
.custom-scrollable-table td:nth-child(4) {
    position: sticky;
    left: 370px;
    z-index: 10;
    background-color: #f8f9fa;
    box-shadow: 2px 0 5px rgba(0,0,0,0.1);
}
.custom-scrollable-table th:nth-child(5),
.custom-scrollable-table td:nth-child(5) {
    position: sticky;
    left: 500px;
    z-index: 10;
    background-color: #f8f9fa;
    box-shadow: 2px 0 5px rgba(0,0,0,0.1);
}
.custom-scrollable-table th {
    background-color: #e9ecef !important;
    font-weight: bold;
}
.custom-scrollable-table a {
    color: #1E90FF;
    text-decoration: none;
}
.custom-scrollable-table a:hover {
    text-decoration: underline;
}
/* Highlight cancelled bookings */
.cancelled-row {
    background-color: #ffe6e6 !important;
}
</style>
"""

def load_direct_reservations_from_supabase():
    """Load ALL direct reservations without any limits using pagination"""
    try:
        all_data = []
        page_size = 1000
        offset = 0
        
        while True:
            response = supabase.table("reservations")\
                .select("*")\
                .range(offset, offset + page_size - 1)\
                .execute()
            
            if response.data:
                all_data.extend(response.data)
                if len(response.data) < page_size:
                    break
                offset += page_size
            else:
                break
        
        return all_data
    except Exception as e:
        st.error(f"Error loading direct reservations: {e}")
        return []

def load_online_reservations_from_supabase():
    """Load ALL online reservations without any limits using pagination"""
    try:
        all_data = []
        page_size = 1000
        offset = 0
        
        while True:
            response = supabase.table("online_reservations")\
                .select("*")\
                .range(offset, offset + page_size - 1)\
                .execute()
            
            if response.data:
                all_data.extend(response.data)
                if len(response.data) < page_size:
                    break
                offset += page_size
            else:
                break
        
        return all_data
    except Exception as e:
        st.error(f"Error loading online reservations: {e}")
        return []

def safe_date_parse(date_str):
    """Robust date parsing"""
    if not date_str:
        return None
    s = str(date_str)
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
    except:
        try:
            return datetime.strptime(s[:10], "%Y-%m-%d").date()
        except:
            return None

def generate_month_dates(year, month):
    """Generate all dates in a month"""
    _, num_days = calendar.monthrange(year, month)
    return [date(year, month, day) for day in range(1, num_days + 1)]

def filter_bookings_by_booking_date(bookings, target_date):
    """Filter bookings that were made on the target date"""
    filtered = []
    for b in bookings:
        # Try different possible booking date field names
        booking_date = None
        
        # Check for booking_date field
        if "booking_date" in b:
            booking_date = safe_date_parse(b.get("booking_date"))
        # Check for created_at field as fallback
        elif "created_at" in b:
            booking_date = safe_date_parse(b.get("created_at"))
        
        if booking_date and booking_date == target_date:
            b["source"] = "direct" if "property_name" in b else "online"
            b["parsed_booking_date"] = booking_date
            filtered.append(b)
    
    return filtered

def create_bookings_table(bookings):
    """Create HTML table from bookings"""
    columns = [
        "Source", "Property", "Booking ID", "Booking Date", "Guest Name", "Mobile No", 
        "Check-in Date", "Check-out Date", "Room No",
        "Advance MOP", "Balance MOP", "Total Tariff", "Advance Amount", 
        "Balance Due", "Booking Status", "Remarks"
    ]
    df_data = []
    
    for booking in bookings:
        source = booking.get("source", "online")
        booking_id = booking.get("booking_id", "") or booking.get("id", "")
        edit_link = f'<a href="?page=Edit Online Reservations&booking_id={booking_id}" target="_self">{booking_id}</a>' if source == "online" else \
                    f'<a href="?page=Edit Reservations&booking_id={booking_id}" target="_self">{booking_id}</a>'
        
        # Get property name
        property_name = booking.get("property") or booking.get("property_name", "") or ""
        
        # Get booking status to check if cancelled
        booking_status = booking.get("booking_status") or booking.get("plan_status", "") or ""
        is_cancelled = "cancel" in str(booking_status).lower()

        df_data.append({
            "Source": source.capitalize(),
            "Property": property_name,
            "Booking ID": edit_link,
            "Booking Date": str(booking.get("parsed_booking_date", "")),
            "Guest Name": booking.get("guest_name") or booking.get("name", "") or "",
            "Mobile No": booking.get("guest_phone") or booking.get("mobile_no", "") or "",
            "Check-in Date": str(safe_date_parse(booking.get("check_in"))) if safe_date_parse(booking.get("check_in")) else "",
            "Check-out Date": str(safe_date_parse(booking.get("check_out"))) if safe_date_parse(booking.get("check_out")) else "",
            "Room No": booking.get("room_no", "") or "",
            "Advance MOP": booking.get("advance_mop", "") or "",
            "Balance MOP": booking.get("balance_mop", "") or "",
            "Total Tariff": booking.get("booking_amount") or booking.get("total_tariff") or 0,
            "Advance Amount": booking.get("total_payment_made") or booking.get("advance_amount") or 0,
            "Balance Due": booking.get("balance_due") or 0,
            "Booking Status": booking_status,
            "Remarks": booking.get("remarks", "") or "",
            "_is_cancelled": is_cancelled
        })
    
    df = pd.DataFrame(df_data, columns=columns + ["_is_cancelled"])
    for col in ['Guest Name', 'Mobile No', 'Room No', 'Remarks', 'Property']:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: f'<span title="{x}">{x}</span>' if pd.notna(x) and str(x).strip() else x)
    return df

@st.cache_data(ttl=300)
def cached_load_online_reservations():
    return load_online_reservations_from_supabase()

@st.cache_data(ttl=300)
def cached_load_direct_reservations():
    return load_direct_reservations_from_supabase()

def show_booking_date_report():
    st.title("Date-wise Booking Made Report (All Properties)")
    st.markdown("**This report shows all bookings across all properties based on when they were created/booked.**")

    if st.button("Refresh Bookings"):
        st.cache_data.clear()
        st.success("Cache cleared! Refreshing bookings...")
        st.rerun()

    current_year = date.today().year
    year = st.selectbox("Select Year", list(range(current_year - 5, current_year + 6)), index=5)
    month = st.selectbox("Select Month", list(range(1, 13)), index=date.today().month - 1)

    # Load ALL bookings
    online_bookings = cached_load_online_reservations()
    direct_bookings = cached_load_direct_reservations()

    st.info(f"Total records loaded: Online={len(online_bookings)}, Direct={len(direct_bookings)}")

    # Normalize property names
    for b in online_bookings:
        if "property" in b:
            b["property"] = property_mapping.get(b["property"], b["property"])
    for b in direct_bookings:
        if "property_name" in b:
            b["property_name"] = property_mapping.get(b["property_name"], b["property_name"])

    if not online_bookings and not direct_bookings:
        st.info("No reservations available.")
        return

    # Combine all bookings
    all_bookings = online_bookings + direct_bookings

    st.subheader(f"Bookings Made in {calendar.month_name[month]} {year}")
    st.markdown(TABLE_CSS, unsafe_allow_html=True)

    # Generate summary statistics
    month_dates = generate_month_dates(year, month)
    total_bookings_month = 0

    for day in month_dates:
        daily_bookings = filter_bookings_by_booking_date(all_bookings, day)
        
        if daily_bookings:
            total_bookings_month += len(daily_bookings)
            
            # Count cancelled vs active bookings
            cancelled_count = sum(1 for b in daily_bookings if "cancel" in str(b.get("booking_status", "")).lower() or "cancel" in str(b.get("plan_status", "")).lower())
            active_count = len(daily_bookings) - cancelled_count
            
            with st.expander(f"📅 {day.strftime('%B %d, %Y')} - {len(daily_bookings)} booking(s) (Active: {active_count}, Cancelled: {cancelled_count})", expanded=False):
                df = create_bookings_table(daily_bookings)
                
                # Convert to HTML and apply cancelled row styling
                table_html = df.to_html(escape=False, index=False)
                
                # Add row classes for cancelled bookings
                rows = table_html.split('<tr>')
                new_rows = [rows[0]]  # Keep header
                
                for i, row in enumerate(rows[1:], 0):
                    if i < len(df) and df.iloc[i]["_is_cancelled"]:
                        row = row.replace('<tr>', '<tr class="cancelled-row">', 1)
                        new_rows.append(row)
                    else:
                        new_rows.append('<tr>' + row)
                
                table_html = ''.join(new_rows)
                
                # Remove the _is_cancelled column from display
                table_html = table_html.replace('<th>_is_cancelled</th>', '')
                import re
                table_html = re.sub(r'<td>(True|False)</td>(?=</tr>)', '', table_html)
                
                st.markdown(f'<div class="custom-scrollable-table">{table_html}</div>', unsafe_allow_html=True)

    if total_bookings_month == 0:
        st.info(f"No bookings made in {calendar.month_name[month]} {year}")

    # Overall summary
    st.markdown("---")
    st.metric(label=f"Total Bookings Made in {calendar.month_name[month]} {year}", value=total_bookings_month)

if __name__ == "__main__":
    show_booking_date_report()
