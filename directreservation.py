import streamlit as st
from supabase import create_client, Client
from datetime import date, timedelta
import calendar
import pandas as pd
from typing import Any, List, Dict
import logging

# Configure file-based logging
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Supabase client
try:
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except KeyError as e:
    st.error(f"Missing Supabase secret: {e}. Please check Streamlit Cloud secrets configuration.")
    st.stop()

# Property synonym mapping
property_mapping = {
    "La Millionaire Luxury Resort": "La Millionaire Resort",
    "Le Poshe Beach View": "Le Poshe Beach view",
    "Le Poshe Beach view": "Le Poshe Beach view",
    "Le Poshe Beach VIEW": "Le Poshe Beach view",
    "Millionaire": "La Millionaire Resort",
}
reverse_mapping = {canonical: [] for canonical in set(property_mapping.values())}
for variant, canonical in property_mapping.items():
    reverse_mapping[canonical].append(variant)

# MOP (Mode of Payment) mapping
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

# MOB (Mode of Booking) mapping
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

# Table CSS
TABLE_CSS = """
<style>
.custom-scrollable-table {
    overflow-x: auto;
    max-width: 100%;
    min-width: 800px;
}
.custom-scrollable-table table {
    table-layout: auto;
    border-collapse: collapse;
}
.custom-scrollable-table td, .custom-scrollable-table th {
    white-space: nowrap;
    text-overflow: ellipsis;
    overflow: hidden;
    max-width: 150px;
    padding: 8px;
    border: 1px solid #ddd;
}
</style>
"""

# Property inventory
PROPERTY_INVENTORY = {
    "Le Poshe Beach view": {
        "all": ["101", "102", "201", "202", "203", "204", "301", "302", "303", "304", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": ["203", "204"]
    },
    "La Millionaire Resort": {
        "all": ["101", "102", "103", "105", "201", "202", "203", "204", "205", "206", "207", "208", "301", "302", "303", "304", "305", "306", "307", "308", "401", "402", "Day Use 1", "Day Use 2", "Day Use 3", "Day Use 4", "Day Use 5", "No Show"],
        "three_bedroom": ["203", "204", "205"]
    },
    "Le Poshe Luxury": {
        "all": ["101", "102", "201", "202", "203", "204", "205", "301", "302", "303", "304", "305", "401", "402", "403", "404", "405", "501", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": ["203", "204", "205"]
    },
    "Le Poshe Suite": {
        "all": ["601", "602", "603", "604", "701", "702", "703", "704", "801", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": []
    },
    "La Paradise Residency": {
        "all": ["101", "102", "103", "201", "202", "203", "301", "302", "303", "304", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": ["203"]
    },
    "La Paradise Luxury": {
        "all": ["101", "102", "103", "201", "202", "203", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": ["203"]
    },
    "La Villa Heritage": {
        "all": ["101", "102", "103", "201", "202", "203", "301", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": ["203"]
    },
    "Le Pondy Beach Side": {
        "all": ["101", "102", "201", "202", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": []
    },
    "Le Royce Villa": {
        "all": ["101", "102", "201", "202", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": []
    },
    "La Tamara Luxury": {
        "all": ["101", "102", "103", "104", "105", "106", "201", "202", "203", "204", "205", "206", "301", "302", "303", "304", "305", "306", "401", "402", "403", "404", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": ["203", "204", "205", "206"]
    },
    "La Antilia Luxury": {
        "all": ["101", "201", "202", "203", "204", "301", "302", "303", "304", "401", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": ["203", "204"]
    },
    "La Tamara Suite": {
        "all": ["101", "102", "103", "104", "201", "202", "203", "204", "205", "206", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": ["203", "204", "205", "206"]
    },
    "Le Park Resort": {
        "all": ["111", "222", "333", "444", "555", "666", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": []
    },
    "Villa Shakti": {
        "all": ["101", "102", "201", "201A", "202", "203", "301", "301A", "302", "303", "401", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": ["203"]
    },
    "Eden Beach Resort": {
        "all": ["101", "102", "103", "201", "202", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": []
    }
}

def initialize_property_inventory(properties: List[str]) -> None:
    fallback = {"all": ["Unknown"], "three_bedroom": []}
    for prop in properties:
        if prop not in PROPERTY_INVENTORY:
            PROPERTY_INVENTORY[prop] = fallback
            logging.warning(f"Added fallback inventory for unknown property: {prop}")

def format_booking_id(booking: Dict) -> str:
    booking_id = sanitize_string(booking.get('booking_id'))
    return f'<a target="_blank" href="/?edit_type={booking["type"]}&booking_id={booking_id}">{booking_id}</a>'

def load_properties() -> List[str]:
    try:
        res_direct = supabase.table("reservations").select("property_name").execute().data
        res_online = supabase.table("online_reservations").select("property").execute().data
        properties = set()
        for r in res_direct:
            prop = r['property_name']
            if prop:
                canonical = property_mapping.get(prop.strip(), prop.strip())
                properties.add(canonical)
        for r in res_online:
            prop = r['property']
            if prop:
                canonical = property_mapping.get(prop.strip(), prop.strip())
                properties.add(canonical)
        properties = sorted(properties)
        initialize_property_inventory(properties)
        logging.info(f"Loaded properties: {properties}")
        return properties
    except Exception as e:
        st.error(f"Error loading properties: {e}")
        return []

def sanitize_string(value: Any, default: str = "Unknown") -> str:
    return str(value).strip() if value is not None else default

def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value) if value is not None else default
    except (ValueError, TypeError):
        return default

def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default

def normalize_booking(booking: Dict, is_online: bool) -> Dict:
    booking_id = sanitize_string(booking.get('booking_id'))
    payment_status = sanitize_string(booking.get('payment_status')).title()
    if payment_status not in ["Fully Paid", "Partially Paid"]:
        logging.warning(f"Skipping booking {booking_id} due to invalid payment status: {payment_status}")
        return None
    booking_status_field = 'booking_status' if is_online else 'plan_status'
    booking_status = sanitize_string(booking.get(booking_status_field))
    try:
        check_in = date.fromisoformat(booking.get('check_in')) if booking.get('check_in') else None
        check_out = date.fromisoformat(booking.get('check_out')) if booking.get('check_out') else None
        days = None
        if check_in and check_out:
            days = (check_out - check_in).days
            if days <= 0:                     # <-- FIXED: skip same-day / backward dates
                logging.warning(f"Skipping booking {booking_id} due to invalid duration: {days} days")
                return None
        property_name = sanitize_string(booking.get('property', booking.get('property_name', '')))
        property_name = property_mapping.get(property_name, property_name)
        guest_name = sanitize_string(booking.get('guest_name', ''))
        mobile_no = sanitize_string(booking.get('guest_phone', booking.get('mobile_no', '')))
        total_pax = safe_int(booking.get('total_pax', 0))
        room_no = sanitize_string(booking.get('room_no', '')).title()
        mob = sanitize_string(booking.get('mode_of_booking', booking.get('mob', '')))
        plan = sanitize_string(booking.get('rate_plans', booking.get('plan', '')))
        submitted_by = sanitize_string(booking.get('submitted_by', ''))
        modified_by = sanitize_string(booking.get('modified_by', ''))
        remarks = sanitize_string(booking.get('remarks', ''))
        total_tariff = safe_float(booking.get('total_amount_with_services', booking.get('booking_amount', 0.0))) or safe_float(booking.get('total_tariff', 0.0))
        advance = safe_float(booking.get('total_payment_made', 0.0)) or safe_float(booking.get('advance_amount', 0.0))
        balance = safe_float(booking.get('balance_due', 0.0)) or safe_float(booking.get('balance_amount', 0.0))
        advance_mop = sanitize_string(booking.get('advance_mop', ''))
        balance_mop = sanitize_string(booking.get('balance_mop', ''))
        room_charges = total_tariff
        gst = safe_float(booking.get('ota_tax', 0.0)) if is_online else 0.0
        commission = safe_float(booking.get('ota_commission', 0.0))
        receivable = room_charges - commission
        per_night = receivable / days if days and days > 0 else 0.0
        booking_type = "online" if is_online else "direct"
        return {
            "type": booking_type,
            "property": property_name,
            "booking_id": booking_id,
            "guest_name": guest_name,
            "mobile_no": mobile_no,
            "total_pax": total_pax,
            "check_in": str(check_in) if check_in else "",
            "check_out": str(check_out) if check_out else "",
            "days": days or 0,
            "room_no": room_no,
            "mob": mob,
            "room_charges": room_charges,
            "gst": gst,
            "total": total_tariff,
            "commission": commission,
            "receivable": receivable,
            "per_night": per_night,
            "advance": advance,
            "advance_mop": advance_mop,
            "balance": balance,
            "balance_mop": balance_mop,
            "plan": plan,
            "booking_status": booking_status,
            "payment_status": payment_status,
            "submitted_by": submitted_by,
            "modified_by": modified_by,
            "remarks": remarks
        }
    except ValueError as e:
        logging.warning(f"Skipping booking {booking_id} due to date error: {e}")
        return None

def load_combined_bookings(property: str, start_date: date, end_date: date) -> List[Dict]:
    try:
        query_properties = [property] + reverse_mapping.get(property, [])
        online_bookings = []
        direct_bookings = []
        for query_property in query_properties:
            online_response = supabase.table("online_reservations").select("*").in_("property", query_properties).lte("check_in", str(end_date)).gte("check_out", str(start_date)).execute()
            online_bookings.extend([normalize_booking(b, True) for b in (online_response.data or []) if normalize_booking(b, True)])
            direct_response = supabase.table("reservations").select("*").eq("property_name", query_property).lte("check_in", str(end_date)).gte("check_out", str(start_date)).execute()
            direct_bookings.extend([normalize_booking(b, False) for b in (direct_response.data or []) if normalize_booking(b, False)])
        return [b for b in online_bookings + direct_bookings if b]
    except Exception as e:
        st.error(f"Error loading bookings: {e}")
        return []

def generate_month_dates(year: int, month: int) -> List[date]:
    _, num_days = calendar.monthrange(year, month)
    return [date(year, month, day) for day in range(1, num_days + 1)]

def filter_bookings_for_day(bookings: List[Dict], target_date: date) -> List[Dict]:
    filtered = []
    for b in bookings:
        try:
            check_in = date.fromisoformat(b["check_in"]) if b.get("check_in") else None
            check_out = date.fromisoformat(b["check_out"]) if b.get("check_out") else None

            # ---- Only show if Confirmed AND (Fully Paid OR Partially Paid) ----
            booking_status = sanitize_string(b.get("booking_status", "")).strip()
            payment_status = sanitize_string(b.get("payment_status", "")).strip()

            if booking_status != "Confirmed":
                continue
            if payment_status not in ["Fully Paid", "Partially Paid"]:
                continue
            # ------------------------------------------------------------------------

            if check_in and check_out and check_in <= target_date < check_out:
                b_copy = b.copy()
                b_copy['target_date'] = target_date
                filtered.append(b_copy)
        except ValueError:
            continue
    return filtered

def assign_inventory_numbers(daily_bookings: List[Dict], property: str) -> tuple[List[Dict], List[Dict]]:
    assigned = []
    overbookings = []
    inventory = PROPERTY_INVENTORY.get(property, {"all": []})["all"]
    inventory_lower = [i.lower() for i in inventory]

    for b in daily_bookings:
        room_no = b.get('room_no', '').strip()
        requested_rooms = [r.strip().title() for r in room_no.split(',') if r.strip()]
        booking_id = b.get('booking_id', 'Unknown')

        if not requested_rooms:
            overbookings.append(b)
            continue

        valid_rooms = []
        for r in requested_rooms:
            if r.lower() in inventory_lower:
                valid_rooms.append(inventory[inventory_lower.index(r.lower())])
            else:
                overbookings.append(b)
                logging.warning(f"Overbooking: {booking_id} - invalid room {r}")
                break
        else:
            valid_rooms.sort()
            days = b.get('days', 1) or 1
            per_night_per_room = b.get('receivable', 0.0) / len(valid_rooms) / days

            base_pax = b['total_pax'] // len(valid_rooms)
            remainder_pax = b['total_pax'] % len(valid_rooms)

            if len(valid_rooms) == 1:
                b['inventory_no'] = valid_rooms
                b['per_night'] = per_night_per_room
                b['is_primary'] = True
                assigned.append(b)
            else:
                for idx, inv in enumerate(valid_rooms):
                    new_b = b.copy()
                    new_b['inventory_no'] = [inv]
                    new_b['room_no'] = inv
                    new_b['total_pax'] = base_pax + (1 if idx < remainder_pax else 0)
                    new_b['per_night'] = per_night_per_room
                    new_b['is_primary'] = (idx == 0)
                    assigned.append(new_b)

    return assigned, overbookings

def create_inventory_table(assigned_bookings: List[Dict], overbookings: List[Dict], property: str) -> pd.DataFrame:
    columns = [
        "Inventory No", "Room No", "Booking ID", "Guest Name", "Mobile No", "Total Pax",
        "Check In", "Check Out", "Days", "MOB", "Room Charges", "GST", "Total",
        "Commision", "Receivable", "Per Night", "Advance", "Advance Mop", "Balance",
        "Balance Mop", "Plan", "Booking Status", "Payment Status", "Submitted by",
        "Modified by", "Remarks"
    ]
    inventory = [i for i in PROPERTY_INVENTORY.get(property, {}).get("all", []) if not i.startswith(("Day Use", "No Show"))]
    df_data = []
    for inv in inventory:
        row = {col: "" for col in columns}
        row["Inventory No"] = inv
        booking = next((b for b in assigned_bookings if inv in b.get("inventory_no", [])), None)
        if booking:
            row.update({
                "Room No": booking["room_no"],
                "Booking ID": format_booking_id(booking),
                "Guest Name": booking["guest_name"],
                "Mobile No": booking["mobile_no"],
                "Total Pax": booking["total_pax"],
                "Check In": booking["check_in"],
                "Check Out": booking["check_out"],
                "Days": booking["days"],
                "MOB": booking["mob"],
                "Plan": booking["plan"],
                "Booking Status": booking["booking_status"],
                "Payment Status": booking["payment_status"],
                "Submitted by": booking["submitted_by"],
                "Modified by": booking["modified_by"],
                "Remarks": booking["remarks"],
                "Per Night": f"{booking.get('per_night', 0):.2f}"
            })
            if booking.get('is_primary', False):
                row.update({
                    "Room Charges": f"{booking.get('room_charges', 0):.2f}",
                    "GST": f"{booking.get('gst', 0):.2f}",
                    "Total": f"{booking.get('total', 0):.2f}",
                    "Commision": f"{booking.get('commission', 0):.2f}",
                    "Receivable": f"{booking.get('receivable', 0):.2f}",
                    "Advance": f"{booking.get('advance', 0):.2f}",
                    "Advance Mop": booking.get("advance_mop", ""),
                    "Balance": f"{booking.get('balance', 0):.2f}",
                    "Balance Mop": booking.get("balance_mop", "")
                })
        df_data.append(row)

    if overbookings:
        overbooking_ids = ", ".join(format_booking_id(b) for b in overbookings)
        overbooking_str = ", ".join(f"{b.get('room_no', '')} ({b.get('booking_id', '')})" for b in overbookings)
        df_data.append({
            "Inventory No": "Overbookings", "Room No": overbooking_str, "Booking ID": overbooking_ids,
            **{col: "" for col in columns[3:]}
        })
    return pd.DataFrame(df_data, columns=columns)

def compute_mop_report(daily_bookings: List[Dict], target_date: date) -> pd.DataFrame:
    mop_types = ["UPI", "Cash", "Go-MMT", "Agoda", "NOT PAID", "Expenses", "Bank Transfer", "Stayflexi", "Card Payment", "Expedia", "Cleartrip", "Website"]
    mop_data = {mop: 0.0 for mop in mop_types}
    total_cash = 0.0
    total = 0.0
    for b in daily_bookings:
        if not (b.get('is_primary', False) and date.fromisoformat(b["check_in"]) == target_date):
            continue
        advance_mop = sanitize_string(b.get("advance_mop", ""))
        balance_mop = sanitize_string(b.get("balance_mop", ""))
        advance = safe_float(b.get("advance", 0.0))
        balance = safe_float(b.get("balance", 0.0))
        for standard_mop, variants in mop_mapping.items():
            if advance_mop in variants:
                mop_data[standard_mop] += advance
                total += advance
                if standard_mop == "Cash":
                    total_cash += advance
            if balance_mop in variants:
                mop_data[standard_mop] += balance
                total += balance
                if standard_mop == "Cash":
                    total_cash += balance
    mop_data["Expenses"] = 0.0
    mop_data["Total Cash"] = total_cash
    mop_data["Total"] = total
    return pd.DataFrame([{"MOP": mop, "Amount": f"{amount:.2f}"} for mop, amount in mop_data.items()], columns=["MOP", "Amount"])

def compute_statistics(bookings: List[Dict], property: str, target_date: date, month_dates: List[date]) -> tuple:
    mob_types = ["Booking", "Direct", "Bkg-Direct", "Agoda", "Go-MMT", "Walk-In", "TIE Group", "Stayflexi", "Airbnb", "Social Media", "Expedia", "Cleartrip", "Website"]
    inventory = PROPERTY_INVENTORY.get(property, {"all": []})["all"]
    total_inventory = len([i for i in inventory if not i.startswith(("Day Use", "No Show"))])
    dtd_data = {mob: {"rooms": 0, "value": 0.0, "arr": 0.0, "comm": 0.0} for mob in mob_types}
    total_rooms = total_value = total_pax = total_gst = total_comm = 0
    daily_assigned, _ = assign_inventory_numbers(filter_bookings_for_day(bookings, target_date), property)
    for b in daily_assigned:
        raw_mob = sanitize_string(b.get("mob", "Unknown"))
        mob = next((m for m, v in mob_mapping.items() if raw_mob.upper() in [x.upper() for x in v]), "Booking")
        rooms = len(b.get("inventory_no", []))
        value = b.get("receivable", 0.0) if b.get("is_primary", False) and date.fromisoformat(b["check_in"]) == target_date else 0.0
        comm = b.get("commission", 0.0) if b.get("is_primary", False) and date.fromisoformat(b["check_in"]) == target_date else 0.0
        dtd_data[mob]["rooms"] += rooms
        dtd_data[mob]["value"] += value
        dtd_data[mob]["comm"] += comm
        total_rooms += rooms
        total_value += value
        total_pax += b.get("total_pax", 0)
        total_gst += b.get("gst", 0.0) if b.get("is_primary", False) and date.fromisoformat(b["check_in"]) == target_date else 0.0
        total_comm += comm
    for mob in mob_types:
        rooms = dtd_data[mob]["rooms"]
        dtd_data[mob]["arr"] = dtd_data[mob]["value"] / rooms if rooms > 0 else 0.0
    dtd_data["Total"] = {"rooms": total_rooms, "value": total_value, "arr": total_value / total_rooms if total_rooms > 0 else 0.0, "comm": total_comm}
    dtd_df = pd.DataFrame([{"MOB": mob, "D.T.D Rooms": d["rooms"], "D.T.D Value": f"{d['value']:.2f}", "D.T.D ARR": f"{d['arr']:.2f}", "D.T.D Comm": f"{d['comm']:.2f}"} for mob, d in dtd_data.items()], columns=["MOB", "D.T.D Rooms", "D.T.D Value", "D.T.D ARR", "D.T.D Comm"])

    mtd_rooms = mtd_value = mtd_pax = mtd_gst = mtd_comm = 0
    mtd_data = {mob: {"rooms": 0, "value": 0.0, "arr": 0.0, "comm": 0.0} for mob in mob_types}
    for day in month_dates:
        if day > target_date: continue
        daily_b = filter_bookings_for_day(bookings, day)
        daily_a, _ = assign_inventory_numbers(daily_b, property)
        for b in daily_a:
            raw_mob = sanitize_string(b.get("mob", "Unknown"))
            mob = next((m for m, v in mob_mapping.items() if raw_mob.upper() in [x.upper() for x in v]), "Booking")
            rooms = len(b.get("inventory_no", []))
            value = b.get("receivable", 0.0) if b.get("is_primary", False) and date.fromisoformat(b["check_in"]) == day else 0.0
            comm = b.get("commission", 0.0) if b.get("is_primary", False) and date.fromisoformat(b["check_in"]) == day else 0.0
            mtd_data[mob]["rooms"] += rooms
            mtd_data[mob]["value"] += value
            mtd_data[mob]["comm"] += comm
            mtd_rooms += rooms
            mtd_value += value
            mtd_pax += b.get("total_pax", 0)
            mtd_gst += b.get("gst", 0.0) if b.get("is_primary", False) and date.fromisoformat(b["check_in"]) == day else 0.0
            mtd_comm += comm
    for mob in mob_types:
        rooms = mtd_data[mob]["rooms"]
        mtd_data[mob]["arr"] = mtd_data[mob]["value"] / rooms if rooms > 0 else 0.0
    mtd_data["Total"] = {"rooms": mtd_rooms, "value": mtd_value, "arr": mtd_value / mtd_rooms if mtd_rooms > 0 else 0.0, "comm": mtd_comm}
    mtd_df = pd.DataFrame([{"MOB": mob, "M.T.D Rooms": d["rooms"], "M.T.D Value": f"{d['value']:.2f}", "M.T.D ARR": f"{d['arr']:.2f}", "M.T.D Comm": f"{d['comm']:.2f}"} for mob, d in mtd_data.items()], columns=["MOB", "M.T.D Rooms", "M.T.D Value", "M.T.D ARR", "M.T.D Comm"])

    summary = {
        "rooms_sold": total_rooms,
        "value": total_value,
        "arr": total_value / total_rooms if total_rooms > 0 else 0.0,
        "occ_percent": (total_rooms / total_inventory * 100) if total_inventory > 0 else 0.0,
        "total_pax": total_pax,
        "total_inventory": total_inventory,
        "gst": total_gst,
        "commission": total_comm,
        "tax_deduction": total_value * 0.003,
        "mtd_occ_percent": min((mtd_rooms / (total_inventory * target_date.day) * 100) if total_inventory > 0 and target_date.day > 0 else 0.0, 100.0),
        "mtd_pax": mtd_pax,
        "mtd_rooms": mtd_rooms,
        "mtd_gst": mtd_gst,
        "mtd_tax_deduction": mtd_value * 0.003,
        "mtd_value": mtd_value
    }
    mop_df = compute_mop_report(daily_assigned, target_date)
    return dtd_df, mtd_df, summary, mop_df

@st.cache_data
def cached_load_properties():
    return load_properties()

@st.cache_data
def cached_load_bookings(property, start_date, end_date):
    return load_combined_bookings(property, start_date, end_date)

def show_daily_status():
    st.title("Daily Status")
    if st.button("Refresh Property List"):
        st.cache_data.clear()
        st.rerun()
    current_year = date.today().year
    year = st.selectbox("Select Year", list(range(current_year - 5, current_year + 6)), index=5)
    month = st.selectbox("Select Month", list(range(1, 13)), index=date.today().month - 1)
    properties = cached_load_properties()
    if not properties:
        st.info("No properties available.")
        return
    st.subheader("Properties")
    st.markdown(TABLE_CSS, unsafe_allow_html=True)
    for prop in properties:
        with st.expander(f"{prop}"):
            month_dates = generate_month_dates(year, month)
            start_date = month_dates[0]
            end_date = month_dates[-1]
            bookings = cached_load_bookings(prop, start_date, end_date)
            for day in month_dates:
                daily_bookings = filter_bookings_for_day(bookings, day)
                st.subheader(f"{prop} - {day.strftime('%B %d, %Y')}")
                if daily_bookings:
                    assigned, overbookings = assign_inventory_numbers(daily_bookings, prop)
                    df = create_inventory_table(assigned, overbookings, prop)
                    if 'Booking ID' in df.columns:
                        df['Booking ID'] = df['Booking ID'].apply(lambda x: f'<span style="font-size: 0.75em;">{x.split(">")[1].split("</a>")[0] if ">" in str(x) else x}</span>')
                    tooltip_cols = ['Guest Name', 'Room No', 'Remarks', 'Mobile No', 'MOB', 'Plan', 'Submitted by', 'Modified by']
                    for col in tooltip_cols:
                        if col in df.columns:
                            df[col] = df[col].apply(lambda x: f'<span title="{x}">{x}</span>' if isinstance(x, str) else x)
                    table_html = df.to_html(escape=False, index=False)
                    st.markdown(f'<div class="custom-scrollable-table">{table_html}</div>', unsafe_allow_html=True)
                    dtd_df, mtd_df, summary, mop_df = compute_statistics(bookings, prop, day, month_dates)
                    col1, col2, col3, col4 = st.columns(4)
                    with col1: st.subheader("MOP Report"); st.dataframe(mop_df, use_container_width=True)
                    with col2: st.subheader("D.T.D"); st.dataframe(dtd_df, use_container_width=True)
                    with col3: st.subheader("M.T.D"); st.dataframe(mtd_df, use_container_width=True)
                    with col4:
                        st.subheader("Summary")
                        st.dataframe(pd.DataFrame([
                            {"Metric": k.replace("_", " ").title(), "Value": f"{v:.2f}" if isinstance(v, float) else v}
                            for k, v in summary.items()
                        ]), use_container_width=True)
                else:
                    st.info("No active bookings on this day.")
