# target_achievement_report (2).py
import streamlit as st
from datetime import date
import calendar
import pandas as pd
from supabase import create_client, Client
from typing import List, Dict
import os

# =========================== FORCE COMPACT TABLE - NO SCROLL ===========================
st.markdown("""
<style>
    /* Make the entire app container use full width but control table */
    .main > div {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Compact table styling */
    .dataframe-container {
        overflow-x: auto;
        max-width: 100vw;
        border-radius: 8px;
        border: 1px solid #ddd;
    }
    
    /* Force small font and tight padding */
    th, td {
        padding: 4px 6px !important;
        font-size: 11.5px !important;
        text-align: center !important;
    }
    
    /* Allow property names to wrap */
    td:nth-child(2), th:nth-child(2) {
        max-width: 130px;
        white-space: normal !important;
        word-wrap: break-word;
        line-height: 1.3;
    }
    
    /* Header style */
    th {
        background-color: #4CAF50 !important;
        color: white !important;
        font-weight: bold !important;
    }
</style>
""", unsafe_allow_html=True)

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
    # ... [your existing build function - unchanged] ...
    # (keeping your original function as-is for logic)
    rows = []
    total_target = total_achieved_so_far = total_available_room_nights = total_rooms_sold = total_receivable = total_per_night_sum = total_rooms_all = total_required_remaining = 0.0
    
    past_dates = [d for d in dates if d <= current_date]
    future_dates = [d for d in dates if d > current_date]
    balance_days = len(future_dates)
    
    for prop in props:
        target = DECEMBER_2025_TARGETS.get(prop, 0)
        
        achieved_so_far = rooms_sold_so_far = receivable_so_far = per_night_sum_so_far = 0.0
        for d in past_dates:
            metrics = compute_daily_metrics(bookings.get(prop, []), prop, d)
            achieved_so_far += metrics.get("receivable", 0.0)
            rooms_sold_so_far += metrics.get("rooms_sold", 0)
            receivable_so_far += metrics.get("receivable", 0.0)
            per_night_sum_so_far += metrics.get("receivable_per_night", 0.0)
        
        achieved = rooms_sold = receivable = per_night_sum = 0.0
        for d in dates:
            metrics = compute_daily_metrics(bookings.get(prop, []), prop, d)
            achieved += metrics.get("receivable", 0.0)
            rooms_sold += metrics.get("rooms_sold", 0)
            receivable += metrics.get("receivable", 0.0)
            per_night_sum += metrics.get("receivable_per_night", 0.0)
        
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
            "Full Projected": achieved,
            "Difference So Far": difference_so_far,
            "Target Achieved %": (achieved / target * 100) if target > 0 else 0.0,
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
        total_per_night_sum += per_night_sum
        total_rooms_all += total_rooms
        total_required_remaining += required_remaining
    
    total_diff_so_far = total_achieved_so_far - total_target
    total_target_pct_projected = (total_receivable / total_target * 100) if total_target > 0 else 0.0
    total_occupancy_projected = (total_rooms_sold / total_available_room_nights * 100) if total_available_room_nights > 0 else 0.0
    total_arr_projected = total_receivable / total_rooms_sold if total_rooms_sold > 0 else 0.0
    total_per_day_needed = total_required_remaining / balance_days if balance_days > 0 else 0.0
    total_arr_focused = total_per_day_needed / total_rooms_all if total_rooms_all > 0 else 0.0
    
    rows.append({
        "Property Name": "TOTAL",
        "Target": total_target,
        "Achieved So Far": total_achieved_so_far,
        "Full Projected": total_receivable,
        "Difference So Far": total_diff_so_far,
        "Target Achieved %": total_target_pct_projected,
        "Available Room Nights": total_available_room_nights,
        "Rooms Sold": total_rooms_sold,
        "Occupancy %": total_occupancy_projected,
        "Receivable": total_receivable,
        "ARR": total_arr_projected,
        "Balance Days": balance_days,
        "Per Day Needed": total_per_day_needed,
        "ARR Focused": total_arr_focused
    })
    
    df = pd.DataFrame(rows)
    df.insert(0, 'S.No', range(1, len(df) + 1))
    return df

# =========================== UPDATED STYLE FUNCTION (COMPACT) ===========================
def style_dataframe(df):
    df_display = df.copy()
    df_display.columns = [
        'S.No', 'Property', 'Target', 'Achieved', 'Projected', 'Diff', '% Ach',
        'Room Nights', 'Sold', 'Occ %', 'Revenue', 'ARR', 'Bal Days', 'Daily Need', 'Focus ARR'
    ]

    def color_diff(val):
        if isinstance(val, (int, float)):
            color = 'green' if val >= 0 else 'red'
            return f'color: {color}; font-weight: bold'
        return ''

    def color_pct(val):
        if isinstance(val, (int, float)):
            color = 'green' if val >= 70 else 'orange' if val >= 50 else 'red'
            return f'color: {color}; font-weight: bold'
        return ''

    return (df_display.style
            .applymap(color_diff, subset=['Diff'])
            .applymap(color_pct, subset=['% Ach', 'Occ %'])
            .format({
                'Target': '₹{:,.0f}', 'Achieved': '₹{:,.0f}', 'Projected': '₹{:,.0f}',
                'Diff': '₹{:,.0f}', 'Revenue': '₹{:,.0f}', 'ARR': '₹{:,.0f}',
                'Daily Need': '₹{:,.0f}', 'Focus ARR': '₹{:,.0f}',
                '% Ach': '{:.1f}%', 'Occ %': '{:.1f}%',
                'Room Nights': '{:,.0f}', 'Sold': '{:,.0f}', 'Bal Days': '{:.0f}'
            })
            .set_properties(**{'font-size': '11.5px', 'padding': '4px'}))

# -------------------------- UI --------------------------
def show_target_achievement_report():
    st.title("Target vs Achievement Report - December 2025")

    today = date.today()
    year = st.selectbox("Year", options=list(range(today.year-5, today.year+6)), index=5)
    month = st.selectbox("Month", options=list(range(1,13)), index=today.month-1)

    if year != 2025 or month != 12:
        st.warning("Targets are set only for December 2025.")
        current_date = date(year, month, 1)
    else:
        current_date = date(2025, 12, 6)  # Update this date as needed

    properties = load_properties()
    if not properties:
        st.info("No properties found.")
        return

    properties_with_targets = [p for p in properties if p in DECEMBER_2025_TARGETS]
    _, days_in_month = calendar.monthrange(year, month)
    month_dates = [date(year, month, d) for d in range(1, days_in_month + 1)]

    with st.spinner("Loading data..."):
        bookings = {p: load_combined_bookings(p, month_dates[0], month_dates[-1]) for p in properties_with_targets}

    df = build_target_achievement_report(properties_with_targets, month_dates, bookings, current_date)
    styled_df = style_dataframe(df)

    st.subheader(f"Target vs Achievement - {calendar.month_name[month]} {year}")

    # Compact table - no horizontal scroll
    st.markdown('<div class="dataframe-container">', unsafe_allow_html=True)
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
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
        st.metric("Achievement %", f"{total_row['Target Achieved %']:.1f}%")
    with col4:
        st.metric("Occupancy", f"{total_row['Occupancy %']:.1f}%")
    with col5:
        st.metric("Daily Needed", f"₹{total_row['Per Day Needed']:,.0f}")

    csv = df.to_csv(index=False)
    st.download_button("Download CSV", data=csv, file_name=f"Target_Achievement_{year}_{month}.csv", mime="text/csv")

if __name__ == "__main__":
    show_target_achievement_report()
