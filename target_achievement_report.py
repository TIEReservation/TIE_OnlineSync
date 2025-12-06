# target_achievement_report.py - FINAL CORRECTED VERSION (Dec 2025)

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
except:
    try:
        supabase: Client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
    except KeyError as e:
        st.error(f"Missing Supabase config: {e}")
        st.stop()

# -------------------------- Property Mapping & Targets --------------------------
PROPERTY_MAPPING = { ... }  # Keep your full mapping
DECEMBER_2025_TARGETS = { ... }  # Keep your full targets
PROPERTY_INVENTORY = { ... }  # Keep your full inventory

def get_total_rooms(prop: str) -> int:
    inv = PROPERTY_INVENTORY.get(prop, {"all": []})["all"]
    return len([r for r in inv if not r.startswith(("Day Use", "No Show"))])

# (All your existing helper functions: load_combined_bookings, compute_daily_metrics, etc. remain unchanged)

def build_target_achievement_report(props: List[str], dates: List[date], bookings: Dict[str, List[Dict]], current_date: date) -> pd.DataFrame:
    rows = []
    total_target = total_achieved = total_projected = total_balance = 0.0
    total_room_nights = total_rooms_sold = total_balance_rooms = total_rooms_count = 0

    past_dates = [d for d in dates if d <= current_date]
    future_dates = [d for d in dates if d > current_date]
    balance_days = len(future_dates)

    for prop in props:
        target = DECEMBER_2025_TARGETS.get(prop, 0)
        total_rooms = get_total_rooms(prop)
        total_room_nights_available = total_rooms * len(dates)
        balance_rooms = total_rooms * balance_days

        achieved = projected = rooms_sold_total = 0.0

        for d in dates:
            metrics = compute_daily_metrics(bookings.get(prop, []), prop, d)
            if d <= current_date:
                achieved += metrics["receivable"]
            projected += metrics["receivable"]
            rooms_sold_total += metrics["rooms_sold"]

        balance = target - achieved
        achieved_pct = (projected / target * 100) if target > 0 else 0
        occupancy = (rooms_sold_total / total_room_nights_available * 100) if total_room_nights_available > 0 else 0
        arr = projected / rooms_sold_total if rooms_sold_total > 0 else 0
        per_day_needed = max(balance, 0) / balance_days if balance_days > 0 else 0
        arr_focused = per_day_needed / total_rooms if total_rooms > 0 else 0

        rows.append({
            "Property Name": prop,
            "Target": target,
            "Achieved": achieved,                    # FIXED
            "Projected": projected,                  # Renamed from Full Projected
            "Balance": balance,                      # FIXED (was Difference So Far)
            "Achieved %": achieved_pct,              # FIXED
            "Total Rooms": total_room_nights_available,  # FIXED (was Available Room Nights)
            "Rooms Sold": rooms_sold_total,
            "Occupancy %": occupancy,
            "Receivable": projected,
            "ARR": arr,
            "Balance Days": balance_days,
            "Balance Rooms": balance_rooms,          # NEW COLUMN
            "Per Day Needed": per_day_needed,
            "ARR Focused": arr_focused
        })

        # Accumulate totals
        total_target += target
        total_achieved += achieved
        total_projected += projected
        total_balance += balance
        total_room_nights += total_room_nights_available
        total_rooms_sold += rooms_sold_total
        total_balance_rooms += balance_rooms
        total_rooms_count += total_rooms

    # TOTAL Row
    total_pct = (total_projected / total_target * 100) if total_target > 0 else 0
    total_occupancy = (total_rooms_sold / total_room_nights * 100) if total_room_nights > 0 else 0
    total_arr = total_projected / total_rooms_sold if total_rooms_sold > 0 else 0
    total_per_day = max(total_balance, 0) / balance_days if balance_days > 0 else 0
    total_arr_focused = total_per_day / total_rooms_count if total_rooms_count > 0 else 0

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
    df.insert(0, "S.No", range(1, len(df) + 1))
    return df

# -------------------------- Styling --------------------------
def style_dataframe(df):
    def color_balance(val):
        if isinstance(val, (int, float)):
            return f"color: {'green' if val >= 0 else 'red'}; font-weight: bold"
        return ""

    def color_pct(val):
        if isinstance(val, (int, float)):
            color = "green" if val >= 70 else "orange" if val >= 50 else "red"
            return f"color: {color}; font-weight: bold"
        return ""

    return df.style \
        .applymap(color_balance, subset=["Balance"]) \
        .applymap(color_pct, subset=["Achieved %", "Occupancy %"]) \
        .format({
            "Target": "₹{:,.0f}",
            "Achieved": "₹{:,.0f}",
            "Projected": "₹{:,.0f}",
            "Balance": "₹{:,.0f}",
            "Total Rooms": "{:,.0f}",
            "Rooms Sold": "{:,.0f}",
            "Receivable": "₹{:,.0f}",
            "ARR": "₹{:,.0f}",
            "Per Day Needed": "₹{:,.0f}",
            "ARR Focused": "₹{:,.0f}",
            "Balance Rooms": "{:,.0f}",
            "Achieved %": "{:.1f}%",
            "Occupancy %": "{:.1f}%"
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

    properties = [p for p in DECEMBER_2025_TARGETS.keys()]

    with st.spinner("Generating report..."):
        bookings = {p: load_combined_bookings(p, dates[0], dates[-1]) for p in properties}
        df = build_target_achievement_report(properties, dates, bookings, current_date)
        styled = style_dataframe(df)

    st.subheader("Target vs Achievement - December 2025")
    st.dataframe(styled, use_container_width=True, hide_index=True)

    total = df[df["Property Name"] == "TOTAL"].iloc[0]
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: st.metric("Total Target", f"₹{total.Target:,.0f}")
    with c2: st.metric("Achieved", f"₹{total.Achieved:,.0f}", delta=f"₹{total.Balance:,.0f}")
    with c3: st.metric("Achieved %", f"{total['Achieved %']:.1f}%")
    with c4: st.metric("Occupancy", f"{total['Occupancy %']:.1f}%")
    with c5: st.metric("Daily Needed", f"₹{total['Per Day Needed']:,.0f}")

    st.download_button("Download CSV", df.to_csv(index=False), "Target_Achievement_Dec2025.csv", "text/csv")

if __name__ == "__main__":
    show_target_achievement_report()
