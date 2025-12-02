# summary_report.py - ENHANCED with Red Zeros + Weekend Highlighting
# Zero values in red | Saturday & Sunday rows in light green

import streamlit as st
from datetime import date, timedelta
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

PROPERTY_SHORT_NAMES = {
    "Eden Beach Resort": "EBR",
    "La Antilia Luxury": "LAL",
    "La Coromandel Luxury": "LCL",
    "La Millionaire Resort": "LMR",
    "La Paradise Luxury": "LaPL",
    "La Paradise Residency": "LPR",
    "La Tamara Luxury": "LTL",
    "La Tamara Suite": "LTS",
    "La Villa Heritage": "LVH",
    "Le Park Resort": "LePR",
    "Le Pondy Beachside": "LPBs",
    "Le Poshe Beach view": "LPBv",
    "Le Poshe Luxury": "LePL",
    "Le Poshe Suite": "LPS",
    "Le Royce Villa": "LRV",
    "Villa Shakti": "VS",
    "Happymates Forest Retreat": "HFR",
    "Le Terra": "LT"
}

# Reverse mapping for querying
reverse_mapping = {c: [] for c in set(PROPERTY_MAPPING.values())}
for v, c in PROPERTY_MAPPING.items():
    reverse_mapping[c].append(v)

def normalize_property_name(prop_name: str) -> str:
    if not prop_name:
        return prop_name
    return PROPERTY_MAPPING.get(prop_name, prop_name)

def get_short_name(prop_name: str) -> str:
    return PROPERTY_SHORT_NAMES.get(prop_name, prop_name)

# -------------------------- Helpers --------------------------
def load_properties() -> List[str]:
    try:
        direct = supabase.table("reservations").select("property_name").execute().data or []
        online = supabase.table("online_reservations").select("property").execute().data or []
        
        props = {
            normalize_property_name(r.get("property_name") or r.get("property"))
            for r in direct + online
            if r.get("property_name") or r.get("property")
        }
        return sorted(props)
    except Exception as e:
        st.error(f"Error loading properties: {e}")
        return []

def load_combined_bookings(prop: str, start: date, end: date) -> List[Dict]:
    normalized_prop = normalize_property_name(prop)
    query_props = [normalized_prop] + reverse_mapping.get(normalized_prop, [])
    
    try:
        direct = (
            supabase.table("reservations")
            .select("*")
            .in_("property_name", query_props)
            .lte("check_in", str(end))
            .gte("check_out", str(start))
            .in_("plan_status", ["Confirmed", "Completed"])
            .in_("payment_status", ["Partially Paid", "Fully Paid"])
            .execute()
            .data or []
        )
        
        online = (
            supabase.table("online_reservations")
            .select("*")
            .in_("property", query_props)
            .lte("check_in", str(end))
            .gte("check_out", str(start))
            .in_("booking_status", ["Confirmed", "Completed"])
            .in_("payment_status", ["Partially Paid", "Fully Paid"])
            .execute()
            .data or []
        )
        
        all_bookings = []
        for booking in direct:
            normalized = normalize_property_name(booking.get("property_name"))
            if normalized == prop:
                booking["property_name"] = normalized
                booking["type"] = "direct"
                all_bookings.append(booking)
        
        for booking in online:
            normalized = normalize_property_name(booking.get("property"))
            if normalized == prop:
                booking["property"] = normalized
                booking["type"] = "online"
                all_bookings.append(booking)
        
        return all_bookings
    except Exception as e:
        st.error(f"Error loading bookings for {prop}: {e}")
        return []

def filter_bookings_for_day(bookings: List[Dict], target: date) -> List[Dict]:
    return [
        b for b in bookings
        if date.fromisoformat(b["check_in"]) &lt;= target &lt; date.fromisoformat(b["check_out"])
    ]

def assign_inventory_numbers(daily: List[Dict], prop: str):
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
        "La Antilia Luxury": {"all": ["101","201","202","202","203","204","301","302","303","304","401","Day Use 1","Day Use 2","No Show"]},
        "La Tamara Suite": {"all": ["101","102","103","104","201","202","203","204","205","206","Day Use 1","Day Use 2","No Show"]},
        "Le Park Resort": {"all": ["111","222","333","444","555","666","Day Use 1","Day Use 2","No Show"]},
        "Villa Shakti": {"all": ["101","102","201","201A","202","203","301","301A","302","303","401","Day Use 1","Day Use 2","No Show"]},
        "Eden Beach Resort": {"all": ["101","102","103","201","202","Day Use 1","Day Use 2","No Show"]},
        "Le Terra": {"all": ["101","102","103","104","105","106","107","Day Use 1","Day Use 2","No Show"]},
        "La Coromandel Luxury": {"all": ["101","102","103","201","202","203","204","205","206","301","Day Use 1","Day Use 2","No Show"]},
        "Happymates Forest Retreat": {"all": ["101","102","Day Use 1","Day Use 2","No Show"]}
    }
    
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
    assigned, over = assign_inventory_numbers(daily, prop)

    rooms_sold = len(set(b.get("assigned_room") for b in assigned if b.get("assigned_room")))

    check_in_primaries = [
        b for b in assigned
        if b.get("is_primary", True) and date.fromisoformat(b["check_in"]) == day
    ]

    room_charges = gst = commission = 0.0
    
    for b in check_in_primaries:
        is_online = b.get("type") == "online"
        if is_online:
            total_amount = safe_float(b.get("booking_amount"))
            gst += safe_float(b.get("ota_tax"))
            commission += safe_float(b.get("ota_commission"))
            room_charges += total_amount - safe_float(b.get("ota_tax"))
        else:
            room_charges += safe_float(b.get("total_tariff"))

    total = room_charges + gst
    receivable = total - commission
    tax_deduction = receivable * 0.003

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
        "room_charges": room_charges,
        "gst": gst,
        "total": total,
        "commission": commission,
        "tax_deduction": tax_deduction,
        "receivable": receivable,
        "receivable_per_night": daily_per_night_sum,
    }

# -------------------------- Report Builder --------------------------
def build_report(props: List[str], dates: List[date], bookings: Dict[str, List[Dict]], metric: str) -> pd.DataFrame:
    rows = []
    prop_totals = {p: 0.0 for p in props}
    grand_total = 0.0

    for d in dates:
        row = {"Date": d.strftime("%Y-%m-%d")}
        day_sum = 0.0
        for p in props:
            val = compute_daily_metrics(bookings.get(p, []), p, d).get(metric, 0.0)
            short_name = get_short_name(p)
            row[short_name] = val
            day_sum += val
            prop_totals[p] += val
        row["Total"] = day_sum
        grand_total += day_sum
        rows.append(row)

    total_row = {"Date": "Total"}
    for p in props:
        total_row[get_short_name(p)] = prop_totals[p]
    total_row["Total"] = grand_total
    rows.append(total_row)

    return pd.DataFrame(rows)

# -------------------------- Styling Function --------------------------
def style_dataframe_with_highlights(df: pd.DataFrame, metric: str) -> str:
    def is_zero(val):
        try:
            if pd.isna(val): return False
            num = float(str(val).replace(",", ""))
            return abs(num) &lt; 0.01
        except:
            return False

    def is_weekend(row):
        if row["Date"] == "Total":
            return [False] * len(row)
        try:
            d = pd.to_datetime(row["Date"]).date()
            return [d.weekday() >= 5] * len(row)
        except:
            return [False] * len(row)

    # Create styling DataFrame
    styles = pd.DataFrame("", index=df.index, columns=df.columns)

    # Light green background for weekends
    weekend_mask = df.apply(is_weekend, axis=1)
    for idx in weekend_mask.index:
        if any(weekend_mask.loc[idx]):
            styles.loc[idx, :] = "background-color: #d4edda;"

    # Red bold text for zeros (overrides background)
    for col in df.columns:
        if col != "Date":
            styles[col] = df[col].apply(lambda x: "color: red; font-weight: bold;" if is_zero(x) else "")

    # Format numbers
    numeric_cols = [c for c in df.columns if c != "Date"]
    formatter = {col: "{:,.0f}" for col in numeric_cols}

    styled = (
        df.style
        .apply(lambda _: styles, axis=None)
        .format(formatter, na_rep="0")
        .set_table_styles([
            {"selector": "th", "props": "font-weight: bold; text-align: center; background-color: #f0f0f0;"},
            {"selector": "td", "props": "text-align: right; padding: 8px;"},
            {"selector": "td:first-child", "props": "text-align: left; font-weight: bold;"},
            {"selector": "tr:hover", "props": "background-color: #f8f9fa;"},
        ])
        .set_properties(**{"border": "1px solid #ddd"})
    )

    return styled.to_html()

# -------------------------- UI --------------------------
def show_summary_report():
    st.set_page_config(page_title="TIE Summary Report", layout="wide")
    st.title("TIE Hotels & Resort Summary Report")

    today = date.today()
    year = st.selectbox("Year", list(range(today.year - 5, today.year + 6)), index=5)
    month = st.selectbox("Month", list(range(1, 13)), index=today.month - 1)

    properties = load_properties()
    if not properties:
        st.info("No properties found in the database.")
        return

    _, days_in_month = calendar.monthrange(year, month)
    month_dates = [date(year, month, d) for d in range(1, days_in_month + 1)]
    start_date = month_dates[0]
    end_date = month_dates[-1]

    with st.spinner("Loading booking data for all properties..."):
        bookings = {p: load_combined_bookings(p, start_date, end_date) for p in properties}

    report_defs = {
        "rooms_report": ("TIE Hotels & Resort Rooms Report", "rooms_sold"),
        "room_charges_report": ("TIE Hotels & Resort Room Charges Report", "room_charges"),
        "gst_report": ("TIE Hotels & Resort GST Report", "gst"),
        "total_report": ("TIE Hotels & Resort Total Report", "total"),
        "commission_report": ("TIE Hotels & Resort Commission Report", "commission"),
        "tax_deduction_report": ("TIE Hotels & Resort Tax Deduction Report", "tax_deduction"),
        "receivable_report": ("TIE Hotels & Resort Receivable Report", "receivable"),
        "receivable_per_night_report": ("TIE Hotels & Resort Receivable Per Night Report", "receivable_per_night"),
    }

    for key, (title, metric) in report_defs.items():
        st.subheader(title)
        df = build_report(properties, month_dates, bookings, metric)

        # Format monetary values
        if metric != "rooms_sold":
            money_cols = [c for c in df.columns if c != "Date"]
            df[money_cols] = df[money_cols].applymap(lambda x: f"{x:,.0f}" if pd.notna(x) and float(x) != 0 else "0")

        html = style_dataframe_with_highlights(df, metric)
        st.markdown(html, unsafe_allow_html=True)
        st.markdown("---")

# -------------------------- Run --------------------------
if __name__ == "__main__":
    show_summary_report()
