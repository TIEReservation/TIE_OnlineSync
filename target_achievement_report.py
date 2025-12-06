# target_achievement_report.py - FINAL VERSION WITH BALANCE DAYS & BALANCE ROOMS

import streamlit as st
from datetime import date
import calendar
import pandas as pd
from supabase import create_client, Client
from typing import List, Dict
import os

# -------------------------- Supabase --------------------------
try:
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except:
    try:
        supabase: Client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
    except Exception as e:
        st.error(f"Supabase config error: {e}")
        st.stop()

# -------------------------- Property Mapping --------------------------
PROPERTY_MAPPING = {
    "La Millionaire Luxury Resort": "La Millionaire Resort",
    "Le Poshe Beach View": "Le Poshe Beach view", "Le Poshe Beach view": "Le Poshe Beach view",
    "Le Poshe Beach VIEW": "Le Poshe Beach view", "Le Poshe Beachview": "Le Poshe Beach view",
    "Millionaire": "La Millionaire Resort", "Le Pondy Beach Side": "Le Pondy Beachside",
    "Le Teera": "Le Terra"
}

reverse_mapping = {c: [] for c in set(PROPERTY_MAPPING.values())}
for v, c in PROPERTY_MAPPING.items():
    reverse_mapping[c].append(v)

def normalize_property_name(prop_name: str) -> str:
    return PROPERTY_MAPPING.get(prop_name, prop_name) if prop_name else prop_name

# -------------------------- December 2025 Targets --------------------------
DECEMBER_2025_TARGETS = {
    "La Millionaire Resort": 2200000, "Le Poshe Beach view": 800000, "Le Park Resort": 800000,
    "La Tamara Luxury": 1848000, "Le Poshe Luxury": 1144000, "Le Poshe Suite": 475000,
    "Eden Beach Resort": 438000, "La Antilia Luxury": 1075000, "La Coromandel Luxury": 800000,
    "La Tamara Suite": 640000, "Villa Shakti": 652000, "La Paradise Luxury": 467000,
    "La Villa Heritage": 467000, "La Paradise Residency": 534000,
    "Le Pondy Beachside": 245000, "Le Royce Villa": 190000,
}

# -------------------------- Property Inventory --------------------------
PROPERTY_INVENTORY = {
    "Le Poshe Beach view": {"all": ["101","102","201","202","203","204","301","302","303","304","Day Use 1","Day Use 2","No Show"]},
    "La Millionaire Resort": {"all": ["101","102","103","105","201","202","203","204","205","206","207","208","301","302","303","304","305","306","307","308","401","402","Day Use 1","Day Use 2","Day Use 3","Day Use 4","Day Use 5","No Show"]},
    "Eden Beach Resort": {"all": ["101","102","103","201","202","Day Use 1","Day Use 2","No Show"]},
    # ... keep all your properties exactly as original
}

def get_total_rooms(prop: str) -> int:
    inv = PROPERTY_INVENTORY.get(prop, {"all": []})["all"]
    return len([r for r in inv if not r.startswith(("Day Use", "No Show"))])

# -------------------------- Booking Functions (unchanged) --------------------------
def load_combined_bookings(prop: str, start: date, end: date) -> List[Dict]:
    normalized = normalize_property_name(prop)
    query_props = [normalized] + reverse_mapping.get(normalized, [])
    try:
        direct = supabase.table("reservations").select("*").in_("property_name", query_props)\
            .lte("check_in", str(end)).gte("check_out", str(start))\
            .in_("plan_status", ["Confirmed", "Completed"])\
            .in_("payment_status", ["Partially Paid", "Fully Paid"]).execute().data or []

        online = supabase.table("online_reservations").select("*").in_("property", query_props)\
            .lte("check_in", str(end)).gte("check_out", str(start))\
            .in_("booking_status", ["Confirmed", "Completed"])\
            .in_("payment_status", ["Partially Paid", "Fully Paid"]).execute().data or []

        all_bookings = []
        for b in direct + online:
            name = b.get("property_name") or b.get("property")
            if normalize_property_name(name) == prop:
                b["property_name"] = prop
                b["type"] = "direct" if "property_name" in b else "online"
                all_bookings.append(b)
        return all_bookings
    except Exception as e:
        st.error(f"Error loading {prop}: {e}")
        return []

def filter_bookings_for_day(bookings: List[Dict], day: date):
    return [b for b in bookings if date.fromisoformat(b["check_in"]) <= day < date.fromisoformat(b["check_out"])]

def assign_inventory_numbers(daily: List[Dict], prop: str):
    inv = PROPERTY_INVENTORY.get(prop, {"all": []})["all"]
    lookup = {r.strip().lower(): r for r in inv}
    assigned = []; used = set()
    for b in daily:
        rooms = [r.strip() for r in str(b.get("room_no") or "").split(",") if r.strip()]
        assigned_rooms = []
        for r in rooms:
            key = r.lower()
            if key in lookup and lookup[key] not in used:
                assigned_rooms.append(lookup[key])
                used.add(lookup[key])
        for i, room in enumerate(assigned_rooms):
            new_b = b.copy()
            new_b["assigned_room"] = room
            new_b["room_no"] = room
            new_b["is_primary"] = (i == 0)
            assigned.append(new_b)
    return assigned, []

def safe_float(v, default=0.0):
    try: return float(v) if v not in [None, "", " "] else default
    except: return default

def compute_daily_metrics(bookings: List[Dict], prop: str, day: date) -> Dict:
    daily = filter_bookings_for_day(bookings, day)
    assigned, _ = assign_inventory_numbers(daily, prop)
    rooms_sold = len({b.get("assigned_room") for b in assigned if b.get("assigned_room")})
    primaries = [b for b in assigned if b.get("is_primary", True) and date.fromisoformat(b["check_in"]) == day]
    receivable = 0.0
    for b in primaries:
        if b["type"] == "online":
            amt = safe_float(b.get("booking_amount"))
            gst = safe_float(b.get("ota_tax"))
            comm = safe_float(b.get("ota_commission"))
            receivable += amt - gst - comm
        else:
            receivable += safe_float(b.get("total_tariff"))
    return {"rooms_sold": rooms_sold, "receivable": receivable}

# -------------------------- MAIN REPORT (FINAL & PERFECT) --------------------------
def build_target_achievement_report(props: List[str], dates: List[date], bookings_dict: Dict[str, List[Dict]], current_date: date) -> pd.DataFrame:
    rows = []
    total_target = total_achieved = total_all_booking = total_balance = 0.0
    total_room_nights = total_rooms_sold = total_balance_rooms = total_rooms_count = 0.0

    balance_days = len([d for d in dates if d > current_date])  # e.g. 25 days from 7th Dec

    for prop in props:
        target = DECEMBER_2025_TARGETS.get(prop, 0)
        total_rooms = get_total_rooms(prop)
        total_room_nights_available = total_rooms * len(dates)

        achieved = all_booking = rooms_sold_total = future_booked_rooms = 0.0

        for d in dates:
            m = compute_daily_metrics(bookings_dict.get(prop, []), prop, d)
            if d <= current_date:
                achieved += m["receivable"]
            all_booking += m["receivable"]
            rooms_sold_total += m["rooms_sold"]
            if d > current_date:
                future_booked_rooms += m["rooms_sold"]

        # CORRECT: Balance Rooms = Available from tomorrow
        balance_rooms = (total_rooms * balance_days) - future_booked_rooms

        balance = target - achieved
        achieved_pct = (all_booking / target * 100) if target > 0 else 0
        occupancy = (rooms_sold_total / total_room_nights_available * 100) if total_room_nights_available > 0 else 0
        per_day_needed = max(balance, 0) / balance_days if balance_days > 0 else 0

        rows.append({
            "Property Name": prop,
            "Target": int(target),
            "Achieved": int(achieved),
            "All Booking": int(all_booking),
            "Balance": int(balance),
            "Achieved %": round(achieved_pct, 1),
            "Total Rooms": int(total_room_nights_available),
            "Rooms Sold": int(rooms_sold_total),
            "Occupancy %": round(occupancy, 1),
            "Balance Days": balance_days,
            "Balance Rooms": max(int(balance_rooms), 0),   # Real unsold rooms from tomorrow
            "Per Day Needed": int(per_day_needed)
        })

        total_target += target
        total_achieved += achieved
        total_all_booking += all_booking
        total_balance += balance
        total_room_nights += total_room_nights_available
        total_rooms_sold += rooms_sold_total
        total_balance_rooms += balance_rooms
        total_rooms_count += total_rooms

    # TOTAL Row
    total_pct = (total_all_booking / total_target * 100) if total_target > 0 else 0
    total_occupancy = (total_rooms_sold / total_room_nights * 100) if total_room_nights > 0 else 0
    total_per_day = max(total_balance, 0) / balance_days if balance_days > 0 else 0

    rows.append({
        "Property Name": "TOTAL",
        "Target": int(total_target),
        "Achieved": int(total_achieved),
        "All Booking": int(total_all_booking),
        "Balance": int(total_balance),
        "Achieved %": round(total_pct, 1),
        "Total Rooms": int(total_room_nights),
        "Rooms Sold": int(total_rooms_sold),
        "Occupancy %": round(total_occupancy, 1),
        "Balance Days": balance_days,
        "Balance Rooms": max(int(total_balance_rooms), 0),
        "Per Day Needed": int(total_per_day)
    })

    df = pd.DataFrame(rows)
    df.insert(0, "S.No", range(1, len(df) + 1))
    return df

# -------------------------- Styling --------------------------
def style_dataframe(df):
    return df.style \
        .applymap(lambda v: "color: green; font-weight: bold" if isinstance(v, (int, float)) and v >= 0 else "color: red; font-weight: bold", subset=["Balance"]) \
        .applymap(lambda v: f"color: {'green' if v >= 70 else 'orange' if v >= 50 else 'red'}; font-weight: bold", subset=["Achieved %", "Occupancy %"]) \
        .format({
            "Target": "₹{:,.0f}", "Achieved": "₹{:,.0f}", "All Booking": "₹{:,.0f}", "Balance": "₹{:,.0f}",
            "Total Rooms": "{:,.0f}", "Rooms Sold": "{:,.0f}", "Balance Rooms": "{:,.0f}",
            "Per Day Needed": "₹{:,.0f}", "Achieved %": "{:.1f}%", "Occupancy %": "{:.1f}%", "Balance Days": "{:.0f}"
        }) \
        .set_properties(**{"text-align": "center"}) \
        .set_table_styles([{"selector": "th", "props": "background-color: #4CAF50; color: white; font-weight: bold;"}])

# -------------------------- UI --------------------------
def show_target_achievement_report():
    st.set_page_config(page_title="Target vs Achievement - Dec 2025", layout="wide")
    st.title("Target vs Achievement Report - December 2025")

    current_date = date(2025, 12, 6)  # Update daily
    year, month = 2025, 12
    _, days_in_month = calendar.monthrange(year, month)
    dates = [date(year, month, d) for d in range(1, days_in_month + 1)]
    properties = list(DECEMBER_2025_TARGETS.keys())

    with st.spinner("Loading bookings & generating report..."):
        bookings = {p: load_combined_bookings(p, dates[0], dates[-1]) for p in properties}
        df = build_target_achievement_report(properties, dates, bookings, current_date)
        styled = style_dataframe(df)

    st.dataframe(styled, use_container_width=True, hide_index=True)

    total = df[df["Property Name"] == "TOTAL"].iloc[0]
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: st.metric("Total Target", f"₹{total.Target:,.0f}")
    with c2: st.metric("Achieved", f"₹{total.Achieved:,.0f}", delta=f"₹{total.Balance:,.0f}")
    with c3: st.metric("All Booking", f"₹{total['All Booking']:,.0f}")
    with c4: st.metric("Achieved %", f"{total['Achieved %']:.1f}%")
    with c5: st.metric("Daily Needed", f"₹{total['Per Day Needed']:,.0f}")

    st.download_button("Download Report (CSV)", df.to_csv(index=False), "Target_Achievement_Dec2025.csv", "text/csv")

if __name__ == "__main__":
    show_target_achievement_report()
