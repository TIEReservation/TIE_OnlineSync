# target_achievement_report.py - FINAL SMART BALANCE COLOR (Dec 2025)

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

# -------------------------- Targets & Inventory (keep yours) --------------------------
DECEMBER_2025_TARGETS = { ... }  # Your full list
PROPERTY_INVENTORY = { ... }     # Your full inventory

def get_total_rooms(prop: str) -> int:
    inv = PROPERTY_INVENTORY.get(prop, {"all": []})["all"]
    return len([r for r in inv if not r.startswith(("Day Use", "No Show"))])

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

# (Keep all your existing functions: load_combined_bookings, compute_daily_metrics, etc.)

# -------------------------- MAIN REPORT --------------------------
def build_target_achievement_report(props: List[str], dates: List[date], bookings_dict: Dict[str, List[Dict]], current_date: date) -> pd.DataFrame:
    # ... (same as last working version - no change needed here)
    # Just make sure you return "Achieved %" as a column
    pass  # Use your last working version

# -------------------------- SMART STYLING (NEW LOGIC) --------------------------
def style_dataframe(df):
    # Balance = Green only if Achieved % >= 90%
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

# -------------------------- UI (with correct property loading) --------------------------
def show_target_achievement_report():
    st.set_page_config(page_title="Target vs Achievement - Dec 2025", layout="wide")
    st.title("Target vs Achievement Report - December 2025")

    current_date = date(2025, 12, 6)
    year, month = 2025, 12
    _, days_in_month = calendar.monthrange(year, month)
    dates = [date(year, month, d) for d in range(1, days_in_month + 1)]

    all_db_props = load_properties()
    properties = [p for p in DECEMBER_2025_TARGETS.keys() if p in all_db_props]

    if not properties:
        st.error("No targeted properties found!")
        st.stop()

    with st.spinner("Generating report..."):
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

    st.download_button("Download CSV", df.to_csv(index=False), "Target_Achievement_Dec2025.csv", "text/csv")

if __name__ == "__main__":
    show_target_achievement_report()
