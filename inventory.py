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
reverse_mapping = {}
for variant, canonical in property_mapping.items():
    reverse_mapping.setdefault(canonical, []).append(variant)

# Table CSS for non-wrapping, scrollable table
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
    max-width: 300px;
    padding: 8px;
    border: 1px solid #ddd;
}
</style>
"""

# Property inventory mapping
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
    """Add missing properties to PROPERTY_INVENTORY with fallback inventory."""
    fallback = {"all": ["Unknown"], "three_bedroom": []}
    for prop in properties:
        if prop not in PROPERTY_INVENTORY:
            PROPERTY_INVENTORY[prop] = fallback
            logging.warning(f"Added fallback inventory for unknown property: {prop}")

def format_booking_id(booking: Dict) -> str:
    """Format booking ID as a clickable hyperlink."""
    booking_id = sanitize_string(booking.get('booking_id'))
    return f'<a target="_blank" href="/?edit_type={booking["type"]}&booking_id={booking_id}">{booking_id}</a>'

def load_properties() -> List[str]:
    """Load unique properties from reservations and online_reservations tables."""
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
    """Convert value to string, handling None and non-string types."""
    return str(value).strip() if value is not None else default

def safe_int(value: Any, default: int = 0) -> int:
    """Safely convert value to int, return default if conversion fails."""
    try:
        return int(value) if value is not None else default
    except (ValueError, TypeError):
        return default

def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float, return default if conversion fails."""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default

def normalize_booking(booking: Dict, is_online: bool) -> Dict:
    """Normalize booking dict to common schema, silently skipping invalid bookings."""
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
            if days < 0:
                logging.warning(f"Skipping booking {booking_id} due to negative duration: check_in={check_in}, check_out={check_out}")
                return None
            if days == 0:
                days = 1  # Treat same-day bookings as 1 day
        room_nights = safe_int(booking.get('room_nights', 0))
        if room_nights and room_nights != days:
            logging.warning(f"Booking {booking_id} has room_nights={room_nights} but calculated days={days}")
        property_name = sanitize_string(booking.get('property', booking.get('property_name', '')))
        property_name = property_mapping.get(property_name, property_name)
        guest_name = sanitize_string(booking.get('guest_name', ''))
        mobile_no = sanitize_string(booking.get('guest_phone', booking.get('mobile_no', '')))
        total_pax = safe_int(booking.get('total_pax', 0))
        room_no = sanitize_string(booking.get('room_no', '')).title()  # Normalize case
        room_type = sanitize_string(booking.get('room_type', ''))
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
        per_night = receivable / days if days else 0.0
        booking_type = "online" if is_online else "direct"
        normalized = {
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
            "room_type": room_type,
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
        logging.info(f"Normalized booking {booking_id} for property {property_name}, room_no: {room_no}, check_in: {check_in}, check_out: {check_out}, days: {days}")
        return normalized
    except ValueError as e:
        logging.warning(f"Skipping booking {booking_id} due to date parsing error: {e}")
        return None

def load_combined_bookings(property: str, start_date: date, end_date: date) -> List[Dict]:
    """Load and combine bookings from both tables for the date range."""
    try:
        query_properties = [property] + reverse_mapping.get(property, [])
        logging.info(f"Querying bookings for property variants: {query_properties}, from {start_date} to {end_date}")
        online_bookings = []
        direct_bookings = []
        # Diagnostic query for specific booking
        if property == "Le Poshe Beach view":
            diag_response = supabase.table("online_reservations").select("*").eq("booking_id", "SFBOOKING_27719_20637").execute()
            if diag_response.data:
                logging.info(f"Diagnostic query found booking SFBOOKING_27719_20637: {diag_response.data}")
            else:
                logging.warning("Diagnostic query did not find booking SFBOOKING_27719_20637")
        for query_property in query_properties:
            # Load online reservations
            online_response = supabase.table("online_reservations").select("*").eq("property", query_property).gte("check_in", str(start_date)).lte("check_out", str(end_date)).execute()
            online_bookings.extend([normalize_booking(b, True) for b in (online_response.data or []) if normalize_booking(b, True)])
            logging.info(f"Retrieved {len(online_response.data or [])} online bookings for {query_property}, {len([b for b in online_bookings if b])} normalized")
            # Load direct reservations
            direct_response = supabase.table("reservations").select("*").eq("property_name", query_property).gte("check_in", str(start_date)).lte("check_out", str(end_date)).execute()
            direct_bookings.extend([normalize_booking(b, False) for b in (direct_response.data or []) if normalize_booking(b, False)])
            logging.info(f"Retrieved {len(direct_response.data or [])} direct bookings for {query_property}, {len([b for b in direct_bookings if b])} normalized")
        combined = [b for b in online_bookings + direct_bookings if b]
        logging.info(f"Total combined bindings for {property}: {len(combined)}")
        return combined
    except Exception as e:
        st.error(f"Error loading bookings for {property}: {e}")
        return []

def generate_month_dates(year: int, month: int) -> List[date]:
    """Generate list of dates for the month."""
    _, num_days = calendar.monthrange(year, month)
    return [date(year, month, day) for day in range(1, num_days + 1)]

def filter_bookings_for_day(bookings: List[Dict], target_date: date) -> List[Dict]:
    """Filter active bookings on target_date, adding target_date for financial display logic."""
    filtered = []
    for b in bookings:
        check_in_str = b["check_in"]
        check_out_str = b["check_out"]
        try:
            check_in = date.fromisoformat(check_in_str) if check_in_str else None
            check_out = date.fromisoformat(check_out_str) if check_out_str else None
            if check_in and check_out:
                if check_in <= target_date <= check_out:
                    b_copy = b.copy()
                    b_copy['target_date'] = target_date
                    filtered.append(b_copy)
                    logging.info(f"Included booking {b.get('booking_id')} for {target_date}: check_in={check_in}, check_out={check_out}")
        except ValueError as e:
            logging.warning(f"Skipping booking {b.get('booking_id', 'Unknown')} due to date parsing error: {e}")
    logging.info(f"Filtered {len(filtered)} bookings for target date {target_date}")
    return filtered

def assign_inventory_numbers(daily_bookings: List[Dict], property: str) -> tuple[List[Dict], List[Dict]]:
    """Assign inventory numbers, handling multi-room bookings with case-insensitive validation."""
    assigned = []
    overbookings = []
    inventory = PROPERTY_INVENTORY.get(property, {"all": []})["all"]
    inventory_lower = [i.lower() for i in inventory]
    for b in daily_bookings:
        room_no = b.get('room_no', '').strip()
        inventory_no = [r.strip().title() for r in room_no.split(',') if r.strip()]
        booking_id = b.get('booking_id', 'Unknown')
        if not inventory_no:
            overbookings.append(b)
            logging.warning(f"Booking {booking_id} moved to overbookings: no valid room_no")
            continue
        valid = all(r.lower() in inventory_lower for r in inventory_no)
        if not valid:
            overbookings.append(b)
            logging.warning(f"Booking {booking_id} moved to overbookings: invalid inventory {inventory_no}")
            continue
        inventory_no = [inventory[inventory_lower.index(r.lower())] for r in inventory_no]
        inventory_no.sort()
        base_pax = b['total_pax'] // len(inventory_no) if inventory_no else 0
        remainder_pax = b['total_pax'] % len(inventory_no) if inventory_no else 0
        days = b.get('days', 1) or 1
        per_night_per_room = b.get('receivable', 0.0) / len(inventory_no) / days if inventory_no else 0.0
        if len(inventory_no) == 1:
            b['inventory_no'] = inventory_no
            b['per_night'] = per_night_per_room
            b['is_primary'] = True
            assigned.append(b)
        else:
            for idx, inv in enumerate(inventory_no):
                new_b = b.copy()
                new_b['inventory_no'] = [inv]
                new_b['room_no'] = inv
                new_b['total_pax'] = base_pax + (1 if idx < remainder_pax else 0)
                new_b['per_night'] = per_night_per_room
                new_b['is_primary'] = (idx == 0)
                assigned.append(new_b)
        logging.info(f"Assigned booking {booking_id} to inventory {inventory_no}")
    logging.info(f"Assigned {len(assigned)} bookings, {len(overbookings)} overbookings for {property}")
    return assigned, overbookings

def create_inventory_table(assigned: List[Dict], overbookings: List[Dict], property: str) -> pd.DataFrame:
    """Create inventory table DataFrame, showing financial fields only for primary room on first date."""
    columns = [
        "Inventory No", "Room No", "Booking ID", "Guest Name", "Mobile No",
        "Total Pax", "Check In", "Check Out", "Days", "MOB", "Room Charges",
        "GST", "Total", "Commision", "Receivable", "Per Night", "Advance",
        "Advance Mop", "Balance", "Balance Mop", "Plan", "Booking Status",
        "Payment Status", "Submitted by", "Modified by", "Remarks"
    ]
    fallback = {"all": ["Unknown"], "three_bedroom": []}
    inventory = PROPERTY_INVENTORY.get(property, fallback)["all"]
    if not inventory:
        st.error(f"No inventory defined for property {property}")
        return pd.DataFrame(columns=columns)
    
    df_data = [{col: "" for col in columns} for _ in inventory]
    for i, inv in enumerate(inventory):
        df_data[i]["Inventory No"] = inv

    financial_fields = ["Room Charges", "GST", "Total", "Commision", "Receivable", 
                       "Advance", "Advance Mop", "Balance"]

    for b in assigned:
        inventory_no = b.get('inventory_no', [])
        booking_id = b.get('booking_id', 'Unknown')
        if not inventory_no or not isinstance(inventory_no, list):
            logging.warning(f"Skipping booking {booking_id} with invalid inventory_no: {inventory_no}")
            continue
        for inv in inventory_no:
            row_indices = [i for i, row in enumerate(df_data) if row["Inventory No"] == inv]
            if not row_indices:
                logging.warning(f"Inventory number {inv} not found in DataFrame for booking {booking_id}")
                continue
            row = df_data[row_indices[0]]
            check_in = date.fromisoformat(b["check_in"]) if b["check_in"] else None
            target_date = b.get('target_date')
            is_first_date = check_in == target_date if check_in and target_date else False
            try:
                row.update({
                    "Inventory No": inv,
                    "Room No": sanitize_string(b.get("room_no", "")),
                    "Booking ID": format_booking_id(b),
                    "Guest Name": sanitize_string(b.get("guest_name", "")),
                    "Mobile No": sanitize_string(b.get("mobile_no", "")),
                    "Total Pax": str(b.get("total_pax", "")),
                    "Check In": b.get("check_in", ""),
                    "Check Out": b.get("check_out", ""),
                    "Days": str(b.get("days", 0)),
                    "MOB": sanitize_string(b.get("mob", "")),
                    "Per Night": f"{b.get('per_night', 0):.2f}" if b.get("per_night") is not None else "0.00",
                    "Plan": sanitize_string(b.get("plan", "")),
                    "Booking Status": sanitize_string(b.get("booking_status", "")),
                    "Payment Status": sanitize_string(b.get("payment_status", "")),
                    "Submitted by": sanitize_string(b.get("submitted_by", "")),
                    "Modified by": sanitize_string(b.get("modified_by", "")),
                    "Remarks": sanitize_string(b.get("remarks", ""))
                })
                if b.get('is_primary', False) and is_first_date:
                    row.update({
                        "Room Charges": f"{b.get('room_charges', 0):.2f}",
                        "GST": f"{b.get('gst', 0):.2f}",
                        "Total": f"{b.get('total', 0):.2f}",
                        "Commision": f"{b.get('commission', 0):.2f}",
                        "Receivable": f"{b.get('receivable', 0):.2f}",
                        "Advance": f"{b.get('advance', 0):.2f}",
                        "Advance Mop": sanitize_string(b.get("advance_mop", "")),
                        "Balance": f"{b.get('balance', 0):.2f}"
                    })
                logging.info(f"Added booking {booking_id} to inventory {inv}")
            except Exception as e:
                st.error(f"Error updating row for inventory {inv} in booking {booking_id}: {e}")
                continue

    if overbookings:
        try:
            overbooking_ids = ", ".join(format_booking_id(b) for b in overbookings)
            overbooking_str = ", ".join(f"{sanitize_string(b.get('room_no', ''))} ({sanitize_string(b.get('booking_id', ''))}, {sanitize_string(b.get('guest_name', ''))})" for b in overbookings)
            df_data.append({
                "Inventory No": "Overbookings",
                "Room No": overbooking_str,
                "Booking ID": overbooking_ids,
                "Guest Name": "",
                "Mobile No": "",
                "Total Pax": "",
                "Check In": "",
                "Check Out": "",
                "Days": "",
                "MOB": "",
                "Room Charges": "",
                "GST": "",
                "Total": "",
                "Commision": "",
                "Receivable": "",
                "Per Night": "",
                "Advance": "",
                "Advance Mop": "",
                "Balance": "",
                "Balance Mop": "",
                "Plan": "",
                "Booking Status": "",
                "Payment Status": "",
                "Submitted by": "",
                "Modified by": "",
                "Remarks": ""
            })
            logging.info(f"Added {len(overbookings)} overbookings to table")
        except Exception as e:
            st.error(f"Error creating overbookings row: {e}")

    return pd.DataFrame(df_data, columns=columns)

def compute_statistics(bookings: List[Dict], property: str, target_date: date, month_dates: List[date]) -> tuple[pd.DataFrame, pd.DataFrame, Dict]:
    """Compute D.T.D and M.T.D statistics for bookings."""
    mob_types = [
        "Booking", "Direct", "Bkg-Direct", "Agoda", "Go-MMT", "Walk-In",
        "TIE Group", "Stayflexi", "Airbnb", "Social Media", "Expedia",
        "Cleartrip", "Website"
    ]
    inventory = PROPERTY_INVENTORY.get(property, {"all": ["Unknown"]})["all"]
    total_inventory = len([inv for inv in inventory if not inv.startswith(("Day Use", "No Show"))])

    # D.T.D calculations
    dtd_data = {mob: {"rooms": 0, "value": 0.0, "arr": 0.0, "comm": 0.0} for mob in mob_types}
    dtd_bookings = filter_bookings_for_day(bookings, target_date)
    dtd_assigned, _ = assign_inventory_numbers(dtd_bookings, property)
    total_rooms = 0
    total_value = 0.0
    total_pax = 0
    total_gst = 0.0
    total_comm = 0.0
    tax_deduction = 0.0  # Assuming 0.3% of value as per example ratio

    for b in dtd_assigned:
        mob = sanitize_string(b.get("mob", "Unknown"))
        if mob not in mob_types:
            mob = "Booking"  # Fallback to Booking
        rooms = len(b.get("inventory_no", []))
        value = b.get("receivable", 0.0) if b.get("is_primary", False) and b.get("target_date") == date.fromisoformat(b["check_in"]) else 0.0
        comm = b.get("commission", 0.0) if b.get("is_primary", False) and b.get("target_date") == date.fromisoformat(b["check_in"]) else 0.0
        dtd_data[mob]["rooms"] += rooms
        dtd_data[mob]["value"] += value
        dtd_data[mob]["comm"] += comm
        total_rooms += rooms
        total_value += value
        total_pax += b.get("total_pax", 0)
        total_gst += b.get("gst", 0.0) if b.get("is_primary", False) and b.get("target_date") == date.fromisoformat(b["check_in"]) else 0.0
        total_comm += comm

    for mob in mob_types:
        rooms = dtd_data[mob]["rooms"]
        dtd_data[mob]["arr"] = dtd_data[mob]["value"] / rooms if rooms > 0 else 0.0

    dtd_data["Total"] = {
        "rooms": total_rooms,
        "value": total_value,
        "arr": total_value / total_rooms if total_rooms > 0 else 0.0,
        "comm": total_comm
    }
    dtd_df = pd.DataFrame(
        [{"MOB": mob, "D.T.D Rooms": data["rooms"], "D.T.D Value": f"{data['value']:.2f}",
          "D.T.D ARR": f"{data['arr']:.2f}", "D.T.D Comm": f"{data['comm']:.2f}"}
         for mob, data in dtd_data.items()],
        columns=["MOB", "D.T.D Rooms", "D.T.D Value", "D.T.D ARR", "D.T.D Comm"]
    )

    # M.T.D calculations
    mtd_data = {mob: {"rooms": 0, "value": 0.0, "arr": 0.0, "comm": 0.0} for mob in mob_types}
    mtd_rooms = 0
    mtd_value = 0.0
    mtd_pax = 0
    mtd_gst = 0.0
    mtd_comm = 0.0
    mtd_tax_deduction = 0.0

    for day in month_dates:
        if day > target_date:
            continue
        daily_bookings = filter_bookings_for_day(bookings, day)
        daily_assigned, _ = assign_inventory_numbers(daily_bookings, property)
        for b in daily_assigned:
            mob = sanitize_string(b.get("mob", "Unknown"))
            if mob not in mob_types:
                mob = "Booking"
            rooms = len(b.get("inventory_no", []))
            value = b.get("receivable", 0.0) if b.get("is_primary", False) and b.get("target_date") == date.fromisoformat(b["check_in"]) else 0.0
            comm = b.get("commission", 0.0) if b.get("is_primary", False) and b.get("target_date") == date.fromisoformat(b["check_in"]) else 0.0
            mtd_data[mob]["rooms"] += rooms
            mtd_data[mob]["value"] += value
            mtd_data[mob]["comm"] += comm
            mtd_rooms += rooms
            mtd_value += value
            mtd_pax += b.get("total_pax", 0)
            mtd_gst += b.get("gst", 0.0) if b.get("is_primary", False) and b.get("target_date") == date.fromisoformat(b["check_in"]) else 0.0
            mtd_comm += comm

    for mob in mob_types:
        rooms = mtd_data[mob]["rooms"]
        mtd_data[mob]["arr"] = mtd_data[mob]["value"] / rooms if rooms > 0 else 0.0

    mtd_data["Total"] = {
        "rooms": mtd_rooms,
        "value": mtd_value,
        "arr": mtd_value / mtd_rooms if mtd_rooms > 0 else 0.0,
        "comm": mtd_comm
    }
    mtd_df = pd.DataFrame(
        [{"MOB": mob, "M.T.D Rooms": data["rooms"], "M.T.D Value": f"{data['value']:.2f}",
          "M.T.D ARR": f"{data['arr']:.2f}", "M.T.D Comm": f"{data['comm']:.2f}"}
         for mob, data in mtd_data.items()],
        columns=["MOB", "M.T.D Rooms", "M.T.D Value", "M.T.D ARR", "M.T.D Comm"]
    )

    # Summary statistics
    summary = {
        "rooms_sold": total_rooms,
        "value": total_value,
        "arr": total_value / total_rooms if total_rooms > 0 else 0.0,
        "occ_percent": (total_rooms / total_inventory * 100) if total_inventory > 0 else 0.0,
        "total_pax": total_pax,
        "total_inventory": total_inventory,
        "gst": total_gst,
        "commission": total_comm,
        "tax_deduction": total_value * 0.003,  # Assuming 0.3% as per example
        "mtd_occ_percent": (mtd_rooms / (total_inventory * (target_date.day)) * 100) if total_inventory > 0 else 0.0,
        "mtd_pax": mtd_pax,
        "mtd_rooms": mtd_rooms,
        "mtd_gst": mtd_gst,
        "mtd_tax_deduction": mtd_value * 0.003,  # Assuming 0.3% as per example
        "mtd_value": mtd_value
    }

    return dtd_df, mtd_df, summary

@st.cache_data
def cached_load_properties():
    return load_properties()

def cached_load_bookings(property, start_date, end_date):
    st.cache_data.clear()
    return load_combined_bookings(property, start_date, end_date)

def show_daily_status():
    """Display daily status table with inventory and bookings."""
    st.title("📅 Daily Status")
    if st.button("🔄 Refresh Property List"):
        st.cache_data.clear()
        st.success("Cache cleared! Refreshing properties...")
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
                    daily_bookings, overbookings = assign_inventory_numbers(daily_bookings, prop)
                    df = create_inventory_table(daily_bookings, overbookings, prop)
                    tooltip_columns = ['Guest Name', 'Room No', 'Remarks', 'Mobile No', 'MOB', 'Plan', 'Submitted by', 'Modified by']
                    for col in tooltip_columns:
                        if col in df.columns:
                            df[col] = df[col].apply(lambda x: f'<span title="{x}">{x}</span>' if isinstance(x, str) else x)
                    table_html = df.to_html(escape=False, index=False)
                    st.markdown(f'<div class="custom-scrollable-table">{table_html}</div>', unsafe_allow_html=True)
                    
                    # Compute and display statistics
                    dtd_df, mtd_df, summary = compute_statistics(bookings, prop, day, month_dates)
                    st.subheader("D.T.D Statistics")
                    st.dataframe(dtd_df, use_container_width=True)
                    st.subheader("M.T.D Statistics")
                    st.dataframe(mtd_df, use_container_width=True)
                    st.subheader("Summary")
                    summary_df = pd.DataFrame([
                        {"Metric": "Rooms Sold", "Value": summary["rooms_sold"]},
                        {"Metric": "Value", "Value": f"{summary['value']:.2f}"},
                        {"Metric": "ARR", "Value": f"{summary['arr']:.2f}"},
                        {"Metric": "Occ%", "Value": f"{summary['occ_percent']:.2f}%"},
                        {"Metric": "Total Pax", "Value": summary["total_pax"]},
                        {"Metric": "Total Inventory", "Value": summary["total_inventory"]},
                        {"Metric": "GST ", "Value": f"{summary['gst']:.2f}"},
                        {"Metric": "Commission", "Value": f"{summary['commission']:.2f}"},
                        {"Metric": "TAX Deduction", "Value": f"{summary['tax_deduction']:.2f}"},
                        {"Metric": "M.T.D Occ %", "Value": f"{summary['mtd_occ_percent']:.2f}%"},
                        {"Metric": "M.T.D Pax", "Value": summary["mtd_pax"]},
                        {"Metric": "M.T.D Rooms", "Value": summary["mtd_rooms"]},
                        {"Metric": "M.T.D GST", "Value": f"{summary['mtd_gst']:.2f}"},
                        {"Metric": "M.T.D Tax Deduc", "Value": f"{summary['mtd_tax_deduction']:.2f}"},
                        {"Metric": "M.T.D Value", "Value": f"{summary['mtd_value']:.2f}"}
                    ])
                    st.dataframe(summary_df, use_container_width=True)
                else:
                    st.info("No active bookings on this day.")
