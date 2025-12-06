# target_achievement_report.py - FULL SCREEN + NO SCROLLBARS + ULTRA COMPACT
import streamlit as st
from datetime import date
import calendar
import pandas as pd
from supabase import create_client, Client
from typing import List, Dict
import os

# =========================== FULL SCREEN + NO SCROLLBARS ===========================
st.set_page_config(page_title="Target vs Achievement", layout="wide")

# Custom CSS - Ultra compact + full-screen perfection
st.markdown("""
<style>
    /* Remove all padding/margin */
    .main > div {padding: 0.5rem !important;}
    .block-container {padding: 0.5rem !important;}
    
    /* Full-screen table when expanded */
    [data-testid="stDataFrame"] {
        width: 100% !important;
    }
    
    /* Ultra-compact table */
    .dataframe-container {
        width: 100%;
        overflow: hidden !important;
        border-radius: 10px;
        border: 1px solid #ddd;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    /* Tiny rows - fits 25+ properties */
    th, td {
        padding: 4px 7px !important;
        font-size: 11.5px !important;
        line-height: 1.3 !important;
        text-align: center !important;
    }
    
    th {
        background-color: #1e6b4f !important;
        color: white !important;
        font-weight: bold !important;
        font-size: 11.8px !important;
        position: sticky;
        top: 0;
        z-index: 10;
    }
    
    /* Property name wrap */
    td:nth-child(2), th:nth-child(2) {
        max-width: 140px;
        white-space: normal !important;
        word-wrap: break-word;
    }
    
    /* When in full-screen mode - remove all scroll */
    section[data-testid="stFullscreen"] .dataframe-container {
        height: calc(100vh - 120px) !important;
        overflow: hidden !important;
    }
    
    section[data-testid="stFullscreen"] table {
        font-size: 12px !important;
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
        st.error(f"Supabase error: {e}")
        st.stop()

# -------------------------- Property Mapping (100% FIXED) --------------------------
PROPERTY_MAPPING = {
    "La Millionaire Luxury Resort": "La Millionaire Resort",
    "Le Poshe Beach View": "Le Poshe Beach view", "Le Poshe Beach view": "Le Poshe Beach view",
    "Le Poshe Beach VIEW": "Le Poshe Beach view", "Le Poshe Beachview": "Le Poshe Beach view",
    "Millionaire": "La Millionaire Resort", "Le Pondy Beach Side": "Le Pondy Beachside",
    "Le Teera": "Le Terra", "La Millionaire Resort": "La Millionaire Resort",
    "Le Pondy Beachside": "Le Pondy Beachside", "Le Terra": "Le Terra"
}

def normalize_property_name(p: str) -> str:
    return PROPERTY_MAPPING.get(p.strip() if p and isinstance(p, str) else "", p.strip() if p and isinstance(p, str) else "")

reverse_mapping = {}
for raw, canon in PROPERTY_MAPPING.items():
    reverse_mapping.setdefault(canon, []).append(raw)

# -------------------------- Targets & Inventory --------------------------
DECEMBER_2025_TARGETS = {
    "La Millionaire Resort": 2200000, "Le Poshe Beach view": 800000, "Le Park Resort": 800000,
    "La Tamara Luxury": 1848000, "Le Poshe Luxury": 1144000, "Le Poshe Suite": 475000,
    "Eden Beach Resort": 438000, "La Antilia Luxury": 1075000, "La Coromandel Luxury": 800000,
    "La Tamara Suite": 640000, "Villa Shakti": 652000, "La Paradise Luxury": 467000,
    "La Villa Heritage": 467000, "La Paradise Residency": 534000, "Le Pondy Beachside": 245000,
    "Le Royce Villa": 190000,
}

PROPERTY_INVENTORY = { ... }  # Your full inventory

def get_total_rooms(prop: str) -> int:
    inv = PROPERTY_INVENTORY.get(prop, {"all": []})
    return len([r for r in inv.get("all", []) if isinstance(r, str) and not r.startswith(("Day Use", "No Show"))])

# -------------------------- Core Functions (safe & fast) --------------------------
def load_properties() -> List[str]:
    try:
        direct = supabase.table("reservations").select("property_name").execute().data or []
        online = supabase.table("online_reservations").select("property").execute().data or []
        props = {normalize_property_name(r.get("property_name") or r.get("property", "")) for r in direct + online}
        return sorted([p for p in props if p in DECEMBER_2025_TARGETS])
    except: return []

def load_combined_bookings(prop: str, start: date, end: date) -> List[Dict]:
    norm = normalize_property_name(prop)
    query = reverse_mapping.get(norm, [norm])
    try:
        direct = supabase.table("reservations").select("*").in_("property_name", query)\
                 .lte("check_in", str(end)).gte("check_out", str(start))\
                 .in_("plan_status", ["Confirmed","Completed"])\
                 .in_("payment_status", ["Partially Paid","Fully Paid"]).execute().data or []
        online = supabase.table("online_reservations").select("*").in_("property", query)\
                 .lte("check_in", str(end)).gte("check_out", str(start))\
                 .in_("booking_status", ["Confirmed","Completed"])\
                 .in_("payment_status", ["Partially Paid","Fully Paid"]).execute().data or []
        return [b for b in direct + online if normalize_property_name(b.get("property_name") or b.get("property") or "") == norm]
    except: return []

def compute_daily_metrics(bookings: List[Dict], prop: str, day: date) -> Dict:
    daily = [b for b in bookings if b.get("check_in") and b.get("check_out") and date.fromisoformat(b["check_in"]) <= day < date.fromisoformat(b["check_out"])]
    assigned = []
    used = set()
    for b in daily:
        room = str(b.get("room_no") or "").strip().split(",")[0]
        if room and room not in used:
            used.add(room)
            assigned.append(b)
    primaries = [b for b in assigned if date.fromisoformat(b["check_in"]) == day]
    rev = sum(
        safe_float(b.get("total_tariff")) if b.get("type") != "online" else
        safe_float(b.get("booking_amount")) - safe_float(b.get("ota_tax",0)) - safe_float(b.get("ota_commission",0))
        for b in primaries
    )
    return {"rooms_sold": len(used), "receivable": rev}

def safe_float(v, d=0.0):
    try: return float(v) if v not in [None,""," "] else d
    except: return d

# -------------------------- Report Builder --------------------------
def build_report():
    props = load_properties()
    dates = [date(2025,12,d) for d in range(1,32)]
    today = date(2025,12,6)
    past = [d for d in dates if d <= today]
    days_left = len([d for d in dates if d > today])

    rows = []
    totals = {"target":0, "achieved":0, "projected":0, "rooms":0, "sold":0}

    for prop in props:
        target = DECEMBER_2025_TARGETS[prop]
        bookings = load_combined_bookings(prop, dates[0], dates[-1])
        achieved = sum(compute_daily_metrics(bookings, prop, d)["receivable"] for d in past)
        projected = sum(compute_daily_metrics(bookings, prop, d)["receivable"] for d in dates)
        sold = sum(compute_daily_metrics(bookings, prop, d)["rooms_sold"] for d in dates)
        rooms = get_total_rooms(prop)
        occ = sold / (rooms * 31) * 100 if rooms else 0

        rows.append({
            "Property": prop,
            "Target": target,
            "Achieved": achieved,
            "Balance": target - achieved,
            "% Ach": achieved/target*100 if target else 0,
            "R/N": rooms*31,
            "Sold": sold,
            "Occ %": occ,
            "Revenue": projected,
            "ARR": projected/sold if sold else 0,
            "Days Left": days_left,
            "Daily Need": max(target-achieved,0)/days_left if days_left else 0
        })
        totals["target"] += target
        totals["achieved"] += achieved
        totals["projected"] += projected
        totals["rooms"] += rooms
        totals["sold"] += sold

    # TOTAL
    rows.append({
        "Property": "TOTAL", "Target": totals["target"], "Achieved": totals["achieved"],
        "Balance": totals["target"]-totals["achieved"], "% Ach": totals["achieved"]/totals["target"]*100,
        "R/N": totals["rooms"]*31, "Sold": totals["sold"], "Occ %": totals["sold"]/(totals["rooms"]*31)*100,
        "Revenue": totals["projected"], "ARR": totals["projected"]/totals["sold"] if totals["sold"] else 0,
        "Days Left": days_left, "Daily Need": max(totals["target"]-totals["achieved"],0)/days_left if days_left else 0
    })

    df = pd.DataFrame(rows)
    df.insert(0, '#', range(1, len(df)+1))
    return df

def style_df(df):
    return df.style\
        .format({"Target":"₹{:.0f}","Achieved":"₹{:.0f}","Balance":"₹{:.0f}","Revenue":"₹{:.0f}",
                 "ARR":"₹{:.0f}","Daily Need":"₹{:.0f}","% Ach":"{:.0f}%","Occ %":"{:.0f}%","R/N":"{:.0f}","Sold":"{:.0f}","Days Left":"{:.0f}"})\
        .applymap(lambda v: "color:green;font-weight:bold" if v>=0 else "color:red;font-weight:bold", subset=["Balance"])\
        .applymap(lambda v: "color:green;font-weight:bold" if v>=70 else "color:orange" if v>=50 else "color:red;font-weight:bold", subset=["% Ach","Occ %"])\
        .set_properties(**{"font-size":"11.5px","padding":"4px 7px"})

# -------------------------- UI --------------------------
st.title("Target vs Achievement – December 2025")

with st.spinner("Loading data..."):
    df = build_report()
    styled = style_df(df)

st.markdown("### Target Achievement Report")

# THIS IS THE KEY: The table with full-screen button that removes scroll
st.markdown('<div class="dataframe-container">', unsafe_allow_html=True)
st.dataframe(
    styled,
    use_container_width=True,
    hide_index=True,
    height=620  # Perfect for 20+ rows - no vertical scroll even in normal view
)
st.markdown('</div>', unsafe_allow_html=True)

# Summary Cards
tot = df.iloc[-1]
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("Target", f"₹{tot['Target']:,.0f}")
with c2: st.metric("Achieved", f"₹{tot['Achieved']:,.0f}", delta=f"₹{tot['Balance']:,.0f}")
with c3: st.metric("Balance to Go", f"₹{tot['Balance']:,.0f}")
with c4: st.metric("Daily Need", f"₹{tot['Daily Need']:,.0f}")

st.download_button("Download CSV", df.to_csv(index=False), "target_dec2025.csv", "text/csv")
