# dms.py — FINAL CLEAN & BEAUTIFUL DMS (No Mess, Perfect Table)
import streamlit as st
from supabase import create_client
from datetime import date
import calendar

# Supabase
supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])

# Property name fix
property_fix = {
    "La Millionaire Luxury Resort": "La Millionaire Resort",
    "Le Poshe Beach View": "Le Poshe Beach view",
    "Le Poshe Beach VIEW": "Le Poshe Beach view",
    "Le Poshe Beachview": "Le Poshe Beach view",
    "Millionaire": "La Millionaire Resort"
}

# Clean & Professional CSS
st.markdown("""
<style>
.dms-container {font-family: 'Segoe UI', sans-serif;}
.dms-table table {width:100%; border-collapse: collapse; margin: 15px 0; background: white; box-shadow: 0 4px 12px rgba(0,0,0,0.1); border-radius: 10px; overflow: hidden;}
.dms-table th {background: #1e40af; color: white; padding: 14px 12px; text-align: left; font-weight: 600;}
.dms-table td {padding: 12px; border-bottom: 1px solid #eee;}
.dms-table tr:nth-child(even) {background: #f8fafc;}
.dms-table a {color: #1d4ed8; font-weight: 600; text-decoration: none;}
.dms-table a:hover {text-decoration: underline;}
.status-pending {background: #fff7ed; color: #9a3412; padding: 6px 10px; border-radius: 8px; font-size: 13px; font-weight: bold;}
.balance-red {color: #dc2626; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=600)
def load_bookings():
    try:
        online = supabase.table("online_reservations").select("*").execute().data or []
        direct = supabase.table("reservations").select("*").execute().data or []
        return online + direct
    except:
        st.error("Failed to connect to database.")
        return []

def is_pending(b):
    status = (b.get("booking_status") or b.get("plan_status") or "").strip()
    pay = (b.get("payment_status") or "").strip()
    return status in ["Pending", "Follow-up", "ON_HOLD"] or (status == "Confirmed" and pay != "Fully Paid")

def get_property(b):
    p = b.get("property") or b.get("property_name") or ""
    return property_fix.get(p, p)

def show_dms():
    st.title("Daily Management Status")
    
    if st.button("REFRESH DATA", type="primary"):
        st.cache_data.clear()
        st.success("Data refreshed!")
        st.rerun()

    today = date.today()
    year = st.selectbox("Year", range(today.year-2, today.year+3), index=2)
    month = st.selectbox("Month", range(1,13), format_func=lambda x: calendar.month_name[x], index=today.month-1)

    all_bookings = [b for b in load_bookings() if is_pending(b)]
    if not all_bookings:
        st.info("No pending bookings found.")
        return

    # Add display fields
    for b in all_bookings:
        b["prop"] = get_property(b)
        b["src"] = "Online" if b.get("booking_id", "").startswith("SF") else "Direct"
        b["balance"] = float(b.get("balance_due") or b.get("balance_amount") or 0)
        b["total"] = float(b.get("booking_amount") or b.get("total_tariff") or 0)

    properties = sorted({b["prop"] for b in all_bookings})
    dates_in_month = [date(year, month, d) for d in range(1, calendar.monthrange(year, month)[1]+1)]

    st.markdown(f"### {calendar.month_name[month]} {year} — **{len(all_bookings)} pending booking(s)**")

    for prop in properties:
        prop_bookings = [b for b in all_bookings if b["prop"] == prop]
        with st.expander(f"{prop} — {len(prop_bookings)} booking(s)", expanded=True):
            
            # Find active days
            active_days = set()
            for b in prop_bookings:
                try:
                    ci = date.fromisoformat(b["check_in"])
                    co = date.fromisoformat(b["check_out"])
                    for d in dates_in_month:
                        if ci <= d < co:
                            active_days.add(d)
                except: pass

            for day in sorted(active_days):
                day_bookings = [b for b in prop_bookings 
                              if date.fromisoformat(b["check_in"]) <= day < date.fromisoformat(b["check_out"])]

                st.subheader(f"{day.strftime('%A, %d %B %Y')} — {len(day_bookings)} booking(s)")

                rows = ""
                for b in day_bookings:
                    bid = b.get("booking_id") or b.get("id") or "N/A"
                    page = 28 if b["src"] == "Online" else 27
                    link = f'<a href="?page={page}&booking_id={bid}">{bid}</a>'
                    status = b.get("booking_status") or b.get("plan_status") or "Pending"
                    
                    rows += f"""
                    <tr>
                        <td>{b["src"]}</td>
                        <td>{link}</td>
                        <td><strong>{b.get("guest_name","")}</strong></td>
                        <td>{b.get("guest_phone") or b.get("mobile_no","")}</td>
                        <td>{b["check_in"]}</td>
                        <td>{b["check_out"]}</td>
                        <td>{b.get("room_no","")}</td>
                        <td>₹{b["total"]:,.0f}</td>
                        <td class="balance-red">₹{b["balance"]:,.0f}</td>
                        <td><span class="status-pending">{status}</span></td>
                        <td style="font-size:13px;color:#555;">{str(b.get("remarks",""))[:90]}{"..." if len(str(b.get("remarks","")))>90 else ""}</td>
                    </tr>
                    """

                st.markdown(f"""
                <div class="dms-table">
                <table>
                    <thead>
                        <tr>
                            <th>Source</th><th>Booking ID</th><th>Guest Name</th><th>Mobile</th>
                            <th>Check-In</th><th>Check-Out</th><th>Room</th><th>Total</th>
                            <th>Balance</th><th>Status</th><th>Remarks</th>
                        </tr>
                    </thead>
                    <tbody>{rows}</tbody>
                </table>
                </div>
                """, unsafe_allow_html=True)

# Run
show_dms()
