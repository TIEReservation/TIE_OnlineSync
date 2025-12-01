# summary_report.py
# ------------------------------------------------------------
# TIE Hotels & Resort – 8-Section Monthly Summary Report
# Re-uses the exact same booking logic as Daily Status → 100% data match
# ------------------------------------------------------------

import streamlit as st
from datetime import date, timedelta
import calendar
import pandas as pd
from supabase import create_client, Client
from typing import List, Dict
import os

# -------------------------- Supabase --------------------------
try:
    # Try secrets first (for Streamlit Cloud)
    supabase: Client = create_client(
        st.secrets["supabase"]["url"],
        st.secrets["supabase"]["key"]
    )
except (KeyError, FileNotFoundError):
    # Fallback to environment variables (for local development)
    try:
        supabase: Client = create_client(
            os.environ["SUPABASE_URL"],
            os.environ["SUPABASE_KEY"]
        )
    except KeyError as e:
        st.error(f"Missing Supabase configuration: {e}. Please check secrets or environment variables.")
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

def normalize_property_name(prop_name: str) -> str:
    """Normalize property name using the mapping."""
    if not prop_name:
        return prop_name
    return PROPERTY_MAPPING.get(prop_name, prop_name)

# -------------------------- Helpers --------------------------
def load_properties() -> List[str]:
    """Return a sorted list of all unique property names (direct + online)."""
    try:
        direct = supabase.table("reservations").select("property_name").execute().data or []
        online = supabase.table("online_reservations").select("property").execute().data or []
        
        # Normalize all property names
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
    """Same query used in Daily Status – fetches both direct & online bookings."""
    try:
        # Direct reservations
        direct = (
            supabase.table("reservations")
            .select("*")
            .gte("check_in", str(start))
            .lt("check_out", str(end + timedelta(days=1)))
            .execute()
            .data
            or []
        )
        
        # Online reservations
        online = (
            supabase.table("online_reservations")
            .select("*")
            .gte("check_in", str(start))
            .lt("check_out", str(end + timedelta(days=1)))
            .execute()
            .data
            or []
        )
        
        # Normalize property names and filter by property
        all_bookings = []
        for booking in direct:
            normalized = normalize_property_name(booking.get("property_name"))
            if normalized == prop:
                booking["property_name"] = normalized
                all_bookings.append(booking)
        
        for booking in online:
            normalized = normalize_property_name(booking.get("property"))
            if normalized == prop:
                booking["property"] = normalized
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
    UPDATED: Now properly splits multi-room bookings into separate inventory entries.
    This matches the logic in inventory.py for accurate room counting.
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
        
        # Split comma-separated rooms (e.g., "101,102,103")
        rooms = [r.strip() for r in raw_room.split(",") if r.strip()]
        if not rooms:
            rooms = ["1"]
        
        # Calculate per-night value for splitting financials
        days = max(b.get("days", 1), 1)
        num_rooms = len(rooms)
        total_nights = days * num_rooms
        
        receivable = b.get("receivable", b.get("booking_amount", 0.0))
        commission = b.get("commission", b.get("ota_commission", 0.0))
        gst = b.get("gst", 0.0)
        room_charges = b.get("room_charges", b.get("booking_amount", 0.0)) - gst
        
        per_night_receivable = receivable / total_nights if total_nights > 0 else 0.0
        per_night_charges = room_charges / total_nights if total_nights > 0 else 0.0
        per_night_gst = gst / total_nights if total_nights > 0 else 0.0
        per_night_commission = commission / total_nights if total_nights > 0 else 0.0
        
        # Split pax across rooms
        base_pax = b.get("total_pax", 0) // num_rooms if num_rooms else 0
        rem_pax = b.get("total_pax", 0) % num_rooms if num_rooms else 0
        
        # Create separate entry for each room
        for idx, room in enumerate(rooms):
            new_b = b.copy()
            new_b["assigned_room"] = room
            new_b["room_no"] = room
            new_b["total_pax"] = base_pax + (1 if idx < rem_pax else 0)
            new_b["per_night_receivable"] = per_night_receivable
            new_b["per_night_charges"] = per_night_charges
            new_b["per_night_gst"] = per_night_gst
            new_b["per_night_commission"] = per_night_commission
            new_b["is_primary"] = (idx == 0)  # Only first room gets full financials on check-in
            assigned.append(new_b)
    
    return assigned, []  # No overbooking handling for reports


def compute_daily_metrics(bookings: List[Dict], prop: str, day: date) -> Dict:
    """
    FIXED: Now counts rooms correctly by using the split assignments.
    Mirrors Daily Status calculations exactly.
    """
    daily = filter_bookings_for_day(bookings, day)
    assigned, _ = assign_inventory_numbers(daily, prop)

    # ---------- Rooms sold = count of assigned inventory entries ----------
    rooms_sold = len(assigned)  # FIXED: Now counts actual room entries, not inventory_no length

    # ---------- Primary-night charges (only on check-in day) ----------
    check_in_bookings = [
        b for b in assigned
        if b.get("is_primary", True) and date.fromisoformat(b["check_in"]) == day
    ]

    room_charges = sum(b.get("room_charges", b.get("booking_amount", 0.0)) for b in check_in_bookings)
    gst = sum(b.get("gst", 0.0) for b in check_in_bookings)
    total = room_charges + gst
    commission = sum(b.get("commission", b.get("ota_commission", 0.0)) for b in check_in_bookings)
    
    receivable = total - commission
    tax_deduction = receivable * 0.003  # 0.3%
    
    # Per night calculation using ALL assigned rooms (not just check-ins)
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

    # ---- month total row ----
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

    # ----- month calendar -----
    _, days_in_month = calendar.monthrange(year, month)
    month_dates = [date(year, month, d) for d in range(1, days_in_month + 1)]
    start_date = month_dates[0]
    end_date = month_dates[-1]

    # ----- load all bookings once -----
    with st.spinner("Loading booking data..."):
        bookings = {
            p: load_combined_bookings(p, start_date, end_date) for p in properties
        }

    # ----- 8 report definitions -----
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

    # ----- render each section -----
    for key, (title, metric) in report_defs.items():
        st.subheader(title)
        df = build_report(properties, month_dates, bookings, metric)

        # pretty-print monetary columns
        if metric != "rooms_sold":
            monetary_cols = df.columns[1:]  # everything except Date
            df[monetary_cols] = df[monetary_cols].applymap(
                lambda x: f"{x:,.2f}" if isinstance(x, (int, float)) else x
            )

        st.dataframe(df, use_container_width=True)
        
        # Add some spacing between reports
        st.markdown("---")


# -------------------------- Run --------------------------
if __name__ == "__main__":
    show_summary_report()
