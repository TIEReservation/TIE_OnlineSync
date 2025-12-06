# target_achievement_report.py - FINAL FIXED (NO ERRORS, NO SCROLLBARS)
import streamlit as st
from datetime import date
import calendar
import pandas as pd
from supabase import create_client, Client
from typing import List, Dict
import os

# =========================== ULTRA-COMPACT LAYOUT - NO SCROLLBARS ===========================
st.set_page_config(layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    /* Compact app */
    .main > div {padding: 1rem 0.5rem !important;}
    .block-container {padding-top: 1rem !important;}
    
    /* No scrollbars, fixed height */
    .dataframe-container {
        overflow: hidden !important;
        border-radius: 8px;
        border: 1px solid #ddd;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    /* Tiny rows & text */
    th, td {
        padding: 3px 6px !important;
        font-size: 11px !important;
        line-height: 1.2 !important;
        text-align: center !important;
        border: 1px solid #eee !important;
    }
    
    th {
        background-color: #1e6b4f !important;
        color: white !important;
        font-weight: bold !important;
        font-size: 11.5px !important;
        position: sticky;
        top: 0;
        z-index: 10;
    }
    
    /* Property wrap */
    td:nth-child(2), th:nth-child(2) {
        max-width: 120px;
        white-space: normal !important;
        word-wrap: break-word;
    }
    
    /* Hide sidebar */
    section[data-testid="stSidebar"] {display: none !important;}
</style>
""", unsafe_allow_html=True)

# -------------------------- Supabase --------------------------
try:
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except:
    try:
        supabase: Client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
    except Exception as e:
        st.error(f"Supabase error: {e}")
        st.stop()

# -------------------------- Property Mapping (BULLETPROOF FIXED - NO 'SET' ERRORS) --------------------------
PROPERTY_MAPPING = {
    "La Millionaire Luxury Resort": "La Millionaire Resort",
    "Le Poshe Beach View": "Le Poshe Beach view",
    "Le Poshe Beach view": "Le Poshe Beach view",
    "Le Poshe Beach VIEW": "Le Poshe Beach view",
    "Le Poshe Beachview": "Le Poshe Beach view",
    "Millionaire": "La Millionaire Resort",
    "Le Pondy Beach Side": "Le Pondy Beachside",
    "Le Teera": "Le Terra",
    "La Millionaire Resort": "La Millionaire Resort",
    "Le Poshe Beach view": "Le Poshe Beach view",
    "Le Pondy Beachside": "Le Pondy Beachside",
    "Le Terra": "Le Terra"
}

def normalize_property_name(p: str) -> str:
    if isinstance(p, str) and p:
        return PROPERTY_MAPPING.get(p.strip(), p.strip())
    return ""

# Build reverse_mapping as DICT (safe from 'set' errors)
reverse_mapping = {}
if isinstance(PROPERTY_MAPPING, dict):
    for raw, canon in PROPERTY_MAPPING.items():
        if isinstance(canon, str):
            reverse_mapping.setdefault(canon, []).append(raw)

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
    if not isinstance(prop, str):
        return 0
    inv = PROPERTY_INVENTORY.get(prop, {"all": []})
    if "all" not in inv:
        return 0
    return len([r for r in inv["all"] if isinstance(r, str) and not r.startswith(("Day Use", "No Show"))])

# -------------------------- Helpers (SAFE FROM 'SET' ERRORS) --------------------------
def load_properties() -> List[str]:
    try:
        direct = supabase.table("reservations").select("property_name").execute().data or []
        online = supabase.table("online_reservations").select("property").execute().data or []
        props_set = set()
        for r in direct + online:
            name = r.get("property_name") or r.get("property")
            if isinstance(name, str):
                norm = normalize_property_name(name)
                if norm:
                    props_set.add(norm)
        props = sorted([p for p in props_set if p in DECEMBER_2025_TARGETS])
        return props
    except Exception as e:
        st.error(f"Error loading properties: {e}")
        return []

def load_combined_bookings(prop: str, start: date, end: date) -> List[Dict]:
    if not isinstance(prop, str):
        return []
    norm = normalize_property_name(prop)
    if not norm:
        return []
    # Safe dict get
    query_props = reverse_mapping.get(norm, [norm]) if isinstance(reverse_mapping, dict) else [norm]
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
        all_bookings = direct + online
        filtered = []
        for b in all_bookings:
            name = b.get("property_name") or b.get("property")
            if isinstance(name, str) and normalize_property_name(name) == norm:
                b["type"] = "direct" if "property_name" in b else "online"
                filtered.append(b)
        return filtered
    except Exception as e:
        st.error(f"Error loading bookings for {prop}: {e}")
        return []

def filter_bookings_for_day(bookings: List[Dict], target: date) -> List[Dict]:
    if not isinstance(target, date):
        return []
    return [
        b for b in bookings
        if isinstance(b, dict) and "check_in" in b and "check_out" in b
        and isinstance(b["check_in"], str) and isinstance(b["check_out"], str)
        and date.fromisoformat(b["check_in"]) <= target < date.fromisoformat(b["check_out"])
    ]

def assign_inventory_numbers(daily: List[Dict], prop: str):
    if not isinstance(prop, str):
        return [], []
    inv = PROPERTY_INVENTORY.get(prop, {"all": []})
    if "all" not in inv:
        return [], daily  # All overbooked
    inv_list = inv["all"]
    inv_lookup = {i.strip().lower(): i for i in inv_list if isinstance(i, str)}
    assigned = []
    over = []
    already_assigned = set()
    
    for b in daily:
        if not isinstance(b, dict):
            continue
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
    if value is None or value == "" or value == " ":
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def compute_daily_metrics(bookings: List[Dict], prop: str, day: date) -> Dict:
    daily = filter_bookings_for_day(bookings, day)
    assigned, _ = assign_inventory_numbers(daily, prop)
    rooms_sold = len(set(b.get("assigned_room") for b in assigned if b.get("assigned_room")))
    check_in_primaries = [
        b for b in assigned
        if b.get("is_primary", True) and isinstance(b.get("check_in"), str)
        and date.fromisoformat(b["check_in"]) == day
    ]

    receivable = 0.0
    for b in check_in_primaries:
        if b.get("type") == "online":
            total_amount = safe_float(b.get("booking_amount"))
            gst = safe_float(b.get("ota_tax"))
            commission = safe_float(b.get("ota_commission"))
            receivable += total_amount - gst - commission
        else:
            receivable += safe_float(b.get("total_tariff"))

    return {
        "rooms_sold": rooms_sold,
        "receivable": receivable,
    }

# -------------------------- Report Builder (with Balance) --------------------------
def build_target_achievement_report(props: List[str], dates: List[date], bookings: Dict[str, List[Dict]], current_date: date) -> pd.DataFrame:
    rows = []
    total_target = 0.0
    total_achieved_so_far = 0.0
    total_available_room_nights = 0
    total_rooms_sold = 0
    total_receivable = 0.0
    total_rooms_all = 0
    total_required_remaining = 0.0
    
    past_dates = [d for d in dates if d <= current_date]
    future_dates = [d for d in dates if d > current_date]
    balance_days = len(future_dates)
    
    for prop in props:
        target = DECEMBER_2025_TARGETS.get(prop, 0)
        
        # Achieved so far
        achieved_so_far = 0.0
        rooms_sold_so_far = 0
        receivable_so_far = 0.0
        
        for d in past_dates:
            metrics = compute_daily_metrics(bookings.get(prop, []), prop, d)
            achieved_so_far += metrics.get("receivable", 0.0)
            rooms_sold_so_far += metrics.get("rooms_sold", 0)
            receivable_so_far += metrics.get("receivable", 0.0)
        
        # Full month
        achieved = 0.0
        rooms_sold = 0
        receivable = 0.0
        
        for d in dates:
            metrics = compute_daily_metrics(bookings.get(prop, []), prop, d)
            achieved += metrics.get("receivable", 0.0)
            rooms_sold += metrics.get("rooms_sold", 0)
            receivable += metrics.get("receivable", 0.0)
        
        difference_so_far = achieved_so_far - target
        required_remaining = max(target - achieved_so_far, 0)
        per_day_needed = required_remaining / balance_days if balance_days > 0 else 0.0
        
        total_rooms = get_total_rooms(prop)
        total_available = total_rooms * len(dates)
        occupancy_pct = (rooms_sold / total_available * 100) if total_available > 0 else 0.0
        
        arr = receivable / rooms_sold if rooms_sold > 0 else 0.0
        arr_focused = per_day_needed / total_rooms if total_rooms > 0 else 0.0
        
        rows.append({
            "Property Name": prop,
            "Target": target,
            "Achieved So Far": achieved_so_far,
            "Balance": required_remaining,  # Renamed from Projected
            "Difference So Far": difference_so_far,
            "Target Achieved %": (achieved_so_far / target * 100) if target > 0 else 0.0,
            "Available Room Nights": total_available,
            "Rooms Sold": rooms_sold,
            "Occupancy %": occupancy_pct,
            "Receivable": receivable,
            "ARR": arr,
            "Balance Days": balance_days,
            "Per Day Needed": per_day_needed,
            "ARR Focused": arr_focused
        })
        
        total_target += target
        total_achieved_so_far += achieved_so_far
        total_available_room_nights += total_available
        total_rooms_sold += rooms_sold
        total_receivable += receivable
        total_rooms_all += total_rooms
        total_required_remaining += required_remaining
    
    # Total row
    total_diff_so_far = total_achieved_so_far - total_target
    total_target_pct = (total_achieved_so_far / total_target * 100) if total_target > 0 else 0.0
    total_occupancy = (total_rooms_sold / total_available_room_nights * 100) if total_available_room_nights > 0 else 0.0
    total_arr = total_receivable / total_rooms_sold if total_rooms_sold > 0 else 0.0
    total_per_day_needed = total_required_remaining / balance_days if balance_days > 0 else 0.0
    total_arr_focused = total_per_day_needed / total_rooms_all if total_rooms_all > 0 else 0.0
    
    rows.append({
        "Property Name": "TOTAL",
        "Target": total_target,
        "Achieved So Far": total_achieved_so_far,
        "Balance": total_required_remaining,
        "Difference So Far": total_diff_so_far,
        "Target Achieved %": total_target_pct,
        "Available Room Nights": total_available_room_nights,
        "Rooms Sold": total_rooms_sold,
        "Occupancy %": total_occupancy,
        "Receivable": total_receivable,
        "ARR": total_arr,
        "Balance Days": balance_days,
        "Per Day Needed": total_per_day_needed,
        "ARR Focused": total_arr_focused
    })
    
    df = pd.DataFrame(rows)
    df.insert(0, 'S.No', range(1, len(df) + 1))
    return df

# -------------------------- Compact Styling --------------------------
def style_dataframe(df):
    # Short column names
    df_display = df.copy()
    df_display.columns = [
        'S.No', 'Property', 'Target', 'Achieved', 'Balance', 'Diff', '% Ach',
        'Room Nights', 'Sold', 'Occ %', 'Revenue', 'ARR', 'Bal Days', 'Daily Need', 'Focus ARR'
    ]

    def color_difference(val):
        if isinstance(val, (int, float)):
            return 'color: green; font-weight: bold' if val >= 0 else 'color: red; font-weight: bold'
        return ''

    def color_percentage(val):
        if isinstance(val, (int, float)):
            if val >= 70:
                return 'color: green; font-weight: bold'
            elif val >= 50:
                return 'color: orange; font-weight: bold'
            else:
                return 'color: red; font-weight: bold'
        return ''

    styled = df_display.style \
        .applymap(color_difference, subset=['Diff', 'Balance']) \
        .applymap(color_percentage, subset=['% Ach', 'Occ %']) \
        .format({
            'Target': '₹{:,.0f}',
            'Achieved': '₹{:,.0f}',
            'Balance': '₹{:,.0f}',
            'Diff': '₹{:,.0f}',
            'Revenue': '₹{:,.0f}',
            'ARR': '₹{:,.0f}',
            'Bal Days': '{:,.0f}',
            'Daily Need': '₹{:,.0f}',
            'Focus ARR': '₹{:,.0f}',
            '% Ach': '{:.1f}%',
            'Occ %': '{:.1f}%',
            'Room Nights': '{:,.0f}',
            'Sold': '{:,.0f}'
        }) \
        .set_properties(**{
            'font-size': '11px',
            'text-align': 'center',
            'padding': '3px 6px',
            'white-space': 'nowrap'
        }) \
        .set_table_styles([
            {'selector': 'th', 'props': [
                ('background-color', '#1e6b4f'),
                ('color', 'white'),
                ('font-weight', 'bold'),
                ('font-size', '11px'),
                ('padding', '3px 6px'),
                ('text-align', 'center')
            ]},
            {'selector': 'td', 'props': [('border', '1px solid #eee')]},
            {'selector': 'table', 'props': [('font-size', '11px')]}
        ])
    
    return styled

# -------------------------- UI --------------------------
def show_target_achievement_report():
    st.title("🎯 Target vs Achievement Report - December 2025")

    today = date.today()
    year = st.selectbox("Year", options=list(range(today.year-5, today.year+6)), index=5)
    month = st.selectbox("Month", options=list(range(1,13)), index=today.month-1)

    if year != 2025 or month != 12:
        st.warning("Targets optimized for December 2025.")
        current_date = date(year, month, 1)
    else:
        current_date = date(2025, 12, 6)

    properties = load_properties()
    if not properties:
        st.info("No properties found in database.")
        return

    _, days_in_month = calendar.monthrange(year, month)
    month_dates = [date(year, month, d) for d in range(1, days_in_month + 1)]

    with st.spinner("Loading booking data and calculating achievements..."):
        bookings = {p: load_combined_bookings(p, month_dates[0], month_dates[-1]) for p in properties}

    st.subheader(f"Target vs Achievement Analysis - {calendar.month_name[month]} {year}")
    
    df = build_target_achievement_report(properties, month_dates, bookings, current_date)
    styled_df = style_dataframe(df)

    # Ultra-compact table - no vertical scroll
    st.markdown('<div class="dataframe-container">', unsafe_allow_html=True)
    st.dataframe(styled_df, use_container_width=True, hide_index=True, height=500)  # Fixed height fits all rows
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Summary metrics
    st.markdown("---")
    total_row = df[df["Property Name"] == "TOTAL"].iloc[0]
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Target", f"₹{total_row['Target']:,.0f}")
    with col2:
        st.metric("Achieved So Far", f"₹{total_row['Achieved So Far']:,.0f}", 
                 delta=f"₹{total_row['Difference So Far']:,.0f}")
    with col3:
        st.metric("Balance to Achieve", f"₹{total_row['Balance']:,.0f}")
    with col4:
        st.metric("Achievement %", f"{total_row['Target Achieved %']:.1f}%")
    with col5:
        st.metric("Daily Needed", f"₹{total_row['Per Day Needed']:,.0f}")
    
    # Download
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download Report as CSV",
        data=csv,
        file_name=f"target_achievement_{calendar.month_name[month]}_{year}.csv",
        mime="text/csv"
    )

if __name__ == "__main__":
    show_target_achievement_report()
