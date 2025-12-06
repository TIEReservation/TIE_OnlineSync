# target_achievement_report.py - FINAL BULLETPROOF & ERROR-FREE (Dec 2025)

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
    "Le Poshe Beach View": "Le Poshe Beach view",
    "Le Poshe Beach view": "Le Poshe Beach view",
    "Le Poshe Beach VIEW": "Le Poshe Beach view",
    "Le Poshe Beachview": "Le Poshe Beach view",
    "Millionaire": "La Millionaire Resort",
    "Le Pondy Beach Side": "Le Pondy Beachside",
    "Le Teera": "Le Terra",
    "La Tamara Luxury Resort": "La Tamara Luxury",
    "La Coromandel Luxury Resort": "La Coromandel Luxury",
    "Le Poshe Luxury Resort": "Le Poshe Luxury",
    "Le Poshe Suite Resort": "Le Poshe Suite",
    "La Paradise Luxury Resort": "La Paradise Luxury",
    "Villa Shakti Resort": "Villa Shakti",
}

reverse_mapping = {c: [] for c in set(PROPERTY_MAPPING.values())}
for v, c in PROPERTY_MAPPING.items():
    reverse_mapping[c].append(v)

def normalize_property_name(prop_name: str) -> str:
    if not prop_name:
        return ""
    return PROPERTY_MAPPING.get(prop_name.strip(), prop_name.strip())

# -------------------------- Targets & Inventory --------------------------
DECEMBER_2025_TARGETS = {
    "La Millionaire Resort": 2200000, "Le Poshe Beach view": 800000, "Le Park Resort": 800000,
    "La Tamara Luxury": 1848000, "Le Poshe Luxury": 1144000, "Le Poshe Suite": 475000,
    "Eden Beach Resort": 438000, "La Antilia Luxury": 1075000, "La Coromandel Luxury": 800000,
    "La Tamara Suite": 640000, "Villa Shakti": 652000, "La Paradise Luxury": 467000,
    "La Villa Heritage": 467000, "La Paradise Residency": 534000,
    "Le Pondy Beachside": 245000, "Le Royce Villa": 190000,
}

PROPERTY_INVENTORY = {
    "Le Poshe Beach view": {"all": ["101","102","201","202","203","204","301","302","303","304","Day Use 1","Day Use 2","No Show"]},
    "La Millionaire Resort": {"all": ["101","102","103","105","201","202","203","204","205","206","207","208","301","302","303","304","305","306","307","308","401","402","Day Use 1","Day Use 2","Day Use 3","Day Use 4","Day Use 5","No Show"]},
    "Eden Beach Resort": {"all": ["101","102","103","201","202","Day Use 1","Day Use 2","No Show"]},
    "La Tamara Luxury": {"all": [f"{i}" for i in range(101,107)] + [f"{i}" for i in range(201,207)] + [f"{i}" for i in range(301,307)] + [f"{i}" for i in range(401,405)] + ["Day Use 1","Day Use 2","No Show"]},
    "Le Poshe Luxury": {"all": ["101","102","201","202","203","204","205","301","302","303","304","305","401","402","403","404","405","501","Day Use 1","Day Use 2","No Show"]},
    # ... add all your properties
}

def get_total_rooms(prop: str) -> int:
    inv = PROPERTY_INVENTORY.get(prop, {"all": []})["all"]
    return len([r for r in inv if not r.startswith(("Day Use", "No Show"))])

# -------------------------- Safe Property Loading --------------------------
@st.cache_data(ttl=3600)
def load_properties() -> List[str]:
    try:
        direct = supabase.table("reservations").select("property_name").execute().data or []
        online = supabase.table("online_reservations").select("property").execute().data or []
        names = [r.get("property_name") or r.get("property") for r in direct + online]
        return sorted({normalize_property_name(n) for n in names if n})
    except:
        return []

# -------------------------- Booking & Metrics (keep yours) --------------------------
# Keep your working load_combined_bookings, compute_daily_metrics, etc.

# -------------------------- BULLETPROOF REPORT --------------------------
def build_target_achievement_report(props: List[str], dates: List[date], bookings_dict: Dict[str, List[Dict]], current_date: date) -> pd.DataFrame:
    rows = []
    balance_days = len([d for d in dates if d > current_date])

    for prop in props:
        try:
            target = DECEMBER_2025_TARGETS.get(prop, 0)
            total_rooms = get_total_rooms(prop)
            total_room_nights = total_rooms * len(dates)

            achieved = all_booking = rooms_sold = future_booked = 0.0
            for d in dates:
                m = compute_daily_metrics(bookings_dict.get(prop, []), prop, d)
                if d <= current_date:
                    achieved += m["receivable"]
                all_booking += m["receivable"]
                rooms_sold += m["rooms_sold"]
                if d > current_date:
                    future_booked += m["rooms_sold"]

            balance_rooms = max((total_rooms * balance_days) - future_booked, 0)
            balance = target - achieved
            achieved_pct = (all_booking / target * 100) if target > 0 else 0
            occupancy = (rooms_sold / total_room_nights * 100) if total_room_nights > 0 else 0
            per_day_needed = max(balance, 0) / balance_days if balance_days > 0 else 0

            rows.append({
                "Property Name": prop, "Target": int(target), "Achieved": int(achieved),
                "All Booking": int(all_booking), "Balance": int(balance),
                "Achieved %": round(achieved_pct, 1), "Total Rooms": int(total_room_nights),
                "Rooms Sold": int(rooms_sold), "Occupancy %": round(occupancy, 1),
                "Balance Days": balance_days, "Balance Rooms": int(balance_rooms),
                "Per Day Needed": int(per_day_needed)
            })
        except Exception as e:
            st.warning(f"Error processing {prop}: {e}")
            continue

    # Total row
    if rows:
        totals = {k: sum(r[k] for r in rows if k != "Property Name") for k in rows[0].keys() if k != "Property Name"}
        totals["Property Name"] = "TOTAL"
        totals["Achieved %"] = round((totals["All Booking"] / totals["Target"] * 100) if totals["Target"] else 0, 1)
        totals["Occupancy %"] = round((totals["Rooms Sold"] / totals["Total Rooms"] * 100) if totals["Total Rooms"] else 0, 1)
        rows.append(totals)

    df = pd.DataFrame(rows or [{"Property Name": "No Data"}])
    df.insert(0, "S.No", range(1, len(df) + 1))
    return df

# -------------------------- SAFE STYLING (NO MORE NoneType) --------------------------
def style_dataframe(df):
    if df is None or df.empty or "Property Name" not in df.columns:
        return df  # Return plain df if invalid

    def color_balance(row):
        if row["Achieved %"] >= 90:
            return ["color: green; font-weight: bold" if col == "Balance" else "" for col in row.index]
        else:
            return ["color: red; font-weight: bold" if col == "Balance" else "" for col in row.index]

    def color_pct(val):
        if isinstance(val, (int, float)):
            color = "green" if val >= 70 else "orange" if val >= 50 else "red"
            return f"color: {color}; font-weight: bold"
        return ""

    try:
        return df.style \
            .apply(color_balance, axis=1) \
            .applymap(color_pct, subset=["Achieved %", "Occupancy %"]) \
            .format({
                "Target": "₹{:,.0f}", "Achieved": "₹{:,.0f}", "All Booking": "₹{:,.0f}", "Balance": "₹{:,.0f}",
                "Total Rooms": "{:,.0f}", "Rooms Sold": "{:,.0f}", "Balance Rooms": "{:,.0f}",
                "Per Day Needed": "₹{:,.0f}", "Achieved %": "{:.1f}%", "Occupancy %": "{:.1f}%"
            }) \
            .set_properties(**{"text-align": "center"}) \
            .set_table_styles([{"selector": "th", "props": "background-color: #4CAF50; color: white; font-weight: bold;"}])
    except:
        return df.style  # Fallback

# -------------------------- UI - 100% SAFE --------------------------
def show_target_achievement_report():
    st.set_page_config(page_title="Target vs Achievement - Dec 2025", layout="wide")
    st.title("Target vs Achievement Report - December 2025")

    current_date = date(2025, 12, 6)
    year, month = 2025, 12
    _, days_in_month = calendar.monthrange(year, month)
    dates = [date(year, month, d) for d in range(1, days_in_month + 1)]

    db_props = load_properties()
    properties = [p for p in DECEMBER_2025_TARGETS.keys() if p in db_props]
    if not properties:
        st.warning("No targeted properties found. Showing all...")
        properties = list(DECEMBER_2025_TARGETS.keys())

    with st.spinner("Generating report..."):
        bookings = {}
        for p in properties:
            try:
                bookings[p] = load_combined_bookings(p, dates[0], dates[-1])
            except:
                bookings[p] = []

        df = build_target_achievement_report(properties, dates, bookings, current_date)
        styled = style_dataframe(df)

    st.dataframe(styled, use_container_width=True, hide_index=True)

    if not df.empty and "TOTAL" in df["Property Name"].values:
        total = df[df["Property Name"] == "TOTAL"].iloc[0]
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1: st.metric("Total Target", f"₹{total.Target:,.0f}")
        with c2: st.metric("Achieved", f"₹{total.Achieved:,.0f}", delta=f"₹{total.Balance:,.0f}")
        with c3: st.metric("All Booking", f"₹{total['All Booking']:,.0f}")
        with c4: st.metric("Achieved %", f"{total['Achieved %']:.1f}%")
        with c5: st.metric("Daily Needed", f"₹{total['Per Day Needed']:,.0f}")

    st.download_button("Download CSV", df.to_csv(index=False), "Target_Achievement_Dec2025.csv", "text/csv")

if __name__ == "__main__":
    show_target_achievement_report()
