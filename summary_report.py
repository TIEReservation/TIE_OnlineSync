# summary_report.py - CORRECTLY FIXED VERSION with Short Property Names
# Now uses the EXACT same booking query logic as Daily Status

import streamlit as st
from datetime import date, timedelta
import calendar
import pandas as pd
from supabase import create_client, Client
from typing import List, Dict
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

def normalize_property_name(prop_name: str) -> str:
    if not prop_name:
        return prop_name
    return PROPERTY_MAPPING.get(prop_name, prop_name)

def get_short_name(prop_name: str) -> str:
    """Get short name for property, fallback to full name if not found"""
    return PROPERTY_SHORT_NAMES.get(prop_name, prop_name)

# -------------------------- Helpers --------------------------
def load_properties() -> List[str]:
    try:
        direct = supabase.table("reservations").select("property_name").execute().data or []
        online = supabase.table("online_reservations").select("property").execute().data or []
        
        props = {
            normalize_property_name(r.get("property_name") or r.get("property"))
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
    """
    normalized_prop = normalize_property_name(prop)
    query_props = [normalized_prop] + reverse_mapping.get(normalized_prop, [])
    
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
        
        # Normalize all bookings
        all_bookings = []
        for booking in direct:
            normalized = normalize_property_name(booking.get("property_name"))
            if normalized == prop:
                booking["property_name"] = normalized
                booking["type"] = "direct"
                all_bookings.append(booking)
        
        for booking in online:
            normalized = normalize_property_name(booking.get("property"))
            if normalized == prop:
                booking["property"] = normalized
                booking["type"] = "online"
                all_bookings.append(booking)
        
        return all_bookings
    except Exception as e:
        st.error(f"Error loading bookings for {prop}: {e}")
        return []


def filter_bookings_for_day(bookings: List[Dict], target: date) -> List[Dict]:
    """Keep only bookings that are active on *target*."""
    return [
        b
        for b in bookings
        if date.fromisoformat(b["check_in"]) <= target < date.fromisoformat(b["check_out"])
    ]


def assign_inventory_numbers(daily: List[Dict], prop: str):
    """
    FIXED: Now properly validates rooms against property inventory.
    Splits comma-separated room_no and creates separate entries per room.
    Returns (assigned, overbookings) - matching inventory.py logic exactly.
    """
    # Get property inventory
    PROPERTY_INVENTORY = {
        "Le Poshe Beach view": {"all": ["101","102","201","202","203","204","301","302","303","304","Day Use 1","Day Use 2","No Show"]},
        "La Millionaire Resort": {"all": ["101","102","103","105","201","202","203","204","205","206","207","208","301","302","303","304","305","306","307","308","401","402","Day Use 1","Day Use 2","Day Use 3","Day Use 4","Day Use 5","No Show"]},
        "Le Poshe Luxury": {"all": ["101","102","201","202","203","204","205","301","302","303","304","305","401","402","403","404","405","501","Day Use 1","Day Use 2","No Show"]},
        "Le Poshe Suite": {"all": ["601","602","603","604","701","702","703","704","801","Day Use 1","Day Use 2","No Show"]},
        "La Paradise Residency": {"all": ["101","102","103","201","202","203","301","302","303","304","Day Use 1","Day Use 2","No Show"]},
        "La Paradise Luxury": {"all": ["101","102","103","201","202","203","Day Use 1","Day Use 2","No Show"]},
        "La Villa Heritage": {"all": ["101","102","103","201","202","203","301","Day Use 1","Day Use 2","No Show"]},
        "Le Pondy Beachside": {"all": ["101","102","201","202","Day Use 1","Day Use 2","No Show"]},
        "Le Royce Villa": {"all": ["101","102","201","202","Day Use 1","Day Use 2","No Show"]},
        "La Tamara Luxury": {"all": ["101","102","103","104","105","106","201","202","203","204","205","206","301","302","303","304","305","306","401","402","403","404","Day Use 1","Day Use 2","No Show"]},
        "La Antilia Luxury": {"all": ["101","201","202","202","203","204","301","302","303","304","401","Day Use 1","Day Use 2","No Show"]},
        "La Tamara Suite": {"all": ["101","102","103","104","201","202","203","204","205","206","Day Use 1","Day Use 2","No Show"]},
        "Le Park Resort": {"all": ["111","222","333","444","555","666","Day Use 1","Day Use 2","No Show"]},
        "Villa Shakti": {"all": ["101","102","201","201A","202","203","301","301A","302","303","401","Day Use 1","Day Use 2","No Show"]},
        "Eden Beach Resort": {"all": ["101","102","103","201","202","Day Use 1","Day Use 2","No Show"]},
        "Le Terra": {"all": ["101","102","103","104","105","106","107","Day Use 1","Day Use 2","No Show"]},
        "La Coromandel Luxury": {"all": ["101","102","103","201","202","203","204","205","206","301","Day Use 1","Day Use 2","No Show"]},
        "Happymates Forest Retreat": {"all": ["101","102","Day Use 1","Day Use 2","No Show"]}
    }
    
    inv = PROPERTY_INVENTORY.get(prop, {"all": []})["all"]
    inv_lookup = {i.strip().lower(): i for i in inv}
    
    assigned = []
    over = []
    
    for b in daily:
        raw_room = str(b.get("room_no") or "").strip()
        if not raw_room:
            # No room number = overbooking
            over.append(b)
            continue
        
        # Split comma-separated rooms
        requested = [r.strip() for r in raw_room.split(",") if r.strip()]
        assigned_rooms = []
        
        # Validate each requested room against inventory
        for r in requested:
            key = r.lower()
            if key in inv_lookup:
                assigned_rooms.append(inv_lookup[key])
            else:
                # Invalid room = overbooking
                over.append(b)
                assigned_rooms = []
                break
        
        if not assigned_rooms:
            continue
        
        # Create separate entry for each valid room
        for idx, room in enumerate(assigned_rooms):
            new_b = b.copy()
            new_b["assigned_room"] = room
            new_b["room_no"] = room
            new_b["is_primary"] = (idx == 0)
            assigned.append(new_b)
    
    return assigned, over


def safe_float(value, default=0.0):
    """Safely convert to float."""
    try:
        return float(value) if value not in [None, "", " "] else default
    except:
        return default


def compute_daily_metrics(bookings: List[Dict], prop: str, day: date) -> Dict:
    """
    FIXED: Calculates metrics matching Daily Status exactly.
    - Rooms sold = count of VALID occupied inventory slots (excludes overbookings)
    - Financials only counted on check-in day for primary bookings
    """
    daily = filter_bookings_for_day(bookings, day)
    assigned, over = assign_inventory_numbers(daily, prop)  # Now using 'over' list

    # FIXED: Rooms sold = count of VALID assigned entries ONLY (excludes overbookings)
    rooms_sold = len(assigned)

    # Financial metrics: ONLY for bookings checking in today (primary only)
    check_in_primaries = [
        b for b in assigned  # Only from valid assigned bookings
        if b.get("is_primary", True) and date.fromisoformat(b["check_in"]) == day
    ]

    # Extract financial values
    room_charges = 0.0
    gst = 0.0
    commission = 0.0
    
    for b in check_in_primaries:
        is_online = b.get("type") == "online"
        
        if is_online:
            total_amount = safe_float(b.get("booking_amount"))
            gst += safe_float(b.get("ota_tax"))
            commission += safe_float(b.get("ota_commission"))
            room_charges += total_amount - safe_float(b.get("ota_tax"))
        else:
            total_amount = safe_float(b.get("total_tariff"))
            room_charges += total_amount
            # Direct bookings: gst and commission already 0

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

        # Pretty-print monetary columns
        if metric != "rooms_sold":
            monetary_cols = df.columns[1:]
            df[monetary_cols] = df[monetary_cols].applymap(
                lambda x: f"{x:,.2f}" if isinstance(x, (int, float)) else x
            )

        st.dataframe(df, use_container_width=True)
        st.markdown("---")


# -------------------------- Run --------------------------
if __name__ == "__main__":
    show_summary_report()
