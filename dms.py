# dms.py - FINAL VERSION: Daily Management Status (Fully Fixed & Enhanced)
import streamlit as st
from supabase import create_client, Client
from datetime import date, timedelta
import pandas as pd
import calendar

# Initialize Supabase
try:
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except KeyError as e:
    st.error(f"Missing Supabase secret: {e}. Please check Streamlit Cloud secrets.")
    st.stop()

# Property synonym mapping
property_mapping = {
    "La Millionaire Luxury Resort": "La Millionaire Resort",
    "Le Poshe Beach View": "Le Poshe Beach view",
    "Le Poshe Beach VIEW": "Le Poshe Beach view",
    "Le Poshe Beachview": "Le Poshe Beach view",
    "Millionaire": "La Millionaire Resort",
}
reverse_mapping = {}
for variant, canonical in property_mapping.items():
    reverse_mapping.setdefault(canonical, []).append(variant)

# Beautiful scrollable table CSS
TABLE_CSS = """
<style>
.custom-scrollable-table {
    overflow-x: auto;
    max-width: 100%;
    min-width: 800px;
    border-radius: 8px;
    margin: 10px 0;
}
.custom-scrollable-table table {
    table-layout: auto;
    border-collapse: collapse;
    width: 100%;
    font-size: 14px;
}
.custom-scrollable-table td, .custom-scrollable-table th {
    white-space: nowrap;
    padding: 10px 12px;
    border: 1px solid #e0e0e0;
    text-align: left;
}
.custom-scrollable-table th {
    background-color: #f5f7fa;
    font-weight: 600;
    position: sticky;
    top: 0;
    z-index: 10;
}
.custom-scrollable-table tr:nth-child(even) {
    background-color: #fafafa;
}
.custom-scrollable-table a {
    color: #1E90FF;
    text-decoration: none;
    font-weight: 500;
}
.custom-scrollable-table a:hover {
    text-decoration: underline;
}
</style>
"""

def load_all_bookings():
    """Load ALL bookings from both tables (no filters)"""
    try:
        online = supabase.table("online_reservations").select("*").execute()
        direct = supabase.table("reservations").select("*").execute()
        return (online.data or []), (direct.data or [])
    except Exception as e:
        st.error(f"Database error: {e}")
        return [], []

def generate_month_dates(year, month):
    _, num_days = calendar.monthrange(year, month)
    return [date(year, month, d) for d in range(1, num_days + 1)]

def is_relevant_status(booking):
    """Check if booking should appear in DMS"""
    status = booking.get("booking_status") or booking.get("plan_status", "")
    payment = booking.get("payment_status", "")
    return (
        status in ["Pending", "Follow-up"] or
        (status == "Confirmed" and payment == "Not Paid")
    )

def normalize_booking(booking, source):
    """Unify fields from online/direct bookings"""
    b = booking.copy()
    b["source"] = source
    
    # Unified fields
    b["booking_id"] = b.get("booking_id") or b.get("id") or "N/A"
    b["guest_name"] = b.get("guest_name", "")
    b["mobile_no"] = b.get("guest_phone") or b.get("mobile_no", "")
    b["check_in"] = b.get("check_in", "")
    b["check_out"] = b.get("check_out", "")
    b["room_no"] = b.get("room_no", "")
    b["advance_mop"] = b.get("advance_mop", "")
    b["balance_mop"] = b.get("balance_mop", "")
    b["total_tariff"] = b.get("booking_amount") or b.get("total_tariff", 0)
    b["advance_amount"] = b.get("total_payment_made") or b.get("advance_amount", 0)
    b["balance_due"] = b.get("balance_due") or b.get("balance_amount", 0)
    b["booking_status"] = b.get("booking_status") or b.get("plan_status", "")
    b["remarks"] = b.get("remarks", "")
    
    # Normalize property
    prop_key = "property" if source == "online" else "property_name"
    original_prop = b.get(prop_key, "")
    b["property"] = property_mapping.get(original_prop, original_prop)
    
    return b

def create_bookings_table(bookings):
    """Create clean HTML table with edit links"""
    if not bookings:
        return pd.DataFrame()

    rows = []
    for b in bookings:
        bid = b["booking_id"]
        if b["source"] == "online":
            link = f'<a href="?page=28&booking_id={bid}" target="_self">{bid}</a>'
        else:
            link = f'<a href="?page=27&booking_id={bid}" target="_self">{bid}</a>'

        rows.append({
            "Source": "Online" if b["source"] == "online" else "Direct",
            "Booking ID": link,
            "Guest Name": b["guest_name"],
            "Mobile No": b["mobile_no"],
            "Check-in Date": b["check_in"],
            "Check-out Date": b["check_out"],
            "Room No": b["room_no"],
            "Advance MOP": b["advance_mop"],
            "Balance MOP": b["balance_mop"],
            "Total Tariff": f"₹{float(b['total_tariff']):,.0f}" if b["total_tariff"] else "",
            "Advance Amount": f"₹{float(b['advance_amount']):,.0f}" if b["advance_amount"] else "",
            "Balance Due": f"₹{float(b['balance_due']):,.0f}" if b["balance_due"] else "",
            "Booking Status": b["booking_status"],
            "Remarks": b["remarks"][:100] + ("..." if len(b["remarks"]) > 100 else "")
        })

    df = pd.DataFrame(rows)
    return df

# MAIN DMS FUNCTION
def show_dms():
    st.title("Daily Management Status (DMS)")
    
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("FORCE REFRESH FROM DB", type="primary", use_container_width=True):
            st.cache_data.clear()
            st.success("All data refreshed from database!")
            st.rerun()

    today = date.today()
    year = st.selectbox("Year", options=list(range(today.year-3, today.year+3)), index=3)
    month = st.selectbox("Month", options=list(range(1,13)), index=today.month-1, format_func=lambda x: calendar.month_name[x])

    st.markdown("---")
    st.markdown(TABLE_CSS, unsafe_allow_html=True)

    # Load ALL bookings (cached but refreshable)
    with st.spinner("Loading all bookings from database..."):
        online_raw, direct_raw = load_all_bookings()

    if not online_raw and not direct_raw:
        st.warning("No bookings found in database.")
        return

    # Normalize all bookings
    all_normalized = []
    for b in online_raw:
        if is_relevant_status(b):
            all_normalized.append(normalize_booking(b, "online"))
    for b in direct_raw:
        if is_relevant_status(b):
            all_normalized.append(normalize_booking(b, "direct"))

    if not all_normalized:
        st.info("No Pending, Follow-up, or Confirmed/Not-Paid bookings found.")
        return

    # Get properties
    properties = sorted({b["property"] for b in all_normalized if b["property"]})

    # Generate dates for selected month
    month_dates = generate_month_dates(year, month)

    st.subheader(f"Pending / Follow-up / Confirmed (Not Paid) Bookings — {calendar.month_name[month]} {year}")

    for prop in properties:
        prop_bookings = [b for b in all_normalized if b["property"] == prop]
        
        if not prop_bookings:
            continue

        with st.expander(f"{prop} • {len(prop_bookings)} pending booking(s)", expanded=False):
            # Find which days have active bookings
            active_days = set()
            for b in prop_bookings:
                try:
                    ci = date.fromisoformat(b["check_in"])
                    co = date.fromisoformat(b["check_out"])
                    for d in month_dates:
                        if ci <= d < co:
                            active_days.add(d)
                except:
                    continue

            if not active_days:
                st.info("No active dates in selected month.")
                continue

            for day in sorted(active_days):
                daily = [b for b in prop_bookings 
                        if date.fromisoformat(b["check_in"]) <= day < date.fromisoformat(b["check_out"])]
                
                st.markdown(f"### {day.strftime('%A, %b %d')}")
                
                if daily:
                    df = create_bookings_table(daily)
                    if not df.empty:
                        html = df.to_html(escape=False, index=False)
                        st.markdown(f'<div class="custom-scrollable-table">{html}</div>', unsafe_allow_html=True)
                    st.caption(f"{len(daily)} booking(s) active on this date")
                else:
                    st.info("No active bookings")

# Run
if __name__ == "__main__":
    show_dms()
