# summary_report.py - FIXED: Room charges only on check-in day (no splitting)
# Matches Daily Status exactly - financials only counted once on check-in for primary booking

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
    "Le Park Resort": "LePR",
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
    Uses EXACT same query logic as Daily Status (inventory.py).
    Fetches bookings that overlap with the date range.
    """
    normalized_prop = normalize_property_name(prop)
    query_props = [normalized_prop] + reverse_mapping.get(normalized_prop, [])
    
    try:
        # Use .lte("check_in") and .gte("check_out") like Daily Status
        direct = (
            supabase.table("reservations")
            .select("*")
            .in_("property_name", query_props)
            .lte("check_in", str(end))
            .gte("check_out", str(start))
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
            .lte("check_in", str(end))
            .gte("check_out", str(start))
            .in_("booking_status", ["Confirmed", "Completed"])
            .in_("payment_status", ["Partially Paid", "Fully Paid"])
            .execute()
            .data
            or []
        )
        
        # Normalize all bookings - FIX: Don't filter by normalized prop here
        all_bookings = []
        for booking in direct:
            booking["property_name"] = normalize_property_name(booking.get("property_name", ""))
            booking["type"] = "direct"
            all_bookings.append(booking)
        
        for booking in online:
            booking["property"] = normalize_property_name(booking.get("property", ""))
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
    Validates rooms against property inventory and detects overbookings.
    Splits comma-separated room_no and creates separate entries per room.
    Returns (assigned, overbookings).
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
    already_assigned = set()
    
    for b in daily:
        raw_room = str(b.get("room_no") or "").strip()
        if not raw_room:
            over.append(b)
            continue
        
        # Split comma-separated rooms
        requested = [r.strip() for r in raw_room.split(",") if r.strip()]
        assigned_rooms = []
        is_over = False
        
        # Validate each requested room
        for r in requested:
            key = r.lower()
            if key not in inv_lookup:
                is_over = True
                break
            
            room = inv_lookup[key]
            if room in already_assigned:
                is_over = True
                break
            
            assigned_rooms.append(room)
        
        if is_over or not assigned_rooms:
            over.append(b)
            continue
        
        # Mark rooms as assigned
        for room in assigned_rooms:
            already_assigned.add(room)
        
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
    FIXED: Matches Daily Status exactly.
    - rooms_sold: count daily (all active bookings)
    - room_charges, gst, total, commission, receivable: ONLY on check-in day
    - receivable_per_night: daily prorated value (uses per_night from assigned bookings)
    """
    daily = filter_bookings_for_day(bookings, day)
    
    # DEBUG: Check if we have bookings
    if not daily:
        return {
            "rooms_sold": 0,
            "room_charges": 0.0,
            "gst": 0.0,
            "total": 0.0,
            "commission": 0.0,
            "tax_deduction": 0.0,
            "receivable": 0.0,
            "receivable_per_night": 0.0,
        }
    
    assigned, over = assign_inventory_numbers(daily, prop)

    # Rooms sold = count of UNIQUE assigned rooms (daily count)
    unique_rooms = set()
    for b in assigned:
        room = b.get("assigned_room")
        if room:
            unique_rooms.add(room)
    
    rooms_sold = len(unique_rooms)

    # Financial metrics (check-in day only): room_charges, gst, total, commission, receivable
    check_in_primaries = [
        b for b in assigned
        if b.get("is_primary", True) and date.fromisoformat(b["check_in"]) == day
    ]

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

    # receivable_per_night: Daily prorated value
    # Calculate per_night for each assigned booking (multi-day/multi-room prorated)
    daily_per_night_sum = 0.0
    for b in assigned:
        if b.get("is_primary", True):  # Only count primary to avoid duplication
            # Get original booking values
            is_online = b.get("type") == "online"
            if is_online:
                booking_total = safe_float(b.get("booking_amount"))
                booking_gst = safe_float(b.get("ota_tax"))
                booking_commission = safe_float(b.get("ota_commission"))
            else:
                booking_total = safe_float(b.get("total_tariff"))
                booking_gst = 0.0
                booking_commission = 0.0
            
            booking_receivable = booking_total - booking_gst - booking_commission
            
            # Prorate by days and rooms
            days = max(b.get("days", 1), 1)
            raw_room = str(b.get("room_no") or "").strip()
            num_rooms = len([r.strip() for r in raw_room.split(",") if r.strip()]) if raw_room else 1
            total_nights = days * num_rooms
            
            per_night = booking_receivable / total_nights if total_nights > 0 else 0.0
            daily_per_night_sum += per_night

    return {
        "rooms_sold": rooms_sold,                # Daily count
        "room_charges": room_charges,            # Only on check-in
        "gst": gst,                              # Only on check-in
        "total": total,                          # Only on check-in
        "commission": commission,                # Only on check-in
        "tax_deduction": tax_deduction,          # Calculated from receivable
        "receivable": receivable,                # Only on check-in
        "receivable_per_night": daily_per_night_sum,  # Daily prorated
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
        # Format date with day name for weekend highlighting
        day_name = d.strftime("%a")  # Mon, Tue, Wed, etc.
        date_str = d.strftime("%Y-%m-%d")
        row = {"Date": date_str, "_date_obj": d, "_day_name": day_name}  # Store for styling
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
    total_row = {"Date": "Total", "_date_obj": None, "_day_name": ""}
    for p in props:
        short_name = get_short_name(p)
        total_row[short_name] = prop_totals[p]
    total_row["Total"] = grand_total
    rows.append(total_row)

    df = pd.DataFrame(rows)
    # Remove helper columns before returning
    return df.drop(columns=["_date_obj", "_day_name"], errors="ignore")


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

    # Helper function to style dataframe
    def style_dataframe(df, metric):
        """Apply styling: highlight 0 as dark red, weekends as green"""
        # Create a copy for processing
        df_display = df.copy()
        
        # Store date info before formatting
        date_weekend_map = {}
        for idx, row in df_display.iterrows():
            date_str = row["Date"]
            if date_str != "Total":
                try:
                    d = date.fromisoformat(date_str)
                    # Check if Saturday (5) or Sunday (6)
                    date_weekend_map[idx] = d.weekday() in [5, 6]
                except:
                    date_weekend_map[idx] = False
            else:
                date_weekend_map[idx] = False
        
        # Format monetary columns
        if metric != "rooms_sold":
            monetary_cols = [col for col in df_display.columns if col != "Date"]
            for col in monetary_cols:
                df_display[col] = df_display[col].apply(
                    lambda x: f"{x:,.0f}" if isinstance(x, (int, float)) else x
                )
        
        # Apply styling
        def highlight_cells(row):
            styles = [''] * len(row)
            row_idx = row.name
            
            # Apply weekend highlighting to Date column
            if date_weekend_map.get(row_idx, False):
                styles[0] = 'background-color: #90EE90'  # Light green for weekends
            
            # Apply zero highlighting to value columns
            for idx, (col, val) in enumerate(row.items()):
                if col != "Date":
                    # Check if value is 0 (handle both numeric and formatted string)
                    is_zero = False
                    if isinstance(val, (int, float)) and val == 0:
                        is_zero = True
                    elif isinstance(val, str) and val.replace(',', '').replace('.', '').strip('0') == '':
                        is_zero = True
                    
                    if is_zero:
                        styles[idx] = 'background-color: #8B0000; color: white'  # Dark red for zeros
            
            return styles
        
        return df_display.style.apply(highlight_cells, axis=1)

    # Render each section
    for key, (title, metric) in report_defs.items():
        st.subheader(title)
        df = build_report(properties, month_dates, bookings, metric)
        
        # Apply styling
        styled_df = style_dataframe(df, metric)
        
        # Display styled table
        table_height = 38 + (len(df) * 35) + 10
        st.dataframe(
            styled_df,
            use_container_width=False,
            height=table_height
        )
        st.markdown("---")


# -------------------------- Run --------------------------
if __name__ == "__main__":
    show_summary_report()
