# dms.py — COMPLETE & FINAL DAILY MANAGEMENT STATUS (DMS)
import streamlit as st
from supabase import create_client, Client
from datetime import date
import calendar
import pandas as pd

# ==================== SUPABASE CLIENT ====================
try:
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except KeyError as e:
    st.error(f"Missing Supabase secret: {e}")
    st.stop()

# ==================== PROPERTY MAPPING (ALL CURRENT PROPERTIES) ====================
property_mapping = {
    "La Millionaire Luxury Resort": "La Millionaire Resort",
    "Le Poshe Beach View": "Le Poshe Beach view",
    "Le Poshe Beach VIEW": "Le Poshe Beach view",
    "Le Poshe Beachview": "Le Poshe Beach view",
    "Millionaire": "La Millionaire Resort",
    "La Antilia Luxury": "La Antilia Luxury",
    "Le Poshe Luxury": "Le Poshe Luxury",
    "La Tamara Luxury": "La Tamara Luxury",
    "La Paradise Residency": "La Paradise Residency",
    "La Paradise Luxury": "La Paradise Luxury",
    "La Villa Heritage": "La Villa Heritage",
    "Le Pondy Beach Side": "Le Pondy Beach Side",
    "Le Royce Villa": "Le Royce Villa",
    "La Tamara Suite": "La Tamara Suite",
    "Le Park Resort": "Le Park Resort",
    "Villa Shakti": "Villa Shakti",
    "Eden Beach Resort": "Eden Beach Resort",
    "Le Poshe Suite": "Le Poshe Suite"
}

# ==================== CSS ====================
TABLE_CSS = """
<style>
.custom-dms-table {
    overflow-x: auto;
    margin: 15px 0;
    border-radius: 10px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.custom-dms-table table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
    background: white;
}
.custom-dms-table th {
    background-color: #1e40af;
    color: white;
    padding: 12px 10px;
    text-align: left;
    font-weight: 600;
    position: sticky;
    top: 0;
    z-index: 10;
}
.custom-dms-table td {
    padding: 10px;
    border-bottom: 1px solid #eee;
}
.custom-dms-table tr:nth-child(even) {
    background-color: #f8fafc;
}
.custom-dms-table a {
    color: #1d4ed8;
    font-weight: 600;
    text-decoration: none;
}
.custom-dms-table a:hover {
    text-decoration: underline;
}
.pending-badge {
    background: #fef3c7;
    color: #92400e;
    padding: 4px 8px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: bold;
}
</style>
"""

# ==================== LOAD ALL BOOKINGS ====================
@st.cache_data(ttl=600)
def load_all_bookings():
    try:
        online = supabase.table("online_reservations").select("*").execute()
        direct = supabase.table("reservations").select("*").execute()
        return (online.data or []), (direct.data or [])
    except Exception as e:
        st.error(f"Database error: {e}")
        return [], []

# ==================== IS RELEVANT FOR DMS ====================
def is_relevant_for_dms(booking):
    status = (booking.get("booking_status") or booking.get("plan_status") or "").strip()
    payment = (booking.get("payment_status") or "").strip()
    return (
        status in ["Pending", "Follow-up", "ON_HOLD"] or
        (status == "Confirmed" and payment in ["Not Paid", "Partially Paid"])
    )

# ==================== NORMALIZE BOOKING ====================
def normalize_booking(b, source):
    prop_key = "property" if source == "online" else "property_name"
    prop = b.get(prop_key, "")
    prop = property_mapping.get(prop, prop) if prop else "Unknown"
    
    return {
        "id": b.get("booking_id") or b.get("id") or "N/A",
        "source": "Online" if source == "online" else "Direct",
        "property": prop,
        "guest_name": b.get("guest_name", ""),
        "mobile": b.get("guest_phone") or b.get("mobile_no", ""),
        "check_in": b.get("check_in", ""),
        "check_out": b.get("check_out", ""),
        "room_no": b.get("room_no", ""),
        "total_pax": int(b.get("total_pax") or b.get("no_of_adults", 0) + b.get("no_of_children", 0)),
        "amount": float(b.get("booking_amount") or b.get("total_tariff") or 0),
        "paid": float(b.get("total_payment_made") or b.get("advance_amount") or 0),
        "balance": float(b.get("balance_due") or b.get("balance_amount") or 0),
        "status": (b.get("booking_status") or b.get("plan_status", "")),
        "advance_mop": b.get("advance_mop", ""),
        "balance_mop": b.get("balance_mop", ""),
        "remarks": str(b.get("remarks") or "").replace("nan", ""),
        "source_table": source
    }

# ==================== BUILD TABLE HTML ====================
def create_table_html(bookings):
    if not bookings:
        return '<p style="color:#666;font-style:italic;">No bookings on this date.</p>'

    rows = ""
    for b in bookings:
        link = f'<a href="?page={"28" if b["source_table"]=="online" else "27"}&booking_id={b["id"]}">{b["id"]}</a>'
        badge = f'<span class="pending-badge">{b["status"]}</span>'
        
        rows += f"""
        <tr>
            <td>{b["source"]}</td>
            <td>{link}</td>
            <td><strong>{b["guest_name"]}</strong></td>
            <td>{b["mobile"]}</td>
            <td>{b["check_in"]}</td>
            <td>{b["check_out"]}</td>
            <td>{b["room_no"]}</td>
            <td>{b["total_pax"]}</td>
            <td>₹{b["amount"]:,.0f}</td>
            <td>₹{b["paid"]:,.0f}</td>
            <td style="color:red;font-weight:bold;">₹{b["balance"]:,.0f}</td>
            <td>{b["advance_mop"] or "-"} → {b["balance_mop"] or "-"}</td>
            <td>{badge}</td>
            <td style="font-size:12px;color:#555;">{b["remarks"][:100]}{"..." if len(b["remarks"])>100 else ""}</td>
        </tr>
        """

    return f"""
    <div class="custom-dms-table">
        <table>
            <thead>
                <tr>
                    <th>Source</th>
                    <th>Booking ID</th>
                    <th>Guest Name</th>
                    <th>Mobile</th>
                    <th>Check-In</th>
                    <th>Check-Out</th>
                    <th>Room</th>
                    <th>Pax</th>
                    <th>Total</th>
                    <th>Paid</th>
                    <th>Balance</th>
                    <th>MOP</th>
                    <th>Status</th>
                    <th>Remarks</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
    </div>
    """

# ==================== MAIN APP ====================
def show_dms():
    st.set_page_config(page_title="DMS", layout="wide")
    st.title("Daily Management Status (DMS)")

    col1, col2 = st.columns([1, 6])
    with col1:
        if st.button("FORCE REFRESH ALL DATA", type="primary", use_container_width=True):
            st.cache_data.clear()
            st.success("Data refreshed from database!")
            st.rerun()

    today = date.today()
    year = st.selectbox("Year", range(today.year-3, today.year+2), index=3)
    month = st.selectbox("Month", range(1,13), format_func=lambda x: calendar.month_name[x], index=today.month-1)

    st.markdown(TABLE_CSS, unsafe_allow_html=True)

    with st.spinner("Loading bookings..."):
        online_raw, direct_raw = load_all_bookings()

    all_relevant = []
    for b in online_raw:
        if is_relevant_for_dms(b):
            all_relevant.append(normalize_booking(b, "online"))
    for b in direct_raw:
        if is_relevant_for_dms(b):
            all_relevant.append(normalize_booking(b, "direct"))

    if not all_relevant:
        st.info("No pending or unpaid bookings found.")
        return

    properties = sorted({b["property"] for b in all_relevant})
    month_dates = [date(year, month, d) for d in range(1, calendar.monthrange(year, month)[1] + 1)]

    st.markdown(f"### {calendar.month_name[month]} {year} — {len(all_relevant)} pending booking(s)")

    for prop in properties:
        prop_bookings = [b for b in all_relevant if b["property"] == prop]
        with st.expander(f"{prop} — {len(prop_bookings)} booking(s)", expanded=True):
            active_days = set()
            for b in prop_bookings:
                try:
                    ci = date.fromisoformat(b["check_in"])
                    co = date.fromisoformat(b["check_out"])
                    for d in month_dates:
                        if ci <= d < co:
                            active_days.add(d)
                except:
                    pass

            if not active_days:
                st.write("No active dates.")
                continue

            for day in sorted(active_days):
                daily = [b for b in prop_bookings if date.fromisoformat(b["check_in"]) <= day < date.fromisoformat(b["check_out"])]
                st.markdown(f"#### {day.strftime('%A, %d %B %Y')} — {len(daily)} booking(s)")
                st.markdown(create_table_html(daily), unsafe_allow_html=True)

# ==================== RUN ====================
if __name__ == "__main__":
    show_dms()
