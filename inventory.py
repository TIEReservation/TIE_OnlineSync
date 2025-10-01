import streamlit as st
from supabase import create_client, Client
from datetime import date, timedelta
import calendar
import pandas as pd
from typing import Any, List, Dict  # Type hints for function signatures

# Initialize Supabase client
supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])

# Property synonym mapping
property_mapping = {
    "La Millionaire Luxury Resort": "La Millionaire Resort",
}
reverse_mapping = {}
for variant, canonical in property_mapping.items():
    reverse_mapping.setdefault(canonical, []).append(variant)

# Table CSS for non-wrapping, scrollable table
TABLE_CSS = """
<style>
/* Styles for non-wrapping, scrollable table in daily status */
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
    "Le Poshe Beach View": {
        "all": ["101", "102", "201", "202", "203", "204", "301", "302", "303", "304", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": ["203", "204"]
    },
    "La Millionaire Resort": {
        "all": ["101", "102", "103", "105", "201", "202", "203", "204", "205", "206", "207", "208", "301", "302", "303", "304", "305", "306", "307", "308", "401", "402", "Day Use 1", "Day Use 2", "Day Use 3", "Day Use 4", "No Show"],
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
            st.warning(f"Added fallback inventory for unknown property: {prop}")

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
                canonical = property_mapping.get(prop, prop)
                properties.add(canonical)
        for r in res_online:
            prop = r['property']
            if prop:
                canonical = property_mapping.get(prop, prop)
                properties.add(canonical)
        properties = sorted(properties)
        initialize_property_inventory(properties)
        return properties
    except Exception as e:
        st.error(f"Error loading properties: {e}")
        return []

def sanitize_string(value: Any, default: str = "Unknown") -> str:
    """Convert value to string, handling None and non-string types."""
    return str(value) if value is not None else default

def normalize_booking(booking: Dict, is_online: bool) -> Dict:
    """Normalize booking dict to common schema."""
    # Sanitize inputs to prevent f-string and HTML issues
    booking_id = sanitize_string(booking.get('booking_id'))
    payment_status = sanitize_string(booking.get('payment_status')).title()
    if payment_status not in ["Fully Paid", "Partially Paid"]:
        st.warning(f"Skipping booking {booking_id} with invalid payment status: {payment_status}")
        return None
    booking_status_field = 'booking_status' if is_online else 'plan_status'
    booking_status = sanitize_string(booking.get(booking_status_field))
    try:
        normalized = {
            'booking_id': booking_id,
            'room_no': sanitize_string(booking.get('room_no')),
            'guest_name': sanitize_string(booking.get('guest_name')),
            'mobile_no': sanitize_string(booking.get('guest_phone') if is_online else booking.get('mobile_no')),
            'total_pax': booking.get('total_pax'),
            'check_in': date.fromisoformat(booking.get('check_in')) if booking.get('check_in') else None,
            'check_out': date.fromisoformat(booking.get('check_out')) if booking.get('check_out') else None,
            'booking_status': booking_status,
            'payment_status': payment_status,
            'remarks': sanitize_string(booking.get('remarks')),
            'type': 'online' if is_online else 'direct'
        }
        if not normalized['check_in'] or not normalized['check_out']:
            st.warning(f"Skipping booking {booking_id} with missing check-in/check-out dates")
            return None
        return normalized
    except Exception as e:
        st.error(f"Error normalizing booking {booking_id}: {sanitize_string(e)}")
        return None

def load_combined_bookings(property: str, start_date: date, end_date: date) -> List[Dict]:
    """Load bookings overlapping the date range for the property with paid statuses."""
    try:
        variants = [property] + reverse_mapping.get(property, [])
        start_str = start_date.isoformat()
        end_str = end_date.isoformat()
        direct = supabase.table("reservations").select("*").in_("property_name", variants)\
            .lte("check_in", end_str).gt("check_out", start_str)\
            .in_("payment_status", ["Fully Paid", "Partially Paid"])\
            .in_("plan_status", ["Confirmed", "Completed"]).execute().data
        st.info(f"Fetched {len(direct)} direct bookings for {property} from {start_str} to {end_str}")
        online = supabase.table("online_reservations").select("*").in_("property", variants)\
            .lte("check_in", end_str).gt("check_out", start_str)\
            .in_("payment_status", ["Fully Paid", "Partially Paid"])\
            .in_("booking_status", ["Confirmed", "Completed"]).execute().data
        st.info(f"Fetched {len(online)} online bookings for {property} from {start_str} to {end_str}")
        normalized = [b for b in [normalize_booking(b, False) for b in direct] + [normalize_booking(b, True) for b in online] if b]
        if len(normalized) < len(direct) + len(online):
            st.warning(f"Skipped {len(direct) + len(online) - len(normalized)} bookings with invalid data for {property}")
        return normalized
    except Exception as e:
        st.error(f"Error loading bookings for {property}: {e}")
        return []

def filter_bookings_for_day(bookings: List[Dict], day: date) -> List[Dict]:
    """Filter bookings active on the given day."""
    return [b for b in bookings if b['check_in'] and b['check_out'] and b['check_in'] <= day < b['check_out']]

def generate_month_dates(year: int, month: int) -> List[date]:
    """Generate all dates in the month."""
    _, num_days = calendar.monthrange(year, month)
    return [date(year, month, d) for d in range(1, num_days + 1)]

def is_special_category(room_no: str) -> bool:
    """Check if room number is a special category (No Show or Day Use)."""
    return room_no in ["No Show", "Day Use 1", "Day Use 2", "Day Use 3", "Day Use 4"]

def parse_inventory_numbers(room_no: str, property: str, available: List[str], three_bedroom: List[str]) -> tuple[List[str], List[str]]:
    """Parse and validate inventory numbers from room_no, handling comma-separated values, ranges like '101to103', and combined rooms like '101&102'."""
    valid = []
    invalid = []
    # Split on commas first, then handle ampersands within each part
    parts = room_no.split(",") if "," in room_no else [room_no]
    nums = []
    for part in parts:
        part = part.strip()
        # Handle ampersand-separated rooms (e.g., "101&102" -> ["101", "102"])
        if "&" in part:
            nums.extend([n.strip() for n in part.split("&")])
        else:
            nums.append(part)
    for num in nums:
        # Handle range format like '101to103'
        if 'to' in num:
            try:
                start, end = num.split('to')
                start = start.strip()
                end = end.strip()
                # Ensure both start and end are numeric and in the same format
                if start.isdigit() and end.isdigit():
                    start_num = int(start)
                    end_num = int(end)
                    # Generate all room numbers in the range (inclusive)
                    for i in range(start_num, end_num + 1):
                        room = str(i)
                        if is_special_category(room):
                            valid.append(room)
                        elif room in ['D1', 'D2', 'D3', "D4", "D5"] and three_bedroom:
                            inv = three_bedroom.pop(0) if three_bedroom else room
                            valid.append(inv)
                            if inv in available:
                                available.remove(inv)
                        elif room in available:
                            valid.append(room)
                            available.remove(room)
                        else:
                            invalid.append(room)
                else:
                    invalid.append(num)
            except ValueError:
                invalid.append(num)
        else:
            if is_special_category(num):
                valid.append(num)
            elif num in ['D1', 'D2', 'D3', "D4", "D5"] and three_bedroom:
                inv = three_bedroom.pop(0) if three_bedroom else num
                valid.append(inv)
                if inv in available:
                    available.remove(inv)
            elif num in available:
                valid.append(num)
                available.remove(num)
            else:
                invalid.append(num)
    return valid, invalid

def assign_inventory_numbers(bookings: List[Dict], property: str) -> tuple[List[Dict], List[Dict]]:
    """Assign inventory numbers to bookings, handling unknown properties."""
    warnings = []
    assigned = []
    overbookings = []
    fallback = {"all": ["Unknown"], "three_bedroom": []}
    inventory = PROPERTY_INVENTORY.get(property, fallback)
    if property not in PROPERTY_INVENTORY:
        warnings.append(f"Unknown property {property}; using fallback inventory")
    available = [n for n in inventory["all"] if not is_special_category(n)]
    available_three_bedroom = sorted(inventory["three_bedroom"])
    used_inventory = {}
    for booking in bookings:
        booking_id = booking.get('booking_id', 'Unknown')
        valid_nums, invalid_nums = parse_inventory_numbers(booking['room_no'], property, available, available_three_bedroom)
        booking['inventory_no'] = valid_nums
        if invalid_nums:
            warnings.append(f"Invalid inventory numbers {', '.join(invalid_nums)} for {property}, booking {booking_id}")
            overbookings.append(booking)
        for inv in valid_nums:
            if inv in used_inventory:
                overbookings.append(booking)
                overbookings.append(used_inventory[inv])
                del used_inventory[inv]
            else:
                used_inventory[inv] = booking
        if not valid_nums and not invalid_nums:
            overbookings.append(booking)
    assigned = list(used_inventory.values())
    if warnings:
        st.warning("\n".join(warnings))
    return assigned, overbookings

def create_inventory_table(assigned: List[Dict], overbookings: List[Dict], property: str) -> pd.DataFrame:
    """Create a DataFrame with inventory numbers, bookings, and overbookings with hyperlinks."""
    columns = ["Inventory No", "Room No", "Booking ID", "Guest Name", "Mobile No", "Total Pax",
               "Check-in Date", "Check-out Date", "Days", "Booking Status", "Payment Status", "Remarks"]
    fallback = {"all": ["Unknown"], "three_bedroom": []}
    inventory = PROPERTY_INVENTORY.get(property, fallback)
    df_data = [{col: "" for col in columns} for _ in inventory["all"]]
    for i, inv in enumerate(inventory["all"]):
        df_data[i]["Inventory No"] = inv
    # Fill assigned bookings
    for b in assigned:
        for inv in b['inventory_no']:
            for row in df_data:
                if row["Inventory No"] == inv:
                    row.update({
                        "Room No": sanitize_string(b["room_no"]),
                        "Booking ID": format_booking_id(b),
                        "Guest Name": sanitize_string(b["guest_name"]),
                        "Mobile No": sanitize_string(b["mobile_no"]),
                        "Total Pax": sanitize_string(b["total_pax"]),
                        "Check-in Date": b["check_in"],
                        "Check-out Date": b["check_out"],
                        "Days": (b["check_out"] - b["check_in"]).days if b["check_in"] and b["check_out"] else "",
                        "Booking Status": sanitize_string(b["booking_status"]),
                        "Payment Status": sanitize_string(b["payment_status"]),
                        "Remarks": sanitize_string(b["remarks"])
                    })
    # Add overbookings row with hyperlinks
    if overbookings:
        overbooking_ids = ", ".join(format_booking_id(b) for b in overbookings)
        overbooking_str = ", ".join(f"{sanitize_string(b['room_no'])} ({sanitize_string(b['booking_id'])}, {sanitize_string(b['guest_name'])})" for b in overbookings)
        df_data.append({"Inventory No": "Overbookings", "Room No": overbooking_str, "Booking ID": overbooking_ids,
                        "Guest Name": "", "Mobile No": "", "Total Pax": "", "Check-in Date": "", "Check-out Date": "",
                        "Days": "", "Booking Status": "", "Payment Status": "", "Remarks": ""})
    return pd.DataFrame(df_data, columns=columns)

@st.cache_data
def cached_load_properties():
    return load_properties()

@st.cache_data
def cached_load_bookings(property, start_date, end_date):
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
            end_date = month_dates[-1] + timedelta(days=1)
            bookings = cached_load_bookings(prop, start_date, end_date - timedelta(days=1))
            st.info(f"Total bookings for {prop}: {len(bookings)}")
            for day in month_dates:
                daily_bookings = filter_bookings_for_day(bookings, day)
                st.subheader(f"{prop} - {day.strftime('%B %d, %Y')}")
                if daily_bookings:
                    daily_bookings, overbookings = assign_inventory_numbers(daily_bookings, prop)
                    df = create_inventory_table(daily_bookings, overbookings, prop)
                    tooltip_columns = ['Guest Name', 'Room No', 'Remarks', 'Mobile No']
                    for col in tooltip_columns:
                        if col in df.columns:
                            df[col] = df[col].apply(lambda x: f'<span title="{x}">{x}</span>' if isinstance(x, str) else x)
                    table_html = df.to_html(escape=False, index=False)
                    st.markdown(f'<div class="custom-scrollable-table">{table_html}</div>', unsafe_allow_html=True)
                else:
                    st.info("No active bookings on this day.")
