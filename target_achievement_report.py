# target_achievement_report.py
# TRUE FULL-SCREEN + ULTRA COMPACT + NO SCROLLBARS (December 2025)

import streamlit as st
from datetime import date
import pandas as pd
from supabase import create_client, Client
from typing import List, Dict
import os

# =========================== PAGE CONFIG & SESSION STATE ===========================
st.set_page_config(page_title="Target vs Achievement - Dec 2025", layout="wide")

if "fullscreen" not in st.session_state:
    st.session_state.fullscreen = False

# =========================== ULTIMATE FULL-SCREEN CSS + JS ===========================
st.markdown("""
<style>
    /* Remove all Streamlit padding & constraints */
    .main > div {padding: 0rem !important;}
    .block-container {padding: 0rem !important; max-width: none !important;}
    section.main {padding: 0 !important;}
    header {visibility: hidden !important;}
    [data-testid="collapsedControl"] {display: none !important;}

    /* Fullscreen overlay */
    .fullscreen-table {
        position: fixed !important;
        top: 0 !important; left: 0 !important;
        width: 100vw !important; height: 100vh !important;
        background: white !important;
        z-index: 9999 !important;
        padding: 15px !important;
        box-sizing: border-box !important;
        overflow: hidden !important;
    }

    .exit-fullscreen {
        position: fixed;
        top: 20px; right: 30px;
        background: #ff4444;
        color: white;
        padding: 12px 24px;
        border-radius: 50px;
        font-weight: bold;
        font-size: 16px;
        cursor: pointer;
        z-index: 99999;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        user-select: none;
    }

    /* Ultra compact table */
    .fullscreen-table table {
        font-size: 12.8px !important;
        width: 100% !important;
        height: calc(100vh - 30px) !important;
    }

    th {
        background-color: #1e6b4f !important;
        color: white !important;
        font-weight: bold !important;
        position: sticky !important;
        top: 0 !important;
        z-index: 10 !important;
        font-size: 13.5px !important;
    }

    td, th {padding: 5px 8px !important; text-align: center !important;}
    td:nth-child(2), th:nth-child(2) {max-width: 160px; white-space: normal !important;}
</style>
""", unsafe_allow_html=True)

# =========================== SUPABASE CLIENT ===========================
try:
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except:
    try:
        supabase: Client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
    except Exception as e:
        st.error(f"Supabase connection failed: {e}")
        st.stop()

# =========================== PROPERTY MAPPING & TARGETS ===========================
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

# Build reverse mapping
reverse_mapping = {}
for raw, canon in PROPERTY_MAPPING.items():
    reverse_mapping.setdefault(canon, []).append(raw)

DECEMBER_2025_TARGETS = {
    "La Millionaire Resort": 2200000,
    "Le Poshe Beach view": 800000,
    "Le Park Resort": 800000,
    "La Tamara Luxury": 1848000,
    "Le Poshe Luxury": 1144000,
    "La Tamara Suite": 640000,
    "Eden Beach Resort": 438000,
    "La Antilia Luxury": 1075000,
    "La Coromandel Luxury": 800000,
    "La Paradise Luxury": 467000,
    "La Villa Heritage": 467000,
    "La Paradise Residency": 534000,
    "Le Pondy Beachside": 245000,
    "Le Royce Villa": 190000,
}

# Dummy inventory (replace with your real one if needed)
PROPERTY_INVENTORY = {
    prop: {"all": ["101", "102", "103", "201", "202"]} for prop in DECEMBER_2025_TARGETS.keys()
}

def get_total_rooms(prop: str) -> int:
    inv = PROPERTY_INVENTORY.get(prop, {"all": []})
    return len([r for r in inv.get("all", []) if isinstance(r, str)])

# =========================== DATA LOADING FUNCTIONS ===========================
def load_properties() -> List[str]:
    try:
        direct = supabase.table("reservations").select("property_name").execute().data or []
        online = supabase.table("online_reservations").select("property").execute().data or []
        props = {normalize_property_name(r.get("property_name") or r.get("property", "")) for r in direct + online}
        return sorted([p for p in props if p in DECEMBER_2025_TARGETS])
    except:
        return list(DECEMBER_2025_TARGETS.keys())

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
    except:
        return []

def safe_float(v, d=0.0):
    try: return float(v) if v not in [None,""," "] else d
    except: return d

def compute_daily_metrics(bookings: List[Dict], prop: str, day: date) -> Dict:
    daily = [b for b in bookings if b.get("check_in") and b.get("check_out") and
             date.fromisoformat(b["check_in"]) <= day < date.fromisoformat(b["check_out"])]
    used_rooms = set()
    primaries = []
    for b in daily:
        room = str(b.get("room_no") or b.get("room") or "").strip().split(",")[0]
        if room and room not in used_rooms:
            used_rooms.add(room)
            if date.fromisoformat(b["check_in"]) == day:
                primaries.append(b)
    rev = sum(
        safe_float(b.get("total_tariff")) if b.get("type") != "online" else
        safe_float(b.get("booking_amount")) - safe_float(b.get("ota_tax",0)) - safe_float(b.get("ota_commission",0))
        for b in primaries
    )
    return {"rooms_sold": len(used_rooms), "receivable": rev}

# =========================== BUILD REPORT ===========================
def build_report():
    props = load_properties()
    dates = [date(2025,12,d) for d in range(1,32)]
    today = date(2025,12,6)
    past = [d for d in dates if d <= today]
    days_left = len([d for d in dates if d > today])

    rows = []
    totals = {"target":0, "achieved":0, "projected":0, "rooms":0, "sold":0}

    for prop in props:
        target = DECEMBER_2025_TARGETS.get(prop, 0)
        bookings = load_combined_bookings(prop, dates[0], dates[-1])
        achieved = sum(compute_daily_metrics(bookings, prop, d)["receivable"] for d in past)
        projected = sum(compute_daily_metrics(bookings, prop, d)["receivable"] for d in dates)
        sold = sum(compute_daily_metrics(bookings, prop, d)["rooms_sold"] for d in dates)
        rooms = get_total_rooms(prop)
        occ = sold / (rooms * 31) * 100 if rooms else 0

        rows.append({
            "Property": prop,
            "Target": target,
            "Achieved": round(achieved),
            "Balance": target - achieved,
            "% Ach": achieved/target*100 if target else 0,
            "R/N": rooms*31,
            "Sold": sold,
            "Occ %": occ,
            "Revenue": round(projected),
            "ARR": projected/sold if sold else 0,
            "Days Left": days_left,
            "Daily Need": max(target-achieved,0)/days_left if days_left else 0,
            "Focus ARR": projected / (rooms * 31) if rooms else 0
        })
        totals["target"] += target
        totals["achieved"] += achieved
        totals["projected"] += projected
        totals["rooms"] += rooms
        totals["sold"] += sold

    # TOTAL ROW
    total_occ = totals["sold"] / (totals["rooms"] * 31) * 100 if totals["rooms"] else 0
    rows.append({
        "Property": "TOTAL", "Target": totals["target"], "Achieved": totals["achieved"],
        "Balance": totals["target"] - totals["achieved"],
        "% Ach": totals["achieved"]/totals["target"]*100,
        "R/N": totals["rooms"]*31, "Sold": totals["sold"], "Occ %": total_occ,
        "Revenue": totals["projected"], "ARR": totals["projected"]/totals["sold"] if totals["sold"] else 0,
        "Days Left": days_left, "Daily Need": (totals["target"]-totals["achieved"])/days_left if days_left else 0,
        "Focus ARR": totals["projected"] / (totals["rooms"] * 31) if totals["rooms"] else 0
    })

    df = pd.DataFrame(rows)
    df.insert(0, 'S.No', range(1, len(df)+1))
    return df

def style_df(df: pd.DataFrame):
    return df.style.format({
        "Target":"₹{:,.0f}", "Achieved":"₹{:,.0f}", "Balance":"₹{:,.0f}",
        "Revenue":"₹{:,.0f}", "ARR":"₹{:,.0f}", "Daily Need":"₹{:,.0f}", "Focus ARR":"₹{:,.0f}",
        "% Ach":"{:.1f}%", "Occ %":"{:.1f}%"
    }).applymap(lambda v: "color:red;font-weight:bold" if v<0 else "color:green;font-weight:bold", subset=["Balance"])\
     .applymap(lambda v: "color:green;font-weight:bold" if v>=70 else "color:orange" if v>=50 else "color:red", subset=["% Ach"])\
     .set_properties(**{"text-align": "center", "font-size": "12px"})

# =========================== MAIN UI ===========================
st.title("Target vs Achievement – December 2025")

with st.spinner("Fetching latest data from Supabase..."):
    df = build_report()
    styled = style_df(df)

# FULLSCREEN TOGGLE BUTTON
col1, col2, col3 = st.columns([1,2,1])
with col2:
    if st.button("GO FULL SCREEN (TV Dashboard Mode)", type="primary", use_container_width=True):
        st.session_state.fullscreen = True
        st.rerun()

# FULLSCREEN MODE
if st.session_state.fullscreen:
    st.markdown("""
    <div class="fullscreen-table">
        <div class="exit-fullscreen" onclick="parent.document.querySelector('button').click()">✕ Exit Full Screen</div>
    </div>
    """, unsafe_allow_html=True)

    st.dataframe(styled, use_container_width=True, hide_index=True, height=900)

    # Auto exit via JS
    st.components.v1.html("""
    <script>
        document.querySelector('.exit-fullscreen').addEventListener('click', () => {
            fetch("/_"/_stcore/streamlit_rerun");
        });
    </script>
    """, height=0)

else:
    # NORMAL MODE
    st.markdown("### Target Achievement Report")
    st.dataframe(styled, use_container_width=True, hide_index=True, height=680)

    # Summary Cards
    tot = df.iloc[-1]
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Monthly Target", f"₹{tot['Target']:,.0f}")
    with c2: st.metric("Achieved So Far", f"₹{tot['Achieved']:,.0f}", delta=f"{tot['% Ach']:.1f}%")
    with c3: st.metric("Balance to Go", f"₹{tot['Balance']:,.0f}")
    with c4: st.metric("Daily Need (25 days)", f"₹{tot['Daily Need']:,.0f}")

    st.download_button("Download CSV", df.to_csv(index=False).encode(), "target_dec2025.csv", "text/csv")

# Optional: Auto full-screen on load (uncomment for kiosk mode)
# st.components.v1.html("""<script>setTimeout(() => document.querySelector('button[kind="primary"]').click(), 800);</script>""", height=0)
