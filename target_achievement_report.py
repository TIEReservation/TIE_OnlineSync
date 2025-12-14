# target_achievement_report.py - CORRECTED VERSION (December 2025) - Dynamic Date System

import streamlit as st
from datetime import date, datetime
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
    "La Coromandel Luxury":  738878,
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
    
    primaries = [b for b in assigned if b.get("is_primary", True) and date.fromisoformat(b["check_in"]) == day]
    
    total_amount = commission = gst = receivable = 0.0
    
    for b in primaries:
        if b["type"] == "online":
            # Online: Total = booking_amount
            booking_amt = safe_float(b.get("booking_amount"))
            comm = safe_float(b.get("ota_commission"))
            tax = safe_float(b.get("ota_tax"))
            
            total_amount += booking_amt
            commission += comm
            gst += tax
            # Receivable = Total - Commission - GST
            receivable += booking_amt - comm - tax
        else:
            # Direct: Total = total_tariff, Receivable = same as Total
            tariff = safe_float(b.get("total_tariff"))
            total_amount += tariff
            receivable += tariff
    
    return {
        "rooms_sold": rooms_sold, 
        "total": total_amount,
        "receivable": receivable,
        "commission": commission,
        "gst": gst
    }

# -------------------------- MAIN REPORT --------------------------
def build_target_achievement_report(props: List[str], dates: List[date], bookings_dict: Dict[str, List[Dict]], current_date: date) -> pd.DataFrame:
    rows = []
    balance_days = len([d for d in dates if d > current_date])

    for prop in props:
        try:
            target = DECEMBER_2025_TARGETS.get(prop, 0)
            total_rooms = get_total_rooms(prop)
            total_room_nights = total_rooms * len(dates)

            achieved = rooms_sold = future_booked = 0.0
            commission_total = receivable_total = gst_total = 0.0
            
            for d in dates:
                m = compute_daily_metrics(bookings_dict.get(prop, []), prop, d)
                achieved += m["total"]  # Total booking amount
                commission_total += m["commission"]
                gst_total += m["gst"]
                receivable_total += m["receivable"]
                rooms_sold += m["rooms_sold"]
                
                if d > current_date:
                    future_booked += m["rooms_sold"]

            balance_rooms = max((total_rooms * balance_days) - future_booked, 0)
            balance = target - achieved
            achieved_pct = (achieved / target * 100) if target > 0 else 0
            occupancy = (rooms_sold / total_room_nights * 100) if total_room_nights > 0 else 0
            per_day_needed = max(balance, 0) / balance_days if balance_days > 0 else 0

            rows.append({
                "Property Name": prop, 
                "Target": int(target), 
                "Achieved": int(achieved),
                "Balance": int(balance),
                "Achieved %": round(achieved_pct, 1), 
                "Total Rooms": int(total_room_nights),
                "Rooms Sold": int(rooms_sold), 
                "Occupancy %": round(occupancy, 1),
                "Balance Rooms": int(balance_rooms),
                "Per Day Needed": int(per_day_needed),
                "GST": int(gst_total),
                "Commission": int(commission_total),
                "Receivable": int(receivable_total)
            })
        except Exception as e:
            st.warning(f"Error processing {prop}: {e}")
            continue

    if rows:
        totals = {k: sum(r[k] for r in rows if k != "Property Name") for k in rows[0].keys() if k != "Property Name"}
        totals["Property Name"] = "TOTAL"
        totals["Achieved %"] = round((totals["Achieved"] / totals["Target"] * 100) if totals["Target"] else 0, 1)
        totals["Occupancy %"] = round((totals["Rooms Sold"] / totals["Total Rooms"] * 100) if totals["Total Rooms"] else 0, 1)
        rows.append(totals)

    df = pd.DataFrame(rows or [{"Property Name": "No Data"}])
    df.insert(0, "S.No", range(1, len(df) + 1))
    return df

# -------------------------- Styling --------------------------
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
                "Target": "₹{:,.0f}", "Achieved": "₹{:,.0f}", 
                "Balance": "₹{:,.0f}", "GST": "₹{:,.0f}", "Commission": "₹{:,.0f}", "Receivable": "₹{:,.0f}",
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

    # Get today's date from system
    current_date = date.today()
    
    # Calculate balance days: if current month is December, balance = 31 - today's date
    year = current_date.year
    month = current_date.month
    
    if month == 12:
        balance_days = 31 - current_date.day
    else:
        # For non-December months, calculate remaining days in the month
        _, days_in_month = calendar.monthrange(year, month)
        balance_days = days_in_month - current_date.day
    
    # Always use December 2025 for the report
    report_year, report_month = 2025, 12
    _, days_in_month = calendar.monthrange(report_year, report_month)
    dates = [date(report_year, report_month, d) for d in range(1, days_in_month + 1)]
    
    # Display current date and balance days info
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
        with c3: st.metric("Balance", f"₹{total.Balance:,.0f}", delta=f"{balance_days} days")
        with c4: st.metric("GST", f"₹{total['GST']:,.0f}")
        with c5: st.metric("Commission", f"₹{total['Commission']:,.0f}")
        with c6: st.metric("Receivable", f"₹{total['Receivable']:,.0f}")

    st.download_button("Download Report (CSV)", df.to_csv(index=False), "Target_Achievement_Dec2025.csv", "text/csv")

if __name__ == "__main__":
    show_target_achievement_report()
