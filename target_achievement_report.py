# target_achievement_report.py - CORRECTED VERSION (December 2025)

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

# -------------------------- December 2025 Targets --------------------------
DECEMBER_2025_TARGETS = {
    "La Millionaire Resort": 2009899,
    "Le Poshe Beach view":   777120,
    "Le Park Resort":        862113,
    "La Tamara Luxury":     1784373,
    "Le Poshe Luxury":      1100469,
    "Le Poshe Suite":        545150,
    "Eden Beach Resort":     413706,
    "La Antilia Luxury":    1275000,
    "La coramandel":         738878,
    "La Tamara Suite":       657956,
    "Villa Shakti":          947947,
    "La Paradise Luxury":    591102,
    "La Villa Heritage":     494469,
    "La Paradise Residency": 450824,
    "Le Pondy Beachside":    238796,
    "Le Royce Villa":        214916,
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
    "La Coromandel Luxury": {"all": ["101","102","103","201","202","203","204","205","206","301","Day Use 1","Day Use 2","No Show"]},
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
    except Exception as e:
        st.warning(f"DB load failed: {e}")
        return []

# -------------------------- Booking Functions --------------------------
def load_combined_bookings(prop: str, start: date, end: date) -> List[Dict]:
    normalized = normalize_property_name(prop)
    query_props = [normalized] + reverse_mapping.get(normalized, [])
    try:
        direct = supabase.table("reservations").select("*")\
            .in_("property_name", query_props)\
            .lte("check_in", str(end)).gte("check_out", str(start))\
            .in_("plan_status", ["Confirmed", "Completed"])\
            .in_("payment_status", ["Partially Paid", "Fully Paid"]).execute().data or []

        online = supabase.table("online_reservations").select("*")\
            .in_("property", query_props)\
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
        st.warning(f"Failed to load bookings for {prop}: {e}")
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
    
    # Get check-in bookings for the day (primary bookings only)
    primaries = [b for b in assigned if b.get("is_primary", True) and date.fromisoformat(b["check_in"]) == day]
    
    # Calculate receivable and net value for check-in bookings
    receivable = net_value = 0.0
    for b in primaries:
        if b["type"] == "online":
            amt = safe_float(b.get("booking_amount"))
            gst = safe_float(b.get("gst"))
            tax = safe_float(b.get("ota_tax"))
            comm = safe_float(b.get("ota_commission"))
            # Net Value = Total - GST - TAX
            net_value += amt - gst - tax
            # Receivable = Total - GST - TAX - Commission
            receivable += amt - gst - tax - comm
        else:
            # For direct bookings, total_tariff is the receivable and net value
            total = safe_float(b.get("total_tariff"))
            receivable += total
            net_value += total
    
    return {
        "rooms_sold": rooms_sold, 
        "receivable": receivable,
        "net_value": net_value
    }

# -------------------------- MAIN REPORT (CORRECTED) --------------------------
def build_target_achievement_report(props: List[str], dates: List[date], bookings_dict: Dict[str, List[Dict]], current_date: date) -> pd.DataFrame:
    rows = []
    # FIXED: Balance Days = remaining days AFTER today (excluding today)
    balance_days = len([d for d in dates if d > current_date])

    for prop in props:
        try:
            target = DECEMBER_2025_TARGETS.get(prop, 0)
            total_rooms = get_total_rooms(prop)
            total_room_nights = total_rooms * len(dates)

            achieved = all_booking = rooms_sold = future_booked = 0.0
            net_value_total = actual_receivable = 0.0
            
            for d in dates:
                m = compute_daily_metrics(bookings_dict.get(prop, []), prop, d)
                if d <= current_date:
                    achieved += m["receivable"]  # Only past + today
                    actual_receivable += m["receivable"]  # Actual receivable from past
                
                all_booking += m["receivable"]  # All bookings (past + future)
                net_value_total += m["net_value"]  # Net value from all bookings
                rooms_sold += m["rooms_sold"]
                
                if d > current_date:
                    future_booked += m["rooms_sold"]

            balance_rooms = max((total_rooms * balance_days) - future_booked, 0)
            
            # FIXED: Balance = Target - All Bookings (not Target - Achieved)
            balance = target - all_booking
            
            # FIXED: Achieved % = Achieved / Target (not All Booking / Target)
            achieved_pct = (achieved / target * 100) if target > 0 else 0
            
            # FIXED: Occupancy % = Rooms Sold / Total Rooms
            occupancy = (rooms_sold / total_room_nights * 100) if total_room_nights > 0 else 0
            
            per_day_needed = max(balance, 0) / balance_days if balance_days > 0 else 0

            rows.append({
                "Property Name": prop, 
                "Target": int(target), 
                "Achieved": int(achieved),
                "All Booking": int(all_booking), 
                "Balance": int(balance),
                "Achieved %": round(achieved_pct, 1), 
                "Net Value": int(net_value_total),  # NEW COLUMN
                "Actual Receivable": int(actual_receivable),  # NEW COLUMN
                "Total Rooms": int(total_room_nights),
                "Rooms Sold": int(rooms_sold), 
                "Occupancy %": round(occupancy, 1),
                "Balance Days": balance_days, 
                "Balance Rooms": int(balance_rooms),
                "Per Day Needed": int(per_day_needed)
            })
        except Exception as e:
            st.warning(f"Error processing {prop}: {e}")
            continue

    if rows:
        # Calculate totals row
        totals = {k: sum(r[k] for r in rows if k != "Property Name") for k in rows[0].keys() if k != "Property Name"}
        totals["Property Name"] = "TOTAL"
        # FIXED: Achieved % = Achieved / Target (not All Booking / Target)
        totals["Achieved %"] = round((totals["Achieved"] / totals["Target"] * 100) if totals["Target"] else 0, 1)
        totals["Occupancy %"] = round((totals["Rooms Sold"] / totals["Total Rooms"] * 100) if totals["Total Rooms"] else 0, 1)
        rows.append(totals)

    df = pd.DataFrame(rows or [{"Property Name": "No Data"}])
    df.insert(0, "S.No", range(1, len(df) + 1))
    return df

# -------------------------- Styling (Balance Green only >=90%) --------------------------
def style_dataframe(df):
    if df is None or df.empty:
        return df

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
                "Target": "₹{:,.0f}", "Achieved": "₹{:,.0f}", "All Booking": "₹{:,.0f}", 
                "Balance": "₹{:,.0f}", "Net Value": "₹{:,.0f}", "Actual Receivable": "₹{:,.0f}",
                "Total Rooms": "{:,.0f}", "Rooms Sold": "{:,.0f}", "Balance Rooms": "{:,.0f}",
                "Per Day Needed": "₹{:,.0f}", "Achieved %": "{:.1f}%", "Occupancy %": "{:.1f}%"
            }) \
            .set_properties(**{"text-align": "center"}) \
            .set_table_styles([{"selector": "th", "props": "background-color: #4CAF50; color: white; font-weight: bold;"}])
    except:
        return df.style

# -------------------------- UI --------------------------
def show_target_achievement_report():
    st.set_page_config(page_title="Target vs Achievement - Dec 2025", layout="wide")
    st.title("Target vs Achievement Report - December 2025")

    # You can change this to date.today() for automatic daily updates
    current_date = date(2025, 12, 8)  # Example: December 8, 2025
    year, month = 2025, 12
    _, days_in_month = calendar.monthrange(year, month)
    dates = [date(year, month, d) for d in range(1, days_in_month + 1)]
    
    # Display current date and balance days info
    balance_days = len([d for d in dates if d > current_date])
    st.info(f"📅 Current Date: {current_date.strftime('%B %d, %Y')} | ⏳ Balance Days: {balance_days}")

    db_props = load_properties()
    properties = [p for p in DECEMBER_2025_TARGETS.keys() if p in db_props]
    if not properties:
        st.info("No data in DB yet. Showing all properties...")
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
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        with c1: st.metric("Total Target", f"₹{total.Target:,.0f}")
        with c2: st.metric("Achieved", f"₹{total.Achieved:,.0f}", delta=f"{total['Achieved %']:.1f}%")
        with c3: st.metric("All Booking", f"₹{total['All Booking']:,.0f}")
        with c4: st.metric("Balance", f"₹{total.Balance:,.0f}", delta=f"{balance_days} days")
        with c5: st.metric("Net Value", f"₹{total['Net Value']:,.0f}")
        with c6: st.metric("Actual Receivable", f"₹{total['Actual Receivable']:,.0f}")

    st.download_button("Download Report (CSV)", df.to_csv(index=False), "Target_Achievement_Dec2025.csv", "text/csv")

if __name__ == "__main__":
    show_target_achievement_report()
