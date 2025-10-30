# inventory.py
import streamlit as st
from supabase import create_client, Client
from datetime import date
import calendar
import pandas as pd
from typing import Any, List, Dict
import logging

# Configure logging
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Supabase
try:
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except KeyError as e:
    st.error(f"Missing Supabase secret: {e}")
    st.stop()

# Property synonym mapping
property_mapping = {
    "La Millionaire Luxury Resort": "La Millionaire Resort",
    "Le Poshe Beach View": "Le Poshe Beach view",
    "Le Poshe Beach view": "Le Poshe Beach view",
    "Le Poshe Beach VIEW": "Le Poshe Beach view",
    "Millionaire": "La Millionaire Resort",
}
reverse_mapping = {}
for variant, canonical in property_mapping.items():
    reverse_mapping.setdefault(canonical, []).append(variant)

# MOP & MOB mappings
mop_mapping = {
    "UPI": ["UPI"],
    "Cash": ["Cash"],
    "Go-MMT": ["Goibibo", "MMT", "Go-MMT", "MAKEMYTRIP"],
    "Agoda": ["Agoda"],
    "NOT PAID": ["Not Paid"],
    "Bank Transfer": ["Bank Transfer"],
    "Stayflexi": ["STAYFLEXI_GHA"],
    "Card Payment": ["Card"],
    "Expedia": ["Expedia"],
    "Cleartrip": ["Cleartrip"],
    "Website": ["Stayflexi Booking Engine"]
}

mob_mapping = {
    "Booking": ["BOOKING"],
    "Direct": ["Direct"],
    "Bkg-Direct": ["Bkg-Direct"],
    "Agoda": ["Agoda"],
    "Go-MMT": ["Goibibo", "MMT", "Go-MMT", "MAKEMYTRIP"],
    "Walk-In": ["Walk-In"],
    "TIE Group": ["TIE Group"],
    "Stayflexi": ["STAYFLEXI_GHA"],
    "Airbnb": ["Airbnb"],
    "Social Media": ["Social Media"],
    "Expedia": ["Expedia"],
    "Cleartrip": ["Cleartrip"],
    "Website": ["Stayflexi Booking Engine"]
}

TABLE_CSS = """
<style>
.custom-scrollable-table {overflow-x: auto; max-width: 100%; min-width: 800px;}
.custom-scrollable-table table {table-layout: auto; border-collapse: collapse;}
.custom-scrollable-table td, .custom-scrollable-table th {
    white-space: nowrap; text-overflow: ellipsis; overflow: hidden;
    max-width: 150px; padding: 8px; border: 1px solid #ddd;
}
</style>
"""

# Full inventory
PROPERTY_INVENTORY = {
    "Le Poshe Beach view": {"all": ["101", "102", "201", "202", "203", "204", "301", "302", "303", "304", "Day Use 1", "Day Use 2", "No Show"], "three_bedroom": ["203", "204"]},
    "La Millionaire Resort": {"all": ["101", "102", "103", "105", "201", "202", "203", "204", "205", "206", "207", "208", "301", "302", "303", "304", "305", "306", "307", "308", "401", "402", "Day Use 1", "Day Use 2", "Day Use 3", "Day Use 4", "Day Use 5", "No Show"], "three_bedroom": ["203", "204", "205"]},
    "Le Poshe Luxury": {"all": ["101", "102", "201", "202", "203", "204", "205", "301", "302", "303", "304", "305", "401", "402", "403", "404", "405", "501", "Day Use 1", "Day Use 2", "No Show"], "three_bedroom": ["203", "204", "205"]},
    "Le Poshe Suite": {"all": ["601", "602", "603", "604", "701", "702", "703", "704", "801", "Day Use 1", "Day Use 2", "No Show"], "three_bedroom": []},
    "La Paradise Residency": {"all": ["101", "102", "103", "201", "202", "203", "301", "302", "303", "304", "Day Use 1", "Day Use 2", "No Show"], "three_bedroom": ["203"]},
    "La Paradise Luxury": {"all": ["101", "102", "103", "201", "202", "203", "Day Use 1", "Day Use 2", "No Show"], "three_bedroom": ["203"]},
    "La Villa Heritage": {"all": ["101", "102", "103", "201", "202", "203", "301", "Day Use 1", "Day Use 2", "No Show"], "three_bedroom": ["203"]},
    "Le Pondy Beach Side": {"all": ["101", "102", "201", "202", "Day Use 1", "Day Use 2", "No Show"], "three_bedroom": []},
    "Le Royce Villa": {"all": ["101", "102", "201", "202", "Day Use 1", "Day Use 2", "No Show"], "three_bedroom": []},
    "La Tamara Luxury": {"all": ["101", "102", "103", "104", "105", "106", "201", "202", "203", "204", "205", "206", "301", "302", "303", "304", "305", "306", "401", "402", "403", "404", "Day Use 1", "Day Use 2", "No Show"], "three_bedroom": ["203", "204", "205", "206"]},
    "La Antilia Luxury": {"all": ["101", "201", "202", "203", "204", "301", "302", "303", "304", "401", "Day Use 1", "Day Use 2", "No Show"], "three_bedroom": ["203", "204"]},
    "La Tamara Suite": {"all": ["101", "102", "103", "104", "201", "202", "203", "204", "205", "206", "Day Use 1", "Day Use 2", "No Show"], "three_bedroom": ["203", "204", "205", "206"]},
    "Le Park Resort": {"all": ["111", "222", "333", "444", "555", "666", "Day Use 1", "Day Use 2", "No Show"], "three_bedroom": []},
    "Villa Shakti": {"all": ["101", "102", "201", "201A", "202", "203", "301", "301A", "302", "303", "401", "Day Use 1", "Day Use 2", "No Show"], "three_bedroom": ["203"]},
    "Eden Beach Resort": {"all": ["101", "102", "103", "201", "202", "Day Use 1", "Day Use 2", "No Show"], "three_bedroom": []}
}

def initialize_property_inventory(properties: List[str]) -> None:
    for prop in properties:
        if prop not in PROPERTY_INVENTORY:
            PROPERTY_INVENTORY[prop] = {"all": ["Unknown"], "three_bedroom": []}
            logging.warning(f"Added fallback inventory for unknown property: {prop}")

def sanitize_string(value: Any, default: str = "Unknown") -> str:
    return str(value).strip() if value is not None else default

def safe_int(value: Any, default: int = 0) -> int:
    try: return int(value) if value is not None else default
    except (ValueError, TypeError): return default

def safe_float(value: Any, default: float = 0.0) -> float:
    try: return float(value) if value is not None else default
    except (ValueError, TypeError): return default

def format_booking_id(booking: Dict) -> str:
    booking_id = sanitize_string(booking.get('booking_id'))
    return f'<a target="_blank" href="/?edit_type={booking["type"]}&booking_id={booking_id}">{booking_id}</a>'

def load_properties() -> List[str]:
    try:
        res_direct = supabase.table("reservations").select("property_name").execute().data
        res_online = supabase.table("online_reservations").select("property").execute().data
        properties = set()
        for r in res_direct + res_online:
            prop = r.get('property_name') or r.get('property')
            if prop:
                canonical = property_mapping.get(prop.strip(), prop.strip())
                properties.add(canonical)
        properties = sorted(properties)
        initialize_property_inventory(properties)
        return properties
    except Exception as e:
        st.error(f"Error loading properties: {e}")
        return []

def normalize_booking(booking: Dict, is_online: bool) -> Dict:
    booking_id = sanitize_string(booking.get('booking_id'))

    # FILTER: Skip Cancelled or Not Paid
    payment_status = sanitize_string(booking.get('payment_status')).title()
    if payment_status not in ["Fully Paid", "Partially Paid"]:
        logging.info(f"Skipping booking {booking_id} - Payment Status: {payment_status}")
        return None

    booking_status_field = 'booking_status' if is_online else 'plan_status'
    booking_status = sanitize_string(booking.get(booking_status_field))
    if booking_status.upper() == "CANCELLED":
        logging.info(f"Skipping booking {booking_id} - Booking Status: Cancelled")
        return None

    try:
        check_in = date.fromisoformat(booking.get('check_in')) if booking.get('check_in') else None
        check_out = date.fromisoformat(booking.get('check_out')) if booking.get('check_out') else None
        if not check_in or not check_out:
            logging.warning(f"Skipping booking {booking_id} - missing check-in/out")
            return None
        days = (check_out - check_in).days
        if days <= 0:
            days = 1

        property_name = sanitize_string(booking.get('property', booking.get('property_name', '')))
        property_name = property_mapping.get(property_name, property_name)

        total_tariff = safe_float(booking.get('total_amount_with_services', booking.get('booking_amount', 0.0))) or safe_float(booking.get('total_tariff', 0.0))
        commission = safe_float(booking.get('ota_commission', 0.0))
        receivable = total_tariff - commission
        per_night = receivable / days if days else 0.0

        return {
            "type": "online" if is_online else "direct",
            "property": property_name,
            "booking_id": booking_id,
            "guest_name": sanitize_string(booking.get('guest_name', '')),
            "mobile_no": sanitize_string(booking.get('guest_phone', booking.get('mobile_no', ''))),
            "total_pax": safe_int(booking.get('total_pax', 0)),
            "check_in": str(check_in),
            "check_out": str(check_out),
            "days": days,
            "room_no": sanitize_string(booking.get('room_no', '')).title(),
            "mob": sanitize_string(booking.get('mode_of_booking', booking.get('mob', ''))),
            "room_charges": total_tariff,
            "gst": safe_float(booking.get('ota_tax', 0.0)) if is_online else 0.0,
            "total": total_tariff,
            "commission": commission,
            "receivable": receivable,
            "per_night": per_night,
            "advance": safe_float(booking.get('total_payment_made', 0.0)) or safe_float(booking.get('advance_amount', 0.0)),
            "advance_mop": sanitize_string(booking.get('advance_mop', '')),
            "balance": safe_float(booking.get('balance_due', 0.0)) or safe_float(booking.get('balance_amount', 0.0)),
            "balance_mop": sanitize_string(booking.get('balance_mop', '')),
            "plan": sanitize_string(booking.get('rate_plans', booking.get('plan', ''))),
            "booking_status": booking_status,
            "payment_status": payment_status,
            "submitted_by": sanitize_string(booking.get('submitted_by', '')),
            "modified_by": sanitize_string(booking.get('modified_by', '')),
            "remarks": sanitize_string(booking.get('remarks', ''))
        }
    except Exception as e:
        logging.warning(f"Skipping booking {booking_id} due to error: {e}")
        return None

def load_combined_bookings(property: str, start_date: date, end_date: date) -> List[Dict]:
    try:
        query_props = [property] + reverse_mapping.get(property, [])
        bookings = []
        for qp in query_props:
            online = supabase.table("online_reservations").select("*").eq("property", qp).gte("check_in", str(start_date)).lte("check_out", str(end_date)).execute().data
            direct = supabase.table("reservations").select("*").eq("property_name", qp).gte("check_in", str(start_date)).lte("check_out", str(end_date)).execute().data
            bookings.extend([normalize_booking(b, True) for b in online if normalize_booking(b, True)])
            bookings.extend([normalize_booking(b, False) for b in direct if normalize_booking(b, False)])
        return [b for b in bookings if b]
    except Exception as e:
        st.error(f"Error loading bookings: {e}")
        return []

def generate_month_dates(year: int, month: int) -> List[date]:
    _, days = calendar.monthrange(year, month)
    return [date(year, month, d) for d in range(1, days + 1)]

def filter_bookings_for_day(bookings: List[Dict], target_date: date) -> List[Dict]:
    return [
        {**b, 'target_date': target_date}
        for b in bookings
        if b.get("check_in") and b.get("check_out") and
           date.fromisoformat(b["check_in"]) <= target_date < date.fromisoformat(b["check_out"])
    ]

def assign_inventory_numbers(daily_bookings: List[Dict], property: str) -> tuple[List[Dict], List[Dict]]:
    assigned, overbookings = [], []
    inventory = [i for i in PROPERTY_INVENTORY.get(property, {}).get("all", []) if not i.startswith(("Day Use", "No Show"))]
    inv_lower = [i.lower() for i in inventory]

    for b in daily_bookings:
        rooms = [r.strip().title() for r in b["room_no"].split(",") if r.strip()]
        if not rooms:
            overbookings.append(b); continue

        valid = []
        for r in rooms:
            if r.lower() in inv_lower:
                valid.append(inventory[inv_lower.index(r.lower())])
            else:
                overbookings.append(b); break
        else:
            days = b.get("days", 1) or 1
            per_night = b["receivable"] / len(valid) / days
            base_pax = b["total_pax"] // len(valid)
            extra = b["total_pax"] % len(valid)

            if len(valid) == 1:
                b.update({"inventory_no": valid, "per_night": per_night, "is_primary": True})
                assigned.append(b)
            else:
                for i, room in enumerate(valid):
                    nb = b.copy()
                    nb.update({
                        "inventory_no": [room], "room_no": room,
                        "total_pax": base_pax + (1 if i < extra else 0),
                        "per_night": per_night, "is_primary": i == 0
                    })
                    assigned.append(nb)
    return assigned, overbookings

def create_inventory_table(assigned: List[Dict], overbookings: List[Dict], property: str) -> pd.DataFrame:
    cols = ["Inventory No", "Room No", "Booking ID", "Guest Name", "Mobile No", "Total Pax", "Check In", "Check Out", "Days", "MOB", "Room Charges", "GST", "Total", "Commision", "Receivable", "Per Night", "Advance", "Advance Mop", "Balance", "Balance Mop", "Plan", "Booking Status", "Payment Status", "Submitted by", "Modified by", "Remarks"]
    inv = PROPERTY_INVENTORY.get(property, {"all": []})["all"]
    data = [{c: "" for c in cols} for _ in inv]
    for i, room in enumerate(inv):
        data[i]["Inventory No"] = room

    for b in assigned:
        for room in b.get("inventory_no", []):
            row = next((r for r in data if r["Inventory No"] == room), None)
            if not row: continue
            is_first = b.get("is_primary", False) and b.get("target_date") == date.fromisoformat(b["check_in"])
            row.update({
                "Room No": b["room_no"], "Booking ID": format_booking_id(b),
                "Guest Name": b["guest_name"], "Mobile No": b["mobile_no"],
                "Total Pax": str(b["total_pax"]), "Check In": b["check_in"],
                "Check Out": b["check_out"], "Days": str(b["days"]),
                "MOB": b["mob"], "Per Night": f"{b['per_night']:.2f}",
                "Plan": b["plan"], "Booking Status": b["booking_status"],
                "Payment Status": b["payment_status"], "Submitted by": b["submitted_by"],
                "Modified by": b["modified_by"], "Remarks": b["remarks"],
                "Balance Mop": b["balance_mop"]
            })
            if is_first:
                row.update({
                    "Room Charges": f"{b['room_charges']:.2f}", "GST": f"{b['gst']:.2f}",
                    "Total": f"{b['total']:.2f}", "Commision": f"{b['commission']:.2f}",
                    "Receivable": f"{b['receivable']:.2f}", "Advance": f"{b['advance']:.2f}",
                    "Advance Mop": b["advance_mop"], "Balance": f"{b['balance']:.2f}"
                })

    if overbookings:
        data.append({
            "Inventory No": "Overbookings",
            "Room No": ", ".join(f"{b['room_no']} ({b['booking_id']})" for b in overbookings),
            "Booking ID": ", ".join(format_booking_id(b) for b in overbookings),
            **{c: "" for c in cols[3:]}
        })
    return pd.DataFrame(data, columns=cols)

def compute_mop_report(bookings: List[Dict], target_date: date) -> pd.DataFrame:
    types = ["UPI", "Cash", "Go-MMT", "Agoda", "NOT PAID", "Expenses", "Bank Transfer", "Stayflexi", "Card Payment", "Expedia", "Cleartrip", "Website"]
    data = {t: 0.0 for t in types}
    total_cash = total = 0.0
    for b in bookings:
        if not (b.get("is_primary") and date.fromisoformat(b["check_in"]) == target_date): continue
        for mop, val in [(b["advance_mop"], b["advance"]), (b["balance_mop"], b["balance"])]:
            for std, vars in mop_mapping.items():
                if mop in vars:
                    data[std] += val
                    total += val
                    if std == "Cash": total_cash += val
    data["Expenses"] = 0.0
    data["Total Cash"] = total_cash
    data["Total"] = total
    return pd.DataFrame([{"MOP": k, "Amount": f"{v:.2f}"} for k, v in data.items()], columns=["MOP", "Amount"])

def compute_statistics(bookings: List[Dict], property: str, target_date: date, month_dates: List[date]) -> tuple:
    mob_types = list(mob_mapping.keys())
    total_inv = len([i for i in PROPERTY_INVENTORY.get(property, {}).get("all", []) if not i.startswith(("Day Use", "No Show"))])

    # D.T.D
    dtd = {m: {"rooms": 0, "value": 0.0, "comm": 0.0} for m in mob_types}
    total_rooms = total_value = total_pax = total_gst = total_comm = 0
    daily_a, _ = assign_inventory_numbers(filter_bookings_for_day(bookings, target_date), property)
    for b in daily_a:
        mob = next((m for m, vs in mob_mapping.items() if b["mob"].upper() in [v.upper() for v in vs]), "Booking")
        rooms = len(b.get("inventory_no", []))
        value = b["receivable"] if b.get("is_primary") and b.get("target_date") == date.fromisoformat(b["check_in"]) else 0.0
        comm = b["commission"] if b.get("is_primary") and b.get("target_date") == date.fromisoformat(b["check_in"]) else 0.0
        dtd[mob]["rooms"] += rooms; dtd[mob]["value"] += value; dtd[mob]["comm"] += comm
        total_rooms += rooms; total_value += value; total_pax += b["total_pax"]; total_gst += b["gst"] if b.get("is_primary") else 0.0; total_comm += comm
    for m in mob_types: dtd[m]["arr"] = dtd[m]["value"] / dtd[m]["rooms"] if dtd[m]["rooms"] else 0.0
    dtd["Total"] = {"rooms": total_rooms, "value": total_value, "arr": total_value/total_rooms if total_rooms else 0.0, "comm": total_comm}
    dtd_df = pd.DataFrame([{"MOB": m, "D.T.D Rooms": d["rooms"], "D.T.D Value": f"{d['value']:.2f}", "D.T.D ARR": f"{d['arr']:.2f}", "D.T.D Comm": f"{d['comm']:.2f}"} for m, d in dtd.items()])

    # M.T.D
    mtd = {m: {"rooms": 0, "value": 0.0, "comm": 0.0} for m in mob_types}
    mtd_rooms = mtd_value = mtd_pax = mtd_gst = mtd_comm = 0
    for day in [d for d in month_dates if d <= target_date]:
        day_a, _ = assign_inventory_numbers(filter_bookings_for_day(bookings, day), property)
        for b in day_a:
            mob = next((m for m, vs in mob_mapping.items() if b["mob"].upper() in [v.upper() for v in vs]), "Booking")
            rooms = len(b.get("inventory_no", []))
            value = b["receivable"] if b.get("is_primary") and b.get("target_date") == date.fromisoformat(b["check_in"]) else 0.0
            comm = b["commission"] if b.get("is_primary") and b.get("target_date") == date.fromisoformat(b["check_in"]) else 0.0
            mtd[mob]["rooms"] += rooms; mtd[mob]["value"] += value; mtd[mob]["comm"] += comm
            mtd_rooms += rooms; mtd_value += value; mtd_pax += b["total_pax"]; mtd_gst += b["gst"] if b.get("is_primary") else 0.0; mtd_comm += comm
    for m in mob_types: mtd[m]["arr"] = mtd[m]["value"] / mtd[m]["rooms"] if mtd[m]["rooms"] else 0.0
    mtd["Total"] = {"rooms": mtd_rooms, "value": mtd_value, "arr": mtd_value/mtd_rooms if mtd_rooms else 0.0, "comm": mtd_comm}
    mtd_df = pd.DataFrame([{"MOB": m, "M.T.D Rooms": d["rooms"], "M.T.D Value": f"{d['value']:.2f}", "M.T.D ARR": f"{d['arr']:.2f}", "M.T.D Comm": f"{d['comm']:.2f}"} for m, d in mtd.items()])

    summary = {
        "rooms_sold": total_rooms, "value": total_value, "arr": total_value/total_rooms if total_rooms else 0.0,
        "occ_percent": total_rooms/total_inv*100 if total_inv else 0.0, "total_pax": total_pax, "total_inventory": total_inv,
        "gst": total_gst, "commission": total_comm, "tax_deduction": total_value*0.003,
        "mtd_occ_percent": min(mtd_rooms/(total_inv*target_date.day)*100 if total_inv and target_date.day else 0.0, 100.0),
        "mtd_pax": mtd_pax, "mtd_rooms": mtd_rooms, "mtd_gst": mtd_gst, "mtd_tax_deduction": mtd_value*0.003, "mtd_value": mtd_value
    }
    mop_df = compute_mop_report(daily_a, target_date)
    return dtd_df, mtd_df, summary, mop_df

@st.cache_data
def cached_load_properties():
    return load_properties()

@st.cache_data
def cached_load_bookings(prop, start, end):
    return load_combined_bookings(prop, start, end)

# EXPORTED FUNCTION
def show_daily_status():
    st.title("Daily Status")
    if st.button("Refresh Property List"):
        st.cache_data.clear()
        st.rerun()

    year = st.selectbox("Year", list(range(date.today().year - 5, date.today().year + 6)), index=5)
    month = st.selectbox("Month", list(range(1, 13)), index=date.today().month - 1)
    properties = cached_load_properties()
    if not properties:
        st.info("No properties.")
        return

    st.markdown(TABLE_CSS, unsafe_allow_html=True)
    for prop in properties:
        with st.expander(prop):
            dates = generate_month_dates(year, month)
            bookings = cached_load_bookings(prop, dates[0], dates[-1])
            for day in dates:
                day_bookings = filter_bookings_for_day(bookings, day)
                st.subheader(f"{prop} - {day.strftime('%B %d, %Y')}")
                if day_bookings:
                    assigned, over = assign_inventory_numbers(day_bookings, prop)
                    df = create_inventory_table(assigned, over, prop)
                    df['Booking ID'] = df['Booking ID'].apply(lambda x: f'<small>{x.split(">")[1].split("<")[0] if ">" in str(x) else x}</small>')
                    for c in ['Guest Name', 'Room No', 'Remarks', 'Mobile No', 'MOB', 'Plan', 'Submitted by', 'Modified by']:
                        if c in df.columns:
                            df[c] = df[c].apply(lambda x: f'<span title="{x}">{x}</span>' if isinstance(x, str) else x)
                    st.markdown(f'<div class="custom-scrollable-table">{df.to_html(escape=False, index=False)}</div>', unsafe_allow_html=True)
                    dtd_df, mtd_df, summary, mop_df = compute_statistics(bookings, prop, day, dates)
                    c1, c2, c3, c4 = st.columns(4)
                    with c1: st.subheader("MOP"); st.dataframe(mop_df, use_container_width=True)
                    with c2: st.subheader("D.T.D"); st.dataframe(dtd_df, use_container_width=True)
                    with c3: st.subheader("M.T.D"); st.dataframe(mtd_df, use_container_width=True)
                    with c4:
                        st.subheader("Summary")
                        st.dataframe(pd.DataFrame([{"Metric": k.replace("_", " ").title(), "Value": f"{v:.2f}" if isinstance(v, float) else v} for k, v in summary.items()]), use_container_width=True)
                else:
                    st.info("No active bookings.")
