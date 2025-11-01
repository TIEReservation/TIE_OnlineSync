# inventory.py
import streamlit as st
from supabase import create_client, Client
from datetime import date
import calendar
import pandas as pd
from typing import Any, List, Dict, Optional
import logging

# ────── Logging ──────
logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# ────── Supabase client ──────
try:
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except KeyError as e:
    st.error(f"Missing Supabase secret: {e}. Please check Streamlit Cloud secrets.")
    st.stop()

# ────── Property synonym mapping ──────
property_mapping = {
    "La Millionaire Luxury Resort": "La Millionaire Resort",
    "Le Poshe Beach View": "Le Poshe Beach view",
    "Le Poshe Beach view": "Le Poshe Beach view",
    "Le Poshe Beach VIEW": "Le Poshe Beach view",
    "Millionaire": "La Millionaire Resort",
}
reverse_mapping = {c: [] for c in set(property_mapping.values())}
for v, c in property_mapping.items():
    reverse_mapping[c].append(v)

# ────── MOP / MOB mappings ──────
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
    "Website": ["Stayflexi Booking Engine"],
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
    "Website": ["Stayflexi Booking Engine"],
}

# ────── CSS ──────
TABLE_CSS = """
<style>
.custom-scrollable-table {overflow-x:auto;max-width:100%;min-width:800px;}
.custom-scrollable-table table {table-layout:auto;border-collapse:collapse;}
.custom-scrollable-table td,.custom-scrollable-table th {white-space:nowrap;
    text-overflow:ellipsis;overflow:hidden;max-width:150px;padding:8px;
    border:1px solid #ddd;}
</style>
"""

# ────── Full inventory (your latest list) ──────
PROPERTY_INVENTORY = {
    "Le Poshe Beach view": {"all": ["101","102","201","202","203","204","301","302","303","304","Day Use 1","Day Use 2","No Show"],"three_bedroom":["203","204"]},
    "La Millionaire Resort": {"all": ["101","102","103","105","201","202","203","204","205","206","207","208","301","302","303","304","305","306","307","308","401","402","Day Use 1","Day Use 2","Day Use 3","Day Use 4","Day Use 5","No Show"],"three_bedroom":["203","204","205"]},
    "Le Poshe Luxury": {"all": ["101","102","201","202","203","204","205","301","302","303","304","305","401","402","403","404","405","501","Day Use 1","Day Use 2","No Show"],"three_bedroom":["203","204","205"]},
    "Le Poshe Suite": {"all": ["601","602","603","604","701","702","703","704","801","Day Use 1","Day Use 2","No Show"],"three_bedroom":[]},
    "La Paradise Residency": {"all": ["101","102","103","201","202","203","301","302","303","304","Day Use 1","Day Use 2","No Show"],"three_bedroom":["203"]},
    "La Paradise Luxury": {"all": ["101","102","103","201","202","203","Day Use 1","Day Use 2","No Show"],"three_bedroom":["203"]},
    "La Villa Heritage": {"all": ["101","102","103","201","202","203","301","Day Use 1","Day Use 2","No Show"],"three_bedroom":["203"]},
    "Le Pondy Beach Side": {"all": ["101","102","201","202","Day Use 1","Day Use 2","No Show"],"three_bedroom":[]},
    "Le Royce Villa": {"all": ["101","102","201","202","Day Use 1","Day Use 2","No Show"],"three_bedroom":[]},
    "La Tamara Luxury": {"all": ["101","102","103","104","105","106","201","202","203","204","205","206","301","302","303","304","305","306","401","402","403","404","Day Use 1","Day Use 2","No Show"],"three_bedroom":["203","204","205","206"]},
    "La Antilia Luxury": {"all": ["101","201","202","203","204","301","302","303","304","401","Day Use 1","Day Use 2","No Show"],"three_bedroom":["203","204"]},
    "La Tamara Suite": {"all": ["101","102","103","104","201","202","203","204","205","206","Day Use 1","Day Use 2","No Show"],"three_bedroom":["203","204","205","206"]},
    "Le Park Resort": {"all": ["111","222","333","444","555","666","Day Use 1","Day Use 2","No Show"],"three_bedroom":[]},
    "Villa Shakti": {"all": ["101","102","201","201A","202","203","301","301A","302","303","401","Day Use 1","Day Use 2","No Show"],"three_bedroom":["203"]},
    "Eden Beach Resort": {"all": ["101","102","103","201","202","Day Use 1","Day Use 2","No Show"],"three_bedroom":[]},
}

# ──────────────────────────────────────────────────────────────────────────────
# Helper utilities
# ──────────────────────────────────────────────────────────────────────────────
def normalize_property(name: str) -> str:
    return property_mapping.get(name.strip(), name.strip())

def sanitize_string(v: Any, default: str = "") -> str:
    return str(v).strip() if v is not None else default

def safe_int(v: Any, default: int = 0) -> int:
    try: return int(v) if v is not None else default
    except (ValueError, TypeError): return default

def safe_float(v: Any, default: float = 0.0) -> float:
    try: return float(v) if v is not None else default
    except (ValueError, TypeError): return default

# ──────────────────────────────────────────────────────────────────────────────
# Exported symbols (for monthlyconsolidation.py)
# ──────────────────────────────────────────────────────────────────────────────
__all__ = [
    "load_properties", "load_combined_bookings", "filter_bookings_for_day",
    "assign_inventory_numbers", "PROPERTY_INVENTORY", "show_daily_status"
]

# ────── Load canonical property list (cached) ──────
@st.cache_data(ttl=3600)
def load_properties() -> List[str]:
    try:
        direct = supabase.table("reservations").select("property_name").execute()
        online = supabase.table("online_reservations").select("property").execute()
        props = set()
        for r in direct.data or []:
            p = normalize_property(r.get("property_name", ""))
            if p: props.add(p)
        for r in online.data or []:
            p = normalize_property(r.get("property", ""))
            if p: props.add(p)
        return sorted(props)
    except Exception as e:
        logging.error(f"load_properties: {e}")
        return []

# ────── Core: load ONLY Confirmed + Paid bookings that overlap the month ──────
@st.cache_data(ttl=300)
def load_combined_bookings(property: str, start_date: date, end_date: date) -> List[Dict]:
    prop = normalize_property(property)
    query_props = [prop] + reverse_mapping.get(prop, [])
    combined: List[Dict] = []

    # ---------- DIRECT ----------
    try:
        q = (
            supabase.table("reservations")
            .select("*")
            .in_("property_name", query_props)
            .lte("check_in", str(end_date))
            .gte("check_out", str(start_date))
            .in_("booking_status", ["Confirmed", "Completed"])   # CORRECT column
            .in_("payment_status", ["Partially Paid", "Fully Paid"])
            .execute()
        )
        for r in q.data or []:
            norm = normalize_booking(r, is_online=False)
            if norm:
                combined.append(norm)
        logging.info(f"Direct ({prop}): {len(q.data or [])} → {len([c for c in combined if c['type']=='direct'])}")
    except Exception as e:
        logging.error(f"Direct query error: {e}")

    # ---------- ONLINE ----------
    try:
        q = (
            supabase.table("online_reservations")
            .select("*")
            .in_("property", query_props)
            .lte("check_in", str(end_date))
            .gte("check_out", str(start_date))
            .in_("booking_status", ["Confirmed", "Completed"])
            .in_("payment_status", ["Partially Paid", "Fully Paid"])
            .execute()
        )
        for r in q.data or []:
            norm = normalize_booking(r, is_online=True)
            if norm:
                combined.append(norm)
        logging.info(f"Online ({prop}): {len(q.data or [])} → {len([c for c in combined if c['type']=='online'])}")
    except Exception as e:
        logging.error(f"Online query error: {e}")

    return combined

    # ---------- ONLINE ----------
    try:
        q = (
            supabase.table("online_reservations")
            .select("*")
            .in_("property", query_props)
            .lte("check_in", str(end_date))
            .gte("check_out", str(start_date))
            .in_("booking_status", ["Confirmed", "Completed"])   # ONLINE
            .in_("payment_status", ["Partially Paid", "Fully Paid"])
            .execute()
        )
        for r in q.data or []:
            norm = normalize_booking(r, is_online=True)
            if norm:
                combined.append(norm)
        logging.info(f"Online ({prop}): {len(q.data or [])} → {len([c for c in combined if c['type']=='online'])}")
    except Exception as e:
        logging.error(f"Online query error: {e}")

    return combined

# ────── Normalise a raw row → dict used everywhere ──────
def normalize_booking(row: Dict, is_online: bool) -> Optional[Dict]:
    try:
        bid = sanitize_string(row.get("booking_id") or row.get("id"))
        # ---- status (plan_status for direct, booking_status for online) ----
        status_field = "plan_status" if not is_online else "booking_status"
        status = sanitize_string(row.get(status_field, "")).title()
        if status not in ["Confirmed", "Completed"]:
            return None

        # ---- payment ----
        pay = sanitize_string(row.get("payment_status")).title()
        if pay not in ["Fully Paid", "Partially Paid"]:
            return None

        # ---- dates ----
        ci = date.fromisoformat(row["check_in"])
        co = date.fromisoformat(row["check_out"])
        if co <= ci: return None
        days = (co - ci).days

        # ---- property (canonical) ----
        p = normalize_property(row.get("property_name") if not is_online else row.get("property"))

        # ---- build dict ----
        return {
            "type": "online" if is_online else "direct",
            "property": p,
            "booking_id": bid,
            "guest_name": sanitize_string(row.get("guest_name")),
            "mobile_no": sanitize_string(row.get("guest_phone") or row.get("mobile_no")),
            "total_pax": safe_int(row.get("total_pax")),
            "check_in": str(ci),
            "check_out": str(co),
            "days": days,
            "room_no": sanitize_string(row.get("room_no")).title(),
            "mob": sanitize_string(row.get("mode_of_booking") or row.get("mob")),
            "plan": sanitize_string(row.get("rate_plans") or row.get("plan")),
            "room_charges": safe_float(row.get("total_amount_with_services") or row.get("booking_amount") or row.get("total_tariff")),
            "gst": safe_float(row.get("ota_tax")) if is_online else 0.0,
            "commission": safe_float(row.get("ota_commission")),
            "receivable": 0.0,   # calculated later
            "advance": safe_float(row.get("total_payment_made") or row.get("advance_amount")),
            "advance_mop": sanitize_string(row.get("advance_mop")),
            "balance": safe_float(row.get("balance_due") or row.get("balance_amount")),
            "balance_mop": sanitize_string(row.get("balance_mop")),
            "booking_status": status,
            "payment_status": pay,
            "submitted_by": sanitize_string(row.get("submitted_by")),
            "modified_by": sanitize_string(row.get("modified_by")),
            "remarks": sanitize_string(row.get("remarks")),
        }
    except Exception as e:
        logging.warning(f"normalize failed ({row.get('booking_id')}): {e}")
        return None

# ────── Simple overlap filter (no extra status checks) ──────
def filter_bookings_for_day(bookings: List[Dict], day: date) -> List[Dict]:
    return [
        b.copy() | {"target_date": day}
        for b in bookings
        if date.fromisoformat(b["check_in"]) <= day < date.fromisoformat(b["check_out"])
    ]

# ────── Room assignment ──────
def assign_inventory_numbers(daily_bookings: List[Dict], property: str):
    assigned, over = [], []
    inv = PROPERTY_INVENTORY.get(property, {"all": []})["all"]
    inv_lower = [i.lower() for i in inv]
    used = set()

    for b in daily_bookings:
        req = [r.strip().title() for r in b.get("room_no","").split(",") if r.strip()]
        if not req:
            over.append(b); continue

        valid = []
        for r in req:
            if r.lower() in inv_lower:
                valid.append(inv[inv_lower.index(r.lower())])
            else:
                over.append(b)
                break
        else:
            days = b.get("days",1) or 1
            per_night = b.get("receivable",0) / len(valid) / days if valid else 0
            base_pax = b["total_pax"] // len(valid) if valid else 0
            rem = b["total_pax"] % len(valid) if valid else 0
            for idx, room in enumerate(valid):
                nb = b.copy()
                nb["inventory_no"] = [room]
                nb["room_no"] = room
                nb["total_pax"] = base_pax + (1 if idx < rem else 0)
                nb["per_night"] = per_night
                nb["is_primary"] = (idx == 0)
                assigned.append(nb)
    return assigned, over

# ────── Table builder ──────
def create_inventory_table(assigned: List[Dict], over: List[Dict], prop: str) -> pd.DataFrame:
    cols = ["Inventory No","Room No","Booking ID","Guest Name","Mobile No","Total Pax",
            "Check In","Check Out","Days","MOB","Room Charges","GST","Total",
            "Commision","Receivable","Per Night","Advance","Advance Mop","Balance",
            "Balance Mop","Plan","Booking Status","Payment Status","Submitted by",
            "Modified by","Remarks"]
    inv = [i for i in PROPERTY_INVENTORY.get(prop,{}).get("all",[]) if not i.startswith(("Day Use","No Show"))]
    rows = []
    for i in inv:
        row = {c:"" for c in cols}
        row["Inventory No"] = i
        match = next((a for a in assigned if i in a.get("inventory_no",[])), None)
        if match:
            row.update({
                "Room No": match["room_no"],
                "Booking ID": f'<a target="_blank" href="/?edit_type={match["type"]}&booking_id={match["booking_id"]}">{match["booking_id"]}</a>',
                "Guest Name": match["guest_name"],
                "Mobile No": match["mobile_no"],
                "Total Pax": match["total_pax"],
                "Check In": match["check_in"],
                "Check Out": match["check_out"],
                "Days": match["days"],
                "MOB": match["mob"],
                "Plan": match["plan"],
                "Booking Status": match["booking_status"],
                "Payment Status": match["payment_status"],
                "Submitted by": match["submitted_by"],
                "Modified by": match["modified_by"],
                "Remarks": match["remarks"],
                "Per Night": f"{match.get('per_night',0):.2f}",
            })
            if match.get("is_primary"):
                row.update({
                    "Room Charges": f"{match.get('room_charges',0):.2f}",
                    "GST": f"{match.get('gst',0):.2f}",
                    "Total": f"{match.get('room_charges',0)+match.get('gst',0):.2f}",
                    "Commision": f"{match.get('commission',0):.2f}",
                    "Receivable": f"{match.get('room_charges',0)-match.get('commission',0):.2f}",
                    "Advance": f"{match.get('advance',0):.2f}",
                    "Advance Mop": match.get("advance_mop",""),
                    "Balance": f"{match.get('balance',0):.2f}",
                    "Balance Mop": match.get("balance_mop",""),
                })
        rows.append(row)

    if over:
        rows.append({
            "Inventory No": "Overbookings",
            "Room No": ", ".join(f"{b.get('room_no','')} ({b.get('booking_id','')})" for b in over),
            "Booking ID": ", ".join(f'<a href="#">{b.get("booking_id","")}</a>' for b in over),
            **{c:"" for c in cols[3:]}
        })
    return pd.DataFrame(rows, columns=cols)

# ────── Statistics ──────
def compute_statistics(bookings: List[Dict], property: str, target_date: date, month_dates: List[date]) -> tuple:
    mob_types = ["Booking", "Direct", "Bkg-Direct", "Agoda", "Go-MMT", "Walk-In", "TIE Group", "Stayflexi", "Airbnb", "Social Media", "Expedia", "Cleartrip", "Website"]
    inventory = PROPERTY_INVENTORY.get(property, {"all": []})["all"]
    total_inventory = len([i for i in inventory if not i.startswith(("Day Use", "No Show"))])
    dtd_data = {mob: {"rooms": 0, "value": 0.0, "arr": 0.0, "comm": 0.0} for mob in mob_types}
    total_rooms = total_value = total_pax = total_gst = total_comm = 0
    daily_assigned, _ = assign_inventory_numbers(filter_bookings_for_day(bookings, target_date), property)
    for b in daily_assigned:
        raw_mob = sanitize_string(b.get("mob", "Unknown"))
        mob = next((m for m, v in mob_mapping.items() if raw_mob.upper() in [x.upper() for x in v]), "Booking")
        rooms = len(b.get("inventory_no", []))
        value = b.get("receivable", 0.0) if b.get("is_primary", False) and date.fromisoformat(b["check_in"]) == target_date else 0.0
        comm = b.get("commission", 0.0) if b.get("is_primary", False) and date.fromisoformat(b["check_in"]) == target_date else 0.0
        dtd_data[mob]["rooms"] += rooms
        dtd_data[mob]["value"] += value
        dtd_data[mob]["comm"] += comm
        total_rooms += rooms
        total_value += value
        total_pax += b.get("total_pax", 0)
        total_gst += b.get("gst", 0.0) if b.get("is_primary", False) and date.fromisoformat(b["check_in"]) == target_date else 0.0
        total_comm += comm
    for mob in mob_types:
        rooms = dtd_data[mob]["rooms"]
        dtd_data[mob]["arr"] = dtd_data[mob]["value"] / rooms if rooms > 0 else 0.0
    dtd_data["Total"] = {"rooms": total_rooms, "value": total_value, "arr": total_value / total_rooms if total_rooms > 0 else 0.0, "comm": total_comm}
    dtd_df = pd.DataFrame([{"MOB": mob, "D.T.D Rooms": d["rooms"], "D.T.D Value": f"{d['value']:.2f}", "D.T.D ARR": f"{d['arr']:.2f}", "D.T.D Comm": f"{d['comm']:.2f}"} for mob, d in dtd_data.items()], columns=["MOB", "D.T.D Rooms", "D.T.D Value", "D.T.D ARR", "D.T.D Comm"])

    mtd_rooms = mtd_value = mtd_pax = mtd_gst = mtd_comm = 0
    mtd_data = {mob: {"rooms": 0, "value": 0.0, "arr": 0.0, "comm": 0.0} for mob in mob_types}
    for day in month_dates:
        if day > target_date: continue
        daily_b = filter_bookings_for_day(bookings, day)
        daily_a, _ = assign_inventory_numbers(daily_b, property)
        for b in daily_a:
            raw_mob = sanitize_string(b.get("mob", "Unknown"))
            mob = next((m for m, v in mob_mapping.items() if raw_mob.upper() in [x.upper() for x in v]), "Booking")
            rooms = len(b.get("inventory_no", []))
            value = b.get("receivable", 0.0) if b.get("is_primary", False) and date.fromisoformat(b["check_in"]) == day else 0.0
            comm = b.get("commission", 0.0) if b.get("is_primary", False) and date.fromisoformat(b["check_in"]) == day else 0.0
            mtd_data[mob]["rooms"] += rooms
            mtd_data[mob]["value"] += value
            mtd_data[mob]["comm"] += comm
            mtd_rooms += rooms
            mtd_value += value
            mtd_pax += b.get("total_pax", 0)
            mtd_gst += b.get("gst", 0.0) if b.get("is_primary", False) and date.fromisoformat(b["check_in"]) == day else 0.0
            mtd_comm += comm
    for mob in mob_types:
        rooms = mtd_data[mob]["rooms"]
        mtd_data[mob]["arr"] = mtd_data[mob]["value"] / rooms if rooms > 0 else 0.0
    mtd_data["Total"] = {"rooms": mtd_rooms, "value": mtd_value, "arr": mtd_value / mtd_rooms if mtd_rooms > 0 else 0.0, "comm": mtd_comm}
    mtd_df = pd.DataFrame([{"MOB": mob, "M.T.D Rooms": d["rooms"], "M.T.D Value": f"{d['value']:.2f}", "M.T.D ARR": f"{d['arr']:.2f}", "M.T.D Comm": f"{d['comm']:.2f}"} for mob, d in mtd_data.items()], columns=["MOB", "M.T.D Rooms", "M.T.D Value", "M.T.D ARR", "M.T.D Comm"])

    summary = {
        "rooms_sold": total_rooms,
        "value": total_value,
        "arr": total_value / total_rooms if total_rooms > 0 else 0.0,
        "occ_percent": (total_rooms / total_inventory * 100) if total_inventory > 0 else 0.0,
        "total_pax": total_pax,
        "total_inventory": total_inventory,
        "gst": total_gst,
        "commission": total_comm,
        "tax_deduction": total_value * 0.003,
        "mtd_occ_percent": min((mtd_rooms / (total_inventory * target_date.day) * 100) if total_inventory > 0 and target_date.day > 0 else 0.0, 100.0),
        "mtd_pax": mtd_pax,
        "mtd_rooms": mtd_rooms,
        "mtd_gst": mtd_gst,
        "mtd_tax_deduction": mtd_value * 0.003,
        "mtd_value": mtd_value
    }
    mop_df = compute_mop_report(daily_assigned, target_date)
    return dtd_df, mtd_df, summary, mop_df

# ────── MOP Report ──────
def compute_mop_report(daily_bookings: List[Dict], target_date: date) -> pd.DataFrame:
    mop_types = ["UPI", "Cash", "Go-MMT", "Agoda", "NOT PAID", "Expenses", "Bank Transfer", "Stayflexi", "Card Payment", "Expedia", "Cleartrip", "Website"]
    mop_data = {mop: 0.0 for mop in mop_types}
    total_cash = 0.0
    total = 0.0
    for b in daily_bookings:
        if not (b.get('is_primary', False) and date.fromisoformat(b["check_in"]) == target_date):
            continue
        advance_mop = sanitize_string(b.get("advance_mop", ""))
        balance_mop = sanitize_string(b.get("balance_mop", ""))
        advance = safe_float(b.get("advance", 0.0))
        balance = safe_float(b.get("balance", 0.0))
        for standard_mop, variants in mop_mapping.items():
            if advance_mop in variants:
                mop_data[standard_mop] += advance
                total += advance
                if standard_mop == "Cash":
                    total_cash += advance
            if balance_mop in variants:
                mop_data[standard_mop] += balance
                total += balance
                if standard_mop == "Cash":
                    total_cash += balance
    mop_data["Expenses"] = 0.0
    mop_data["Total Cash"] = total_cash
    mop_data["Total"] = total
    return pd.DataFrame([{"MOP": mop, "Amount": f"{amount:.2f}"} for mop, amount in mop_data.items()], columns=["MOP", "Amount"])

# ────── UI – Daily Status ──────
def show_daily_status():
    st.title("Daily Status")
    if st.button("Refresh Property List"):
        st.cache_data.clear()
        st.rerun()

    today = date.today()
    year = st.selectbox("Year", list(range(today.year-5, today.year+6)), index=5)
    month = st.selectbox("Month", list(range(1,13)), index=today.month-1)

    props = load_properties()
    if not props:
        st.info("No properties.")
        return

    st.subheader("Properties")
    st.markdown(TABLE_CSS, unsafe_allow_html=True)

    for prop in props:
        with st.expander(prop):
            month_dates = [date(year, month, d) for d in range(1, calendar.monthrange(year, month)[1]+1)]
            start, end = month_dates[0], month_dates[-1]
            bookings = load_combined_bookings(prop, start, end)

            for day in month_dates:
                daily = filter_bookings_for_day(bookings, day)
                st.subheader(f"{prop} – {day.strftime('%B %d, %Y')}")
                if daily:
                    assigned, over = assign_inventory_numbers(daily, prop)
                    df = create_inventory_table(assigned, over, prop)

                    # shrink IDs + tooltips
                    if "Booking ID" in df.columns:
                        df["Booking ID"] = df["Booking ID"].apply(
                            lambda x: f'<span style="font-size:0.75em;">{x.split(">")[1].split("<")[0] if ">" in str(x) else x}</span>'
                        )
                    for c in ["Guest Name","Room No","Remarks","Mobile No","MOB","Plan","Submitted by","Modified by"]:
                        if c in df.columns:
                            df[c] = df[c].apply(lambda v: f'<span title="{v}">{v}</span>' if isinstance(v,str) and v else v)

                    st.markdown(f'<div class="custom-scrollable-table">{df.to_html(escape=False,index=False)}</div>', unsafe_allow_html=True)

                    dtd, mtd, summary, mop = compute_statistics(bookings, prop, day, month_dates)
                    c1,c2,c3,c4 = st.columns(4)
                    with c1: st.subheader("MOP"); st.dataframe(mop, use_container_width=True)
                    with c2: st.subheader("D.T.D"); st.dataframe(dtd, use_container_width=True)
                    with c3: st.subheader("M.T.D"); st.dataframe(mtd, use_container_width=True)
                    with c4:
                        st.subheader("Summary")
                        st.dataframe(pd.DataFrame([{"Metric":k.replace("_"," ").title(),"Value":f"{v:.2f}" if isinstance(v,float) else v}
                                                  for k,v in summary.items()]), use_container_width=True)
                else:
                    st.info("No active bookings.")
