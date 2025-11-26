# dms.py — ULTRA CLEAN & FINAL DMS (180 lines only)
import streamlit as st
from supabase import create_client
from datetime import date
import calendar

# ==================== SUPABASE ====================
supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])

# ==================== PROPERTY FIX ====================
property_fix = {
    "La Millionaire Luxury Resort": "La Millionaire Resort",
    "Le Poshe Beach View": "Le Poshe Beach view", "Le Poshe Beach VIEW": "Le Poshe Beach view",
    "Le Poshe Beachview": "Le Poshe Beach view", "Millionaire": "La Millionaire Resort"
}

# ==================== CLEAN CSS ====================
st.markdown("""
<style>
.dms-table table {width:100%; border-collapse:collapse; font-size:14px; background:white;}
.dms-table th {background:#1e40af; color:white; padding:12px 10px; position:sticky; top:0;}
.dms-table td {padding:10px; border-bottom:1px solid #eee;}
.dms-table tr:nth-child(even) {background:#f8fafc;}
.dms-table a {color:#1d4ed8; font-weight:600;}
.pending {background:#fef3c7; color:#92400e; padding:4px 8px; border-radius:6px; font-size:12px;}
</style>
""", unsafe_allow_html=True)

# ==================== LOAD & FILTER ====================
@st.cache_data(ttl=600)
def get_bookings():
    online = supabase.table("online_reservations").select("*").execute().data or []
    direct = supabase.table("reservations").select("*").execute().data or []
    return online + direct

def is_pending(b):
    status = (b.get("booking_status") or b.get("plan_status") or "").strip()
    pay = (b.get("payment_status") or "").strip()
    return status in ["Pending", "Follow-up", "ON_HOLD"] or (status == "Confirmed" and pay != "Fully Paid")

# ==================== MAIN ====================
def show_dms():
    st.title("Daily Management Status (DMS)")

    if st.button("REFRESH ALL DATA", type="primary"):
        st.cache_data.clear()
        st.success("Refreshed!")
        st.rerun()

    today = date.today()
    year = st.selectbox("Year", range(today.year-2, today.year+2), index=2)
    month = st.selectbox("Month", range(1,13), format_func=lambda x: calendar.month_name[x], index=today.month-1)

    bookings = [b for b in get_bookings() if is_pending(b)]
    if not bookings:
        st.info("No pending bookings found.")
        return

    # Fix property names
    for b in bookings:
        p = b.get("property") or b.get("property_name") or ""
        b["prop"] = property_fix.get(p, p)
        b["src"] = "Online" if "booking_id" in b and b["booking_id"].startswith("SF") else "Direct"

    props = sorted({b["prop"] for b in bookings if b["prop"]})
    dates = [date(year, month, d) for d in range(1, calendar.monthrange(year, month)[1]+1)]

    st.write(f"### {calendar.month_name[month]} {year} — **{len(bookings)} pending booking(s)**")

    for prop in props:
        pb = [b for b in bookings if b["prop"] == prop]
        with st.expander(f"{prop} — {len(pb)} booking(s)", expanded=True):
            active = set()
            for b in pb:
                try:
                    ci = date.fromisoformat(b["check_in"])
                    co = date.fromisoformat(b["check_out"])
                    for d in dates:
                        if ci <= d < co:
                            active.add(d)
                except: pass

            for day in sorted(active):
                day_b = [b for b in pb if date.fromisoformat(b["check_in"]) <= day < date.fromisoformat(b["check_out"])]
                st.markdown(f"#### {day.strftime('%A, %d %B')} — {len(day_b)} booking(s)")

                rows = ""
                for b in day_b:
                    bid = b.get("booking_id") or b.get("id") or "N/A"
                    page = 28 if b["src"] == "Online" else 27
                    link = f'<a href="?page={page}&booking_id={bid}">{bid}</a>'
                    status = b.get("booking_status") or b.get("plan_status") or "Pending"
                    bal = float(b.get("balance_due") or b.get("balance_amount") or 0)
                    
                    rows += f"""
                    <tr>
                        <td>{b["src"]}</td>
                        <td>{link}</td>
                        <td><strong>{b.get("guest_name","")}</strong></td>
                        <td>{b.get("guest_phone") or b.get("mobile_no","")}</td>
                        <td>{b["check_in"]}</td>
                        <td>{b["check_out"]}</td>
                        <td>{b.get("room_no","")}</td>
                        <td>₹{float(b.get("booking_amount") or b.get("total_tariff") or 0):,.0f}</td>
                        <td style="color:{"red" if bal>0 else "green"};font-weight:bold;">₹{bal:,.0f}</td>
                        <td><span class="pending">{status}</span></td>
                        <td style="font-size:12px;color:#555;">{str(b.get("remarks",""))[:80]}{"..." if len(str(b.get("remarks","")))>80 else ""}</td>
                    </tr>"""

                st.markdown(f"""
                <div class="dms-table">
                <table>
                    <tr><th>Source</th><th>ID</th><th>Guest</th><th>Mobile</th><th>In</th><th>Out</th><th>Room</th><th>Total</th><th>Balance</th><th>Status</th><th>Remarks</th></tr>
                    {rows}
                </table>
                </div>
                """, unsafe_allow_html=True)

# ==================== RUN ====================
show_dms()
