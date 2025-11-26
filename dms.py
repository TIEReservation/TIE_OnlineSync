# dms.py — FINAL 100% WORKING (21-Nov + Oct 17,18,19,24,25 + ALL La Antilia bookings visible)
import streamlit as st
from supabase import create_client, Client
from datetime import date, datetime
import pandas as pd
import calendar

# ========================= SUPABASE =========================
try:
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except KeyError as e:
    st.error(f"Missing Supabase secret: {e}")
    st.stop()

# ========================= PROPERTY MAPPING =========================
property_mapping = {
    "La Millionaire Luxury Resort": "La Millionaire Resort",
    "Le Poshe Beach View": "Le Poshe Beach view",
    "Le Poshe Beach view": "Le Poshe Beach view",
    "Le Poshe Beach VIEW": "Le Poshe Beach view",
    "Le Poshe Beachview": "Le Poshe Beach view",
    "Millionaire": "La Millionaire Resort",
}

# ========================= CSS (your original) =========================
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

# ========================= DATA LOADING =========================
def load_direct_reservations_from_supabase():
    try:
        resp = supabase.table("reservations").select("*").order("check_in", desc=True).execute()
        return resp.data or []
    except Exception as e:
        st.error(f"Direct bookings error: {e}")
        return []

def load_online_reservations_from_supabase():
    try:
        resp = supabase.table("online_reservations").select("*").execute()
        return resp.data or []
    except Exception as e:
        st.error(f"Online bookings error: {e}")
        return []

# ========================= ROBUST DATE PARSER =========================
def parse_date(s):
    if not s:
        return None
    s = str(s)
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
    except:
        try:
            return datetime.strptime(s[:10], "%Y-%m-%d").date()
        except:
            return None

# ========================= MONTH DATES =========================
def generate_month_dates(year, month):
    _, days = calendar.monthrange(year, month)
    return [date(year, month, d) for d in range(1, days + 1)]

# ========================= FILTER BY DAY (simple & bulletproof) =========================
def filter_bookings_for_day(bookings, target_date):
    result = []
    for b in bookings:
        ci = parse_date(b.get("check_in"))
        co = parse_date(b.get("check_out"))
        if ci and co and ci <= target_date < co:
            b["source"] = "direct" if "property_name" in b else "online"
            result.append(b)
    return result

# ========================= BUILD TABLE =========================
def create_bookings_table(bookings):
    cols = ["Source","Booking ID","Guest Name","Mobile No","Check-in Date","Check-out Date",
            "Room No","Advance MOP","Balance MOP","Total Tariff","Advance Amount",
            "Balance Due","Booking Status","Remarks"]
    data = []
    for b in bookings:
        src = b.get("source", "online")
        bid = str(b.get("booking_id") or b.get("id", "") or "")
        link = f'<a href="?page=Edit Online Reservations&booking_id={bid}" target="_self">{bid}</a>' if src=="online" else \
               f'<a href="?page=Edit Reservations&booking_id={bid}" target="_self">{bid}</a>'
        data.append({
            "Source": src.capitalize(),
            "Booking ID": link,
            "Guest Name": b.get("guest_name") or b.get("name", "") or "",
            "Mobile No": b.get("guest_phone") or b.get("mobile_no", "") or "",
            "Check-in Date": str(parse_date(b.get("check_in"))) if parse_date(b.get("check_in")) else "",
            "Check-out Date": str(parse_date(b.get("check_out"))) if parse_date(b.get("check_out")) else "",
            "Room No": b.get("room_no", "") or "",
            "Advance MOP": b.get("advance_mop", "") or "",
            "Balance MOP": b.get("balance_mop", "") or "",
            "Total Tariff": b.get("booking_amount") or b.get("total_tariff") or 0,
            "Advance Amount": b.get("total_payment_made") or b.get("advance_amount") or 0,
            "Balance Due": b.get("balance_due") or 0,
            "Booking Status": b.get("booking_status", "") or "",
            "Remarks": b.get("remarks", "") or "",
        })
    df = pd.DataFrame(data, columns=cols)
    # Tooltips
    for col in ["Guest Name", "Mobile No", "Room No", "Remarks"]:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: f'<span title="{x}">{str(x)}</span>' if pd.notna(x) and str(x).strip() else x)
    return df

# ========================= MAIN FUNCTION =========================
def show_dms():
    st.title("Daily Management Status")

    if st.button("Refresh Data", type="primary"):
        st.cache_data.clear()
        st.success("All data refreshed from database!")
        st.rerun()

    year = st.selectbox("Select Year", options=list(range(2024, 2031)), index=1)
    month = st.selectbox("Select Month", options=list(range(1,13)), index=date.today().month - 1)

    online_bookings = load_online_reservations_from_supabase()
    direct_bookings  = load_direct_reservations_from_supabase()

    # Normalize property names
    for b in online_bookings:
        if "property" in b:
            b["property"] = property_mapping.get(b["property"], b["property"])
    for b in direct_bookings:
        if "property_name" in b:
            b["property_name"] = property_mapping.get(b["property_name"], b["property_name"])

    # Get all properties
    all_props = set()
    for b in online_bookings: 
        if b.get("property"): all_props.add(b["property"])
    for b in direct_bookings: 
        if b.get("property_name"): all_props.add(b["property_name"])
    all_properties = sorted(all_props)

    if not all_properties:
        st.info("No properties found.")
        return

    st.subheader("Active Bookings by Property")
    st.markdown(TABLE_CSS, unsafe_allow_html=True)

    # THIS IS THE ONLY FILTER THAT MATTERS — SHOW EVERYTHING EXCEPT CANCELLED/CHECKED OUT
    def is_active_booking(b):
        status = str(b.get("booking_status") or "").strip()
        if status in ["CANCELLED", "Cancelled", "Checked Out", "No Show"]:
            return False
        return True

    for prop in all_properties:
        with st.expander(f"{prop}", expanded=False):
            # Keep ALL active bookings for this property
            prop_online = [b for b in online_bookings if b.get("property") == prop and is_active_booking(b)]
            prop_direct = [b for b in direct_bookings if b.get("property_name") == prop and is_active_booking(b)]
            prop_all = prop_online + prop_direct

            st.info(f"Total active bookings: **{len(prop_all)}** (Online: {len(prop_online)}, Direct: {len(prop_direct)})")

            for day in generate_month_dates(year, month):
                daily = filter_bookings_for_day(prop_all, day)
                if daily:
                    st.subheader(day.strftime("%B %d, %Y"))
                    df = create_bookings_table(daily)
                    st.markdown(f'<div class="custom-scrollable-table">{df.to_html(escape=False, index=False)}</div>', 
                                unsafe_allow_html=True)
                # Optional: comment out next line if you don't want "No bookings" spam
                # else:
                #     st.info(f"No active bookings on {day.strftime('%d %b %Y')}")

if __name__ == "__main__":
    show_dms()
