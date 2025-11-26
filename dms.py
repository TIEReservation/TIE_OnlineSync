# dms.py — ORIGINAL LOOK + WORKING REFRESH BUTTON (FINAL)
import streamlit as st
from supabase import create_client, Client
from datetime import date, timedelta
from datetime import datetime
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

def generate_month_dates(year, month):
    _, num_days = calendar.monthrange(year, month)
    return [date(year, month, day) for day in range(1, num_days + 1)]

def filter_bookings_for_day(bookings, target_date):
    filtered_bookings = []
    for booking in bookings:
        status = booking.get("booking_status", "")
        payment = booking.get("payment_status", "")

        # Skip cancelled/no-show
        if status in ["CANCELLED", "Cancelled", "Checked Out", "No Show"]:
            continue

        # Include logic (same as before but simpler)
        if status in ["Pending", "Follow-up", "ON_HOLD", "On Hold"]:
            include = True
        elif status == "Confirmed":
            include = (payment in ["Not Paid", "Partially Paid"]) or \
                     (payment == "Fully Paid" and booking.get("check_in", "").split("T")[0] >= str(target_date))
        else:
            include = False

        if not include:
            continue

        # ROBUST DATE PARSING — THIS IS THE KEY FIX
        ci_str = booking.get("check_in", "")
        co_str = booking.get("check_out", "")

        if not ci_str or not co_str:
            continue

        try:
            # Handle any format: 2025-10-17, 2025-10-17 05:30:00, 2025-10-17T00:00:00.000Z
            check_in = datetime.fromisoformat(ci_str.replace("Z", "+00:00")).date()
            check_out = datetime.fromisoformat(co_str.replace("Z", "+00:00")).date()
        except:
            # Fallback: try stripping everything after space or T
            try:
                check_in = datetime.strptime(ci_str.split("T")[0].split()[0], "%Y-%m-%d").date()
                check_out = datetime.strptime(co_str.split("T")[0].split()[0], "%Y-%m-%d").date()
            except:
                continue  # completely malformed → skip

        if check_in <= target_date < check_out:
            booking["source"] = "direct" if "property_name" in booking else "online"
            filtered_bookings.append(booking)

    return filtered_bookings
def create_bookings_table(bookings):
    columns = [
        "Source", "Booking ID", "Guest Name", "Mobile No", "Check-in Date", "Check-out Date", "Room No",
        "Advance MOP", "Balance MOP", "Total Tariff", "Advance Amount", "Balance Due",
        "Booking Status", "Remarks"
    ]
    df_data = []
    for booking in bookings:
        booking_id = booking.get("booking_id", "")
        source = booking.get("source", "online")
        if source == "online":
            edit_link = f'<a href="?page=Edit Online Reservations&booking_id={booking_id}" target="_self">{booking_id}</a>'
        else:
            edit_link = f'<a href="?page=Edit Reservations&booking_id={booking_id}" target="_self">{booking_id}</a>'
        guest_name = booking.get("guest_name", "")
        mobile_no = booking.get("guest_phone") if source == "online" else booking.get("mobile_no", "")
        check_in_date = booking.get("check_in", "")
        check_out_date = booking.get("check_out", "")
        room_no = booking.get("room_no", "")
        advance_mop = booking.get("advance_mop", "")
        balance_mop = booking.get("balance_mop", "")
        total_tariff = booking.get("booking_amount") if source == "online" else booking.get("total_tariff", 0.0)
        advance_amount = booking.get("total_payment_made") if source == "online" else booking.get("advance_amount", 0.0)
        balance_due = booking.get("balance_due", 0.0)
        booking_status = booking.get("booking_status", "")
        remarks = booking.get("remarks", "")
        df_data.append({
            "Source": source.capitalize(),
            "Booking ID": edit_link,
            "Guest Name": guest_name,
            "Mobile No": mobile_no,
            "Check-in Date": check_in_date,
            "Check-out Date": check_out_date,
            "Room No": room_no,
            "Advance MOP": advance_mop,
            "Balance MOP": balance_mop,
            "Total Tariff": total_tariff,
            "Advance Amount": advance_amount,
            "Balance Due": balance_due,
            "Booking Status": booking_status,
            "Remarks": remarks
        })
    return pd.DataFrame(df_data, columns=columns)

# ——— REFRESH BUTTON AT THE TOP (LIKE INVENTORY PAGE) ———
def show_dms():
    st.title("Daily Management Status")

    # THIS IS THE WORKING REFRESH BUTTON (exactly like your inventory page)
    if st.button("Refresh Data", type="primary"):
        st.cache_data.clear()
        st.success("All data refreshed from database!")
        st.rerun()

    current_year = date.today().year
    year = st.selectbox("Select Year", list(range(current_year - 5, current_year + 6)), index=5)
    month = st.selectbox("Select Month", list(range(1, 13)), index=date.today().month - 1)

    # Load fresh data every time (no caching issues)
    online_bookings = load_online_reservations_from_supabase()
    direct_bookings = load_direct_reservations_from_supabase()

    # Map plan_status → booking_status for direct
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
    online_properties = sorted(online_df["property"].dropna().unique().tolist())
    direct_properties = sorted(direct_df["property_name"].dropna().unique().tolist())
    all_properties = sorted(list(set(online_properties + direct_properties)))

    if not all_properties:
        st.info("No properties found in reservations.")
        return

    st.subheader("Pending, Follow-up, and Confirmed/Not Paid Bookings by Property")
    st.markdown(TABLE_CSS, unsafe_allow_html=True)

    for prop in all_properties:
        with st.expander(f"{prop}"):
            month_dates = generate_month_dates(year, month)

            # Filter relevant bookings for this property
            prop_online_bookings = [b for b in online_bookings if b.get("property") == prop and
                                   (b.get("booking_status") in ["Pending", "Follow-up"] or
                                    (b.get("booking_status") == "Confirmed" and b.get("payment_status") == "Not Paid"))]
            prop_direct_bookings = [b for b in direct_bookings if b.get("property_name") == prop and
                                   (b.get("booking_status") in ["Pending", "Follow-up"] or
                                    (b.get("booking_status") == "Confirmed" and b.get("payment_status") == "Not Paid"))]

            prop_all_bookings = prop_online_bookings + prop_direct_bookings
            st.info(f"Total Pending/Follow-up/Unpaid bookings: {len(prop_all_bookings)} (Online: {len(prop_online_bookings)}, Direct: {len(prop_direct_bookings)})")

            for day in month_dates:
                daily_bookings = filter_bookings_for_day(prop_all_bookings, day)
                st.subheader(f"{prop} - {day.strftime('%B %d, %Y')}")

                if daily_bookings:
                    df = create_bookings_table(daily_bookings)
                    # Tooltips
                    for col in ['Guest Name', 'Mobile No', 'Room No', 'Remarks']:
                        if col in df.columns:
                            df[col] = df[col].apply(lambda x: f'<span title="{x}">{x}</span>' if isinstance(x, str) else x)
                    table_html = df.to_html(escape=False, index=False)
                    st.markdown(f'<div class="custom-scrollable-table">{table_html}</div>', unsafe_allow_html=True)
                else:
                    st.info("No Pending, Follow-up, or Confirmed/Not Paid bookings on this day.")

# Run
if __name__ == "__main__":
    show_dms()
