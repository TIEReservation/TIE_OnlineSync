# inventory.py – FINAL: With Summary section fully restored + all previous fixes
import streamlit as st
from supabase import create_client, Client
from datetime import date
import calendar
import pandas as pd
from typing import Any, List, Dict, Optional
import logging

# ────── Logging ──────
logging.basicConfig(filename="app.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ────── Supabase client ──────
try:
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except KeyError as e:
    st.error(f"Missing Supabase secret: {e}. Please check Streamlit Cloud secrets.")
    st.stop()

# ────── Property synonym mapping ──────
property_mapping = {
    "La Millionaire Luxury Resort": "La Millionaire Resort",
    "Le Poshe Beach View": "Le Poshe Beach view",
    "Le Poshe Beach view": "Le Poshe Beach view",
    "Le Poshe Beach VIEW": "Le Poshe Beach view",
    "Le Poshe Beachview": "Le Poshe Beach view",
    "Millionaire": "La Millionaire Resort",
    "Le Pondy Beach Side": "Le Pondy Beachside",
    "Le Teera": "Le Terra"
}
reverse_mapping = {c: [] for c in set(property_mapping.values())}
for v, c in property_mapping.items():
    reverse_mapping[c].append(v)

# ────── MOP / MOB mappings ──────
mop_mapping = {
    "UPI": ["UPI"],
    "Cash": ["Cash"],
    "Go-MMT": ["Goibibo", "MMT", "Go-MMT", "MAKEMYTRIP"],
    "Agoda": ["Agoda"],
    "NOT PAID": ["Not Paid", "", " "],
    "Bank Transfer": ["Bank Transfer"],
    "Stayflexi": ["STAYFLEXI_GHA"],
    "Card Payment": ["Card"],
    "Expedia": ["Expedia"],
    "Cleartrip": ["Cleartrip"],
    "Website": ["Stayflexi Booking Engine"],
}
mob_mapping = {
    "Booking": ["BOOKING"],
    "Direct": ["Direct"],
    "Bkg-Direct": ["Bkg-Direct"],
    "Agoda": ["Agoda"],
    "Go-MMT": ["Goibibo", "MMT", "Go-MMT", "MAKEMYTRIP"],
    "Walk-In": ["Walk-In"],
    "TIE Group": ["T Allowing Group"],
    "Stayflexi": ["STAYFLEXI_GHA"],
    "Airbnb": ["Airbnb"],
    "Social Media": ["Social Media"],
    "Expedia": ["Expedia"],
    "Cleartrip": ["Cleartrip"],
    "Website": ["Stayflexi Booking Engine"],
}

# ────── Full inventory ──────
PROPERTY_INVENTORY = {
    "Le Poshe Beach view": {"all": ["101","102","201","202","203","204","301","302","303","304","Day Use 1","Day Use 2","No Show"],"three_bedroom":["203","204"]},
    "La Millionaire Resort": {"all": ["101","102","103","105","201","202","203","204","205","206","207","208","301","302","303","304","305","306","307","308","401","402","Day Use 1","Day Use 2","Day Use 3","Day Use 4","Day Use 5","No Show"],"three_bedroom":["203","204","205"]},
    "Le Poshe Luxury": {"all": ["101","102","201","202","203","204","205","301","302","303","304","305","401","402","403","404","405","501","Day Use 1","Day Use 2","No Show"],"three_bedroom":["203","204","205"]},
    "Le Poshe Suite": {"all": ["601","602","603","604","701","702","703","704","801","Day Use 1","Day Use 2","No Show"],"three_bedroom":[]},
    "La Paradise Residency": {"all": ["101","102","103","201","202","203","301","302","303","304","Day Use 1","Day Use 2","No Show"],"three_bedroom":["203"]},
    "La Paradise Luxury": {"all": ["101","102","103","201","202","203","Day Use 1","Day Use 2","No Show"],"three_bedroom":["203"]},
    "La Villa Heritage": {"all": ["101","102","103","201","202","203","301","Day Use 1","Day Use 2","No Show"],"three_bedroom":["203"]},
    "Le Pondy Beachside": {"all": ["101","102","201","202","Day Use 1","Day Use 2","No Show"],"three_bedroom":[]},
    "Le Royce Villa": {"all": ["101","102","201","202","Day Use 1","Day Use 2","No Show"],"three_bedroom":[]},
    "La Tamara Luxury": {"all": ["101","102","103","104","105","106","201","202","203","204","205","206","301","302","303","304","305","306","401","402","403","404","Day Use 1","Day Use 2","No Show"],"three_bedroom":["203","204","205","206"]},
    "La Antilia Luxury": {"all": ["101","201","202","203","204","301","302","303","304","401","Day Use 1","Day Use 2","No Show"],"three_bedroom":["203","204"]},
    "La Tamara Suite": {"all": ["101","102","103","104","201","202","203","204","205","206","Day Use 1","Day Use 2","No Show"],"three_bedroom":["203","204","205","206"]},
    "Le Park Resort": {"all": ["111","222","333","444","555","666","Day Use 1","Day Use 2","No Show"],"three_bedroom":[]},
    "Villa Shakti": {"all": ["101","102","201","201A","202","203","301","301A","302","303","401","Day Use 1","Day Use 2","No Show"],"three_bedroom":["203"]},
    "Eden Beach Resort": {"all": ["101","102","103","201","202","Day Use 1","Day Use 2","No Show"],"three_bedroom":[]},
    "Le Terra": {"all": ["101","102","103","104","105","106","107","Day Use 1","Day Use 2","No Show"],"three_bedroom":[]},
    "La Coromandel Luxury": {"all": ["101","102","103","201","202","203","204","205","206","301","Day Use 1","Day Use 2","No Show"],"three_bedroom":[]},
    "Happymates Forest Retreat": {"all": ["101","102","Day Use 1","Day Use 2","No Show"],"three_bedroom":[]}  
}

# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════
def normalize_property(name: str) -> str:
    return property_mapping.get(name.strip(), name.strip())

def sanitize_string(v: Any, default: str = "") -> str:
    return str(v).strip() if v is not None else default

def safe_int(v: Any, default: int = 0) -> int:
    try:
        return int(float(v)) if v not in [None, "", " "] else default
    except:
        return default

def safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v) if v not in [None, "", " "] else default
    except:
        return default

# (load_properties, load_combined_bookings, normalize_booking, filter_bookings_for_day, assign_inventory_numbers, create_inventory_table remain exactly as in your latest file)

# ══════════════════════════════════════════════════════════════════════════════
# Extract Stats (restored full version)
# ══════════════════════════════════════════════════════════════════════════════
def extract_stats_from_table(df: pd.DataFrame, mob_types: List[str]) -> Dict:
    occupied = df[df["Booking ID"].fillna("").str.strip() != ""].copy()

    def to_float(col):
        return pd.to_numeric(occupied[col].replace('', '0').str.replace(',', ''), errors='coerce').fillna(0.0)

    def to_int(col):
        return pd.to_numeric(occupied[col], errors='coerce').fillna(0).astype(int)

    occupied["Per Night"] = to_float("Per Night")
    occupied["Hotel Receivable"] = to_float("Hotel Receivable")
    occupied["GST"] = to_float("GST")
    occupied["TAX"] = to_float("TAX")
    occupied["Commission"] = to_float("Commission")
    occupied["Advance"] = to_float("Advance")
    occupied["Balance"] = to_float("Balance")
    occupied["Total Pax"] = to_int("Total Pax")

    mop_data = {m: 0.0 for m in ["UPI","Cash","Go-MMT","Agoda","NOT PAID","Expenses","Bank Transfer","Stayflexi","Card Payment","Expedia","Cleartrip","Website"]}
    total_cash = total = 0.0

    for _, row in occupied.iterrows():
        for mop_col, amount_col in [("Advance Mop", "Advance"), ("Balance Mop", "Balance")]:
            mop = sanitize_string(row[mop_col])
            amount = row[amount_col]
            if not mop or amount == 0: continue
            for std, variants in mop_mapping.items():
                if mop in variants:
                    mop_data[std] += amount
                    total += amount
                    if std == "Cash": total_cash += amount

    mop_data["Expenses"] = 0.0
    mop_data["Total Cash"] = total_cash
    mop_data["Total"] = total

    dtd = {m: {"rooms":0,"value":0.0,"comm":0.0,"gst":0.0,"tax":0.0,"pax":0} for m in mob_types}
    dtd_rooms = len(occupied)
    dtd_value = occupied["Per Night"].sum()
    dtd_comm = occupied["Commission"].sum()
    dtd_gst = occupied["GST"].sum()
    dtd_tax = occupied["TAX"].sum()
    dtd_pax = occupied["Total Pax"].sum()

    for _, row in occupied.iterrows():
        mob_raw = sanitize_string(row["MOB"])
        mob = next((m for m, vs in mob_mapping.items() if mob_raw.upper() in [v.upper() for v in vs]), "Booking")
        dtd[mob]["rooms"] += 1
        dtd[mob]["value"] += row["Per Night"]
        dtd[mob]["comm"] += row["Commission"]
        dtd[mob]["gst"] += row["GST"]
        dtd[mob]["tax"] += row["TAX"]
        dtd[mob]["pax"] += row["Total Pax"]

    for m in mob_types:
        r = dtd[m]["rooms"]
        dtd[m]["arr"] = dtd[m]["value"] / r if r > 0 else 0.0

    dtd["Total"] = {
        "rooms": dtd_rooms,
        "value": dtd_value,
        "arr": dtd_value / dtd_rooms if dtd_rooms > 0 else 0.0,
        "comm": dtd_comm,
        "gst": dtd_gst,
        "tax": dtd_tax,
        "pax": dtd_pax
    }

    return {"mop": mop_data, "dtd": dtd}

# ══════════════════════════════════════════════════════════════════════════════
# UI – Dashboard (with Summary fully restored)
# ══════════════════════════════════════════════════════════════════════════════
def show_daily_status():
    st.title("Daily Status Dashboard")
    if st.button("Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    today = date.today()
    year = st.selectbox("Year", list(range(today.year-5, today.year+6)), index=5)
    month = st.selectbox("Month", list(range(1,13)), index=today.month-1)

    props = load_properties()
    if not props:
        st.info("No properties found.")
        return

    mob_types = ["Booking","Direct","Bkg-Direct","Agoda","Go-MMT","Walk-In","TIE Group","Stayflexi","Airbnb","Social Media","Expedia","Cleartrip","Website"]

    for prop in props:
        if st.checkbox(f"**{prop}**", key=f"expand_{prop}"):
            month_dates = [date(year, month, d) for d in range(1, calendar.monthrange(year, month)[1]+1)]
            start, end = month_dates[0], month_dates[-1]
            bookings = load_combined_bookings(prop, start, end)

            mtd_rooms = mtd_value = mtd_comm = mtd_gst = mtd_tax = mtd_pax = 0
            mtd = {m: {"rooms":0,"value":0.0,"comm":0.0,"gst":0.0,"tax":0.0,"pax":0} for m in mob_types}

            for day in month_dates:
                daily = filter_bookings_for_day(bookings, day)
                st.markdown(f"### {prop} - {day.strftime('%b %d, %Y')}")

                assigned, over = assign_inventory_numbers(daily, prop)
                display_df, full_df = create_inventory_table(assigned, over, prop, day)

                stats = extract_stats_from_table(display_df, mob_types)
                dtd = stats["dtd"]
                mop_data = stats["mop"]

                # Accumulate MTD
                mtd_rooms += dtd["Total"]["rooms"]
                mtd_value += dtd["Total"]["value"]
                mtd_comm += dtd["Total"]["comm"]
                mtd_gst += dtd["Total"]["gst"]
                mtd_tax += dtd["Total"]["tax"]
                mtd_pax += dtd["Total"]["pax"]
                for m in mob_types:
                    mtd[m]["rooms"] += dtd[m]["rooms"]
                    mtd[m]["value"] += dtd[m]["value"]
                    mtd[m]["comm"] += dtd[m]["comm"]
                    mtd[m]["gst"] += dtd[m]["gst"]
                    mtd[m]["tax"] += dtd[m]["tax"]
                    mtd[m]["pax"] += dtd[m]["pax"]

                if daily:
                    is_accounts_team = st.session_state.get('role', '') == "Accounts Team"

                    # COLUMN CONFIG (pinned columns + editable fields)
                    col_config = {
                        "Inventory No": st.column_config.TextColumn("Inventory No", disabled=True, pinned=True),
                        "Room No": st.column_config.TextColumn("Room No", disabled=True, pinned=True),
                        "Booking ID": st.column_config.TextColumn("Booking ID", disabled=True, pinned=True),
                        "Guest Name": st.column_config.TextColumn("Guest Name", disabled=True, pinned=True),
                        "Mobile No": st.column_config.TextColumn("Mobile No", disabled=True),
                        "Total Pax": st.column_config.NumberColumn("Total Pax", disabled=True),
                        "Check In": st.column_config.TextColumn("Check In", disabled=True),
                        "Check Out": st.column_config.TextColumn("Check Out", disabled=True),
                        "Days": st.column_config.NumberColumn("Days", disabled=True),
                        "MOB": st.column_config.TextColumn("MOB", disabled=True),
                        "Room Charges": st.column_config.TextColumn("Room Charges", disabled=True),
                        "GST": st.column_config.TextColumn("GST", disabled=True),
                        "TAX": st.column_config.TextColumn("TAX", disabled=True),
                        "Total": st.column_config.TextColumn("Total", disabled=True),
                        "Commission": st.column_config.TextColumn("Commission", disabled=True),
                        "Hotel Receivable": st.column_config.TextColumn("Hotel Receivable", disabled=True),
                        "Per Night": st.column_config.TextColumn("Per Night", disabled=True),
                        "Advance": st.column_config.TextColumn("Advance", disabled=True),
                        "Advance Mop": st.column_config.TextColumn("Advance Mop", disabled=True),
                        "Balance": st.column_config.TextColumn("Balance", disabled=True),
                        "Balance Mop": st.column_config.TextColumn("Balance Mop", disabled=True),
                        "Plan": st.column_config.TextColumn("Plan", disabled=True),
                        "Booking Status": st.column_config.TextColumn("Booking Status", disabled=True),
                        "Payment Status": st.column_config.TextColumn("Payment Status", disabled=True),
                        "Submitted by": st.column_config.TextColumn("Submitted by", disabled=True),
                        "Modified by": st.column_config.TextColumn("Modified by", disabled=True),
                        "Remarks": st.column_config.TextColumn("Remarks", disabled=True),
                        "Advance Remarks": st.column_config.TextColumn("Advance Remarks", disabled=not is_accounts_team, max_chars=500),
                        "Balance Remarks": st.column_config.TextColumn("Balance Remarks", disabled=not is_accounts_team, max_chars=500),
                        "Accounts Status": st.column_config.SelectboxColumn("Accounts Status", options=["Pending", "Completed"], disabled=not is_accounts_team),
                    }

                    # Filters + Editing (your existing logic – unchanged)
                    if is_accounts_team:
                        filter_col1, filter_col2 = st.columns(2)
                        booking_id_filter = filter_col1.text_input("Filter by Booking ID", placeholder="Paste or type Booking ID", key=f"bid_filter_{prop}_{day.isoformat()}")
                        guest_name_filter = filter_col2.text_input("Filter by Guest Name", placeholder="Paste or type Guest Name", key=f"guest_filter_{prop}_{day.isoformat()}")

                        filtered_display = display_df.copy()
                        if booking_id_filter:
                            filtered_display = filtered_display[filtered_display["Booking ID"].str.contains(booking_id_filter, case=False, na=False)]
                        if guest_name_filter:
                            filtered_display = filtered_display[filtered_display["Guest Name"].str.contains(guest_name_filter, case=False, na=False)]

                        if booking_id_filter or guest_name_filter:
                            st.subheader("Filtered Editable View")
                            with st.form(key=f"form_filtered_{prop}_{day.isoformat()}"):
                                edited_display = st.data_editor(filtered_display, column_config=col_config, hide_index=True, use_container_width=True, num_rows="fixed")
                                submitted = st.form_submit_button("💾 Save Changes")
                                # ... (your existing filtered save logic here – keep as-is)
                        else:
                            with st.form(key=f"form_{prop}_{day.isoformat()}"):
                                edited_display = st.data_editor(display_df, column_config=col_config, hide_index=True, use_container_width=True, num_rows="fixed")
                                submitted = st.form_submit_button("💾 Save Changes")
                                # ... (your existing full save logic here – keep as-is)
                    else:
                        st.data_editor(display_df, column_config=col_config, hide_index=True, use_container_width=True, num_rows="fixed", key=f"view_{prop}_{day}")

                    # ──────────────────────────────
                    # RESTORED SUMMARY SECTION
                    # ──────────────────────────────
                    dtd_df = pd.DataFrame([
                        {"MOB": m, "D.T.D Rooms": d["rooms"], "D.T.D Value": f"₹{d['value']:,.2f}",
                         "D.T.D ARR": f"₹{d['arr']:,.2f}", "D.T.D Comm": f"₹{d['comm']:,.2f}"} 
                        for m, d in dtd.items() if m != "Total"
                    ] + [{"MOB": "Total", "D.T.D Rooms": dtd["Total"]["rooms"], 
                          "D.T.D Value": f"₹{dtd['Total']['value']:,.2f}",
                          "D.T.D ARR": f"₹{dtd['Total']['arr']:,.2f}", 
                          "D.T.D Comm": f"₹{dtd['Total']['comm']:,.2f}"}],
                        columns=["MOB","D.T.D Rooms","D.T.D Value","D.T.D ARR","D.T.D Comm"])

                    mop_df = pd.DataFrame([{"MOP": m, "Amount": f"₹{v:,.2f}"} for m, v in mop_data.items()], 
                                         columns=["MOP", "Amount"])

                    mtd_df = pd.DataFrame([
                        {"MOB": m, "M.T.D Rooms": mtd[m]["rooms"], "M.T.D Value": f"₹{mtd[m]['value']:,.2f}",
                         "M.T.D ARR": f"₹{mtd[m]['value']/mtd[m]['rooms']:,.2f}" if mtd[m]["rooms"] > 0 else "₹0.00",
                         "M.T.D Comm": f"₹{mtd[m]['comm']:,.2f}"} for m in mob_types
                    ] + [{"MOB": "Total", "M.T.D Rooms": mtd_rooms, "M.T.D Value": f"₹{mtd_value:,.2f}",
                          "M.T.D ARR": f"₹{mtd_value/mtd_rooms:,.2f}" if mtd_rooms > 0 else "₹0.00",
                          "M.T.D Comm": f"₹{mtd_comm:,.2f}"}], 
                        columns=["MOB","M.T.D Rooms","M.T.D Value","M.T.D ARR","M.T.D Comm"])

                    total_inventory = len([i for i in PROPERTY_INVENTORY.get(prop,{}).get("all",[]) if not i.startswith(("Day Use","No Show"))])
                    occ_pct = (dtd["Total"]["rooms"] / total_inventory * 100) if total_inventory else 0.0
                    mtd_occ_pct = (mtd_rooms / (total_inventory * day.day) * 100) if total_inventory and day.day > 0 else 0.0

                    summary = {
                        "Rooms Sold": dtd["Total"]["rooms"],
                        "Hotel Revenue": f"₹{dtd['Total']['value']:,.2f}",
                        "ARR": f"₹{dtd['Total']['arr']:,.2f}",
                        "Occupancy": f"{occ_pct:.1f}%",
                        "Total Pax": dtd["Total"]["pax"],
                        "Total Rooms": total_inventory,
                        "GST Paid": f"₹{dtd['Total']['gst']:,.2f}",
                        "TAX Paid": f"₹{dtd['Total']['tax']:,.2f}",
                        "Commission Paid": f"₹{dtd['Total']['comm']:,.2f}",
                        "MTD Occupancy": f"{mtd_occ_pct:.1f}%",
                        "MTD Revenue": f"₹{mtd_value:,.2f}",
                    }

                    c1, c2, c3, c4 = st.columns(4)
                    with c1: st.subheader("MOP"); st.dataframe(mop_df, use_container_width=True)
                    with c2: st.subheader("Day Revenue"); st.dataframe(dtd_df, use_container_width=True)
                    with c3: st.subheader("Month Revenue"); st.dataframe(mtd_df, use_container_width=True)
                    with c4:
                        st.subheader("Summary")
                        st.dataframe(pd.DataFrame([{"Metric": k, "Value": v} for k, v in summary.items()]), use_container_width=True)
                else:
                    st.info("No active bookings.")

# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    show_daily_status()
