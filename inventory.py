import streamlit as st
from supabase import create_client, Client
from datetime import date
import calendar
import pandas as pd
from typing import Any, List, Dict
import logging

logging.basicConfig(filename='app.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

try:
    supabase: Client = create_client(st.secrets["supabase"]["url"],
                                    st.secrets["supabase"]["key"])
except KeyError as e:
    st.error(f"Missing Supabase secret: {e}. Please check Streamlit Cloud secrets.")
    st.stop()

property_mapping = {
    "La Millionaire Luxury Resort": "La Millionaire Resort",
    "Le Poshe Beach View": "Le Poshe Beach view",
    "Le Poshe Beach view": "Le Poshe Beach view",
    "Le Poshe Beach VIEW": "Le Poshe Beach view",
    "Millionaire": "La Millionaire Resort",
}
reverse_mapping = {}
for variant, canonical in property_mapping.items():
    reverse_mapping.setdefault(canonical, []).append(variant)

mop_mapping = {
    "UPI": ["UPI"],
    "Cash": ["Cash"],
    "Go-MMT": ["Goibibo", "MMT", "Go-MMT", "MAKEMYTRIP"],
    "Agoda": ["Agoda"],
    "NOT PAID": ["Not Paid"],
    "Bank Transfer": ["Bank Transfer"],
    "Stayflexi": ["STAYFLEXI_GHA"],
    "Card Payment": ["Card"],
    "Expedia": ["Expedia"],
    "Cleartrip": ["Cleartrip"],
    "Website": ["Stayflexi Booking Engine"]
}

mob_mapping = {
    "Booking": ["BOOKING"],
    "Direct": ["Direct"],
    "Bkg-Direct": ["Bkg-Direct"],
    "Agoda": ["Agoda"],
    "Go-MMT": ["Goibibo", "MMT", "Go-MMT", "MAKEMYTRIP"],
    "Walk-In": ["Walk-In"],
    "TIE Group": ["TIE Group"],
    "Stayflexi": ["STAYFLEXI_GHA"],
    "Airbnb": ["Airbnb"],
    "Social Media": ["Social Media"],
    "Expedia": ["Expedia"],
    "Cleartrip": ["Cleartrip"],
    "Website": ["Stayflexi Booking Engine"]
}

TABLE_CSS = """
<style>
.custom-scrollable-table {overflow-x:auto; max-width:100%; min-width:800px;}
.custom-scrollable-table table {table-layout:auto; border-collapse:collapse;}
.custom-scrollable-table td, .custom-scrollable-table th {
    white-space:nowrap; text-overflow:ellipsis; overflow:hidden;
    max-width:150px; padding:8px; border:1px solid #ddd;
}
</style>
"""

PROPERTY_INVENTORY = {
    "Le Poshe Beach view": {"all": ["101","102","201","202","203","204","301","302","303","304","Day Use 1","Day Use 2","No Show"], "three_bedroom":["203","204"]},
    "La Millionaire Resort": {"all": ["101","102","103","105","201","202","203","204","205","206","207","208","301","302","303","304","305","306","307","308","401","402","Day Use 1","Day Use 2","Day Use 3","Day Use 4","Day Use 5","No Show"], "three_bedroom":["203","204","205"]},
    "Le Poshe Luxury": {"all": ["101","102","201","202","203","204","205","301","302","303","304","305","401","402","403","404","405","501","Day Use 1","Day Use 2","No Show"], "three_bedroom":["203","204","205"]},
    "Le Poshe Suite": {"all": ["601","602","603","604","701","702","703","704","801","Day Use 1","Day Use 2","No Show"], "three_bedroom":[]},
    "La Paradise Residency": {"all": ["101","102","103","201","202","203","301","302","303","304","Day Use 1","Day Use 2","No Show"], "three_bedroom":["203"]},
    "La Paradise Luxury": {"all": ["101","102","103","201","202","203","Day Use 1","Day Use 2","No Show"], "three_bedroom":["203"]},
    "La Villa Heritage": {"all": ["101","102","103","201","202","203","301","Day Use 1","Day Use 2","No Show"], "three_bedroom":["203"]},
    "Le Pondy Beach Side": {"all": ["101","102","201","202","Day Use 1","Day Use 2","No Show"], "three_bedroom":[]},
    "Le Royce Villa": {"all": ["101","102","201","202","Day Use 1","Day Use 2","No Show"], "three_bedroom":[]},
    "La Tamara Luxury": {"all": ["101","102","103","104","105","106","201","202","203","204","205","206","301","302","303","304","305","306","401","402","403","404","Day Use 1","Day Use 2","No Show"], "three_bedroom":["203","204","205","206"]},
    "La Antilia Luxury": {"all": ["101","201","202","203","204","301","302","303","304","401","Day Use 1","Day Use 2","No Show"], "three_bedroom":["203","204"]},
    "La Tamara Suite": {"all": ["101","102","103","104","201","202","203","204","205","206","Day Use 1","Day Use 2","No Show"], "three_bedroom":["203","204","205","206"]},
    "Le Park Resort": {"all": ["111","222","333","444","555","666","Day Use 1","Day Use 2","No Show"], "three_bedroom":[]},
    "Villa Shakti": {"all": ["101","102","201","201A","202","203","301","301A","302","303","401","Day Use 1","Day Use 2","No Show"], "three_bedroom":["203"]},
    "Eden Beach Resort": {"all": ["101","102","103","201","202","Day Use 1","Day Use 2","No Show"], "three_bedroom":[]}
}

def initialize_property_inventory(properties: List[str]) -> None:
    fallback = {"all": ["Unknown"], "three_bedroom": []}
    for p in properties:
        if p not in PROPERTY_INVENTORY:
            PROPERTY_INVENTORY[p] = fallback
            logging.warning(f"Added fallback inventory for unknown property: {p}")

def format_booking_id(booking: Dict) -> str:
    bid = sanitize_string(booking.get('booking_id'))
    return f'<a target="_blank" href="/?edit_type={booking["type"]}&booking_id={bid}">{bid}</a>'

def load_properties() -> List[str]:
    try:
        res_direct = supabase.table("reservations").select("property_name").execute().data
        res_online = supabase.table("online_reservations").select("property").execute().data
        props = set()
        for r in res_direct:
            p = r.get('property_name')
            if p: props.add(property_mapping.get(p.strip(), p.strip()))
        for r in res_online:
            p = r.get('property')
            if p: props.add(property_mapping.get(p.strip(), p.strip()))
        props = sorted(props)
        initialize_property_inventory(props)
        logging.info(f"Loaded properties: {props}")
        return props
    except Exception as e:
        st.error(f"Error loading properties: {e}")
        return []

def sanitize_string(v: Any, default: str = "Unknown") -> str:
    return str(v).strip() if v is not None else default

def safe_int(v: Any, default: int = 0) -> int:
    try: return int(v) if v is not None else default
    except (ValueError, TypeError): return default

def safe_float(v: Any, default: float = 0.0) -> float:
    try: return float(v) if v is not None else default
    except (ValueError, TypeError): return default

def normalize_booking(booking: Dict, is_online: bool) -> Dict | None:
    bid = sanitize_string(booking.get('booking_id'))
    payment_status = sanitize_string(booking.get('payment_status')).title()
    if payment_status not in ["Fully Paid", "Partially Paid"]:
        logging.warning(f"Skip {bid} – invalid payment_status {payment_status}")
        return None

    status_field = 'booking_status' if is_online else 'plan_status'
    booking_status = sanitize_string(booking.get(status_field))

    try:
        ci = date.fromisoformat(booking.get('check_in')) if booking.get('check_in') else None
        co = date.fromisoformat(booking.get('check_out')) if booking.get('check_out') else None
        days = (co - ci).days if ci and co else 0
        if days < 0: return None
        if days == 0: days = 1
    except ValueError as e:
        logging.warning(f"Skip {bid} – date error: {e}")
        return None

    prop = property_mapping.get(sanitize_string(booking.get('property', booking.get('property_name'))), sanitize_string(booking.get('property_name')))

    total_tariff = safe_float(booking.get('total_amount_with_services', booking.get('booking_amount', 0.0))) or safe_float(booking.get('total_tariff', 0.0))
    advance = safe_float(booking.get('total_payment_made', 0.0)) or safe_float(booking.get('advance_amount', 0.0))
    balance = safe_float(booking.get('balance_due', 0.0)) or safe_float(booking.get('balance_amount', 0.0))
    gst = safe_float(booking.get('ota_tax', 0.0)) if is_online else 0.0
    commission = safe_float(booking.get('ota_commission', 0.0))
    receivable = total_tariff - commission
    per_night = receivable / days if days else 0.0

    return {
        "type": "online" if is_online else "direct",
        "property": prop,
        "booking_id": bid,
        "guest_name": sanitize_string(booking.get('guest_name')),
        "mobile_no": sanitize_string(booking.get('guest_phone', booking.get('mobile_no'))),
        "total_pax": safe_int(booking.get('total_pax', 0)),
        "check_in": str(ci) if ci else "",
        "check_out": str(co) if co else "",
        "days": days,
        "room_no": sanitize_string(booking.get('room_no', '')).title(),
        "room_type": sanitize_string(booking.get('room_type')),
        "mob": sanitize_string(booking.get('mode_of_booking', booking.get('mob'))),
        "room_charges": total_tariff,
        "gst": gst,
        "total": total_tariff,
        "commission": commission,
        "receivable": receivable,
        "per_night": per_night,
        "advance": advance,
        "advance_mop": sanitize_string(booking.get('advance_mop')),
        "balance": balance,
        "balance_mop": sanitize_string(booking.get('balance_mop')),
        "plan": sanitize_string(booking.get('rate_plans', booking.get('plan'))),
        "booking_status": booking_status,
        "payment_status": payment_status,
        "submitted_by": sanitize_string(booking.get('submitted_by')),
        "modified_by": sanitize_string(booking.get('modified_by')),
        "remarks": sanitize_string(booking.get('remarks'))
    }

def load_combined_bookings(property: str, start_date: date, end_date: date) -> List[Dict]:
    try:
        query_props = [property] + reverse_mapping.get(property, [])
        logging.info(f"Overlap query for {property} → {start_date} to {end_date}")

        online, direct = [], []

        for qp in query_props:
            online_response = (
                supabase.table("online_reservations")
                .select("*")
                .eq("property", qp)
                .or_(f"and(check_in.lte.{end_date},check_out.gte.{start_date})")
                .execute()
            )
            online.extend([b for b in (online_response.data or []) if normalize_booking(b, True)])

            direct_response = (
                supabase.table("reservations")
                .select("*")
                .eq("property_name", qp)
                .or_(f"and(check_in.lte.{end_date},check_out.gte.{start_date})")
                .execute()
            )
            direct.extend([b for b in (direct_response.data or []) if normalize_booking(b, False)])

        combined = [b for b in online + direct if b]
        logging.info(f"Total overlapping bookings: {len(combined)}")
        return combined
    except Exception as e:
        st.error(f"Error loading overlapping bookings: {e}")
        return []

def generate_month_dates(year: int, month: int) -> List[date]:
    _, days = calendar.monthrange(year, month)
    return [date(year, month, d) for d in range(1, days + 1)]

def filter_bookings_for_day(bookings: List[Dict], target: date) -> List[Dict]:
    filtered = []
    for b in bookings:
        try:
            ci = date.fromisoformat(b["check_in"]) if b["check_in"] else None
            co = date.fromisoformat(b["check_out"]) if b["check_out"] else None
            if ci and co and ci <= target < co:
                bc = b.copy()
                bc["target_date"] = target
                filtered.append(bc)
        except ValueError:
            continue
    return filtered

def assign_inventory_numbers(daily: List[Dict], prop: str) -> tuple[List[Dict], List[Dict]]:
    assigned, over = [], []
    inv = PROPERTY_INVENTORY.get(prop, {"all": []})["all"]
    inv_low = [i.lower() for i in inv]

    for b in daily:
        rooms = [r.strip().title() for r in b.get("room_no", "").split(",") if r.strip()]
        if not rooms:
            over.append(b); continue
        if not all(r.lower() in inv_low for r in rooms):
            over.append(b); continue

        rooms = [inv[inv_low.index(r.lower())] for r in rooms]
        rooms.sort()
        base_pax = b["total_pax"] // len(rooms) if rooms else 0
        rem_pax = b["total_pax"] % len(rooms) if rooms else 0
        per_night = b["receivable"] / len(rooms) / b["days"] if rooms else 0.0

        if len(rooms) == 1:
            b["inventory_no"] = rooms
            b["per_night"] = per_night
            b["is_primary"] = True
            assigned.append(b)
        else:
            for i, r in enumerate(rooms):
                nb = b.copy()
                nb["inventory_no"] = [r]
                nb["room_no"] = r
                nb["total_pax"] = base_pax + (1 if i < rem_pax else 0)
                nb["per_night"] = per_night
                nb["is_primary"] = (i == 0)
                assigned.append(nb)
    return assigned, over

def create_inventory_table(assigned: List[Dict], over: List[Dict], prop: str) -> pd.DataFrame:
    cols = ["Inventory No","Room No","Booking ID","Guest Name","Mobile No","Total Pax",
            "Check In","Check Out","Days","MOB","Room Charges","GST","Total","Commision",
            "Receivable","Per Night","Advance","Advance Mop","Balance","Balance Mop",
            "Plan","Booking Status","Payment Status","Submitted by","Modified by","Remarks"]
    inv = PROPERTY_INVENTORY.get(prop, {"all": []})["all"]
    df = pd.DataFrame([{c: "" for c in cols} for _ in inv], columns=cols)
    for i, r in enumerate(inv):
        df.at[i, "Inventory No"] = r

    fin = ["Room Charges","GST","Total","Commision","Receivable","Advance","Advance Mop","Balance"]

    for b in assigned:
        inv_no = b.get("inventory_no", [])
        if not inv_no: continue
        for inv in inv_no:
            idx = df[df["Inventory No"] == inv].index
            if idx.empty: continue
            row = df.loc[idx[0]]
            ci = date.fromisoformat(b["check_in"]) if b["check_in"] else None
            first_day = ci == b.get("target_date")
            row.update({
                "Inventory No": inv,
                "Room No": b.get("room_no",""),
                "Booking ID": format_booking_id(b),
                "Guest Name": b.get("guest_name",""),
                "Mobile No": b.get("mobile_no",""),
                "Total Pax": str(b.get("total_pax","")),
                "Check In": b.get("check_in",""),
                "Check Out": b.get("check_out",""),
                "Days": str(b.get("days",0)),
                "MOB": b.get("mob",""),
                "Per Night": f"{b.get('per_night',0):.2f}",
                "Plan": b.get("plan",""),
                "Booking Status": b.get("booking_status",""),
                "Payment Status": b.get("payment_status",""),
                "Submitted by": b.get("submitted_by",""),
                "Modified by": b.get("modified_by",""),
                "Remarks": b.get("remarks",""),
                "Balance Mop": b.get("balance_mop","")
            })
            if b.get("is_primary") and first_day:
                row.update({f: f"{b.get(f.lower().replace(' ','_'),0):.2f}" if f not in ["Advance Mop"] else b.get(f.lower().replace(' ','_'),"")
                            for f in fin})

    if over:
        df.loc[len(df)] = {
            "Inventory No": "Overbookings",
            "Room No": ", ".join(f"{sanitize_string(b.get('room_no',''))} ({sanitize_string(b.get('booking_id',''))})" for b in over),
            "Booking ID": ", ".join(format_booking_id(b) for b in over)
        }
    return df

def compute_mop_report(daily_assigned: List[Dict], target: date) -> pd.DataFrame:
    types = ["UPI","Cash","Go-MMT","Agoda","NOT PAID","Expenses",
             "Bank Transfer","Stayflexi","Card Payment","Expedia","Cleartrip","Website"]
    data = {t: 0.0 for t in types}
    cash = total = 0.0

    for b in daily_assigned:
        if not (b.get("is_primary") and date.fromisoformat(b["check_in"]) == target):
            continue
        adv_mop = sanitize_string(b.get("advance_mop",""))
        bal_mop = sanitize_string(b.get("balance_mop",""))
        adv = safe_float(b.get("advance",0))
        bal = safe_float(b.get("balance",0))

        for std, vars in mop_mapping.items():
            if adv_mop in vars: data[std] += adv; total += adv; cash += adv if std == "Cash" else 0
            if bal_mop in vars: data[std] += bal; total += bal; cash += bal if std == "Cash" else 0

    data["Expenses"] = 0.0
    data["Total Cash"] = cash
    data["Total"] = total

    return pd.DataFrame([{"MOP": k, "Amount": f"{v:.2f}"} for k, v in data.items()],
                        columns=["MOP","Amount"])

def compute_statistics(bookings: List[Dict], prop: str, target: date, month_dates: List[date]) -> tuple[pd.DataFrame, pd.DataFrame, Dict, pd.DataFrame]:
    mob_types = list(mob_mapping.keys())
    inv = [i for i in PROPERTY_INVENTORY.get(prop, {"all": []})["all"] if not i.startswith(("Day Use","No Show"))]
    total_inv = len(inv)

    dtd = {m: {"rooms":0,"value":0.0,"arr":0.0,"comm":0.0} for m in mob_types}
    daily = filter_bookings_for_day(bookings, target)
    assigned, _ = assign_inventory_numbers(daily, prop)
    dtd_tot_rooms = dtd_tot_val = dtd_tot_pax = dtd_tot_gst = dtd_tot_comm = 0

    for b in assigned:
        raw = sanitize_string(b.get("mob",""))
        mob = next((std for std, vars in mob_mapping.items() if raw.upper() in [v.upper() for v in vars]), "Booking")
        rooms = len(b.get("inventory_no",[]))
        val = b["receivable"] if b.get("is_primary") and b.get("target_date")==date.fromisoformat(b["check_in"]) else 0.0
        com = b["commission"] if b.get("is_primary") and b.get("target_date")==date.fromisoformat(b["check_in"]) else 0.0
        dtd[mob]["rooms"] += rooms; dtd[mob]["value"] += val; dtd[mob]["comm"] += com
        dtd_tot_rooms += rooms; dtd_tot_val += val; dtd_tot_pax += b["total_pax"]; dtd_tot_gst += b["gst"] if b.get("is_primary") and b.get("target_date")==date.fromisoformat(b["check_in"]) else 0.0; dtd_tot_comm += com

    for m in mob_types:
        r = dtd[m]["rooms"]
        dtd[m]["arr"] = dtd[m]["value"]/r if r else 0.0
    dtd["Total"] = {"rooms":dtd_tot_rooms,"value":dtd_tot_val,"arr":dtd_tot_val/dtd_tot_rooms if dtd_tot_rooms else 0.0,"comm":dtd_tot_comm}
    dtd_df = pd.DataFrame([{"MOB":m, "D.T.D Rooms":d["rooms"], "D.T.D Value":f"{d['value']:.2f}",
                           "D.T.D ARR":f"{d['arr']:.2f}", "D.T.D Comm":f"{d['comm']:.2f}"} for m,d in dtd.items()])

    mtd = {m: {"rooms":0,"value":0.0,"arr":0.0,"comm":0.0} for m in mob_types}
    mtd_tot_rooms = mtd_tot_val = mtd_tot_pax = mtd_tot_gst = mtd_tot_comm = 0

    for day in month_dates:
        if day > target: continue
        daily = filter_bookings_for_day(bookings, day)
        ass, _ = assign_inventory_numbers(daily, prop)
        for b in ass:
            raw = sanitize_string(b.get("mob",""))
            mob = next((std for std, vars in mob_mapping.items() if raw.upper() in [v.upper() for v in vars]), "Booking")
            rooms = len(b.get("inventory_no",[]))
            val = b["receivable"] if b.get("is_primary") and b.get("target_date")==date.fromisoformat(b["check_in"]) else 0.0
            com = b["commission"] if b.get("is_primary") and b.get("target_date")==date.fromisoformat(b["check_in"]) else 0.0
            mtd[mob]["rooms"] += rooms; mtd[mob]["value"] += val; mtd[mob]["comm"] += com
            mtd_tot_rooms += rooms; mtd_tot_val += val; mtd_tot_pax += b["total_pax"]; mtd_tot_gst += b["gst"] if b.get("is_primary") and b.get("target_date")==date.fromisoformat(b["check_in"]) else 0.0; mtd_tot_comm += com

    for m in mob_types:
        r = mtd[m]["rooms"]
        mtd[m]["arr"] = mtd[m]["value"]/r if r else 0.0
    mtd["Total"] = {"rooms":mtd_tot_rooms,"value":mtd_tot_val,"arr":mtd_tot_val/mtd_tot_rooms if mtd_tot_rooms else 0.0,"comm":mtd_tot_comm}
    mtd_df = pd.DataFrame([{"MOB":m, "M.T.D Rooms":d["rooms"], "M.T.D Value":f"{d['value']:.2f}",
                           "M.T.D ARR":f"{d['arr']:.2f}", "M.T.D Comm":f"{d['comm']:.2f}"} for m,d in mtd.items()])

    summary = {
        "rooms_sold": dtd_tot_rooms,
        "value": dtd_tot_val,
        "arr": dtd_tot_val/dtd_tot_rooms if dtd_tot_rooms else 0.0,
        "occ_percent": (dtd_tot_rooms/total_inv*100) if total_inv else 0.0,
        "total_pax": dtd_tot_pax,
        "total_inventory": total_inv,
        "gst": dtd_tot_gst,
        "commission": dtd_tot_comm,
        "tax_deduction": dtd_tot_val*0.003,
        "mtd_occ_percent": min((mtd_tot_rooms/(total_inv*target.day)*100) if total_inv and target.day else 0.0, 100.0),
        "mtd_pax": mtd_tot_pax,
        "mtd_rooms": mtd_tot_rooms,
        "mtd_gst": mtd_tot_gst,
        "mtd_tax_deduction": mtd_tot_val*0.003,
        "mtd_value": mtd_tot_val
    }

    mop_df = compute_mop_report(assigned, target)
    return dtd_df, mtd_df, summary, mop_df

@st.cache_data(ttl=600)
def cached_load_properties() -> List[str]:
    return load_properties()

@st.cache_data(ttl=600)
def cached_load_bookings(_prop: str, _start: date, _end: date) -> List[Dict]:
    return load_combined_bookings(_prop, _start, _end)

def show_daily_status():
    st.title("Daily Status")
    if st.button("Refresh Property List"):
        st.cache_data.clear()
        st.rerun()

    year = st.selectbox("Year", range(date.today().year-5, date.today().year+6), index=5)
    month = st.selectbox("Month", range(1,13), index=date.today().month-1)

    props = cached_load_properties()
    if not props:
        st.info("No properties found.")
        return

    st.markdown(TABLE_CSS, unsafe_allow_html=True)

    for prop in props:
        with st.expander(prop):
            month_dates = generate_month_dates(year, month)
            start = month_dates[0]
            end   = month_dates[-1]

            bookings = cached_load_bookings(prop, start, end)

            for day in month_dates:
                daily = filter_bookings_for_day(bookings, day)
                st.subheader(f"{prop} – {day:%B %d, %Y}")

                if daily:
                    assigned, over = assign_inventory_numbers(daily, prop)
                    inv_df = create_inventory_table(assigned, over, prop)

                    for c in ["Guest Name","Room No","Remarks","Mobile No","MOB","Plan","Submitted by","Modified by"]:
                        if c in inv_df.columns:
                            inv_df[c] = inv_df[c].apply(lambda x: f'<span title="{x}">{x}</span>' if isinstance(x,str) else x)

                    st.markdown(f'<div class="custom-scrollable-table">{inv_df.to_html(escape=False, index=False)}</div>', unsafe_allow_html=True)

                    dtd_df, mtd_df, summary, mop_df = compute_statistics(bookings, prop, day, month_dates)

                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.subheader("MOP Report")
                        st.dataframe(mop_df, use_container_width=True, hide_index=True)

                    with col2:
                        st.subheader("D.T.D Statistics")
                        st.dataframe(dtd_df, use_container_width=True, hide_index=True)

                    with col3:
                        st.subheader("M.T.D Statistics")
                        st.dataframe(mtd_df, use_container_width=True, hide_index=True)

                    with col4:
                        st.subheader("Summary")
                        summary_df = pd.DataFrame([
                            {"Metric":"Rooms Sold","Value":summary["rooms_sold"]},
                            {"Metric":"Value","Value":f"{summary['value']:.2f}"},
                            {"Metric":"ARR","Value":f"{summary['arr']:.2f}"},
                            {"Metric":"Occ%","Value":f"{summary['occ_percent']:.2f}%"},
                            {"Metric":"Total Pax","Value":summary["total_pax"]},
                            {"Metric":"GST","Value":f"{summary['gst']:.2f}"},
                            {"Metric":"Commission","Value":f"{summary['commission']:.2f}"},
                            {"Metric":"TAX Deduction","Value":f"{summary['tax_deduction']:.2f}"},
                            {"Metric":"M.T.D Occ%","Value":f"{summary['mtd_occ_percent']:.2f}%"},
                            {"Metric":"M.T.D Pax","Value":summary["mtd_pax"]},
                            {"Metric":"M.T.D Rooms","Value":summary["mtd_rooms"]},
                            {"Metric":"M.T.D GST","Value":f"{summary['mtd_gst']:.2f}"},
                            {"Metric":"M.T.D Tax Ded.","Value":f"{summary['mtd_tax_deduction']:.2f}"},
                            {"Metric":"M.T.D Value","Value":f"{summary['mtd_value']:.2f}"}
                        ])
                        st.dataframe(summary_df, use_container_width=True, hide_index=True)

                else:
                    st.info("No active bookings on this day.")

if __name__ == "__main__":
    show_daily_status()
