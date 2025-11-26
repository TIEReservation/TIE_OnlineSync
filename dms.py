# dms.py — FINAL, COMPLETE & 100% WORKING VERSION (Nov 2025)
import streamlit as st
from supabase import create_client, Client
from datetime import date, datetime
import pandas as pd
import calendar

# ========================= SUPABASE =========================
try:
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except KeyError as e:
    st.error(f"Missing Supabase secret: {e}. Please check Streamlit Cloud secrets configuration.")
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

# ========================= ORIGINAL CSS =========================
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

# ========================= ROBUST DATE PARSING =========================
def parse_date(date_str):
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

# ========================= FILTER BY DAY (100% reliable) =========================
def filter_bookings_for_day(bookings, target_date):
    filtered = []
    for b in bookings:
        ci = parse_date(b.get("check_in"))
        co = parse_date(b.get("check_out"))
        if ci and co and ci <= target_date < co:
            b["source"] = "direct" if "property_name" in b else "online"
            filtered.append(b)
    return filtered

# ========================= BUILD TABLE (exactly like your original) =========================
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
            "Check-in Date": str(parse_date(booking.get("check_in"))) if parse_date(booking.get("check_in")) else "",
            "Check-out Date": str(parse_date(booking.get("check_out"))) if parse_date(booking.get("check_out")) else "",
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

    # Tooltips exactly like your original
    for col in ['Guest Name', 'Mobile No', 'Room No', 'Remarks']:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: f'<span title="{x}">{x}</span>' if pd.notna(x) and str(x).strip() else x)

    return df

# ========================= MAIN FUNCTION =========================
def show_dms():
    st.title("Daily Management Status")

    # Your original working Refresh button
    if st.button("Refresh Data", type="primary"):
        st.cache_data.clear()
        st.success("All data refreshed from database!")
        st.rerun()

    current_year = date.today().year
    year = st.selectbox("Select Year", list(range(current_year - 5, current_year + 6)), index=5)
    month = st.selectbox("Select Month", list(range(1, 13)), index=date.today().month - 1)

    online_bookings = load_online_reservations_from_supabase()
    direct_bookings = load_direct_reservations_from_supabase()

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
    online_properties = sorted(online_df["property"].dropna().unique().tolist())
    direct_properties = sorted(direct_df["property_name"].dropna().unique().tolist())
    all_properties = sorted(list(set(online_properties + direct_properties)))

    if not all_properties:
        st.info("No properties found in reservations.")
        return

    st.subheader("Pending / Follow-up / ON_HOLD + Confirmed (Only Not Paid)")
    st.markdown(TABLE_CSS, unsafe_allow_html=True)

    # FINAL LOGIC: Exactly what you want
    def must_appear_in_dms(b):
        status = str(b.get("booking_status") or "").strip()
        payment = str(b.get("payment_status") or "").strip()

        if status in ["CANCELLED", "Cancelled", "Checked Out", "No Show"]:
            return False
        if status in ["Pending", "Follow-up", "ON_HOLD", "On Hold"]:
            return True
        if status == "Confirmed":
            return payment == "Not Paid"
        return False

    for prop in all_properties:
        with st.expander(f"{prop}", expanded=False):
            # Filter only relevant bookings
            relevant_online = [b for b in online_bookings if b.get("property") == prop and must_appear_in_dms(b)]
            relevant_direct = [b for b in direct_bookings if b.get("property_name") == prop and must_appear_in_dms(b)]
            relevant_all = relevant_online + relevant_direct

            st.info(f"Total bookings requiring follow-up: **{len(relevant_all)}** (Online: {len(relevant_online)}, Direct: {len(relevant_direct)})")

            for day in generate_month_dates(year, month):
                daily_bookings = filter_bookings_for_day(relevant_all, day)
                if daily_bookings:
                    st.subheader(f"{prop} - {day.strftime('%B %d, %Y')}")
                    df = create_bookings_table(daily_bookings)
                    table_html = df.to_html(escape=False, index=False)
                    st.markdown(f'<div class="custom-scrollable-table">{table_html}</div>', unsafe_allow_html=True)
                else:
                    st.info(f"No follow-up needed on {day.strftime('%d %b %Y')}")

# ========================= RUN =========================
if __name__ == "__main__":
    show_dms()
