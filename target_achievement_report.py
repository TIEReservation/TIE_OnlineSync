# target_achievement_report.py - FINAL FIXED & COMPACT VERSION
import streamlit as st
from datetime import date
import calendar
import pandas as pd
from supabase import create_client, Client
from typing import List, Dict
import os

# =========================== COMPACT TABLE STYLING - NO SCROLL ===========================
st.markdown("""
<style>
    .main > div {padding-top: 2rem;}
    .dataframe-container {
        overflow-x: hidden !important;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        background: white;
    }
    th, td {
        padding: 5px 7px !important;
        font-size: 11.8px !important;
        text-align: center !important;
    }
    th {
        background-color: #1e6b4f !important;
        color: white !important;
        font-weight: bold !important;
    }
    td:nth-child(2), th:nth-child(2) {
        max-width: 135px;
        white-space: normal !important;
        line-height: 1.35;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------- Supabase --------------------------
try:
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except:
    try:
        supabase: Client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
    except Exception as e:
        st.error(f"Supabase config error: {e}")
        st.stop()

# -------------------------- Property Name Normalization (FIXED!) --------------------------
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

def normalize_property_name(prop_name: str) -> str:
    if not prop_name:
        return ""
    return PROPERTY_MAPPING.get(prop_name.strip(), prop_name.strip())

# Build reverse mapping: canonical → list of raw names
reverse_mapping = {}
for raw, canon in PROPERTY_MAPPING.items():
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
    query_props = reverse_mapping.get(normalized_prop, [normalized_prop])
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
        for b in direct + online:
            name = normalize_property_name(b.get("property_name") or b.get("property") or "")
            if name == normalized_prop:
                b["property_name"] = prop
                b["type"] = "direct" if "property_name" in b else "online"
                all_bookings.append(b)
        return all_bookings
    except Exception as e:
        st.error(f"Error loading bookings: {e}")
        return []

def filter_bookings_for_day(bookings: List[Dict], target: date) -> List[Dict]:
    return [b for b in bookings if date.fromisoformat(b["check_in"]) <= target < date.fromisoformat(b["check_out"])]

def assign_inventory_numbers(daily: List[Dict], prop: str):
    inv = PROPERTY_INVENTORY.get(prop, {"all": []})["all"]
    inv_lookup = {i.strip().lower(): i for i in inv}
    assigned = []
    already_assigned = set()
    
    for b in daily:
        raw_room = str(b.get("room_no") or "").strip()
        if not raw_room:
            continue
        requested = [r.strip() for r in raw_room.split(",") if r.strip()]
        assigned_rooms = []
        for r in requested:
            key = r.lower()
            if key not in inv_lookup or inv_lookup[key] in already_assigned:
                break
            room = inv_lookup[key]
            assigned_rooms.append(room)
            already_assigned.add(room)
        else:
            for idx, room in enumerate(assigned_rooms):
                new_b = b.copy()
                new_b["assigned_room"] = room
                new_b["room_no"] = room
                new_b["is_primary"] = (idx == 0)
                assigned.append(new_b)
    return assigned, []

def safe_float(value, default=0.0):
    try:
        return float(value) if value not in [None, "", " "] else default
    except:
        return default

def compute_daily_metrics(bookings: List[Dict], prop: str, day: date) -> Dict:
    daily = filter_bookings_for_day(bookings, day)
    assigned, _ = assign_inventory_numbers(daily, prop)
    rooms_sold = len({b.get("assigned_room") for b in assigned if b.get("assigned_room")})
    primaries = [b for b in assigned if b.get("is_primary", True) and date.fromisoformat(b["check_in"]) == day]

    receivable = sum(
        safe_float(b.get("total_tariff")) if b.get("type") == "direct" else
        safe_float(b.get("booking_amount")) - safe_float(b.get("ota_tax")) - safe_float(b.get("ota_commission"))
        for b in primaries
    )
    return {"rooms_sold": rooms_sold, "receivable": receivable}

# -------------------------- MAIN REPORT (Balance Column) --------------------------
def build_target_achievement_report(props: List[str], dates: List[date], bookings: Dict[str, List[Dict]], current_date: date) -> pd.DataFrame:
    rows = []
    total_target = total_achieved = total_projected = total_rooms = total_sold = 0.0
    past_dates = [d for d in dates if d <= current_date]
    future_dates = [d for d in dates if d > current_date]
    days_left = len(future_dates)

    for prop in props:
        target = DECEMBER_2025_TARGETS.get(prop, 0)
        achieved = sum(compute_daily_metrics(bookings.get(prop, []), prop, d)["receivable"] for d in past_dates)
        projected = sum(compute_daily_metrics(bookings.get(prop, []), prop, d)["receivable"] for d in dates)
        rooms_sold = sum(compute_daily_metrics(bookings.get(prop, []), prop, d)["rooms_sold"] for d in dates)
        total_room_nights = get_total_rooms(prop) * len(dates)
        occupancy = rooms_sold / total_room_nights * 100 if total_room_nights else 0

        rows.append({
            "Property Name": prop,
            "Target": target,
            "Achieved So Far": achieved,
            "Balance": target - achieved,
            "Diff": achieved - target,
            "Achieved %": (achieved / target * 100) if target else 0,
            "Room Nights": total_room_nights,
            "Sold": rooms_sold,
            "Occ %": occupancy,
            "Revenue": projected,
            "ARR": projected / rooms_sold if rooms_sold else 0,
            "Days Left": days_left,
            "Daily Need": max(target - achieved, 0) / days_left if days_left else 0,
            "Focus ARR": (max(target - achieved, 0) / days_left) / get_total_rooms(prop) if get_total_rooms(prop) and days_left else 0
        })

        total_target += target
        total_achieved += achieved
        total_projected += projected
        total_sold += rooms_sold
        total_rooms += get_total_rooms(prop)

    # TOTAL ROW
    rows.append({
        "Property Name": "TOTAL",
        "Target": total_target,
        "Achieved So Far": total_achieved,
        "Balance": total_target - total_achieved,
        "Diff": total_achieved - total_target,
        "Achieved %": total_achieved / total_target * 100 if total_target else 0,
        "Room Nights": total_rooms * len(dates),
        "Sold": total_sold,
        "Occ %": total_sold / (total_rooms * len(dates)) * 100 if total_rooms else 0,
        "Revenue": total_projected,
        "ARR": total_projected / total_sold if total_sold else 0,
        "Days Left": days_left,
        "Daily Need": max(total_target - total_achieved, 0) / days_left if days_left else 0,
        "Focus ARR": (max(total_target - total_achieved, 0) / days_left) / total_rooms if total_rooms and days_left else 0
    })

    df = pd.DataFrame(rows)
    df.insert(0, 'S.No', range(1, len(df) + 1))
    return df

# -------------------------- Styling --------------------------
def style_dataframe(df: pd.DataFrame):
    df_disp = df.copy()
    df_disp.columns = ['#', 'Property', 'Target', 'Achieved', 'Balance', 'Diff', '% Ach',
                       'R/N', 'Sold', 'Occ', 'Rev', 'ARR', 'Left', 'Need/Day', 'F-ARR']

    def color(val, good=[70, 0]):
        if isinstance(val, (int, float)):
            if val >= good[0]: return "color: green; font-weight: bold"
            if val >= good[1]: return "color: orange"
            return "color: red; font-weight: bold"
        return ""

    return (df_disp.style
            .applymap(lambda v: "color: green; font-weight: bold" if v >= 0 else "color: red; font-weight: bold", subset=['Diff', 'Balance'])
            .applymap(lambda v: color(v, [70, 50]), subset=['% Ach', 'Occ'])
            .format({
                'Target': '₹{:,.0f}', 'Achieved': '₹{:,.0f}', 'Balance': '₹{:,.0f}',
                'Diff': '₹{:,.0f}', 'Rev': '₹{:,.0f}', 'ARR': '₹{:,.0f}',
                'Need/Day': '₹{:,.0f}', 'F-ARR': '₹{:,.0f}',
                '% Ach': '{:.0f}%', 'Occ': '{:.0f}%'
            }))

# -------------------------- UI --------------------------
def show_target_achievement_report():
    st.title("Target vs Achievement – December 2025")

    current_date = date(2025, 12, 6)  # Update daily
    properties = [p for p in load_properties() if p in DECEMBER_2025_TARGETS]
    dates = [date(2025, 12, d) for d in range(1, 32)]

    with st.spinner("Loading & calculating..."):
        bookings = {p: load_combined_bookings(p, dates[0], dates[-1]) for p in properties}
        df = build_target_achievement_report(properties, dates, bookings, current_date)
        styled = style_dataframe(df)

    st.subheader("Target Achievement Report")

    st.markdown('<div class="dataframe-container">', unsafe_allow_html=True)
    st.dataframe(styled, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    tot = df[df["Property Name"] == "TOTAL"].iloc[0]
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: st.metric("Total Target", f"₹{tot['Target']:,.0f}")
    with c2: st.metric("Achieved So Far", f"₹{tot['Achieved So Far']:,.0f}", delta=f"₹{tot['Diff']:,.0f}")
    with c3: st.metric("Balance to Go", f"₹{tot['Balance']:,.0f}")
    with c4: st.metric("Achievement %", f"{tot['Achieved %']:.1f}%")
    with c5: st.metric("Daily Need", f"₹{tot['Daily Need']:,.0f}")

    st.download_button("Download CSV", df.to_csv(index=False), "Target_Achievement_Dec2025.csv", "text/csv")

if __name__ == "__main__":
    show_target_achievement_report()
