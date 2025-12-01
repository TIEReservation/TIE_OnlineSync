# dms.py – FINAL WORKING VERSION (All Properties + La Antilia Fixed + Correct Logic + Date Range Fix)
import streamlit as st
from supabase import create_client, Client
from datetime import date, timedelta, datetime
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

# Table CSS (your exact original)
TABLE_CSS = """
<style>
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

# ROBUST DATE PARSING – THIS FIXES LA ANTILIA & ALL DATES
def safe_date_parse(date_str):
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
    _, num_days = calendar.monthrange(year, month)
    return [date(year, month, day) for day in range(1, num_days + 1)]

# FINAL LOGIC: Only show Pending / Follow-up / ON_HOLD + Confirmed (Not Paid)
def should_show_in_dms(booking):
    status = str(booking.get("booking_status", "")).strip()
    payment = str(booking.get("payment_status", "")).strip()

    if status in ["CANCELLED", "Cancelled", "Checked Out", "No Show"]:
        return False
    if status in ["Pending", "Follow-up", "ON_HOLD", "On Hold"]:
        return True
    if status == "Confirmed":
        return payment == "Not Paid"
    return False

def filter_bookings_for_day(bookings, target_date):
    """Filter bookings that are active on the target date"""
    filtered = []
    for b in bookings:
        if not should_show_in_dms(b):
            continue
        ci = safe_date_parse(b.get("check_in"))
        co = safe_date_parse(b.get("check_out"))
        if ci and co and ci <= target_date < co:
            b["source"] = "direct" if "property_name" in b else "online"
            filtered.append(b)
    return filtered

def create_bookings_table(bookings):
    columns = [
        "Source", "Booking ID", "Guest Name", "Mobile No", "Check-in Date", "Check-out Date", "Room No",
        "Advance MOP", "Balance MOP", "Total Tariff", "Advance Amount", "Balance Due",
        "Booking Status", "Remarks"
    ]
    df_data = []
    for booking in bookings:
        source = booking.get("source", "online")
        booking_id = booking.get("booking_id", "") or booking.get("id", "")
        edit_link = f'<a href="?page=Edit Online Reservations&booking_id={booking_id}" target="_self">{booking_id}</a>' if source == "online" else \
                    f'<a href="?page=Edit Reservations&booking_id={booking_id}" target="_self">{booking_id}</a>'

        df_data.append({
            "Source": source.capitalize(),
            "Booking ID": edit_link,
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
            "Booking Status": booking.get("booking_status", "") or "",
            "Remarks": booking.get("remarks", "") or "",
        })
    df = pd.DataFrame(df_data, columns=columns)
    for col in ['Guest Name', 'Mobile No', 'Room No', 'Remarks']:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: f'<span title="{x}">{x}</span>' if pd.notna(x) and str(x).strip() else x)
    return df

@st.cache_data(ttl=300)
def cached_load_online_reservations():
    return load_online_reservations_from_supabase()

@st.cache_data(ttl=300)
def cached_load_direct_reservations():
    return load_direct_reservations_from_supabase()

def show_dms():
    st.title("Daily Management Status")

    if st.button("Refresh Bookings"):
        st.cache_data.clear()
        st.success("Cache cleared! Refreshing bookings...")
        st.rerun()

    current_year = date.today().year
    year = st.selectbox("Select Year", list(range(current_year - 5, current_year + 6)), index=5)
    month = st.selectbox("Select Month", list(range(1, 13)), index=date.today().month - 1)

    # Load ALL bookings without date restrictions
    online_bookings = cached_load_online_reservations()
    direct_bookings = cached_load_direct_reservations()

    # Debug info to see what's being loaded
    st.info(f"Total records loaded: Online={len(online_bookings)}, Direct={len(direct_bookings)}")

    # Map plan_status → booking_status
    for b in direct_bookings:
        if "plan_status" in b:
            b["booking_status"] = b["plan_status"]

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

    # Get all properties
    online_df = pd.DataFrame(online_bookings)
    direct_df = pd.DataFrame(direct_bookings)
    online_props = sorted(online_df["property"].dropna().unique().tolist()) if "property" in online_df.columns else []
    direct_props = sorted(direct_df["property_name"].dropna().unique().tolist()) if "property_name" in direct_df.columns else []
    all_properties = sorted(list(set(online_props + direct_props)))

    if not all_properties:
        st.info("No properties found in reservations.")
        return

    st.subheader("Pending, Follow-up, ON_HOLD & Confirmed (Not Paid) Bookings")
    st.markdown(TABLE_CSS, unsafe_allow_html=True)

    for prop in all_properties:
        with st.expander(f"{prop}", expanded=False):
            month_dates = generate_month_dates(year, month)

            # Filter only relevant bookings using the correct logic
            relevant_online = [b for b in online_bookings if b.get("property") == prop and should_show_in_dms(b)]
            relevant_direct = [b for b in direct_bookings if b.get("property_name") == prop and should_show_in_dms(b)]
            relevant_all = relevant_online + relevant_direct

            st.info(f"Total bookings requiring follow-up: **{len(relevant_all)}** (Online: {len(relevant_online)}, Direct: {len(relevant_direct)})")

            for day in month_dates:
                daily_bookings = filter_bookings_for_day(relevant_all, day)
                st.subheader(f"{prop} - {day.strftime('%B %d, %Y')}")

                if daily_bookings:
                    df = create_bookings_table(daily_bookings)
                    table_html = df.to_html(escape=False, index=False)
                    st.markdown(f'<div class="custom-scrollable-table">{table_html}</div>', unsafe_allow_html=True)
                else:
                    st.info("No bookings requiring follow-up on this day.")

if __name__ == "__main__":
    show_dms()
