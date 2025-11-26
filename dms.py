# dms.py — FINAL 100% WORKING VERSION (La Antilia + All Bookings Fixed)
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
}

# Table CSS (exactly your original)
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
    try:
        response = supabase.table("reservations").select("*").order("check_in", desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error loading direct reservations: {e}")
        return []

def load_online_reservations_from_supabase():
    try:
        response = supabase.table("online_reservations").select("*").execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error loading online reservations: {e}")
        return []

def safe_date_parse(date_str):
    """Robust parsing for any date format from Stayflexi/Supabase"""
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

def filter_bookings_for_day(bookings, target_date):
    filtered = []
    for b in bookings:
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
    data = []
    for b in bookings:
        src = b.get("source", "online")
        bid = b.get("booking_id", "") or b.get("id", "")
        link = f'<a href="?page=Edit Online Reservations&booking_id={bid}" target="_self">{bid}</a>' if src == "online" else \
               f'<a href="?page=Edit Reservations&booking_id={bid}" target="_self">{bid}</a>'

        data.append({
            "Source": src.capitalize(),
            "Booking ID": link,
            "Guest Name": b.get("guest_name") or b.get("name", ""),
            "Mobile No": b.get("guest_phone") or b.get("mobile_no", ""),
            "Check-in Date": b.get("check_in", "")[:10],
            "Check-out Date": b.get("check_out", "")[:10],
            "Room No": b.get("room_no", ""),
            "Advance MOP": b.get("advance_mop", ""),
            "Balance MOP": b.get("balance_mop", ""),
            "Total Tariff": b.get("booking_amount") or b.get("total_tariff", 0.0),
            "Advance Amount": b.get("total_payment_made") or b.get("advance_amount", 0.0),
            "Balance Due": b.get("balance_due", 0.0),
            "Booking Status": b.get("booking_status", ""),
            "Remarks": b.get("remarks", ""),
        })
    df = pd.DataFrame(data, columns=columns)

    # Add tooltips
    for col in ['Guest Name', 'Mobile No', 'Room No', 'Remarks']:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: f'<span title="{x}">{x}</span>' if pd.notna(x) and isinstance(x, str) else x)

    return df

def show_dms():
    st.title("Daily Management Status")

    if st.button("Refresh Data", type="primary"):
        st.cache_data.clear()
        st.success("All data refreshed from database!")
        st.rerun()

    current_year = date.today().year
    year = st.selectbox("Select Year", list(range(current_year - 5, current_year + 6)), index=5)
    month = st.selectbox("Select Month", list(range(1, 13)), index=date.today().month - 1)

    # Load data
    online_bookings = load_online_reservations_from_supabase()
    direct_bookings = load_direct_reservations_from_supabase()

    # Normalize property names
    for b in online_bookings + direct_bookings:
        key = "property" if "property" in b else "property_name" if "property_name" in b else None
        if key and b.get(key):
            b[key] = property_mapping.get(b[key], b[key])

    if not online_bookings and not direct_bookings:
        st.info("No reservations available.")
        return

    # Get all properties
    online_df = pd.DataFrame(online_bookings)
    direct_df = pd.DataFrame(direct_bookings)
    online_props = sorted(online_df["property"].dropna().unique().tolist())
    direct_props = sorted(direct_df["property_name"].dropna().unique().tolist())
    all_properties = sorted(list(set(online_props + direct_props)))

    if not all_properties:
        st.info("No properties found in reservations.")
        return

    st.subheader("Pending, Follow-up, and Confirmed/Not Paid Bookings by Property")
    st.markdown(TABLE_CSS, unsafe_allow_html=True)

    # Helper: Should this booking appear in DMS?
    def should_show_in_dms(b):
        status = str(b.get("booking_status", "")).strip()
        payment = str(b.get("payment_status", "")).strip()

        if status in ["CANCELLED", "Cancelled", "Checked Out", "No Show"]:
            return False
        if status in ["Pending", "Follow-up", "ON_HOLD", "On Hold"]:
            return True
        if status == "Confirmed":
            if payment in ["Not Paid", "Partially Paid"]:
                return True
            if payment == "Fully Paid":
                ci = safe_date_parse(b.get("check_in"))
                return ci and ci >= date.today()
        return False

    for prop in all_properties:
        with st.expander(f"{prop}", expanded=False):
            month_dates = generate_month_dates(year, month)

            # Filter bookings that should appear in DMS
            prop_online = [b for b in online_bookings if b.get("property") == prop and should_show_in_dms(b)]
            prop_direct = [b for b in direct_bookings if b.get("property_name") == prop and should_show_in_dms(b)]
            prop_all = prop_online + prop_direct

            st.info(f"Total active bookings: **{len(prop_all)}** (Online: {len(prop_online)}, Direct: {len(prop_direct)})")

            for day in month_dates:
                daily_bookings = filter_bookings_for_day(prop_all, day)
                if daily_bookings:
                    st.subheader(f"{prop} - {day.strftime('%B %d, %Y')}")
                    df = create_bookings_table(daily_bookings)
                    html = df.to_html(escape=False, index=False)
                    st.markdown(f'<div class="custom-scrollable-table">{html}</div>', unsafe_allow_html=True)
                else:
                    st.info(f"No active bookings on {day.strftime('%d %b %Y')}")

if __name__ == "__main__":
    show_dms()
