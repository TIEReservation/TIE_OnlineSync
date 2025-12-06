# target_achievement_report.py
# FINAL BEAUTIFUL VERSION | TINY FULLSCREEN BUTTON TOP-RIGHT | 17 PROPERTIES | LIVE DATA

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

    # BEAUTIFUL MODERN CSS + TINY FULLSCREEN BUTTON
    st.markdown("""
    <style>
        .main {background: #f8f9fa; padding-top: 1rem;}
        .block-container {padding: 1.5rem 2rem !important; max-width: 95% !important;}

        h1 {color: #1e6b4f; text-align: center; font-size: 2.6rem; margin-bottom: 0.5rem;}
        .subtitle {text-align: center; color: #555; font-size: 1.2rem; margin-bottom: 2rem;}

        /* Tiny Fullscreen Button - Top Right Corner */
        .fs-button {
            position: fixed !important;
            top: 20px !important;
            right: 30px !important;
            z-index: 99999 !important;
            background: #1e6b4f !important;
            color: white !important;
            border: none !important;
            padding: 10px 18px !important;
            border-radius: 10px !important;
            font-size: 14px !important;
            font-weight: 600 !important;
            cursor: pointer !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
            transition: all 0.3s;
        }
        .fs-button:hover {
            background: #165c42 !important;
            transform: translateY(-2px);
        }

        /* Fullscreen Mode */
        .fullscreen-overlay {
            position: fixed !important;
            top: 0; left: 0;
            width: 100vw !important;
            height: 100vh !important;
            background: white !important;
            z-index: 9998 !important;
            padding: 40px !important;
            box-sizing: border-box !important;
            overflow-y: auto;
        }
        .exit-fullscreen {
            position: fixed;
            top: 25px;
            right: 35px;
            background: #d32f2f;
            color: white;
            padding: 14px 28px;
            border-radius: 50px;
            font-weight: bold;
            font-size: 16px;
            cursor: pointer;
            z-index: 99999;
            box-shadow: 0 6px 20px rgba(0,0,0,0.3);
        }

        /* Table Styling */
        th {
            background: #1e6b4f !important;
            color: white !important;
            font-weight: 600 !important;
            padding: 14px 10px !important;
            font-size: 14px !important;
        }
        td {
            padding: 12px 10px !important;
            font-size: 13.5px !important;
            text-align: center;
        }
        td:nth-child(2) {text-align: left !important; font-weight: 500;}
        tr:hover {background: #e8f5f0 !important;
        .dataframe {border-radius: 12px; overflow: hidden; box-shadow: 0 8px 30px rgba(0,0,0,0.12);}
    </style>
    """, unsafe_allow_html=True)

    # SUPABASE CONNECTION
    try:
        supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
    except:
        try:
            supabase: Client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
        except Exception as e:
            st.error(f"Cannot connect to database: {e}")
            st.stop()

    # ALL 17 PROPERTIES WITH CORRECT TARGETS
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

    # PROPERTY NAME MAPPING
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
        return PROPERTY_MAPPING.get(name.strip(), name.strip())

    # Reverse mapping for queries
    reverse_mapping = {}
    for canon in DECEMBER_2025_TARGETS:
        reverse_mapping[canon] = [canon]
    for raw, canon in PROPERTY_MAPPING.items():
        if canon in reverse_mapping:
            reverse_mapping[canon].append(raw)

    # Dummy room count (30 rooms per property)
    def get_total_rooms(prop: str) -> int:
        return 30

    # Load bookings for a property
    def load_bookings(prop: str) -> List[Dict]:
        names = reverse_mapping.get(prop, [prop])
        try:
            direct = supabase.table("reservations").select("*")\
                .in_("property_name", names)\
                .lte("check_in", "2025-12-31")\
                .gte("check_out", "2025-12-01")\
                .in_("plan_status", ["Confirmed", "Completed"])\
                .in_("payment_status", ["Partially Paid", "Fully Paid"])\
                .execute().data or []

            online = supabase.table("online_reservations").select("*")\
                .in_("property", names)\
                .lte("check_in", "2025-12-31")\
                .gte("check_out", "2025-12-01")\
                .in_("booking_status", ["Confirmed", "Completed"])\
                .in_("payment_status", ["Partially Paid", "Fully Paid"])\
                .execute().data or []

            return [b for b in direct + online if normalize_property_name(b.get("property_name") or b.get("property") or "") == prop]
        except:
            return []

    # Calculate revenue for arrival day only
    def calculate_arrival_revenue(bookings: List[Dict]) -> float:
        total = 0.0
        for b in bookings:
            if b.get("check_in", "").startswith("2025-12") and int(b["check_in"].split("-")[2]) <= 6:  # up to 6th
                amt = b.get("total_tariff") or b.get("booking_amount", 0)
                tax = b.get("ota_tax", 0)
                comm = b.get("ota_commission", 0)
                net = float(amt or 0) - float(tax or 0) - float(comm or 0)
                total += net
        return total

    # BUILD REPORT
    @st.cache_data(ttl=300)  # Refresh every 5 minutes
    def build_report():
        rows = []
        total_target = 0
        total_achieved = 0

        for i, (prop, target) in enumerate(DECEMBER_2025_TARGETS.items(), 1):
            bookings = load_bookings(prop)
            achieved = calculate_arrival_revenue(bookings)

            balance = target - achieved
            pct_ach = (achieved / target * 100) if target else 0
            rooms_total = get_total_rooms(prop) * 31
            sold = len(bookings)
            occ = (sold / rooms_total * 100) if rooms_total else 0

            rows.append({
                "S.No": i,
                "Property": prop,
                "Target": f"₹{target:,.0f}",
                "Achieved": f"₹{achieved:,.0f}",
                "Balance": f"₹{balance:,.0f}",
                "% Ach": f"{pct_ach:.1f}%",
                "R/N": rooms_total,
                "Sold": sold,
                "Occ %": f"{occ:.1f}%",
                "Revenue": f"₹{achieved:,.0f}",
                "ARR": f"₹{int(achieved/max(1,sold)):,.0f}" if sold else "₹0",
                "Daily Need": f"₹{int(balance / 25):,.0f}" if balance > 0 else "₹0"
            })

            total_target += target
            total_achieved += achieved

        # TOTAL ROW
        total_balance = total_target - total_achieved
        total_pct = (total_achieved / total_target * 100) if total_target else 0
        rows.append({
            "S.No": "",
            "Property": "<strong>TOTAL</strong>",
            "Target": f"<strong>₹{total_target:,.0f}</strong>",
            "Achieved": f"<strong>₹{total_achieved:,.0f}</strong>",
            "Balance": f"<strong>₹{total_balance:,.0f}</strong>",
            "% Ach": f"<strong>{total_pct:.1f}%</strong>",
            "R/N": "<strong>15,810</strong>",
            "Sold": "",
            "Occ %": "",
            "Revenue": "",
            "ARR": "",
            "Daily Need": f"<strong>₹{int(total_balance / 25):,.0f}</strong>"
        })

        return pd.DataFrame(rows)

    # UI LOGIC
    if st.session_state.fullscreen:
        # FULLSCREEN MODE
        st.markdown('<div class="fullscreen-overlay">', unsafe_allow_html=True)
        st.markdown('<div class="exit-fullscreen" onclick="location.reload()">Exit Full Screen</div>', unsafe_allow_html=True)

        st.markdown("<h1 style='text-align:center; margin-top:20px; color:#1e6b4f;'>Target vs Achievement – December 2025</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; font-size:1.3rem; color:#555;'>Live Data • Updated every 5 minutes</p>", unsafe_allow_html=True)

        df = build_report()
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown('</div>', unsafe_allow_html=True)

    else:
        # NORMAL MODE WITH TINY BUTTON
        st.markdown("<h1>Target vs Achievement Dashboard</h1>", unsafe_allow_html=True)
        st.markdown("<div class='subtitle'>December 2025 • Live from Supabase</div>", unsafe_allow_html=True)

        # TINY FULLSCREEN BUTTON (TOP RIGHT)
        st.markdown("""
        <button class="fs-button" id="fsBtn">Full Screen</button>
        <script>
            document.getElementById('fsBtn').addEventListener('click', () => {
                window.location.href = window.location.href + '?fs=1';
            });
        </script>
        """, unsafe_allow_html=True)

        # Hidden trigger
        if st.button("Go Fullscreen", key="trigger_fs", help="Hidden"):
            st.session_state.fullscreen = True
            st.rerun()

        # Show report
        df = build_report()
        st.dataframe(df, use_container_width=True, hide_index=True, height=750)

        # Summary Cards
        total_target = sum(DECEMBER_2025_TARGETS.values())
        total_achieved = sum(calculate_arrival_revenue(load_bookings(p)) for p in DECEMBER_2025_TARGETS)
        balance = total_target - total_achieved
        daily_need = int(balance / 25)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Monthly Target", f"₹{total_target:,.0f}")
        col2.metric("Achieved So Far", f"₹{total_achieved:,.0f}", f"{(total_achieved/total_target*100):.1f}%")
        col3.metric("Still Required", f"₹{balance:,.0f}")
        col4.metric("Daily Need (25 days)", f"₹{daily_need:,.0f}")

        st.caption("Dashboard auto-refreshes every 5 minutes • Data directly from Supabase")

# REQUIRED FOR MULTI-PAGE APPS
__all__ = ["show_target_achievement_report"]

# Run standalone
if __name__ == "__main__":
    show_target_achievement_report()
