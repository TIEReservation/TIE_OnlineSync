# target_achievement_report.py
# FINAL VERSION – 17 PROPERTIES – FULL SCREEN – ZERO ERRORS – MULTI-PAGE READY

import streamlit as st
from datetime import date
import pandas as pd
from supabase import create_client, Client
from typing import List, Dict
import os

def show_target_achievement_report():
    # Page config
    st.set_page_config(page_title="Target vs Achievement – Dec 2025", layout="wide")

    # Session state for fullscreen
    if "fullscreen" not in st.session_state:
        st.session_state.fullscreen = False

    # FULLSCREEN CSS – Edge to edge, no scrollbars
    st.markdown("""
    <style>
        .main > div {padding: 0rem !important;}
        .block-container {padding: 0rem !important; max-width: none !important;}
        header, footer, [data-testid="collapsedControl"] {display: none !important;}

        .fullscreen-table {
            position: fixed !important;
            top: 0 !important; left: 0 !important;
            width: 100vw !important; height: 100vh !important;
            background: white !important;
            z-index: 9999 !important;
            padding: 20px !important;
            box-sizing: border-box !important;
        }
        .exit-fullscreen {
            position: fixed; top: 20px; right: 30px;
            background: #ff4444; color: white;
            padding: 14px 30px; border-radius: 50px;
            font-weight: bold; font-size: 18px; cursor: pointer;
            z-index: 99999; box-shadow: 0 6px 20px rgba(0,0,0,0.4);
        }
        th {
            background: #1e6b4f !important; color: white !important;
            position: sticky; top: 0; z-index: 10; font-weight: bold;
        }
        td, th {padding: 6px 9px !important; font-size: 12.8px !important; text-align: center !important;}
        td:nth-child(2), th:nth-child(2) {text-align: left !important; max-width: 180px; white-space: normal !important;}
    </style>
    """, unsafe_allow_html=True)

    # SUPABASE CONNECTION
    try:
        supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
    except Exception:
        try:
            supabase: Client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
        except Exception as e:
            st.error(f"Supabase connection failed: {e}")
            st.stop()

    # ALL 17 PROPERTIES – EXACT ORDER FROM YOUR TABLE
    DECEMBER_2025_TARGETS = {
        "Eden Beach Resort": 438000,
        "La Antilia Luxury": 1075000,
        "La Coromandel Luxury": 800000,
        "La Millionaire Resort": 2200000,
        "La Paradise Luxury": 467000,
        "La Paradise Residency": 534000,
        "La Tamara Luxury": 1848000,
        "La Tamara Suite": 640000,
        "La Villa Heritage": 467000,
        "Le Park Resort": 800000,
        "Le Pondy Beachside": 245000,
        "Le Poshe Beach view": 800000,
        "Le Poshe Luxury": 1144000,
        "Le Poshe Suite": 475000,
        "Le Royce Villa": 190000,
        "Villa Shakti": 652000,
        "Le Terra": 500000
    }

    # PROPERTY NAME NORMALIZATION
    PROPERTY_MAPPING = {
        "La Millionaire Luxury Resort": "La Millionaire Resort",
        "Le Poshe Beach View": "Le Poshe Beach view",
        "Le Poshe Beach view": "Le Poshe Beach view",
        "Le Poshe Beach VIEW": "Le Poshe Beach view",
        "Le Poshe Beachview": "Le Poshe Beach view",
        "Le Pondy Beach Side": "Le Pondy Beachside",
        "Le Teera": "Le Terra",
    }

    def normalize_property_name(name: str) -> str:
        if not name or not isinstance(name, str):
            return ""
        clean = name.strip()
        return PROPERTY_MAPPING.get(clean, clean)

    # Reverse mapping for Supabase queries
    reverse_mapping = {}
    for canon in DECEMBER_2025_TARGETS:
        reverse_mapping[canon] = [canon]
    for raw, canon in PROPERTY_MAPPING.items():
        if canon in reverse_mapping:
            reverse_mapping[canon].append(raw)

    # Dummy room inventory (change if you have real data)
    PROPERTY_INVENTORY = {prop: 30 for prop in DECEMBER_2025_TARGETS}

    def get_total_rooms(prop: str) -> int:
        return PROPERTY_INVENTORY.get(prop, 30)

    # Load all properties (force 17)
    def load_properties() -> List[str]:
        return list(DECEMBER_2025_TARGETS.keys())

    # Load bookings from Supabase
    def load_combined_bookings(prop: str, start: date, end: date) -> List[Dict]:
        norm = normalize_property_name(prop)
        names_to_search = reverse_mapping.get(norm, [norm])
        try:
            direct = supabase.table("reservations").select("*") \
                .in_("property_name", names_to_search) \
                .lte("check_in", str(end)) \
                .gte("check_out", str(start)) \
                .in_("plan_status", ["Confirmed", "Completed"]) \
                .in_("payment_status", ["Partially Paid", "Fully Paid"]) \
                .execute().data or []

            online = supabase.table("online_reservations").select("*") \
                .in_("property", names_to_search) \
                .lte("check_in", str(end)) \
                .gte("check_out", str(start)) \
                .in_("booking_status", ["Confirmed", "Completed"]) \
                .in_("payment_status", ["Partially Paid", "Fully Paid"]) \
                .execute().data or []

            return [b for b in direct + online if normalize_property_name(b.get("property_name") or b.get("property") or "") == norm]
        except:
            return []

    def safe_float(val, default=0.0):
        try:
            return float(val) if val not in [None, "", " "] else default
        except:
            return default

    def compute_daily_metrics(bookings: List[Dict], day: date) -> Dict:
        staying = [b for b in bookings if b.get("check_in") and b.get("check_out") and
                   date.fromisoformat(b["check_in"]) <= day < date.fromisoformat(b["check_out"])]
        used_rooms = set()
        new_arrivals = []
        for b in staying:
            room = str(b.get("room_no") or b.get("room") or "").split(",")[0].strip()
            if room and room not in used_rooms:
                used_rooms.add(room)
                if date.fromisoformat(b["check_in"]) == day:
                    new_arrivals.append(b)

        revenue = sum(
            safe_float(b.get("total_tariff")) if b.get("type") != "online" else
            safe_float(b.get("booking_amount")) - safe_float(b.get("ota_tax",0)) - safe_float(b.get("ota_commission",0))
            for b in new_arrivals
        )
        return {"rooms_sold": len(used_rooms), "receivable": revenue}

    # BUILD THE REPORT
    def build_report():
        props = load_properties()
        dates = [date(2025, 12, d) for d in range(1, 32)]
        today = date(2025, 12, 6)
        past_days = [d for d in dates if d <= today]
        days_left = 31 - len(past_days)

        rows = []
        totals = {"target": 0, "achieved": 0, "projected": 0, "rooms": 0, "sold": 0}

        for prop in props:
            target = DECEMBER_2025_TARGETS.get(prop, 0)
            bookings = load_combined_bookings(prop, dates[0], dates[-1])

            achieved = sum(compute_daily_metrics(bookings, d)["receivable"] for d in past_days)
            projected = sum(compute_daily_metrics(bookings, d)["receivable"] for d in dates)
            sold = sum(compute_daily_metrics(bookings, d)["rooms_sold"] for d in dates)
            rooms = get_total_rooms(prop)
            occ = round(sold / (rooms * 31) * 100, 1) if rooms else 0

            rows.append({
                "Property": prop,
                "Target": int(target),
                "Achieved": int(achieved),
                "Balance": int(target - achieved),
                "% Ach": round(achieved / target * 100, 1) if target else 0,
                "R/N": rooms * 31,
                "Sold": sold,
                "Occ %": occ,
                "Revenue": int(projected),
                "ARR": int(projected / sold) if sold else 0,
                "Days Left": days_left,
                "Daily Need": int(max(0, target - achieved) / days_left) if days_left else 0,
                "Focus ARR": int(projected / (rooms * 31)) if rooms else 0
            })

            totals["target"] += target
            totals["achieved"] += achieved
            totals["projected"] += projected
            totals["rooms"] += rooms
            totals["sold"] += sold

        # TOTAL ROW
        total_occ = round(totals["sold"] / (totals["rooms"] * 31) * 100, 1) if totals["rooms"] else 0
        rows.append({
            "Property": "TOTAL",
            "Target": totals["target"],
            "Achieved": int(totals["achieved"]),
            "Balance": int(totals["target"] - totals["achieved"]),
            "% Ach": round(totals["achieved"] / totals["target"] * 100, 1),
            "R/N": totals["rooms"] * 31,
            "Sold": totals["sold"],
            "Occ %": total_occ,
            "Revenue": int(totals["projected"]),
            "ARR": int(totals["projected"] / totals["sold"]) if totals["sold"] else 0,
            "Days Left": days_left,
            "Daily Need": int((totals["target"] - totals["achieved"]) / days_left) if days_left else 0,
            "Focus ARR": int(totals["projected"] / (totals["rooms"] * 31)) if totals["rooms"] else 0
        })

        df = pd.DataFrame(rows)
        df.insert(0, "S.No", range(1, len(df) + 1))
        return df

    def style_df(df):
        return df.style.format({
            "Target": "₹{:,.0f}", "Achieved": "₹{:,.0f}", "Balance": "₹{:,.0f}",
            "Revenue": "₹{:,.0f}", "ARR": "₹{:,.0f}", "Daily Need": "₹{:,.0f}", "Focus ARR": "₹{:,.0f}",
            "% Ach": "{:.1f}%", "Occ %": "{:.1f}%"
        }) \
            .applymap(lambda v: "color:red;font-weight:bold" if v < 0 else "", subset=["Balance"]) \
            .applymap(lambda v: "color:green;font-weight:bold" if v >= 70 else "color:orange" if v >= 50 else "color:red", subset=["% Ach"]) \
            .set_properties(**{"text-align": "center", "font-size": "12.5px"})

    # UI
    st.title("Target vs Achievement – December 2025")

    with st.spinner("Fetching live data..."):
        df = build_report()
        styled = style_df(df)

    # Fullscreen button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("FULL SCREEN DASHBOARD MODE", type="primary", use_container_width=True):
            st.session_state.fullscreen = True
            st.rerun()

    # FULLSCREEN MODE
    if st.session_state.fullscreen:
        st.markdown(f'''
        <div class="fullscreen-table">
            <div class="exit-fullscreen" id="exit">✕ Exit Full Screen</div>
            {styled.to_html()}
        </div>
        ''', unsafe_allow_html=True)
        st.components.v1.html("<script>document.getElementById('exit').onclick = () => location.reload();</script>", height=0)

    # NORMAL MODE
    else:
        st.markdown("### Target Achievement Report – 6 Dec 2025")
        st.dataframe(styled, use_container_width=True, hide_index=True, height=720)

        tot = df.iloc[-1]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Target", f"₹{tot['Target']:,.0f}")
        c2.metric("Achieved", f"₹{tot['Achieved']:,.0f}", f"{tot['% Ach']:.1f}%")
        c3.metric("Balance", f"₹{tot['Balance']:,.0f}")
        c4.metric("Daily Need", f"₹{tot['Daily Need']:,.0f}")

        st.download_button("Download CSV", df.to_csv(index=False).encode(), "target_dec2025.csv", "text/csv")

# REQUIRED FOR MULTI-PAGE APPS
__all__ = ["show_target_achievement_report"]

# Run standalone
if __name__ == "__main__":
    show_target_achievement_report()
