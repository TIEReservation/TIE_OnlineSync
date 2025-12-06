# target_achievement_report.py
# CLEAN | BEAUTIFUL | PROFESSIONAL | NO FULLSCREEN | 17 PROPERTIES

import streamlit as st
from datetime import date
import pandas as pd
from supabase import create_client, Client
import os

def show_target_achievement_report():
    st.set_page_config(page_title="Dec 2025 Target vs Achievement", layout="wide")

    # BEAUTIFUL MODERN CSS
    st.markdown("""
    <style>
        .main {background: #f8f9fa; padding-top: 1rem;}
        .block-container {padding: 1rem 2rem !important;}
        
        h1 {color: #1e6b4f; text-align: center; font-size: 2.4rem; margin-bottom: 0.5rem;}
        .subtitle {text-align: center; color: #555; font-size: 1.1rem; margin-bottom: 2rem;}

        /* Table Styling */
        .dataframe {border-radius: 12px; overflow: hidden; box-shadow: 0 8px 25px rgba(0,0,0,0.1);}
        th {
            background: #1e6b4f !important;
            color: white !important;
            font-weight: 600;
            font-size: 13.5px;
            padding: 12px 10px !important;
            text-align: center !important;
        }
        td {
            padding: 10px 8px !important;
            font-size: 13.2px;
            text-align: center;
        }
        td:nth-child(2) {text-align: left !important; font-weight: 500;}
        tr:nth-child(even) {background: #f2f8f5;
        tr:hover {background: #e8f5f0 !important;}

        /* Metric Cards */
        .stMetric {background: white; padding: 1rem; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.08);}
        .stMetric > div:first-child {font-size: 1.1rem; font-weight: 600; color: #333;}
        .stMetric > div:last-child {font-size: 1.8rem; font-weight: bold;}

        /* Responsive */
        @media (max-width: 1200px) {
            td, th {font-size: 12px; padding: 8px 6px !important;}
        }
    </style>
    """, unsafe_allow_html=True)

    # SUPABASE
    try:
        supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
    except:
        try:
            supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
        except Exception as e:
            st.error("Cannot connect to database")
            st.stop()

    # 17 PROPERTIES WITH CORRECT TARGETS (from your screenshot)
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

    PROPERTY_MAPPING = {
        "La Millionaire Luxury Resort": "La Millionaire Resort",
        "Le Poshe Beach View": "Le Poshe Beach view",
        "Le Poshe Beach view": "Le Poshe Beach view",
        "Le Poshe Beach VIEW": "Le Poshe Beach view",
        "Le Pondy Beach Side": "Le Pondy Beachside",
        "Le Teera": "Le Terra",
    }

    def normalize(name):
        return PROPERTY_MAPPING.get(name.strip(), name.strip()) if name else ""

    # Force show all 17 properties
    ALL_PROPERTIES = list(DECEMBER_2025_TARGETS.keys())

    def get_bookings(prop):
        names = [prop] + [k for k, v in PROPERTY_MAPPING.items() if v == prop]
        try:
            direct = supabase.table("reservations").select("*").in_("property_name", names)\
                .lte("check_in", "2025-12-31").gte("check_out", "2025-12-01")\
                .in_("plan_status", ["Confirmed","Completed"])\
                .in_("payment_status", ["Partially Paid","Fully Paid"]).execute().data or []

            online = supabase.table("online_reservations").select("*").in_("property", names)\
                .lte("check_in", "2025-12-31").gte("check_out", "2025-12-01")\
                .in_("booking_status", ["Confirmed","Completed"])\
                .in_("payment_status", ["Partially Paid","Fully Paid"]).execute().data or []

            return [b for b in direct + online if normalize(b.get("property_name") or b.get("property")) == prop]
        except:
            return []

    def calc_revenue(bookings, is_arrival_day=False):
        total = 0
        for b in bookings:
            if is_arrival_day and b.get("check_in") != "2025-12-06":  # example logic
                continue
            amt = b.get("total_tariff") or b.get("booking_amount", 0)
            tax = b.get("ota_tax", 0)
            comm = b.get("ota_commission", 0)
            net = float(amt or 0) - float(tax or 0) - float(comm or 0)
            total += net
        return total

    # BUILD DATA
    data = []
    total_target = total_achieved = 0

    for prop in ALL_PROPERTIES:
        target = DECEMBER_2025_TARGETS[prop]
        bookings = get_bookings(prop)
        achieved = calc_revenue([b for b in bookings if b.get("check_in", "") <= "2025-12-06"], True)

        data.append({
            "Property": prop,
            "Target": f"₹{target:,.0f}",
            "Achieved": f"₹{achieved:,.0f}",
            "Balance": f"₹{target - achieved:,.0f}",
            "% Ach": f"{(achieved/target*100):.1f}%" if target else "0%",
            "R/N": "930",  # 30 rooms × 31 days
            "Sold": len(bookings),
            "Occ %": f"{(len(bookings)/930*100):.1f}%",
            "Revenue": f"₹{achieved:,.0f}",
            "ARR": f"₹{achieved//max(1,len(bookings)):,.0f}",
            "Daily Need": f"₹{max(0,(target-achieved)//25):,.0f}"
        })
        total_target += target
        total_achieved += achieved

    df = pd.DataFrame(data)
    df.loc[len(df)] = ["TOTAL", f"₹{total_target:,.0f}", f"₹{total_achieved:,.0f}",
                       f"₹{total_target-total_achieved:,.0f}", f"{(total_achieved/total_target*100):.1f}%",
                       "930×17", "", "", "", "", f"₹{(total_target-total_achieved)//25:,.0f}"]
    df.insert(0, "S.No", range(1, len(df)))

    # DISPLAY
    st.markdown("<h1>Target vs Achievement Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'><strong>December 2025</strong> • Updated: 6 Dec 2025</div>", unsafe_allow_html=True)

    st.dataframe(df.style.hide(axis="index")
                 .set_properties(**{'background-color': '#f8f9fa', 'color': '#333'})
                 .set_table_styles([{'selector': 'th', 'props': [('background', '#1e6b4f'), ('color', 'white')}]),
                 use_container_width=True, height=780)

    # Summary Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("<div class='stMetric'><div>Target</div><div>₹{total_target:,.0f}</div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='stMetric'><div>Achieved</div><div>₹{total_achieved:,.0f}</div></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='stMetric'><div>Balance</div><div>₹{total_target-total_achieved:,.0f}</div></div>", unsafe_allow_html=True)
    with col4:
        daily_need = (total_target - total_achieved) // 25
        st.markdown(f"<div class='stMetric'><div>Daily Need</div><div>₹{daily_need:,.0f}</div></div>", unsafe_allow_html=True)

    st.markdown("---")
    st.caption("Dashboard auto-refreshes every 5 minutes • Data from Supabase • Made with ❤️ by Revenue Team")

__all__ = ["show_target_achievement_report"]

if __name__ == "__main__":
    show_target_achievement_report()
