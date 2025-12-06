# inventory.py – FINAL VERSION: Multi-night + Correct Hotel Receivable + Comprehensive Column Config
import streamlit as st
from supabase import create_client, Client
from datetime import date
import calendar
import pandas as pd
from typing import Any, List, Dict, Optional
import logging

# ────── Logging ──────
logging.basicConfig(filename="app.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

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
    "Le Poshe Beachview": "Le Poshe Beach view",
    "Millionaire": "La Millionaire Resort",
    "Le Pondy Beach Side": "Le Pondy Beachside",
    "Le Teera": "Le Terra"
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
    "NOT PAID": ["Not Paid", "", " "],
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

# ────── Full inventory ──────
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
    "Le Terra": {"all": ["101","102","103","104","105","106","107","Day Use 1","Day Use 2","No Show"],"three_bedroom":[]},
    "La Coromandel Luxury": {"all": ["101","102","103","201","202","203","204","205","206","301","Day Use 1","Day Use 2","No Show"],"three_bedroom":[]},
    "Happymates Forest Retreat": {"all": ["101","102","Day Use 1","Day Use 2","No Show"],"three_bedroom":[]}  
}

# ───────────────────────────────────────────────────────────────────────────
# Helpers
# ───────────────────────────────────────────────────────────────────────────
def normalize_property(name: str) -> str:
    return property_mapping.get(name.strip(), name.strip())

def sanitize_string(v: Any, default: str = "") -> str:
    return str(v).strip() if v is not None else default

def safe_int(v: Any, default: int = 0) -> int:
    try:
        return int(float(v)) if v not in [None, "", " "] else default
    except:
        return default

def safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v) if v not in [None, "", " "] else default
    except:
        return default

# ───────────────────────────────────────────────────────────────────────────
# Load Properties & Bookings
# ───────────────────────────────────────────────────────────────────────────
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

@st.cache_data(ttl=300)
def load_combined_bookings(property: str, start_date: date, end_date: date) -> List[Dict]:
    prop = normalize_property(property)
    query_props = [prop] + reverse_mapping.get(prop, [])
    combined: List[Dict] = []

    try:
        q = supabase.table("reservations").select("*").in_("property_name", query_props).lte("check_in", str(end_date)).gte("check_out", str(start_date)).in_("plan_status", ["Confirmed", "Completed"]).in_("payment_status", ["Partially Paid", "Fully Paid"]).execute()
        for r in q.data or []:
            norm = normalize_booking(r, is_online=False)
            if norm: combined.append(norm)
    except Exception as e: logging.error(f"Direct query error: {e}")

    try:
        q = supabase.table("online_reservations").select("*").in_("property", query_props).lte("check_in", str(end_date)).gte("check_out", str(start_date)).in_("booking_status", ["Confirmed", "Completed"]).in_("payment_status", ["Partially Paid", "Fully Paid"]).execute()
        for r in q.data or []:
            norm = normalize_booking(r, is_online=True)
            if norm: combined.append(norm)
    except Exception as e: logging.error(f"Online query error: {e}")

    return combined

# ───────────────────────────────────────────────────────────────────────────
# CORRECTED: Receivable = Total - GST - Commission
# ───────────────────────────────────────────────────────────────────────────
def normalize_booking(row: Dict, is_online: bool) -> Optional[Dict]:
    try:
        bid = sanitize_string(row.get("booking_id") or row.get("id"))
        status_field = "booking_status" if is_online else "plan_status"
        status = sanitize_string(row.get(status_field, "")).title()
        if status not in ["Confirmed", "Completed"]: return None
        pay = sanitize_string(row.get("payment_status")).title()
        if pay not in ["Fully Paid", "Partially Paid"]: return None
        ci = date.fromisoformat(row["check_in"])
        co = date.fromisoformat(row["check_out"])
        if co <= ci: return None
        days_field = "room_nights" if is_online else "no_of_days"
        days = safe_int(row.get(days_field)) or (co - ci).days
        if days <= 0: days = 1
        p = normalize_property(row.get("property_name") if not is_online else row.get("property"))

        # Raw values
        if is_online:
            total_amount = safe_float(row.get("booking_amount")) or 0.0
            gst = safe_float(row.get("ota_tax")) or 0.0
            commission = safe_float(row.get("ota_commission")) or 0.0
            room_charges = total_amount - gst
        else:
            total_amount = safe_float(row.get("total_tariff")) or 0.0
            gst = 0.0
            commission = 0.0
            room_charges = total_amount

        # CORRECT: Hotel actually receives this
        receivable = total_amount - gst - commission
        if receivable < 0: receivable = 0.0

        return {
            "type": "online" if is_online else "direct",
            "property": p,
            "booking_id": bid,
            "guest_name": sanitize_string(row.get("guest_name")),
            "mobile_no": sanitize_string(row.get("guest_phone") if is_online else row.get("mobile_no")),
            "total_pax": safe_int(row.get("total_pax")),
            "check_in": str(ci),
            "check_out": str(co),
            "days": days,
            "room_no": sanitize_string(row.get("room_no")).title(),
            "mob": sanitize_string(row.get("mode_of_booking") if is_online else row.get("mob")),
            "plan": sanitize_string(row.get("rate_plans") if is_online else row.get("breakfast")),
            "room_charges": room_charges,
            "gst": gst,
            "total_amount": total_amount,
            "commission": commission,
            "receivable": receivable,  # NOW 100% CORRECT
            "advance": safe_float(row.get("total_payment_made") if is_online else row.get("advance_amount")),
            "advance_mop": sanitize_string(row.get("advance_mop")),
            "balance": safe_float(row.get("balance_due") if is_online else row.get("balance_amount")),
            "balance_mop": sanitize_string(row.get("balance_mop")),
            "booking_status": status,
            "payment_status": pay,
            "submitted_by": sanitize_string(row.get("submitted_by")),
            "modified_by": sanitize_string(row.get("modified_by")),
            "remarks": sanitize_string(row.get("remarks")),
            "advance_remarks": sanitize_string(row.get("advance_remarks", "")),
            "balance_remarks": sanitize_string(row.get("balance_remarks", "")),
            "accounts_status": sanitize_string(row.get("accounts_status", "Pending")).title(),
            "db_id": row.get("id"),
        }
    except Exception as e:
        logging.warning(f"normalize failed ({row.get('booking_id')}): {e}")
        return None

# ───────────────────────────────────────────────────────────────────────────
# Filter & Assign
# ───────────────────────────────────────────────────────────────────────────
def filter_bookings_for_day(bookings: List[Dict], day: date) -> List[Dict]:
    return [b.copy() | {"target_date": day} for b in bookings if date.fromisoformat(b["check_in"]) <= day < date.fromisoformat(b["check_out"])]

# ───────────────────────────────────────────────────────────────────────────
# FINAL FIXED: assign_inventory_numbers – now 100% reliable for "No Show"
# ───────────────────────────────────────────────────────────────────────────
def assign_inventory_numbers(daily_bookings: List[Dict], property: str):
    assigned, over = [], []
    inv = PROPERTY_INVENTORY.get(property, {"all": []})["all"]
    inv_lookup = {i.strip().lower(): i for i in inv}
    occupied_rooms = set()  # Track already assigned rooms
    
    # Sort bookings by booking_date to ensure first-come-first-served
    sorted_bookings = sorted(daily_bookings, key=lambda x: (x.get("check_in", ""), x.get("booking_id", "")))

    for b in sorted_bookings:
        raw_room = str(b.get("room_no", "") or "").strip()
        booking_id = b.get("booking_id", "Unknown")
        
        if not raw_room:
            over.append(b)
            logging.warning(f"Booking {booking_id} has no room number - moved to overbookings")
            continue

        # Handle comma-separated rooms
        requested = [r.strip() for r in raw_room.split(",") if r.strip()]
        assigned_rooms = []
        is_overbooking = False

        for r in requested:
            key = r.lower()
            if key not in inv_lookup:
                # Invalid room number
                logging.warning(f"Booking {booking_id}: Invalid room '{r}' not in inventory")
                over.append(b)
                assigned_rooms = []
                is_overbooking = True
                break
            
            room_name = inv_lookup[key]
            if room_name in occupied_rooms:
                # Room already assigned - this is an overbooking
                logging.warning(f"Booking {booking_id}: Room '{room_name}' already occupied - OVERBOOKING detected")
                over.append(b)
                assigned_rooms = []
                is_overbooking = True
                break
            
            assigned_rooms.append(room_name)

        if is_overbooking or not assigned_rooms:
            continue

        # Mark rooms as occupied
        for room in assigned_rooms:
            occupied_rooms.add(room)
            logging.info(f"Booking {booking_id}: Assigned room '{room}'")

        days = max(b.get("days", 1), 1)
        receivable = b.get("receivable", 0.0)
        num_rooms = len(assigned_rooms)
        total_nights = days * num_rooms
        per_night = receivable / total_nights if total_nights > 0 else 0.0
        base_pax = b["total_pax"] // num_rooms if num_rooms else 0
        rem = b["total_pax"] % num_rooms if num_rooms else 0

        for idx, room in enumerate(assigned_rooms):
            nb = b.copy()
            nb["assigned_room"] = room                    # ← NEW: single string
            nb["room_no"] = room                           # ← display correct
            nb["total_pax"] = base_pax + (1 if idx < rem else 0)
            nb["per_night"] = per_night
            nb["is_primary"] = (idx == 0)
            assigned.append(nb)

    logging.info(f"Property {property}: {len(assigned)} bookings assigned, {len(over)} overbookings detected")
    return assigned, over

# ───────────────────────────────────────────────────────────────────────────
# Build Table – Financials ONLY on Check-in Day
# ───────────────────────────────────────────────────────────────────────────
def create_inventory_table(assigned: List[Dict], over: List[Dict], prop: str, target_date: date):
    visible_cols = ["Inventory No","Room No","Booking ID","Guest Name","Mobile No","Total Pax",
            "Check In","Check Out","Days","MOB","Room Charges","GST","Total","Commission",
            "Hotel Receivable","Per Night","Advance","Advance Mop","Balance","Balance Mop",
            "Plan","Booking Status","Payment Status","Submitted by","Modified by","Remarks",
            "Advance Remarks","Balance Remarks","Accounts Status"]
    
    # Hidden columns for editing (not in display cols, but in DF)
    hidden_cols = ["edit_type", "db_id", "booking_id_raw", "primary"]
    
    all_inventory = PROPERTY_INVENTORY.get(prop, {}).get("all", [])
    rows = []

    for inventory_no in all_inventory:
        row = {c: "" for c in visible_cols + hidden_cols}  # Include hidden
        row["Inventory No"] = inventory_no

        match = next(
            (a for a in assigned if str(a.get("assigned_room", "")).strip() == inventory_no.strip()),
            None
        )
        
        if match:
            check_in_date = date.fromisoformat(match["check_in"])
            is_check_in_day = (target_date == check_in_date)
            is_primary = match.get("is_primary", False)

            row.update({
                "Room No": match["room_no"],
                "Booking ID": match["booking_id"],  # ← Plain text for data_editor
                "Guest Name": match["guest_name"],
                "Mobile No": match["mobile_no"],
                "Total Pax": match["total_pax"],
                "Check In": match["check_in"],
                "Check Out": match["check_out"],
                "Days": match["days"],
                "MOB": match["mob"],
                "Per Night": f"{match.get('per_night', 0):.2f}",
                "edit_type": match["type"],  # Hidden
                "db_id": match["db_id"],  # Hidden
                "booking_id_raw": match["booking_id"],  # Hidden (backup)
                "primary": is_primary,  # Hidden (for logic if needed)
            })

            if is_check_in_day and is_primary:  # ← Only populate/edit on check-in primary
                row.update({
                    "Room Charges": f"{match.get('room_charges', 0):.2f}",
                    "GST": f"{match.get('gst', 0):.2f}",
                    "Total": f"{match.get('total_amount', 0):.2f}",
                    "Commission": f"{match.get('commission', 0):.2f}",
                    "Hotel Receivable": f"{match.get('receivable', 0):.2f}",
                    "Advance": f"{match.get('advance', 0):.2f}",
                    "Advance Mop": match.get("advance_mop", ""),
                    "Balance": f"{match.get('balance', 0):.2f}",
                    "Balance Mop": match.get("balance_mop", ""),
                    "Plan": match["plan"],
                    "Booking Status": match["booking_status"],
                    "Payment Status": match["payment_status"],
                    "Submitted by": match["submitted_by"],
                    "Modified by": match["modified_by"],
                    "Remarks": match.get("remarks", ""),
                    "Advance Remarks": match.get("advance_remarks", ""),
                    "Balance Remarks": match.get("balance_remarks", ""),
                    "Accounts Status": match["accounts_status"],
                })
            else:
                # For non-primary/non-checkin: Empty new fields to avoid confusion
                row["Advance Remarks"] = ""
                row["Balance Remarks"] = ""
                row["Accounts Status"] = ""

        rows.append(row)

    if over:
        over_row = {c: "" for c in visible_cols + hidden_cols}
        over_row["Inventory No"] = "Overbookings"
        over_row["Room No"] = ", ".join(f"{b.get('room_no','')} ({b.get('booking_id','')})" for b in over)
        rows.append(over_row)

    df = pd.DataFrame(rows, columns=visible_cols + hidden_cols)
    display_df = df[visible_cols].copy()
    full_df = df
    return display_df, full_df

# ───────────────────────────────────────────────────────────────────────────
# Extract Stats – uses "Per Night" for daily value, full for others
# ───────────────────────────────────────────────────────────────────────────
def extract_stats_from_table(df: pd.DataFrame, mob_types: List[str]) -> Dict:
    occupied = df[df["Booking ID"].fillna("").str.strip() != ""].copy()

    def to_float(col):
        return pd.to_numeric(occupied[col].replace('', '0').str.replace(',', ''), errors='coerce').fillna(0.0)

    def to_int(col):
        return pd.to_numeric(occupied[col], errors='coerce').fillna(0).astype(int)

    occupied["Per Night"] = to_float("Per Night")
    occupied["Hotel Receivable"] = to_float("Hotel Receivable")  # Full, only on check-in
    occupied["GST"] = to_float("GST")  # Full, only on check-in
    occupied["Commission"] = to_float("Commission")  # Full, only on check-in
    occupied["Advance"] = to_float("Advance")  # Full, only on check-in primary
    occupied["Balance"] = to_float("Balance")  # Full, only on check-in primary
    occupied["Total Pax"] = to_int("Total Pax")  # Unchanged (per-room split sums to booking total)

    # MOP (unchanged: uses full Advance/Balance on check-in)
    mop_data = {m: 0.0 for m in ["UPI","Cash","Go-MMT","Agoda","NOT PAID","Expenses","Bank Transfer","Stayflexi","Card Payment","Expedia","Cleartrip","Website"]}
    total_cash = total = 0.0

    for _, row in occupied.iterrows():
        for mop_col, amount_col in [("Advance Mop", "Advance"), ("Balance Mop", "Balance")]:
            mop = sanitize_string(row[mop_col])
            amount = row[amount_col]
            if not mop or amount == 0: continue
            for std, variants in mop_mapping.items():
                if mop in variants:
                    mop_data[std] += amount
                    total += amount
                    if std == "Cash": total_cash += amount

    mop_data["Expenses"] = 0.0
    mop_data["Total Cash"] = total_cash
    mop_data["Total"] = total

    # DTD: Use Per Night sum for value (daily prorated hotel receivable)
    dtd = {m: {"rooms":0,"value":0.0,"comm":0.0,"gst":0.0,"pax":0} for m in mob_types}
    dtd_rooms = len(occupied)
    dtd_value = occupied["Per Night"].sum()  # Sum of per_night values
    dtd_comm = occupied["Commission"].sum()  # Full on check-in
    dtd_gst = occupied["GST"].sum()  # Full on check-in
    dtd_pax = occupied["Total Pax"].sum()

    for _, row in occupied.iterrows():
        mob_raw = sanitize_string(row["MOB"])
        mob = next((m for m, vs in mob_mapping.items() if mob_raw.upper() in [v.upper() for v in vs]), "Booking")
        dtd[mob]["rooms"] += 1
        dtd[mob]["value"] += row["Per Night"]  # Use per_night for daily value
        dtd[mob]["comm"] += row["Commission"]  # Full
        dtd[mob]["gst"] += row["GST"]  # Full
        dtd[mob]["pax"] += row["Total Pax"]

    for m in mob_types:
        r = dtd[m]["rooms"]
        dtd[m]["arr"] = dtd[m]["value"] / r if r > 0 else 0.0

    dtd["Total"] = {
        "rooms": dtd_rooms,
        "value": dtd_value,
        "arr": dtd_value / dtd_rooms if dtd_rooms > 0 else 0.0,
        "comm": dtd_comm,
        "gst": dtd_gst,
        "pax": dtd_pax
    }

    return {"mop": mop_data, "dtd": dtd}

# ──────────────────────────────────────────────────────────────────────────────
# UI – Dashboard
# ──────────────────────────────────────────────────────────────────────────────
def show_daily_status():
    st.title("Daily Status Dashboard")
    if st.button("Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    today = date.today()
    year = st.selectbox("Year", list(range(today.year-5, today.year+6)), index=5)
    month = st.selectbox("Month", list(range(1,13)), index=today.month-1)

    props = load_properties()
    if not props:
        st.info("No properties found.")
        return

    mob_types = ["Booking","Direct","Bkg-Direct","Agoda","Go-MMT","Walk-In","TIE Group","Stayflexi","Airbnb","Social Media","Expedia","Cleartrip","Website"]

    for prop in props:
        with st.expander(f"**{prop}**", expanded=False):
            month_dates = [date(year, month, d) for d in range(1, calendar.monthrange(year, month)[1]+1)]
            start, end = month_dates[0], month_dates[-1]
            bookings = load_combined_bookings(prop, start, end)

            mtd_rooms = mtd_value = mtd_comm = mtd_gst = mtd_pax = 0
            mtd = {m: {"rooms":0,"value":0.0,"comm":0.0,"gst":0.0,"pax":0} for m in mob_types}

            for day in month_dates:
                daily = filter_bookings_for_day(bookings, day)
                st.markdown(f"### {day.strftime('%b %d, %Y')}")

                assigned, over = assign_inventory_numbers(daily, prop)
                display_df, full_df = create_inventory_table(assigned, over, prop, day)

                stats = extract_stats_from_table(display_df, mob_types)
                dtd = stats["dtd"]
                mop_data = stats["mop"]

                mtd_rooms += dtd["Total"]["rooms"]
                mtd_value += dtd["Total"]["value"]
                mtd_comm += dtd["Total"]["comm"]
                mtd_gst += dtd["Total"]["gst"]
                mtd_pax += dtd["Total"]["pax"]
                for m in mob_types:
                    mtd[m]["rooms"] += dtd[m]["rooms"]
                    mtd[m]["value"] += dtd[m]["value"]
                    mtd[m]["comm"] += dtd[m]["comm"]
                    mtd[m]["gst"] += dtd[m]["gst"]
                    mtd[m]["pax"] += dtd[m]["pax"]

                if daily:
                    # Check if user is Accounts Team
                    is_accounts_team = st.session_state.get('role', '') == "Accounts Team"

                    # Comprehensive column configuration - ONLY 3 fields editable
                    col_config = {
                        # Read-only columns (explicitly disabled)
                        "Inventory No": st.column_config.TextColumn("Inventory No", disabled=True),
                        "Room No": st.column_config.TextColumn("Room No", disabled=True),
                        "Booking ID": st.column_config.TextColumn("Booking ID", disabled=True),
                        "Guest Name": st.column_config.TextColumn("Guest Name", disabled=True),
                        "Mobile No": st.column_config.TextColumn("Mobile No", disabled=True),
                        "Total Pax": st.column_config.NumberColumn("Total Pax", disabled=True),
                        "Check In": st.column_config.TextColumn("Check In", disabled=True),
                        "Check Out": st.column_config.TextColumn("Check Out", disabled=True),
                        "Days": st.column_config.NumberColumn("Days", disabled=True),
                        "MOB": st.column_config.TextColumn("MOB", disabled=True),
                        "Room Charges": st.column_config.TextColumn("Room Charges", disabled=True),
                        "GST": st.column_config.TextColumn("GST", disabled=True),
                        "Total": st.column_config.TextColumn("Total", disabled=True),
                        "Commission": st.column_config.TextColumn("Commission", disabled=True),
                        "Hotel Receivable": st.column_config.TextColumn("Hotel Receivable", disabled=True),
                        "Per Night": st.column_config.TextColumn("Per Night", disabled=True),
                        "Advance": st.column_config.TextColumn("Advance", disabled=True),
                        "Advance Mop": st.column_config.TextColumn("Advance Mop", disabled=True),
                        "Balance": st.column_config.TextColumn("Balance", disabled=True),
                        "Balance Mop": st.column_config.TextColumn("Balance Mop", disabled=True),
                        "Plan": st.column_config.TextColumn("Plan", disabled=True),
                        "Booking Status": st.column_config.TextColumn("Booking Status", disabled=True),
                        "Payment Status": st.column_config.TextColumn("Payment Status", disabled=True),
                        "Submitted by": st.column_config.TextColumn("Submitted by", disabled=True),
                        "Modified by": st.column_config.TextColumn("Modified by", disabled=True),
                        "Remarks": st.column_config.TextColumn("Remarks", disabled=True),
                        
                        # EDITABLE columns (only these 3, and only for Accounts Team)
                        "Advance Remarks": st.column_config.TextColumn(
                            "Advance Remarks",
                            help="Enter remarks for advance payment",
                            max_chars=500,
                            required=False,
                            disabled=not is_accounts_team
                        ),
                        "Balance Remarks": st.column_config.TextColumn(
                            "Balance Remarks",
                            help="Enter remarks for balance payment",
                            max_chars=500,
                            required=False,
                            disabled=not is_accounts_team
                        ),
                        "Accounts Status": st.column_config.SelectboxColumn(
                            "Accounts Status",
                            help="Select accounting status",
                            options=["Pending", "Completed"],
                            default="Pending",
                            required=False,
                            disabled=not is_accounts_team
                        ),
                    }
                    
                    # Interactive editor with comprehensive configuration
                    edited_display = st.data_editor(
                        display_df,
                        column_config=col_config,
                        hide_index=True,
                        use_container_width=True,
                        num_rows="fixed",  # Prevent adding/deleting rows
                        key=f"editor_{prop}_{day.isoformat()}"
                    )
                                        
                   # Save button with unique key (show only if editable)
                    if is_accounts_team and st.button(f"💾 Save Changes", key=f"save_{prop}_{day.isoformat()}"):
                        # Merge edited visible with full
                        edited_full = full_df.copy()
                        editable_cols = ["Advance Remarks", "Balance Remarks", "Accounts Status"]
                        for col in editable_cols:
                            edited_full[col] = edited_display[col]
                        
                        updated_bookings = {}
                        for _, row in edited_full.iterrows():
                            bid = row.get("Booking ID")
                            db_id = row.get("db_id")
                            if pd.isna(bid) or pd.isna(db_id): continue
                            if bid not in updated_bookings:
                                updated_bookings[bid] = {
                                    "advance_remarks": row["Advance Remarks"],
                                    "balance_remarks": row["Balance Remarks"],
                                    "accounts_status": row["Accounts Status"],
                                    "type": row["edit_type"],
                                    "db_id": db_id
                                }
                        
                        success_count = 0
                        for bid, data in updated_bookings.items():
                            table_name = "online_reservations" if data["type"] == "online" else "reservations"
                            update_data = {
                                "advance_remarks": data["advance_remarks"],
                                "balance_remarks": data["balance_remarks"],
                                "accounts_status": data["accounts_status"]
                            }
                            try:
                                res = supabase.table(table_name).update(update_data).eq("id", data["db_id"]).execute()
                                if res.data:
                                    success_count += 1
                                    logging.info(f"Updated {table_name} id={data['db_id']}")
                                else:
                                    st.warning(f"No update for {bid} (no matching record)")
                            except Exception as e:
                                st.error(f"Update failed for {bid}: {e}")
                                logging.error(f"Update error {bid}: {e}")
                        
                        st.success(f"✅ Saved {success_count} bookings successfully. Refresh to see changes.")
                        st.cache_data.clear()
                        st.rerun()

                    # Tables
                    dtd_df = pd.DataFrame([
                        {"MOB": m, "D.T.D Rooms": d["rooms"], "D.T.D Value": f"₹{d['value']:,.2f}",
                         "D.T.D ARR": f"₹{d['arr']:,.2f}", "D.T.D Comm": f"₹{d['comm']:,.2f}"} 
                        for m, d in dtd.items() if m != "Total"
                    ] + [{"MOB": "Total", "D.T.D Rooms": dtd["Total"]["rooms"], 
                          "D.T.D Value": f"₹{dtd['Total']['value']:,.2f}",
                          "D.T.D ARR": f"₹{dtd['Total']['arr']:,.2f}", 
                          "D.T.D Comm": f"₹{dtd['Total']['comm']:,.2f}"}],
                        columns=["MOB","D.T.D Rooms","D.T.D Value","D.T.D ARR","D.T.D Comm"])

                    mop_df = pd.DataFrame([{"MOP": m, "Amount": f"₹{v:,.2f}"} for m, v in mop_data.items()], 
                                         columns=["MOP", "Amount"])

                    mtd_df = pd.DataFrame([
                        {"MOB": m, "M.T.D Rooms": mtd[m]["rooms"], "M.T.D Value": f"₹{mtd[m]['value']:,.2f}",
                         "M.T.D ARR": f"₹{mtd[m]['value']/mtd[m]['rooms']:,.2f}" if mtd[m]["rooms"] > 0 else "₹0.00",
                         "M.T.D Comm": f"₹{mtd[m]['comm']:,.2f}"} for m in mob_types
                    ] + [{"MOB": "Total", "M.T.D Rooms": mtd_rooms, "M.T.D Value": f"₹{mtd_value:,.2f}",
                          "M.T.D ARR": f"₹{mtd_value/mtd_rooms:,.2f}" if mtd_rooms > 0 else "₹0.00",
                          "M.T.D Comm": f"₹{mtd_comm:,.2f}"}], 
                        columns=["MOB","M.T.D Rooms","M.T.D Value","M.T.D ARR","M.T.D Comm"])

                    total_inventory = len([i for i in PROPERTY_INVENTORY.get(prop,{}).get("all",[]) if not i.startswith(("Day Use","No Show"))])
                    occ_pct = (dtd["Total"]["rooms"] / total_inventory * 100) if total_inventory else 0.0
                    mtd_occ_pct = (mtd_rooms / (total_inventory * day.day) * 100) if total_inventory and day.day > 0 else 0.0

                    summary = {
                        "Rooms Sold": dtd["Total"]["rooms"],
                        "Hotel Revenue": f"₹{dtd['Total']['value']:,.2f}",
                        "ARR": f"₹{dtd['Total']['arr']:,.2f}",
                        "Occupancy": f"{occ_pct:.1f}%",
                        "Total Pax": dtd["Total"]["pax"],
                        "Total Rooms": total_inventory,
                        "GST Paid": f"₹{dtd['Total']['gst']:,.2f}",
                        "Commission Paid": f"₹{dtd['Total']['comm']:,.2f}",
                        "MTD Occupancy": f"{mtd_occ_pct:.1f}%",
                        "MTD Revenue": f"₹{mtd_value:,.2f}",
                    }

                    c1, c2, c3, c4 = st.columns(4)
                    with c1: st.subheader("MOP"); st.dataframe(mop_df, use_container_width=True)
                    with c2: st.subheader("Day Revenue"); st.dataframe(dtd_df, use_container_width=True)
                    with c3: st.subheader("Month Revenue"); st.dataframe(mtd_df, use_container_width=True)
                    with c4:
                        st.subheader("Summary")
                        st.dataframe(pd.DataFrame([{"Metric": k, "Value": v} for k, v in summary.items()]), use_container_width=True)
                else:
                    st.info("No active bookings.")

# ──────────────────────────────────────────────────────────────────────────────
# Run
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    show_daily_status()
