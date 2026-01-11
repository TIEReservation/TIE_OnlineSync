# booking_date_report_datewise.py - Date-wise Booking Made Report (All Properties)
import streamlit as st
from supabase import create_client, Client
from datetime import date, datetime
import pandas as pd
import calendar
from io import BytesIO

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

# Table CSS with frozen columns till Guest Name and DataTables integration
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
}
.custom-scrollable-table th {
    background-color: #e9ecef !important;
    font-weight: bold;
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
.custom-scrollable-table a {
    color: #1E90FF;
    text-decoration: none;
}
.custom-scrollable-table a:hover {
    text-decoration: underline;
}
/* Highlight cancelled bookings */
.cancelled-row td {
    background-color: #ffe6e6 !important;
}
/* DataTables customization */
.dataTables_wrapper .dataTables_filter input {
    border: 1px solid #ddd;
    border-radius: 3px;
    padding: 5px;
    margin-left: 5px;
}
.dataTables_wrapper .dataTables_length select {
    border: 1px solid #ddd;
    border-radius: 3px;
    padding: 5px;
}
</style>
<link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.11.5/css/jquery.dataTables.css">
<script type="text/javascript" charset="utf8" src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<script type="text/javascript" charset="utf8" src="https://cdn.datatables.net/1.11.5/js/jquery.dataTables.js"></script>
<script type="text/javascript" charset="utf8" src="https://cdn.datatables.net/buttons/2.2.2/js/dataTables.buttons.min.js"></script>
<script type="text/javascript" charset="utf8" src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.1.3/jszip.min.js"></script>
<script type="text/javascript" charset="utf8" src="https://cdn.datatables.net/buttons/2.2.2/js/buttons.html5.min.js"></script>
<link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/buttons/2.2.2/css/buttons.dataTables.min.css">
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

def create_bookings_dataframe(bookings):
    """Create pandas DataFrame from bookings for download"""
    if not bookings:
        return pd.DataFrame()
    
    data = []
    for booking in bookings:
        source = booking.get("source", "online")
        booking_id = booking.get("booking_id", "") or booking.get("id", "")
        property_name = booking.get("property") or booking.get("property_name", "") or ""
        booking_status = booking.get("booking_status") or booking.get("plan_status", "") or ""
        
        data.append({
            "Source": source.capitalize(),
            "Property": property_name,
            "Booking ID": booking_id,
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
        })
    
    return pd.DataFrame(data)

def create_bookings_table(bookings, table_id):
    """Create HTML table from bookings with DataTables integration"""
    if not bookings:
        return "<p>No bookings found.</p>"
    
    columns = [
        "Source", "Property", "Booking ID", "Booking Date", "Guest Name", "Mobile No", 
        "Check-in Date", "Check-out Date", "Room No",
        "Advance MOP", "Balance MOP", "Total Tariff", "Advance Amount", 
        "Balance Due", "Booking Status", "Remarks"
    ]
    
    # Build HTML manually for better control
    html_parts = [f'<table id="{table_id}" class="display" style="width:100%">']
    
    # Header row
    html_parts.append('<thead><tr>')
    for col in columns:
        html_parts.append(f'<th>{col}</th>')
    html_parts.append('</tr></thead>')
    
    # Body rows
    html_parts.append('<tbody>')
    
    for booking in bookings:
        source = booking.get("source", "online")
        booking_id = booking.get("booking_id", "") or booking.get("id", "")
        edit_link = f'<a href="?page=Edit Online Reservations&booking_id={booking_id}" target="_self">{booking_id}</a>' if source == "online" else \
                    f'<a href="?page=Edit Direct Reservation&booking_id={booking_id}" target="_self">{booking_id}</a>'
        
        # Get property name
        property_name = booking.get("property") or booking.get("property_name", "") or ""
        
        # Get booking status to check if cancelled
        booking_status = booking.get("booking_status") or booking.get("plan_status", "") or ""
        is_cancelled = "cancel" in str(booking_status).lower()
        
        # Add cancelled class to row if needed
        row_class = ' class="cancelled-row"' if is_cancelled else ''
        html_parts.append(f'<tr{row_class}>')
        
        # Source
        html_parts.append(f'<td>{source.capitalize()}</td>')
        
        # Property
        html_parts.append(f'<td><span title="{property_name}">{property_name}</span></td>')
        
        # Booking ID with link
        html_parts.append(f'<td>{edit_link}</td>')
        
        # Booking Date
        html_parts.append(f'<td>{booking.get("parsed_booking_date", "")}</td>')
        
        # Guest Name
        guest_name = booking.get("guest_name") or booking.get("name", "") or ""
        html_parts.append(f'<td><span title="{guest_name}">{guest_name}</span></td>')
        
        # Mobile No
        mobile = booking.get("guest_phone") or booking.get("mobile_no", "") or ""
        html_parts.append(f'<td><span title="{mobile}">{mobile}</span></td>')
        
        # Check-in Date
        checkin = str(safe_date_parse(booking.get("check_in"))) if safe_date_parse(booking.get("check_in")) else ""
        html_parts.append(f'<td>{checkin}</td>')
        
        # Check-out Date
        checkout = str(safe_date_parse(booking.get("check_out"))) if safe_date_parse(booking.get("check_out")) else ""
        html_parts.append(f'<td>{checkout}</td>')
        
        # Room No
        room_no = booking.get("room_no", "") or ""
        html_parts.append(f'<td><span title="{room_no}">{room_no}</span></td>')
        
        # Advance MOP
        adv_mop = booking.get("advance_mop", "") or ""
        html_parts.append(f'<td>{adv_mop}</td>')
        
        # Balance MOP
        bal_mop = booking.get("balance_mop", "") or ""
        html_parts.append(f'<td>{bal_mop}</td>')
        
        # Total Tariff
        total_tariff = booking.get("booking_amount") or booking.get("total_tariff") or 0
        html_parts.append(f'<td>{total_tariff}</td>')
        
        # Advance Amount
        advance = booking.get("total_payment_made") or booking.get("advance_amount") or 0
        html_parts.append(f'<td>{advance}</td>')
        
        # Balance Due
        balance = booking.get("balance_due") or 0
        html_parts.append(f'<td>{balance}</td>')
        
        # Booking Status
        html_parts.append(f'<td>{booking_status}</td>')
        
        # Remarks
        remarks = booking.get("remarks", "") or ""
        html_parts.append(f'<td><span title="{remarks}">{remarks}</span></td>')
        
        html_parts.append('</tr>')
    
    html_parts.append('</tbody></table>')
    
    # Add DataTables initialization script
    html_parts.append(f"""
    <script>
    $(document).ready(function() {{
        $('#{table_id}').DataTable({{
            "pageLength": 25,
            "order": [[3, "desc"]],
            "dom": 'Bfrtip',
            "buttons": [
                {{
                    extend: 'excelHtml5',
                    text: 'Download Excel',
                    title: 'Bookings Report'
                }},
                {{
                    extend: 'csvHtml5',
                    text: 'Download CSV',
                    title: 'Bookings Report'
                }}
            ],
            "scrollX": true,
            "fixedColumns": {{
                left: 5
            }}
        }});
    }});
    </script>
    """)
    
    return ''.join(html_parts)

def convert_df_to_excel(df):
    """Convert DataFrame to Excel file"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Bookings')
    return output.getvalue()

@st.cache_data(ttl=300)
def cached_load_online_reservations():
    return load_online_reservations_from_supabase()

@st.cache_data(ttl=300)
def cached_load_direct_reservations():
    return load_direct_reservations_from_supabase()

def show_datewise_booking_report():
    """Main function to display the date-wise booking report"""
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
    
    # Generate summary statistics
    month_dates = generate_month_dates(year, month)
    total_bookings_month = 0
    all_month_bookings = []

    # Collect all bookings for the month
    for day in month_dates:
        daily_bookings = filter_bookings_by_booking_date(all_bookings, day)
        if daily_bookings:
            all_month_bookings.extend(daily_bookings)
            total_bookings_month += len(daily_bookings)

    # Download button for entire month
    if all_month_bookings:
        st.markdown("### Download Options")
        col1, col2 = st.columns(2)
        
        df_month = create_bookings_dataframe(all_month_bookings)
        
        with col1:
            excel_data = convert_df_to_excel(df_month)
            st.download_button(
                label="📥 Download Month Report (Excel)",
                data=excel_data,
                file_name=f"bookings_{calendar.month_name[month]}_{year}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        with col2:
            csv_data = df_month.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Month Report (CSV)",
                data=csv_data,
                file_name=f"bookings_{calendar.month_name[month]}_{year}.csv",
                mime="text/csv"
            )

    st.markdown("---")
    st.markdown(TABLE_CSS, unsafe_allow_html=True)

    # Display day-wise data
    for day in month_dates:
        daily_bookings = filter_bookings_by_booking_date(all_bookings, day)
        
        if daily_bookings:
            # Count cancelled vs active bookings
            cancelled_count = sum(1 for b in daily_bookings if "cancel" in str(b.get("booking_status", "")).lower() or "cancel" in str(b.get("plan_status", "")).lower())
            active_count = len(daily_bookings) - cancelled_count
            
            with st.expander(f"📅 {day.strftime('%B %d, %Y')} - {len(daily_bookings)} booking(s) (Active: {active_count}, Cancelled: {cancelled_count})", expanded=False):
                # Create unique table ID for each day
                table_id = f"bookings_table_{day.strftime('%Y%m%d')}"
                table_html = create_bookings_table(daily_bookings, table_id)
                st.markdown(f'<div class="custom-scrollable-table">{table_html}</div>', unsafe_allow_html=True)
                
                # Download buttons for this day
                st.markdown("---")
                col1, col2 = st.columns(2)
                df_day = create_bookings_dataframe(daily_bookings)
                
                with col1:
                    excel_data_day = convert_df_to_excel(df_day)
                    st.download_button(
                        label=f"📥 Download {day.strftime('%b %d')} (Excel)",
                        data=excel_data_day,
                        file_name=f"bookings_{day.strftime('%Y_%m_%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"excel_{day.strftime('%Y%m%d')}"
                    )
                
                with col2:
                    csv_data_day = df_day.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label=f"📥 Download {day.strftime('%b %d')} (CSV)",
                        data=csv_data_day,
                        file_name=f"bookings_{day.strftime('%Y_%m_%d')}.csv",
                        mime="text/csv",
                        key=f"csv_{day.strftime('%Y%m%d')}"
                    )

    if total_bookings_month == 0:
        st.info(f"No bookings made in {calendar.month_name[month]} {year}")

    # Overall summary
    st.markdown("---")
    st.metric(label=f"Total Bookings Made in {calendar.month_name[month]} {year}", value=total_bookings_month)

if __name__ == "__main__":
    show_datewise_booking_report()
