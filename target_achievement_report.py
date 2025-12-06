# target_achievement_report.py - FINAL BULLETPROOF VERSION (December 2025)

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
    # Add more if needed
}

reverse_mapping = {c: [] for c in set(PROPERTY_MAPPING.values())}
for v, c in PROPERTY_MAPPING.items():
    reverse_mapping[c].append(v)

def normalize_property_name(prop_name: str) -> str:
    if not prop_name:
        return prop_name
    return PROPERTY_MAPPING.get(prop_name.strip(), prop_name.strip())

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

# -------------------------- Property Inventory (keep yours) --------------------------
PROPERTY_INVENTORY = {
    "Le Poshe Beach view": {"all": ["101","102","201","202","203","204","301","302","303","304","Day Use 1","Day Use 2","No Show"]},
    "La Millionaire Resort": {"all": ["101","102","103","105","201","202","203","204","205","206","207","208","301","302","303","304","305","306","307","308","401","402","Day Use 1","Day Use 2","Day Use 3","Day Use 4","Day Use 5","No Show"]},
    "Eden Beach Resort": {"all": ["101","102","103","201","202","Day Use 1","Day Use 2","No Show"]},
    # ... keep all your properties
}

def get_total_rooms(prop: str) -> int:
    inv = PROPERTY_INVENTORY.get(prop, {"all": []})["all"]
    return len([r for r in inv if not r.startswith(("Day Use", "No Show"))])

# -------------------------- SAFE PROPERTY LOADING (NO MORE CRASH) --------------------------
@st.cache_data(ttl=3600)
def load_properties() -> List[str]:
    try:
        direct = supabase.table("reservations").select("property_name").execute().data or []
        online = supabase.table("online_reservations").select("property").execute().data or []
        raw_names = [r.get("property_name") or r.get("property") for r in direct + online]
        normalized = {normalize_property_name(name) for name in raw_names if name}
        return sorted(normalized)
    except Exception as e:
        st.warning(f"Could not load properties from DB: {e}. Using target list only.")
        return []

# -------------------------- Rest of functions (unchanged) --------------------------
# Keep all your existing: load_combined_bookings, compute_daily_metrics, etc.

# -------------------------- MAIN REPORT (same as last working) --------------------------
def build_target_achievement_report(props: List[str], dates: List[date], bookings_dict: Dict[str, List[Dict]], current_date: date) -> pd.DataFrame:
    # ... (use your last working version - unchanged)
    pass

# -------------------------- SMART STYLING (Balance = Green only if ≥90%) --------------------------
def style_dataframe(df):
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

    return df.style \
        .apply(color_balance, axis=1) \
        .applymap(color_pct, subset=["Achieved %", "Occupancy %"]) \
        .format({
            "Target": "₹{:,.0f}", "Achieved": "₹{:,.0f}", "All Booking": "₹{:,.0f}", "Balance": "₹{:,.0f}",
            "Total Rooms": "{:,.0f}", "Rooms Sold": "{:,.0f}", "Balance Rooms": "{:,.0f}",
            "Per Day Needed": "₹{:,.0f}", "Achieved %": "{:.1f}%", "Occupancy %": "{:.1f}%", "Balance Days": "{:.0f}"
        }) \
        .set_properties(**{"text-align": "center"}) \
        .set_table_styles([{"selector": "th", "props": "background-color: #4CAF50; color: white; font-weight: bold;"}])

# -------------------------- UI - BULLETPROOF PROPERTY LOADING --------------------------
def show_target_achievement_report():
    st.set_page_config(page_title="Target vs Achievement - Dec 2025", layout="wide")
    st.title("Target vs Achievement Report - December 2025")

    current_date = date(2025, 12, 6)
    year, month = 2025, 12
    _, days_in_month = calendar.monthrange(year, month)
    dates = [date(year, month, d) for d in range(1, days_in_month + 1)]

    # SAFE & ROBUST PROPERTY LOADING
    db_properties = load_properties()
    target_properties = list(DECEMBER_2025_TARGETS.keys())
    
    # Final list: only properties that have target AND exist in DB (or fallback to all targets)
    properties = [p for p in target_properties if p in db_properties]
    if not properties:
        st.warning("No matching properties found in database. Showing all targeted properties...")
        properties = target_properties  # Fallback

    with st.spinner("Loading bookings & generating report..."):
        bookings = {}
        for p in properties:
            try:
                bookings[p] = load_combined_bookings(p, dates[0], dates[-1])
            except:
                bookings[p] = []

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
