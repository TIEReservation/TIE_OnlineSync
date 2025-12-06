# target_achievement_report.py - COMPACT + "Balance" Column

import streamlit as st
from datetime import date
import calendar
import pandas as pd
from supabase import create_client, Client
from typing import List, Dict
import os

# =========================== FORCE COMPACT LAYOUT - NO SCROLL ===========================
st.markdown("""
<style>
    .main > div {padding-top: 2rem;}
    .dataframe-container {
        overflow-x: hidden !important;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    th, td {
        padding: 5px 7px !important;
        font-size: 11.8px !important;
        text-align: center !important;
    }
    th {background-color: #1e6b4f !important; color: white !important;}
    td:nth-child(2), th:nth-child(2) {max-width: 135px; white-space: normal !important; line-height: 1.3;}
</style>
""", unsafe_allow_html=True)

# -------------------------- Supabase Config --------------------------
try:
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except:
    try:
        supabase: Client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
    except KeyError as e:
        st.error(f"Missing Supabase config: {e}"); st.stop()

# -------------------------- Property Mapping & Targets (unchanged) --------------------------
PROPERTY_MAPPING = { ... }  # Keep your existing mapping
reverse_mapping = {c: [] for c in set(PROPERTY_MAPPING.values())}
for v, c in PROPERTY_MAPPING.items():
    reverse_mapping[c].append(v)

def normalize_property_name(prop_name: str) -> str:
    return PROPERTY_MAPPING.get(prop_name, prop_name) if prop_name else prop_name

DECEMBER_2025_TARGETS = { ... }  # Keep your targets

PROPERTY_INVENTORY = { ... }  # Keep your inventory

def get_total_rooms(prop: str) -> int:
    inv = PROPERTY_INVENTORY.get(prop, {"all": []})["all"]
    return len([r for r in inv if not r.startswith(("Day Use", "No Show"))])

# -------------------------- All helper functions (unchanged) --------------------------
# (load_properties, load_combined_bookings, filter_bookings_for_day, assign_inventory_numbers,
#  safe_float, compute_daily_metrics) → keep exactly as before

# -------------------------- MAIN REPORT FUNCTION (Only change: "Balance" column) --------------------------
def build_target_achievement_report(props: List[str], dates: List[date], bookings: Dict[str, List[Dict]], current_date: date) -> pd.DataFrame:
    rows = []
    total_target = total_achieved_so_far = total_available = total_sold = total_receivable = total_rooms_all = total_remaining_needed = 0.0
    past_dates = [d for d in dates if d <= current_date]
    future_dates = [d for d in dates if d > current_date]
    balance_days = len(future_dates)

    for prop in props:
        target = DECEMBER_2025_TARGETS.get(prop, 0)
        achieved_so_far = receivable_full = rooms_sold_full = 0.0
        total_rooms = get_total_rooms(prop)

        for d in past_dates:
            m = compute_daily_metrics(bookings.get(prop, []), prop, d)
            achieved_so_far += m["receivable"]
        for d in dates:
            m = compute_daily_metrics(bookings.get(prop, []), prop, d)
            receivable_full += m["receivable"]
            rooms_sold_full += m["rooms_sold"]

        balance_amount = target - achieved_so_far
        per_day_needed = max(balance_amount, 0) / balance_days if balance_days > 0 else 0
        occupancy = (rooms_sold_full / (total_rooms * len(dates)) * 100) if total_rooms else 0
        arr = receivable_full / rooms_sold_full if rooms_sold_full > 0 else 0
        focus_arr = per_day_needed / total_rooms if total_rooms > 0 else 0

        rows.append({
            "Property Name": prop,
            "Target": target,
            "Achieved So Far": achieved_so_far,
            "Balance": balance_amount,                   # ← Renamed!
            "Diff": achieved_so_far - target,
            "Achieved %": (achieved_so_far / target * 100) if target else 0,
            "Room Nights": total_rooms * len(dates),
            "Sold": rooms_sold_full,
            "Occ %": occupancy,
            "Revenue": receivable_full,
            "ARR": arr,
            "Days Left": balance_days,
            "Daily Need": max(balance_amount, 0),
            "Focus ARR": focus_arr
        })

        # Totals
        total_target += target
        total_achieved_so_far += achieved_so_far
        total_receivable += receivable_full
        total_sold += rooms_sold_full
        total_rooms_all += total_rooms
        total_remaining_needed += max(balance_amount, 0)

    # TOTAL ROW
    total_balance = total_target - total_achieved_so_far
    rows.append({
        "Property Name": "TOTAL",
        "Target": total_target,
        "Achieved So Far": total_achieved_so_far,
        "Balance": total_balance,
        "Diff": total_achieved_so_far - total_target,
        "Achieved %": (total_achieved_so_far / total_target * 100) if total_target else 0,
        "Room Nights": total_rooms_all * len(dates),
        "Sold": total_sold,
        "Occ %": (total_sold / (total_rooms_all * len(dates)) * 100) if total_rooms_all else 0,
        "Revenue": total_receivable,
        "ARR": total_receivable / total_sold if total_sold > 0 else 0,
        "Days Left": balance_days,
        "Daily Need": total_remaining_needed / balance_days if balance_days > 0 else 0,
        "Focus ARR": (total_remaining_needed / balance_days) / total_rooms_all if total_rooms_all and balance_days else 0
    })

    df = pd.DataFrame(rows)
    df.insert(0, 'S.No', range(1, len(df) + 1))
    return df

# =========================== ULTRA-COMPACT STYLING ===========================
def style_dataframe(df: pd.DataFrame):
    df_disp = df.copy()
    df_disp.columns = [
        '#', 'Property', 'Target', 'Achieved', 'Balance', 'Diff', '% Ach',
        'R/N', 'Sold', 'Occ', 'Rev', 'ARR', 'Left', 'Need/Day', 'F-ARR'
    ]

    def color_neg(val): 
        return f"color: {'green' if val >= 0 else 'red'}; font-weight: bold" if isinstance(val, (int, float)) else ''
    def color_pct(val): 
        color = 'green' if val >= 70 else 'orange' if val >= 50 else 'red'
        return f"color: {color}; font-weight: bold" if isinstance(val, (int, float)) else ''

    return (df_disp.style
            .applymap(color_neg, subset=['Diff', 'Balance'])
            .applymap(color_pct, subset=['% Ach', 'Occ'])
            .format({
                'Target': '₹{:,.0f}', 'Achieved': '₹{:,.0f}', 'Balance': '₹{:,.0f}',
                'Diff': '₹{:,.0f}', 'Rev': '₹{:,.0f}', 'ARR': '₹{:,.0f}',
                'Need/Day': '₹{:,.0f}', 'F-ARR': '₹{:,.0f}',
                '% Ach': '{:.0f}%', 'Occ': '{:.0f}%', 'R/N': '{:,.0f}', 'Sold': '{:,.0f}', 'Left': '{:.0f}'
            })
            .set_properties(**{'font-size': '11.8px', 'padding': '4px 6px'}))

# -------------------------- UI --------------------------
def show_target_achievement_report():
    st.title("Target vs Achievement – December 2025")

    year = 2025
    month = 12
    current_date = date(2025, 12, 6)  # Update daily

    properties = [p for p in load_properties() if p in DECEMBER_2025_TARGETS]
    month_dates = [date(2025, 12, d) for d in range(1, 32)]

    with st.spinner("Calculating..."):
        bookings = {p: load_combined_bookings(p, date(2025,12,1), date(2025,12,31)) for p in properties}
        df = build_target_achievement_report(properties, month_dates, bookings, current_date)
        styled = style_dataframe(df)

    st.subheader("Target vs Achievement Report")

    # Perfect fit table
    st.markdown('<div class="dataframe-container">', unsafe_allow_html=True)
    st.dataframe(styled, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Summary cards
    st.markdown("---")
    tot = df[df["Property Name"] == "TOTAL"].iloc[0]
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: st.metric("Target", f"₹{tot['Target']:,.0f}")
    with c2: st.metric("Achieved", f"₹{tot['Achieved So Far']:,.0f}", delta=f"₹{tot['Diff']:,.0f}")
    with c3: st.metric("Balance to Go", f"₹{tot['Balance']:,.0f}")
    with c4: st.metric("Achievement", f"{tot['Achieved %']:.1f}%")
    with c5: st.metric("Daily Need", f"₹{tot['Daily Need']:,.0f}")

    st.download_button("Download CSV", df.to_csv(index=False), 
                       file_name="Target_Achievement_Dec2025.csv", mime="text/csv")

if __name__ == "__main__":
    show_target_achievement_report()
