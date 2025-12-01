# summary_report.py - CORRECTLY FIXED VERSION
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

# Add reverse mapping
reverse_mapping = {c: [] for c in set(PROPERTY_MAPPING.values())}
for v, c in PROPERTY_MAPPING.items():
    reverse_mapping[c].append(v)

def normalize_property_name(prop_name: str) -> str:
    if not prop_name:
        return prop_name
    return PROPERTY_MAPPING.get(prop_name, prop_name)

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
    Splits comma-separated room_no and creates separate entries per room.
    Matches inventory.py logic exactly.
    """
    assigned = []
    
    for b in daily:
        raw_room = str(b.get("room_no") or "").strip()
        if not raw_room:
            # Fallback: treat as 1 room
            new_b = b.copy()
            new_b["assigned_room"] = "1"
            new_b["is_primary"] = True
            assigned.append(new_b)
            continue
        
        # Split comma-separated rooms
        rooms = [r.strip() for r in raw_room.split(",") if r.strip()]
        if not rooms:
            rooms = ["1"]
        
        # Create separate entry for each room
        for idx, room in enumerate(rooms):
            new_b = b.copy()
            new_b["assigned_room"] = room
            new_b["room_no"] = room
            new_b["is_primary"] = (idx == 0)
            assigned.append(new_b)
    
    return assigned, []


def safe_float(value, default=0.0):
    """Safely convert to float."""
    try:
        return float(value) if value not in [None, "", " "] else default
    except:
        return default


def compute_daily_metrics(bookings: List[Dict], prop: str, day: date) -> Dict:
    """
    FIXED: Calculates metrics matching Daily Status exactly.
    - Rooms sold = count of occupied inventory slots on that day
    - Financials only counted on check-in day for primary bookings
    """
    daily = filter_bookings_for_day(bookings, day)
    assigned, _ = assign_inventory_numbers(daily, prop)

    # Rooms sold = count of assigned inventory entries
    rooms_sold = len(assigned)

    # Financial metrics: ONLY for bookings checking in today (primary only)
    check_in_primaries = [
        b for b in assigned
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
    Columns: Date | <Property1> | <Property2> … | Total
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
            row[p] = val
            day_sum += val
            prop_totals[p] += val
        row["Total"] = day_sum
        grand_total += day_sum
        rows.append(row)

    # Month total row
    total_row = {"Date": "Total"}
    for p in props:
        total_row[p] = prop_totals[p]
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
