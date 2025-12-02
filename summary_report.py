# summary_report.py - CORRECTLY FIXED VERSION with Short Property Names
# Now uses the EXACT same booking query logic as Daily Status

import streamlit as st
from datetime import date, timedelta
import calendar
import pandas as pd
from supabase import create_client, Client
from typing import List, Dict, Optional
import os

# -------------------------- Supabase --------------------------
try:
    supabase: Client = create_client(
        st.secrets["supabase"]["url"],
        st.secrets["supabase"]["key"]
    )
except (KeyError, FileNotFoundError):
    try:
        supabase: Client = create_client(
            os.environ["SUPABASE_URL"],
            os.environ["SUPABASE_KEY"]
        )
    except KeyError as e:
        st.error(f"Missing Supabase configuration: {e}")
        st.stop()

# -------------------------- Property Mapping --------------------------
PROPERTY_MAPPING = {
    "La Millionaire Luxury Resort": "La Millionaire Resort",
    "Le Poshe Beach View": "Le Poshe Beach view",
    "Le Poshe Beach view": "Le Poshe Beach view",
    "Le Poshe Beach VIEW": "Le Poshe Beach view",
    "Le Poshe Beachview": "Le Poshe Beach view",
    "Millionaire": "La Millionaire Resort",
    "Le Pondy Beach Side": "Le Pondy Beachside",
    "Le Teera": "Le Terra"
}

# Property short names for display
PROPERTY_SHORT_NAMES = {
    "Eden Beach Resort": "EBR",
    "La Antilia Luxury": "LAL",
    "La Coromandel Luxury": "LCL",
    "La Millionaire Resort": "LMR",
    "La Paradise Luxury": "LaPL",
    "La Paradise Residency": "LPR",
    "La Tamara Luxury": "LTL",
    "La Tamara Suite": "LTS",
    "La Villa Heritage": "LVH",
    "Le Park Resort": "LPR",
    "Le Pondy Beachside": "LPBs",
    "Le Poshe Beach view": "LPBv",
    "Le Poshe Luxury": "LePL",
    "Le Poshe Suite": "LPS",
    "Le Royce Villa": "LRV",
    "Villa Shakti": "VS",
    "Happymates Forest Retreat": "HFR",
    "Le Terra": "LT"
}

# Add reverse mapping
reverse_mapping = {c: [] for c in set(PROPERTY_MAPPING.values())}
for v, c in PROPERTY_MAPPING.items():
    reverse_mapping[c].append(v)

def normalize_property(name: str) -> str:
    return PROPERTY_MAPPING.get(name.strip(), name.strip())

def sanitize_string(v, default: str = "") -> str:
    return str(v).strip() if v is not None else default

def safe_int(v, default: int = 0) -> int:
    try:
        return int(float(v)) if v not in [None, "", " "] else default
    except:
        return default

def safe_float(v, default: float = 0.0) -> float:
    try:
        return float(v) if v not in [None, "", " "] else default
    except:
        return default

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
            "receivable": receivable,
            "advance": safe_float(row.get("total_payment_made") if is_online else row.get("advance_amount")),
            "advance_mop": sanitize_string(row.get("advance_mop")),
            "balance": safe_float(row.get("balance_due") if is_online else row.get("balance_amount")),
            "balance_mop": sanitize_string(row.get("balance_mop")),
            "booking_status": status,
            "payment_status": pay,
            "submitted_by": sanitize_string(row.get("submitted_by")),
            "modified_by": sanitize_string(row.get("modified_by")),
            "remarks": sanitize_string(row.get("remarks")),
        }
    except Exception as e:
        st.warning(f"normalize failed ({row.get('booking_id')}): {e}")
        return None

def get_short_name(prop_name: str) -> str:
    """Get short name for property, fallback to full name if not found"""
    return PROPERTY_SHORT_NAMES.get(prop_name, prop_name)

# -------------------------- Helpers --------------------------
def load_properties() -> List[str]:
    try:
        direct = supabase.table("reservations").select("property_name").execute().data or []
        online = supabase.table("online_reservations").select("property").execute().data or []
        
        props = {
            normalize_property(r.get("property_name") or r.get("property", ""))
            for r in direct + online
            if r.get("property_name") or r.get("property")
        }
        return sorted(props)
    except Exception as e:
        st.error(f"Error loading properties: {e}")
        return []


def load_combined_bookings(prop: str, start: date, end: date) -> List[Dict]:
    """
    FIXED: Now uses EXACT same query logic as Daily Status (inventory.py).
    Fetches bookings that overlap with the date range, not just those starting in range.
    Uses normalize_booking for consistency.
    """
    normalized_prop = normalize_property(prop)
    query_props = [normalized_prop] + reverse_mapping.get(normalized_prop, [])
    combined: List[Dict] = []
    
    try:
        # FIXED: Use .lte("check_in") and .gte("check_out") like Daily Status
        direct = (
            supabase.table("reservations")
            .select("*")
            .in_("property_name", query_props)
            .lte("check_in", str(end))  # Check-in on or before end date
            .gte("check_out", str(start))  # Check-out on or after start date
            .in_("plan_status", ["Confirmed", "Completed"])
            .in_("payment_status", ["Partially Paid", "Fully Paid"])
            .execute()
            .data
            or []
        )
        
        for r in direct:
            norm = normalize_booking(r, is_online=False)
            if norm and norm["property"] == normalized_prop:
                combined.append(norm)
        
        online = (
            supabase.table("online_reservations")
            .select("*")
            .in_("property", query_props)
            .lte("check_in", str(end))  # Check-in on or before end date
            .gte("check_out", str(start))  # Check-out on or after start date
            .in_("booking_status", ["Confirmed", "Completed"])
            .in_("payment_status", ["Partially Paid", "Fully Paid"])
            .execute()
            .data
            or []
        )
        
        for r in online:
            norm = normalize_booking(r, is_online=True)
            if norm and norm["property"] == normalized_prop:
                combined.append(norm)
        
        return combined
    except Exception as e:
        st.error(f"Error loading bookings for {prop}: {e}")
        return []


def filter_bookings_for_day(bookings: List[Dict], target: date) -> List[Dict]:
    """Keep only bookings that are active on *target*."""
    return [
        b.copy() | {"target_date": target}
        for b in bookings
        if date.fromisoformat(b["check_in"]) <= target < date.fromisoformat(b["check_out"])
    ]


def assign_inventory_numbers(daily_bookings: List[Dict], property: str):
    """
    FIXED: EXACT COPY from inventory.py – now 100% reliable for "No Show" and duplicate detection.
    Uses already_assigned set to prevent counting overbooked duplicates as sold rooms.
    Splits multi-room bookings correctly, prorate per_night.
    Returns (assigned, overbookings)
    """
    assigned, over = [], []
    inv = PROPERTY_INVENTORY.get(property, {"all": []})["all"]
    inv_lookup = {i.strip().lower(): i for i in inv}
    already_assigned = set()  # Track which rooms are already assigned

    for b in daily_bookings:
        raw_room = str(b.get("room_no", "") or "").strip()
        if not raw_room:
            over.append(b)
            continue

        # Handle comma-separated rooms
        requested = [r.strip() for r in raw_room.split(",") if r.strip()]
        assigned_rooms = []
        is_overbooking = False

        for r in requested:
            key = r.lower()
            
            # Check if room exists in inventory
            if key not in inv_lookup:
                is_overbooking = True
                break
            
            room_name = inv_lookup[key]
            
            # Check if room is already assigned (duplicate booking)
            if room_name in already_assigned:
                is_overbooking = True
                break
            
            assigned_rooms.append(room_name)

        # If any issue found, mark as overbooking
        if is_overbooking or not assigned_rooms:
            over.append(b)
            continue

        # Mark rooms as assigned
        for room in assigned_rooms:
            already_assigned.add(room)

        # Calculate split values (matching inventory.py)
        days = max(b.get("days", 1), 1)
        receivable = b.get("receivable", 0.0)
        num_rooms = len(assigned_rooms)
        total_nights = days * num_rooms
        per_night = receivable / total_nights if total_nights > 0 else 0.0
        base_pax = b["total_pax"] // num_rooms if num_rooms else 0
        rem = b["total_pax"] % num_rooms if num_rooms else 0

        for idx, room in enumerate(assigned_rooms):
            nb = b.copy()
            nb["assigned_room"] = room
            nb["room_no"] = room
            nb["total_pax"] = base_pax + (1 if idx < rem else 0)
            nb["per_night"] = per_night
            nb["is_primary"] = (idx == 0)
            assigned.append(nb)

    return assigned, over


# -------------------------- Property Inventory (EXACT from inventory.py) --------------------------
PROPERTY_INVENTORY = {
    "Le Poshe Beach view": {"all": ["101","102","201","202","203","204","301","302","303","304","Day Use 1","Day Use 2","No Show"],"three_bedroom":["203","204"]},
    "La Millionaire Resort": {"all": ["101","102","103","105","201","202","203","204","205","206","207","208","301","302","303","304","305","306","307","308","401","402","Day Use 1","Day Use 2","Day Use 3","Day Use 4","Day Use 5","No Show"],"three_bedroom":["203","204","205"]},
    "Le Poshe Luxury": {"all": ["101","102","201","202","203","204","205","301","302","303","304","305","401","402","403","404","405","501","Day Use 1","Day Use 2","No Show"],"three_bedroom":["203","204","205"]},
    "Le Poshe Suite": {"all": ["601","602","603","604","701","702","703","704","801","Day Use 1","Day Use 2","No Show"],"three_bedroom":[]},
    "La Paradise Residency": {"all": ["101","102","103","201","202","203","301","302","303","304","Day Use 1","Day Use 2","No Show"],"three_bedroom":["203"]},
    "La Paradise Luxury": {"all": ["101","102","103","201","202","203","Day Use 1","Day Use 2","No Show"],"three_bedroom":["203"]},
    "La Villa Heritage": {"all": ["101","102","103","201","202","203","301","Day Use 1","Day Use 2","No Show"],"three_bedroom":["203"]},
    "Le Pondy Beachside": {"all": ["101","102","201","202","Day Use 1","Day Use 2","No Show"],"three_bedroom":[]},
    "Le Royce Villa": {"all": ["101","102","201","202","Day Use 1","Day Use 2","No Show"],"three_bedroom":[]},
    "La Tamara Luxury": {"all": ["101","102","103","104","105","106","201","202","203","204","205","206","301","302","303","304","305","306","401","402","403","404","Day Use 1","Day Use 2","No Show"],"three_bedroom":["203","204","205","206"]},
    "La Antilia Luxury": {"all": ["101","201","202","202","203","204","301","302","303","304","401","Day Use 1","Day Use 2","No Show"],"three_bedroom":["203","204"]},
    "La Tamara Suite": {"all": ["101","102","103","104","201","202","203","204","205","206","Day Use 1","Day Use 2","No Show"],"three_bedroom":["203","204","205","206"]},
    "Le Park Resort": {"all": ["111","222","333","444","555","666","Day Use 1","Day Use 2","No Show"],"three_bedroom":[]},
    "Villa Shakti": {"all": ["101","102","201","201A","202","203","301","301A","302","303","401","Day Use 1","Day Use 2","No Show"],"three_bedroom":["203"]},
    "Eden Beach Resort": {"all": ["101","102","103","201","202","Day Use 1","Day Use 2","No Show"],"three_bedroom":[]},
    "Le Terra": {"all": ["101","102","103","104","105","106","107","Day Use 1","Day Use 2","No Show"],"three_bedroom":[]},
    "La Coromandel Luxury": {"all": ["101","102","103","201","202","203","204","205","206","301","Day Use 1","Day Use 2","No Show"],"three_bedroom":[]},
    "Happymates Forest Retreat": {"all": ["101","102","Day Use 1","Day Use 2","No Show"],"three_bedroom":[]}  
}


def compute_daily_metrics(bookings: List[Dict], prop: str, day: date) -> Dict:
    """
    FIXED: Calculates metrics matching Daily Status exactly.
    - Rooms sold = count of UNIQUE occupied inventory slots (after duplicate detection)
    - Financials only counted on check-in day for primary bookings
    Uses normalized bookings and full assign_inventory_numbers.
    """
    daily = filter_bookings_for_day(bookings, day)
    assigned, over = assign_inventory_numbers(daily, prop)

    # FIXED: Count unique assigned rooms (not entries) – matches inventory.py
    rooms_sold = len(set(b.get("assigned_room") for b in assigned if b.get("assigned_room")))

    # Financial metrics: ONLY for bookings checking in today (primary only)
    check_in_primaries = [
        b for b in assigned  # Only from valid assigned bookings
        if b.get("is_primary", True) and date.fromisoformat(b["check_in"]) == day
    ]

    # Extract financial values – now from normalized fields
    room_charges = 0.0
    gst = 0.0
    commission = 0.0
    
    for b in check_in_primaries:
        # Use normalized values directly
        room_charges += b.get("room_charges", 0.0)
        gst += b.get("gst", 0.0)
        commission += b.get("commission", 0.0)

    total = room_charges + gst
    receivable = total - commission
    tax_deduction = receivable * 0.003
    per_night = receivable / rooms_sold if rooms_sold else 0.0

    return {
        "rooms_sold": rooms_sold,
        "room_charges": room_charges,
        "gst": gst,
        "total": total,
        "commission": commission,
        "tax_deduction": tax_deduction,
        "receivable": receivable,
        "receivable_per_night": per_night,
    }


# -------------------------- Report Builder --------------------------
def build_report(
    props: List[str],
    dates: List[date],
    bookings: Dict[str, List[Dict]],
    metric: str,
) -> pd.DataFrame:
    """
    Generic builder – one DataFrame per metric.
    Columns: Date | <Short Property Name> | ... | Total
    Last row = month totals.
    """
    rows = []
    prop_totals = {p: 0.0 for p in props}
    grand_total = 0.0

    for d in dates:
        row = {"Date": d.strftime("%Y-%m-%d")}
        day_sum = 0.0
        for p in props:
            val = compute_daily_metrics(bookings.get(p, []), p, d).get(metric, 0.0)
            # Use short name as column header
            short_name = get_short_name(p)
            row[short_name] = val
            day_sum += val
            prop_totals[p] += val
        row["Total"] = day_sum
        grand_total += day_sum
        rows.append(row)

    # Month total row
    total_row = {"Date": "Total"}
    for p in props:
        short_name = get_short_name(p)
        total_row[short_name] = prop_totals[p]
    total_row["Total"] = grand_total
    rows.append(total_row)

    return pd.DataFrame(rows)


# -------------------------- UI --------------------------
def show_summary_report():
    st.title("TIE Hotels & Resort Summary Report")

    today = date.today()
    year = st.selectbox(
        "Year",
        list(range(today.year - 5, today.year + 6)),
        index=5,
    )
    month = st.selectbox(
        "Month",
        list(range(1, 13)),
        index=today.month - 1,
    )

    properties = load_properties()
    if not properties:
        st.info("No properties found in the database.")
        return

    # Month calendar
    _, days_in_month = calendar.monthrange(year, month)
    month_dates = [date(year, month, d) for d in range(1, days_in_month + 1)]
    start_date = month_dates[0]
    end_date = month_dates[-1]

    # Load all bookings once
    with st.spinner("Loading booking data..."):
        bookings = {
            p: load_combined_bookings(p, start_date, end_date) for p in properties
        }

    # 8 report definitions
    report_defs = {
        "rooms_report": ("TIE Hotels & Resort Rooms Report", "rooms_sold"),
        "room_charges_report": ("TIE Hotels & Resort Room Charges Report", "room_charges"),
        "gst_report": ("TIE Hotels & Resort GST Report", "gst"),
        "total_report": ("TIE Hotels & Resort Total Report", "total"),
        "commission_report": ("TIE Hotels & Resort Commission Report", "commission"),
        "tax_deduction_report": ("TIE Hotels & Resort Tax Deduction Report", "tax_deduction"),
        "receivable_report": ("TIE Hotels & Resort Receivable Report", "receivable"),
        "receivable_per_night_report": (
            "TIE Hotels & Resort Receivable Per Night Report",
            "receivable_per_night",
        ),
    }

    # Render each section
    for key, (title, metric) in report_defs.items():
        st.subheader(title)
        df = build_report(properties, month_dates, bookings, metric)

        # Pretty-print monetary columns with compact formatting
        if metric != "rooms_sold":
            monetary_cols = df.columns[1:]
            df[monetary_cols] = df[monetary_cols].applymap(
                lambda x: f"{x:,.0f}" if isinstance(x, (int, float)) else x
            )

        # Display full table without scrolling - calculate appropriate height
        # Height = header (38px) + rows (35px each) + padding
        table_height = 38 + (len(df) * 35) + 10
        st.dataframe(
            df, 
            use_container_width=False,  # Let columns auto-fit to content
            height=table_height
        )
        st.markdown("---")


# -------------------------- Run --------------------------
if __name__ == "__main__":
    show_summary_report()
