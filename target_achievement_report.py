# target_achievement_report.py - Target vs Achievement Analysis (Updated with Corrected Column Names)

import streamlit as st
from datetime import date
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

reverse_mapping = {c: [] for c in set(PROPERTY_MAPPING.values())}
for v, c in PROPERTY_MAPPING.items():
    reverse_mapping[c].append(v)

def normalize_property_name(prop_name: str) -> str:
    return PROPERTY_MAPPING.get(prop_name, prop_name) if prop_name else prop_name

# -------------------------- December 2025 Targets --------------------------
DECEMBER_2025_TARGETS = {
    "La Millionaire Resort": 2200000,
    "Le Poshe Beach view": 800000,
    "Le Park Resort": 800000,
    "La Tamara Luxury": 1848000,
    "Le Poshe Luxury": 1144000,
    "Le Poshe Suite": 475000,
    "Eden Beach Resort": 438000,
    "La Antilia Luxury": 1075000,
    "La Coromandel Luxury": 800000,
    "La Tamara Suite": 640000,
    "Villa Shakti": 652000,
    "La Paradise Luxury": 467000,
    "La Villa Heritage": 467000,
    "La Paradise Residency": 534000,
    "Le Pondy Beachside": 245000,
    "Le Royce Villa": 190000,
}

# -------------------------- Property Inventory --------------------------
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
    "La Antilia Luxury": {"all": ["101","201","202","203","204","301","302","303","304","401","Day Use 1","Day Use 2","No Show"]},
    "La Tamara Suite": {"all": ["101","102","103","104","201","202","203","204","205","206","Day Use 1","Day Use 2","No Show"]},
    "Le Park Resort": {"all": ["111","222","333","444","555","666","Day Use 1","Day Use 2","No Show"]},
    "Villa Shakti": {"all": ["101","102","201","201A","202","203","301","301A","302","303","401","Day Use 1","Day Use 2","No Show"]},
    "Eden Beach Resort": {"all": ["101","102","103","201","202","Day Use 1","Day Use 2","No Show"]},
    "Le Terra": {"all": ["101","102","103","104","105","106","107","Day Use 1","Day Use 2","No Show"]},
    "La Coromandel Luxury": {"all": ["101","102","103","201","202","203","204","205","206","301","Day Use 1","Day Use 2","No Show"]},
    "Happymates Forest Retreat": {"all": ["101","102","Day Use 1","Day Use 2","No Show"]}
}

def get_total_rooms(prop: str) -> int:
    """Get total bookable rooms (excluding Day Use and No Show)"""
    inv = PROPERTY_INVENTORY.get(prop, {"all": []})["all"]
    return len([r for r in inv if not r.startswith(("Day Use", "No Show"))])

# -------------------------- Helpers --------------------------
def load_properties() -> List[str]:
    try:
        direct = supabase.table("reservations").select("property_name").execute().data or []
        online = supabase.table("online_reservations").select("property").execute().data or []
        props = {normalize_property_name(r.get("property_name") or r.get("property"))
                 for r in direct + online if r.get("property_name") or r.get("property")}
        return sorted(props)
    except Exception as e:
        st.error(f"Error loading properties: {e}")
        return []

def load_combined_bookings(prop: str, start: date, end: date) -> List[Dict]:
    normalized_prop = normalize_property_name(prop)
    query_props = [normalized_prop] + reverse_mapping.get(normalized_prop, [])
    try:
        direct = (supabase.table("reservations").select("*")
                  .in_("property_name", query_props)
                  .lte("check_in", str(end))
                  .gte("check_out", str(start))
                  .in_("plan_status", ["Confirmed", "Completed"])
                  .in_("payment_status", ["Partially Paid", "Fully Paid"])
                  .execute().data or [])

        online = (supabase.table("online_reservations").select("*")
                  .in_("property", query_props)
                  .lte("check_in", str(end))
                  .gte("check_out", str(start))
                  .in_("booking_status", ["Confirmed", "Completed"])
                  .in_("payment_status", ["Partially Paid", "Fully Paid"])
                  .execute().data or [])

        all_bookings = []
        for b in direct:
            if normalize_property_name(b.get("property_name")) == prop:
                b["property_name"] = prop
                b["type"] = "direct"
                all_bookings.append(b)
        for b in online:
            if normalize_property_name(b.get("property")) == prop:
                b["property"] = prop
                b["type"] = "online"
                all_bookings.append(b)
        return all_bookings
    except Exception as e:
        st.error(f"Error loading bookings for {prop}: {e}")
        return []

def filter_bookings_for_day(bookings: List[Dict], target: date) -> List[Dict]:
    return [
        b for b in bookings
        if date.fromisoformat(b["check_in"]) <= target < date.fromisoformat(b["check_out"])
    ]

def assign_inventory_numbers(daily: List[Dict], prop: str):
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
        requested = [r.strip() for r in raw_room.split(",") if r.strip()]
        assigned_rooms = []
        is_over = False
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
        for room in assigned_rooms:
            already_assigned.add(room)
        for idx, room in enumerate(assigned_rooms):
            new_b = b.copy()
            new_b["assigned_room"] = room
            new_b["room_no"] = room
            new_b["is_primary"] = (idx == 0)
            assigned.append(new_b)
    return assigned, over

def safe_float(value, default=0.0):
    try:
        return float(value) if value not in [None, "", " "] else default
    except:
        return default

def compute_daily_metrics(bookings: List[Dict], prop: str, day: date) -> Dict:
    daily = filter_bookings_for_day(bookings, day)
    assigned, _ = assign_inventory_numbers(daily, prop)
    rooms_sold = len(set(b.get("assigned_room") for b in assigned if b.get("assigned_room")))
    check_in_primaries = [b for b in assigned if b.get("is_primary", True) and date.fromisoformat(b["check_in"]) == day]

    room_charges = gst = commission = 0.0
    for b in check_in_primaries:
        if b.get("type") == "online":
            total_amount = safe_float(b.get("booking_amount"))
            gst += safe_float(b.get("ota_tax"))
            commission += safe_float(b.get("ota_commission"))
            room_charges += total_amount - safe_float(b.get("ota_tax"))
        else:
            room_charges += safe_float(b.get("total_tariff"))

    total = room_charges + gst
    receivable = total - commission

    daily_per_night_sum = 0.0
    for b in assigned:
        if b.get("is_primary", True):
            is_online = b.get("type") == "online"
            if is_online:
                booking_total = safe_float(b.get("booking_amount"))
                booking_gst = safe_float(b.get("ota_tax"))
                booking_commission = safe_float(b.get("ota_commission"))
            else:
                booking_total = safe_float(b.get("total_tariff"))
                booking_gst = booking_commission = 0.0
            booking_receivable = booking_total - booking_gst - booking_commission
            days = max(b.get("days", 1), 1)
            raw_room = str(b.get("room_no") or "").strip()
            num_rooms = len([r.strip() for r in raw_room.split(",") if r.strip()]) if raw_room else 1
            total_nights = days * num_rooms
            per_night = booking_receivable / total_nights if total_nights > 0 else 0.0
            daily_per_night_sum += per_night

    return {
        "rooms_sold": rooms_sold,
        "receivable": receivable,
        "receivable_per_night": daily_per_night_sum,
    }

def build_target_achievement_report(props: List[str], dates: List[date], bookings: Dict[str, List[Dict]], current_date: date) -> pd.DataFrame:
    rows = []
    total_target = total_achieved = total_projected = total_balance = 0.0
    total_room_nights = total_rooms_sold = total_balance_rooms = total_rooms_all = 0

    past_dates = [d for d in dates if d <= current_date]
    future_dates = [d for d in dates if d > current_date]
    balance_days = len(future_dates)

    for prop in props:
        target = DECEMBER_2025_TARGETS.get(prop, 0)
        total_rooms = get_total_rooms(prop)
        total_room_nights_available = total_rooms * len(dates)
        balance_rooms = total_rooms * balance_days

        achieved = projected_receivable = rooms_sold_total = per_night_total = 0.0

        for d in dates:
            metrics = compute_daily_metrics(bookings.get(prop, []), prop, d)
            if d <= current_date:
                achieved += metrics["receivable"]
            projected_receivable += metrics["receivable"]
            rooms_sold_total += metrics["rooms_sold"]
            per_night_total += metrics["receivable_per_night"]

        balance = target - achieved
        achieved_pct = (projected_receivable / target * 100) if target > 0 else 0
        occupancy = (rooms_sold_total / total_room_nights_available * 100) if total_room_nights_available > 0 else 0
        arr = projected_receivable / rooms_sold_total if rooms_sold_total > 0 else 0
        per_day_needed = max(balance, 0) / balance_days if balance_days > 0 else 0
        arr_focused = per_day_needed / total_rooms if total_rooms > 0 else 0

        rows.append({
            "Property Name": prop,
            "Target": target,
            "Achieved": achieved,
            "Projected": projected_receivable,
            "Balance": balance,
            "Achieved %": achieved_pct,
            "Total Rooms": total_room_nights_available,
            "Rooms Sold": rooms_sold_total,
            "Occupancy %": occupancy,
            "Receivable": projected_receivable,
            "ARR": arr,
            "Balance Days": balance_days,
            "Balance Rooms": balance_rooms,
            "Per Day Needed": per_day_needed,
            "ARR Focused": arr_focused
        })

        # Accumulate totals
        total_target += target
        total_achieved += achieved
        total_projected += projected_receivable
        total_balance += balance
        total_room_nights += total_room_nights_available
        total_rooms_sold += rooms_sold_total
        total_balance_rooms += balance_rooms
        total_rooms_all += total_rooms

    # TOTAL Row
    total_pct = (total_projected / total_target * 100) if total_target > 0 else 0
    total_occupancy = (total_rooms_sold / total_room_nights * 100) if total_room_nights > 0 else 0
    total_arr = total_projected / total_rooms_sold if total_rooms_sold > 0 else 0
    total_per_day = max(total_balance, 0) / balance_days if balance_days > 0 else 0
    total_arr_focused = total_per_day / total_rooms_all if total_rooms_all > 0 else 0

    rows.append({
        "Property Name": "TOTAL",
        "Target": total_target,
        "Achieved": total_achieved,
        "Projected": total_projected,
        "Balance": total_balance,
        "Achieved %": total_pct,
        "Total Rooms": total_room_nights,
        "Rooms Sold": total_rooms_sold,
        "Occupancy %": total_occupancy,
        "Receivable": total_projected,
        "ARR": total_arr,
        "Balance Days": balance_days,
        "Balance Rooms": total_balance_rooms,
        "Per Day Needed": total_per_day,
        "ARR Focused": total_arr_focused
    })

    df = pd.DataFrame(rows)
    df.insert(0, 'S.No', range(1, len(df) + 1))
    return df

def style_dataframe(df):
    # Function to color balance: green for non-negative, red for negative
    def color_balance(val):
        if isinstance(val, (int, float)):
            color = 'green' if val >= 0 else 'red'
            return f'color: {color}; font-weight: bold'
        return ''
    
    # Function for % columns: green if >=70%, orange if >=50%, red if <50%
    def color_percentage(val):
        if isinstance(val, (int, float)):
            if val >= 70:
                color = 'green'
            elif val >= 50:
                color = 'orange'
            else:
                color = 'red'
            return f'color: {color}; font-weight: bold'
        return ''
    
    # Apply styles
    styled = df.style \
        .applymap(color_balance, subset=['Balance']) \
        .applymap(color_percentage, subset=['Achieved %', 'Occupancy %']) \
        .set_properties(**{'text-align': 'center'}) \
        .set_table_styles([{'selector': 'th', 'props': [('background-color', '#4CAF50'), ('color', 'white'), ('font-weight', 'bold')]}]) \
        .format({
            'Target': '{:,.0f}',
            'Achieved': '{:,.0f}',
            'Projected': '{:,.0f}',
            'Balance': '{:,.0f}',
            'Achieved %': '{:.1f}%',
            'Total Rooms': '{:,.0f}',
            'Rooms Sold': '{:,.0f}',
            'Occupancy %': '{:.1f}%',
            'Receivable': '{:,.0f}',
            'ARR': '{:,.0f}',
            'Balance Days': '{:,.0f}',
            'Balance Rooms': '{:,.0f}',
            'Per Day Needed': '{:,.0f}',
            'ARR Focused': '{:,.0f}'
        })
    
    return styled

# -------------------------- UI --------------------------
def show_target_achievement_report():
    st.set_page_config(page_title="Target vs Achievement Report - December 2025", layout="wide")
    st.title("🎯 Target vs Achievement Report - December 2025")

    today = date.today()
    year = st.selectbox("Year", options=list(range(today.year-5, today.year+6)), index=5)
    month = st.selectbox("Month", options=list(range(1,13)), index=11)  # Default to December (index 11)

    if year != 2025 or month != 12:
        st.warning("Targets and balance calculations are optimized for December 2025.")
        current_date = date(year, month, 1)  # Full month if not Dec
    else:
        current_date = date(2025, 12, 6)

    properties = load_properties()
    if not properties:
        st.info("No properties found in database.")
        return

    # Filter only properties with targets
    properties_with_targets = [p for p in properties if p in DECEMBER_2025_TARGETS]

    _, days_in_month = calendar.monthrange(year, month)
    month_dates = [date(year, month, d) for d in range(1, days_in_month + 1)]

    with st.spinner("Loading booking data and calculating achievements..."):
        bookings = {p: load_combined_bookings(p, month_dates[0], month_dates[-1]) for p in properties_with_targets}

    st.subheader(f"Target vs Achievement Analysis - {calendar.month_name[month]} {year}")
    
    df = build_target_achievement_report(properties_with_targets, month_dates, bookings, current_date)
    
    # Style and display the dataframe
    styled_df = style_dataframe(df)
    st.dataframe(styled_df, use_container_width=True)
    
    # Summary metrics
    st.markdown("---")
    total_row = df[df["Property Name"] == "TOTAL"].iloc[0]
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Target", f"₹{total_row['Target']:,.0f}")
    with col2:
        st.metric("Achieved", f"₹{total_row['Achieved']:,.0f}", 
                 delta=f"₹{total_row['Balance']:,.0f}")
    with col3:
        st.metric("Achieved %", f"{total_row['Achieved %']:.1f}%")
    with col4:
        st.metric("Overall Occupancy", f"{total_row['Occupancy %']:.1f}%")
    with col5:
        st.metric("Daily Needed (Remaining)", f"₹{total_row['Per Day Needed']:,.0f}")
    
    # Download button
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download Report as CSV",
        data=csv,
        file_name=f"target_achievement_{calendar.month_name[month]}_{year}.csv",
        mime="text/csv"
    )

if __name__ == "__main__":
    show_target_achievement_report()
